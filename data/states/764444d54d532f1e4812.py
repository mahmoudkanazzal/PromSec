import os
import sys
import json
import hashlib
import sqlite3
import yaml
import requests
from flask import Flask, jsonify, request

CONFIG_FILE = "config.yaml"
DB_FILE = "config.db"
REMOTE_URL = "https://example.com/api/config"

def load_local_config(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}

def fetch_remote_config(url, timeout=5):
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.RequestException:
        return {}
    if resp.status_code == 200:
        return resp.json()
    return {}

def merge_configs(base, override):
    result = base.copy()
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = merge_configs(result[k], v)
        else:
            result[k] = v
    return result

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS config (
                       key TEXT PRIMARY KEY,
                       value TEXT
                   )""")
    conn.commit()
    return conn

def save_config_to_db(conn, config):
    cur = conn.cursor()
    for k, v in config.items():
        cur.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (k, json.dumps(v)),
        )
    conn.commit()

def load_config_from_db(conn):
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM config")
    rows = cur.fetchall()
    cfg = {}
    for k, v in rows:
        cfg[k] = json.loads(v)
    return cfg

def compute_config_hash(config):
    raw = json.dumps(config, sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()

def create_app(db_path):
    app = Flask(__name__)

    @app.route("/config", methods=["GET"])
    def get_config():
        conn = sqlite3.connect(db_path)
        cfg = load_config_from_db(conn)
        conn.close()
        return jsonify(cfg)

    @app.route("/config/<key>", methods=["GET"])
    def get_config_key(key):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT value FROM config WHERE key=?", (key,))
        row = cur.fetchone()
        conn.close()
        if row:
            return jsonify({key: json.loads(row[0])})
        return jsonify({"error": "not found"}), 404

    @app.route("/reload", methods=["POST"])
    def reload_config():
        local_cfg = load_local_config(CONFIG_FILE)
        remote_cfg = fetch_remote_config(REMOTE_URL)
        merged = merge_configs(local_cfg, remote_cfg)
        conn = sqlite3.connect(db_path)
        save_config_to_db(conn, merged)
        conn.close()
        return jsonify({"status": "reloaded", "hash": compute_config_hash(merged)})

    return app

def main():
    local_cfg = load_local_config(CONFIG_FILE)
    remote_cfg = fetch_remote_config(REMOTE_URL)
    merged_cfg = merge_configs(local_cfg, remote_cfg)

    conn = init_db(DB_FILE)
    save_config_to_db(conn, merged_cfg)
    conn.close()

    app = create_app(DB_FILE)
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "127.0.0.1")
    app.run(host=host, port=port)

if __name__ == "__main__":
    main()