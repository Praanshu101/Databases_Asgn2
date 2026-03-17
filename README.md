# CS432 Track 1 Submission (Assignment 2)

## Structure

- `Module_A/database/`: B+ Tree engine, brute-force baseline, table abstraction, DB manager.
- `Module_A/report.ipynb`: benchmarking + visualisation report template.
- `Module_B/app/`: local Flask UI + API with session validation and RBAC.
- `Module_B/sql/`: schema and indexing scripts.
- `Module_B/logs/audit.log`: security audit trail.
- `Module_B/report.ipynb`: optimisation and security report template.

## Run Module A quick test

```powershell
cd Module_A
python -c "from database.table import Table; t=Table('t'); [t.insert(i, {'v': i}) for i in [5,2,9,1,7]]; print(t.range_query(2,8))"
```

## Run Module B

```powershell
cd Module_B/app
python main.py
```

Open `http://127.0.0.1:5000`.
Default admin is `admin / admin123`.
