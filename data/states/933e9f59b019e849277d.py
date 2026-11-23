from __future__ import annotations
import threading
import time
import json
import hashlib
import sqlite3
import requests
from flask import Flask, request, jsonify
import yaml
import os
CONFIG_PATH = "sync_config.yaml"
DB_PATH = "local.db"

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {"remote_url": "http://localhost:5001", "sync_interval": 30}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, data TEXT, hash TEXT)""")
    conn.commit()
    conn.close()

def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def get_local_records() -> dict:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, data, hash FROM records")
    rows = c.fetchall()
    conn.close()
    return {row[0]: {"data": row[1], "hash": row[2]} for row in rows}

def upsert_local_record(rec_id: str, data: str) -> None:
    h = compute_hash(data)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO records (id, data, hash) VALUES (?, ?, ?)", (rec_id, data, h))
    conn.commit()
    conn.close()

def fetch_remote_records(remote_url: str) -> dict:
    try:
        r = requests.get(f"{remote_url}/records", timeout=5)
        return r.json()
    except Exception:
        return {}

def push_local_changes(remote_url: str) -> None:
    local = get_local_records()
    for rec_id, rec in local.items():
        try:
            requests.post(f"{remote_url}/record", json={"id": rec_id, "data": rec["data"]}, timeout=5)
        except Exception:
            pass

def sync_once(config: dict) -> None:
    remote = config["remote_url"]
    remote_recs = fetch_remote_records(remote)
    for rec_id, rec in remote_recs.items():
        local = get_local_records().get(rec_id)
        if not local or local["hash"] != compute_hash(rec["data"]):
            upsert_local_record(rec_id, rec["data"])
    push_local_changes(remote)

def sync_loop(config: dict) -> None:
    interval = config.get("sync_interval", 30)
    while True:
        sync_once(config)
        time.sleep(interval)

app = Flask(__name__)

@app.route("/records", methods=["GET"])
def api_get_records():
    return jsonify(get_local_records())

@app.route("/record", methods=["POST"])
def api_post_record():
    payload = request.get_json()
    rec_id = payload.get("id")
    data = payload.get("data", "")
    if rec_id:
        upsert_local_record(rec_id, data)
        return jsonify({"status": "ok"}), 200
    return jsonify({"error": "missing id"}), 400

def start_server():
    app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    cfg = load_config()
    init_db()
    t = threading.Thread(target=sync_loop, args=(cfg,), daemon=True)
    t.start()
    start_server()