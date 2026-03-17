from __future__ import annotations

import json
import time
import uuid
from functools import wraps
from pathlib import Path

from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import apply_indexes, get_connection, init_db

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parents[0]
LOG_PATH = BASE_DIR / "logs" / "audit.log"

app = Flask(__name__)
app.secret_key = "change-me-in-production"


@app.before_request
def start_timer() -> None:
    g.request_start = time.perf_counter()


@app.after_request
def append_timing_header(response):
    elapsed_ms = (time.perf_counter() - g.request_start) * 1000
    response.headers["X-Response-Time-ms"] = f"{elapsed_ms:.3f}"
    return response


def _write_log_line(payload: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=True) + "\n")


def audit(event_type: str, status: str, target_table: str | None = None, target_id: int | None = None, details: str = "") -> None:
    actor = session.get("username")
    role = session.get("role")
    request_id = str(uuid.uuid4())

    payload = {
        "event_type": event_type,
        "status": status,
        "actor": actor,
        "role": role,
        "target_table": target_table,
        "target_id": target_id,
        "details": details,
        "request_id": request_id,
        "ts": time.time(),
    }

    _write_log_line(payload)

    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO audit_log(event_type, actor, role, target_table, target_id, details, status, request_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (event_type, actor, role, target_table, target_id, details, status, request_id),
        )
    conn.close()


def require_login(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return view(*args, **kwargs)

    return wrapper


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            audit("rbac_denied", "blocked", details="Admin role required")
            return jsonify({"error": "Admin role required"}), 403
        return view(*args, **kwargs)

    return wrapper


def _set_audit_context(conn, request_id: str) -> None:
    with conn:
        conn.execute(
            """
            INSERT INTO audit_context(id, actor, request_id, session_token)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                actor=excluded.actor,
                request_id=excluded.request_id,
                session_token=excluded.session_token,
                updated_at=CURRENT_TIMESTAMP
            """,
            (session.get("username"), request_id, session.get("session_token")),
        )


def _clear_audit_context(conn) -> None:
    with conn:
        conn.execute("UPDATE audit_context SET actor = NULL, request_id = NULL, session_token = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = 1")


@app.get("/")
def home():
    if "user_id" in session:
        return redirect(url_for("portfolio_page"))
    return render_template("login.html")


@app.post("/login")
def login():
    payload = request.get_json(silent=True) or request.form
    username = payload.get("username", "")
    password = payload.get("password", "")

    conn = get_connection()
    row = conn.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if row is None or not check_password_hash(row["password_hash"], password):
        audit("login", "failed", details=f"Invalid login for '{username}'")
        return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"] = row["id"]
    session["username"] = row["username"]
    session["role"] = row["role"]
    session["session_token"] = str(uuid.uuid4())

    audit("login", "success", details=f"User '{username}' logged in")
    return jsonify({"message": "Logged in", "role": row["role"]})


@app.post("/logout")
@require_login
def logout():
    username = session.get("username")
    session.clear()
    audit("logout", "success", details=f"User '{username}' logged out")
    return jsonify({"message": "Logged out"})


@app.get("/portfolio")
@require_login
def portfolio_page():
    return render_template("portfolio.html", username=session.get("username"), role=session.get("role"))


@app.get("/api/portfolios")
@require_login
def list_portfolios():
    conn = get_connection()

    if session.get("role") == "admin":
        rows = conn.execute(
            "SELECT p.id, p.user_id, u.username, p.full_name, p.email, p.bio, p.skills, p.updated_at "
            "FROM portfolios p JOIN users u ON u.id = p.user_id ORDER BY p.updated_at DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT p.id, p.user_id, u.username, p.full_name, p.email, p.bio, p.skills, p.updated_at "
            "FROM portfolios p JOIN users u ON u.id = p.user_id WHERE p.user_id = ? ORDER BY p.updated_at DESC",
            (session["user_id"],),
        ).fetchall()

    conn.close()
    return jsonify([dict(r) for r in rows])


@app.post("/api/portfolios")
@require_login
def create_portfolio():
    payload = request.get_json(force=True)
    owner_id = payload.get("user_id", session["user_id"])

    if session.get("role") != "admin":
        owner_id = session["user_id"]

    request_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        _set_audit_context(conn, request_id)
        with conn:
            cur = conn.execute(
                """
                INSERT INTO portfolios(user_id, full_name, email, bio, skills, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    owner_id,
                    payload["full_name"],
                    payload["email"],
                    payload.get("bio", ""),
                    payload.get("skills", ""),
                ),
            )
            new_id = cur.lastrowid
        _clear_audit_context(conn)
        audit("create_portfolio", "success", "portfolios", new_id, f"request_id={request_id}")
        return jsonify({"id": new_id}), 201
    except Exception as exc:
        _clear_audit_context(conn)
        audit("create_portfolio", "failed", "portfolios", details=str(exc))
        return jsonify({"error": str(exc)}), 400
    finally:
        conn.close()


@app.put("/api/portfolios/<int:portfolio_id>")
@require_login
def update_portfolio(portfolio_id: int):
    payload = request.get_json(force=True)
    conn = get_connection()
    row = conn.execute("SELECT user_id FROM portfolios WHERE id = ?", (portfolio_id,)).fetchone()

    if row is None:
        conn.close()
        return jsonify({"error": "Portfolio not found"}), 404

    if session.get("role") != "admin" and row["user_id"] != session["user_id"]:
        conn.close()
        audit("update_portfolio", "blocked", "portfolios", portfolio_id, "User tried modifying another profile")
        return jsonify({"error": "Forbidden"}), 403

    request_id = str(uuid.uuid4())
    try:
        _set_audit_context(conn, request_id)
        with conn:
            conn.execute(
                """
                UPDATE portfolios
                SET full_name = ?, email = ?, bio = ?, skills = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    payload["full_name"],
                    payload["email"],
                    payload.get("bio", ""),
                    payload.get("skills", ""),
                    portfolio_id,
                ),
            )
        _clear_audit_context(conn)
        audit("update_portfolio", "success", "portfolios", portfolio_id, f"request_id={request_id}")
        return jsonify({"message": "Updated"})
    except Exception as exc:
        _clear_audit_context(conn)
        audit("update_portfolio", "failed", "portfolios", portfolio_id, str(exc))
        return jsonify({"error": str(exc)}), 400
    finally:
        conn.close()


@app.delete("/api/portfolios/<int:portfolio_id>")
@require_login
def delete_portfolio(portfolio_id: int):
    conn = get_connection()
    row = conn.execute("SELECT user_id FROM portfolios WHERE id = ?", (portfolio_id,)).fetchone()

    if row is None:
        conn.close()
        return jsonify({"error": "Portfolio not found"}), 404

    if session.get("role") != "admin" and row["user_id"] != session["user_id"]:
        conn.close()
        audit("delete_portfolio", "blocked", "portfolios", portfolio_id, "User tried deleting another profile")
        return jsonify({"error": "Forbidden"}), 403

    request_id = str(uuid.uuid4())
    try:
        _set_audit_context(conn, request_id)
        with conn:
            conn.execute("DELETE FROM portfolios WHERE id = ?", (portfolio_id,))
        _clear_audit_context(conn)
        audit("delete_portfolio", "success", "portfolios", portfolio_id, f"request_id={request_id}")
        return jsonify({"message": "Deleted"})
    finally:
        conn.close()


@app.post("/api/members")
@require_login
@require_admin
def create_member():
    payload = request.get_json(force=True)
    request_id = str(uuid.uuid4())
    conn = get_connection()

    try:
        _set_audit_context(conn, request_id)
        with conn:
            cur = conn.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (?, ?, ?)",
                (
                    payload["username"],
                    generate_password_hash(payload.get("password", "changeme")),
                    payload.get("role", "user"),
                ),
            )
            user_id = cur.lastrowid

            group_name = payload.get("group", "default")
            group_row = conn.execute("SELECT id FROM groups WHERE name = ?", (group_name,)).fetchone()
            if group_row is None:
                gcur = conn.execute("INSERT INTO groups(name) VALUES (?)", (group_name,))
                group_id = gcur.lastrowid
            else:
                group_id = group_row["id"]

            conn.execute("INSERT INTO member_group_map(user_id, group_id) VALUES (?, ?)", (user_id, group_id))
        _clear_audit_context(conn)
        audit("create_member", "success", "users", user_id, f"request_id={request_id}")
        return jsonify({"user_id": user_id}), 201
    except Exception as exc:
        _clear_audit_context(conn)
        audit("create_member", "failed", "users", details=str(exc))
        return jsonify({"error": str(exc)}), 400
    finally:
        conn.close()


@app.delete("/api/members/<int:user_id>")
@require_login
@require_admin
def delete_member(user_id: int):
    request_id = str(uuid.uuid4())
    conn = get_connection()

    try:
        _set_audit_context(conn, request_id)
        with conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        _clear_audit_context(conn)
        audit("delete_member", "success", "users", user_id, f"request_id={request_id}")
        return jsonify({"message": "Member deleted"})
    finally:
        conn.close()


@app.get("/api/admin/unauthorized-changes")
@require_login
@require_admin
def unauthorized_changes():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, table_name, operation, row_id, actor, request_id, source, created_at
        FROM db_change_log
        WHERE source = 'DIRECT_DB' OR actor = 'UNAUTHORIZED'
        ORDER BY id DESC
        """
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


def seed_admin() -> None:
    conn = get_connection()
    row = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if row is None:
        with conn:
            conn.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", generate_password_hash("admin123"), "admin"),
            )
    conn.close()


if __name__ == "__main__":
    init_db()
    apply_indexes()
    seed_admin()
    app.run(debug=True, port=5000)
