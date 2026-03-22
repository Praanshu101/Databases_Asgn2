# CS432 Track 1 Submission (Assignment 2)

# Module A

## Structure

- `Module_A/database/`: B+ Tree engine, brute-force baseline, table abstraction, DB manager.
- `Module_A/report.ipynb`: benchmarking + visualisation report template.

## Run Module A quick test

```powershell
cd Module_A
python -c "from database.table import Table; t=Table('t'); [t.insert(i, {'v': i}) for i in [5,2,9,1,7]]; print(t.range_query(2,8))"
```

# Module B – Shuttle System Web App & SQL Optimization


Main components:
- Flask Web App (app.py)
- Database Schema (01_shuttle_system.sql)
- Indexing & Query Optimization (03_indexing.sql)
- Benchmarking (benchmark.py)

---

## Folder Structure
```bash
Module_B/
│
├── app/
│   ├── templates/
│   ├── app.py
│   ├── benchmark.py
│   ├── generate_data.py
│   ├── generate_graph.py
│   └── bottleneck_graph.png
│
├── logs/
│   └── audit.log
│
├── sql/
│   ├── 01_shuttle_system.sql
│   └── 03_indexing.sql
```
---

## Setup Instructions 

### 1. Create Database
First run the shuttle system SQL file:
```bash
mysql -u root -p < sql/01_shuttle_system.sql
```

This will create the database and insert initial data.

Default users already exist in the database:
Username: admin_rahul  
Password: password123

(Default passwords for users created in the database are set to password123. Users created by the admin through the web interface may have different passwords as specified by the admin.)

---

### 2. Run Flask App
Go to app folder and run:
```bash
cd Module_B/app
python app.py
```

Open the website:
http://localhost:5000

---

### 3. Run Benchmark (Before Indexing)
To measure query execution time:
```bash
python benchmark.py
```
This prints average execution time of the main booking query.

---

### 4. Apply Indexing
Run indexing SQL to optimize queries:
```bash
mysql -u root -p shuttle_system < sql/03_indexing.sql
```
This creates indexes to improve query performance.

---

### 5. Run Benchmark Again (After Indexing)
Run again:
```bash
python benchmark.py
```
---

### 6. Generate Dummy Data (Optional part)
If more data is needed:
```bash
python generate_data.py
```
---


## Logs
All security, admin actions, and performance logs are stored in:
logs/audit.log
