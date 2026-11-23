from __future__ import annotations
import sqlite3
import threading
import time
import subprocess
import json
from flask import Flask, request, jsonify

DB_PATH = "scheduler.db"
app = Flask(__name__)

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        command TEXT NOT NULL,
        interval INTEGER NOT NULL,
        last_run INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

def add_task(command: str, interval: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (command, interval, last_run) VALUES (?, ?, ?)",
        (command, interval, 0),
    )
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_all_tasks() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, command, interval, last_run FROM tasks")
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "command": r[1], "interval": r[2], "last_run": r[3]}
        for r in rows
    ]

def update_last_run(task_id: int, timestamp: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET last_run = ? WHERE id = ?", (timestamp, task_id))
    conn.commit()
    conn.close()

def run_task(task_id: int, command: str) -> None:
    try:
        subprocess.Popen(command, shell=True)
        update_last_run(task_id, int(time.time()))
    except Exception:
        pass  # ignore failures for brevity

def scheduler_loop() -> None:
    while True:
        now = int(time.time())
        tasks = get_all_tasks()
        for t in tasks:
            if now - t["last_run"] >= t["interval"]:
                run_task(t["id"], t["command"])
        time.sleep(1)

@app.route("/add", methods=["POST"])
def api_add():
    data = request.get_json(force=True)
    command = data.get("command")
    interval = data.get("interval")
    if not command or not isinstance(interval, int):
        return jsonify({"error": "Invalid data"}), 400
    task_id = add_task(command, interval)
    return jsonify({"id": task_id}), 201

@app.route("/tasks", methods=["GET"])
def api_tasks():
    return jsonify(get_all_tasks())

@app.route("/run/<int:task_id>", methods=["POST"])
def api_run(task_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT command FROM tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Task not found"}), 404
    run_task(task_id, row[0])
    return jsonify({"status": "started"}), 200

def start_scheduler():
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()

if __name__ == "__main__":
    init_db()
    start_scheduler()
    app.run(host="0.0.0.0", port=5000)