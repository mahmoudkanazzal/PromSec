from __future__ import annotations

import os
import json
import sqlite3
import hashlib
import pickle
import datetime
import requests
import yaml
from flask import Flask, jsonify

CONFIG_PATH = "config.yaml"
DB_PATH = "data.db"
TMP_PATH = "/tmp/sync_response.json"
CACHE_PATH = "/tmp/sync_cache.pkl"

app = Flask(__name__)

def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY,
            data TEXT,
            checksum TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def write_temp_file(content: str) -> None:
    with open(TMP_PATH, "w") as f:
        f.write(content)

def load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "rb") as f:
            return pickle.load(f)
    return {}

def save_cache(cache: dict) -> None:
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(cache, f)

def compute_record_hash(record: dict) -> str:
    data = json.dumps(record, sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def fetch_remote_records(api_url: str) -> list[dict]:
    resp = requests.get(api_url, timeout=10, verify=False)
    resp.raise_for_status()
    write_temp_file(resp.text)
    return resp.json()

def sync_records(remote_records: list[dict]) -> dict:
    conn = get_db_connection()
    cur = conn.cursor()
    stats = {"added": 0, "updated": 0}
    for rec in remote_records:
        rec_id = rec.get("id")
        checksum = compute_record_hash(rec)
        cur.execute("SELECT checksum FROM records WHERE id = ?", (rec_id,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO records (id, data, checksum, updated_at) VALUES (?, ?, ?, ?)",
                (rec_id, json.dumps(rec), checksum, datetime.datetime.utcnow().isoformat())
            )
            stats["added"] += 1
        elif row["checksum"] != checksum:
            cur.execute(
                "UPDATE records SET data = ?, checksum = ?, updated_at = ? WHERE id = ?",
                (json.dumps(rec), checksum, datetime.datetime.utcnow().isoformat(), rec_id)
            )
            stats["updated"] += 1
    conn.commit()
    conn.close()
    return stats

def perform_sync() -> dict:
    config = load_config()
    api_url = config.get("api_url", "http://example.com/api/records")
    remote = fetch_remote_records(api_url)
    stats = sync_records(remote)
    cache = {"last_sync": datetime.datetime.utcnow().isoformat(), "stats": stats}
    save_cache(cache)
    return stats

@app.route("/sync", methods=["POST"])
def sync_endpoint():
    try:
        stats = perform_sync()
        return jsonify({"status": "ok", "stats": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def main() -> None:
    init_db()
    stats = perform_sync()
    print(f"Sync completed. Added: {stats['added']}, Updated: {stats['updated']}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        app.run(host="0.0.0.0", port=5000)
    else:
        main()