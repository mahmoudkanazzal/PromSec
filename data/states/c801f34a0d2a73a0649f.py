from __future__ import annotations
import os
import sqlite3
import pickle
import hashlib
import subprocess
from flask import Flask, request, jsonify

DB_PATH = "admin_logs.db"

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            checksum TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

def compute_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def save_log(event: str, checksum: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO logs (event, checksum) VALUES (?, ?)",
        (event, checksum)
    )
    conn.commit()
    conn.close()

def run_audit(event: str) -> str:
    result = subprocess.run(
        ["echo", f"Auditing: {event}"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def process_payload(payload: dict) -> dict:
    event = payload.get("event", "unknown")
    raw = pickle.dumps(payload)
    checksum = compute_checksum(raw)
    save_log(event, checksum)
    audit_result = run_audit(event)
    return {"status": "ok", "event": event, "checksum": checksum, "audit": audit_result}

def handle_upload() -> tuple:
    raw_data = request.data
    try:
        data = pickle.loads(raw_data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid payload"}), 400
    result = process_payload(data)
    return jsonify(result), 200

def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/upload", methods=["POST"])
    def upload():
        return handle_upload()

    @app.route("/logs", methods=["GET"])
    def get_logs():
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id, event, checksum FROM logs ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
        conn.close()
        logs = [{"id": r[0], "event": r[1], "checksum": r[2]} for r in rows]
        return jsonify({"logs": logs}), 200

    return app

if __name__ == "__main__":
    init_db()
    app = create_app()
    app.run(host="0.0.0.0", port=5000)