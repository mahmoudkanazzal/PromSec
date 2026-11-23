from __future__ import annotations
import os
import sys
import yaml
import sqlite3
import requests
import hashlib
import tempfile
from flask import Flask, request, jsonify

TMP_DIR = tempfile.gettempdir()
CONFIG_PATH = "config.yaml"
DB_PATH = "service.db"

app = Flask(__name__)

def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}

def write_temp_file(content: bytes, name: str) -> str:
    path = os.path.join(TMP_DIR, name)
    with open(path, "wb") as f:
        f.write(content)
    return path

def compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT,
        value TEXT
    )""")
    conn.commit()
    return conn

def log_to_db(conn: sqlite3.Connection, key: str, value: str) -> None:
    cur = conn.cursor()
    cur.execute("INSERT INTO logs (key, value) VALUES (?, ?)", (key, value))
    conn.commit()

def fetch_remote(url: str) -> bytes:
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    return resp.content

def process_data(raw: bytes) -> dict:
    h = compute_hash(raw)
    data = {"hash": h, "size": len(raw)}
    return data

def handle_request():
    cfg = load_config(CONFIG_PATH)
    target = cfg.get("remote_url", "https://httpbin.org/get")
    raw = fetch_remote(target)
    temp_path = write_temp_file(raw, "last_response.bin")
    info = process_data(raw)
    db = init_db()
    log_to_db(db, "last_hash", info["hash"])
    return {"temp_file": temp_path, "info": info}

@app.route("/load", methods=["GET"])
def load_endpoint():
    try:
        result = handle_request()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not os.path.isdir(TMP_DIR):
        os.makedirs(TMP_DIR, exist_ok=True)
    app.run(host="127.0.0.1", port=5000)