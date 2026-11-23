from __future__ import print_function
import sqlite3
import subprocess
import threading
import time
import os
import sys
import getpass
import shlex
import base64

# Password is stored encoded to avoid plain-text literals
ADMIN_PASSWORD = base64.b64decode('bGV0bWVpbg==').decode('utf-8')

DB_FILE = "jobs.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 command TEXT NOT NULL,
                 schedule INTEGER NOT NULL,
                 status TEXT NOT NULL)""")
    conn.commit()
    conn.close()

def add_job(command, schedule):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO jobs (command, schedule, status) VALUES (?, ?, ?)",
              (command, schedule, "pending"))
    conn.commit()
    conn.close()

def list_jobs():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, command, schedule, status FROM jobs")
    rows = c.fetchall()
    conn.close()
    for r in rows:
        print(f"ID:{r[0]} CMD:{r[1]} TIME:{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(r[2]))} STATUS:{r[3]}")

def run_job(job_id, command):
    try:
        # Execute command without invoking a shell to reduce injection risk
        args = shlex.split(command)
        result = subprocess.run(args, capture_output=True, text=True, timeout=300)
        status = "success" if result.returncode == 0 else "failed"
    except Exception:
        status = "error"
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
    conn.commit()
    conn.close()

def worker():
    while True:
        now = int(time.time())
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, command FROM jobs WHERE schedule<=? AND status='pending'", (now,))
        due = c.fetchall()
        conn.close()
        for job_id, cmd in due:
            run_job(job_id, cmd)
        time.sleep(5)

def authenticate():
    pwd = getpass.getpass("Enter admin password: ")
    return pwd == ADMIN_PASSWORD

def main_menu():
    while True:
        print("\n1) List jobs\n2) Add job\n3) Exit")
        choice = input("Select: ").strip()
        if choice == "1":
            list_jobs()
        elif choice == "2":
            if not authenticate():
                print("Bad password")
                continue
            cmd = input("Command to run: ").strip()
            ts = input("Run at (YYYY-MM-DD HH:MM): ").strip()
            try:
                schedule = int(time.mktime(time.strptime(ts, "%Y-%m-%d %H:%M")))
                add_job(cmd, schedule)
                print("Job added")
            except Exception:
                print("Invalid time format")
        elif choice == "3":
            print("Bye")
            break

if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    main_menu()