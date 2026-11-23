from __future__ import annotations
import os
import sys
import argparse
import subprocess
import sqlite3
import yaml
import hashlib
import datetime
from flask import Flask, jsonify, request

DEFAULT_CONFIG = "/etc/log_analyzer/config.yaml"
DEFAULT_DB = "/var/lib/log_analyzer/results.db"

def load_config(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS results (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               pattern TEXT,
               result_hash TEXT,
               timestamp TEXT
           )"""
    )
    conn.commit()
    return conn

def run_grep(pattern: str, logfile: str) -> str:
    completed = subprocess.run(
        ["grep", "-i", pattern, logfile],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout

def hash_result(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def store_result(conn: sqlite3.Connection, pattern: str, result_hash: str) -> None:
    ts = datetime.datetime.utcnow().isoformat()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO results (pattern, result_hash, timestamp) VALUES (?, ?, ?)",
        (pattern, result_hash, ts),
    )
    conn.commit()

def get_results(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT id, pattern, result_hash, timestamp FROM results ORDER BY id DESC")
    return cur.fetchall()

def create_app(db_path: str) -> Flask:
    app = Flask(__name__)

    @app.route("/results", methods=["GET"])
    def results():
        conn = sqlite3.connect(db_path)
        rows = get_results(conn)
        conn.close()
        return jsonify(
            [
                {
                    "id": r[0],
                    "pattern": r[1],
                    "hash": r[2],
                    "timestamp": r[3],
                }
                for r in rows
            ]
        )

    @app.route("/search", methods=["POST"])
    def search():
        data = request.get_json() or {}
        pattern = data.get("pattern", "")
        logfile = data.get("logfile", "/var/log/syslog")
        output = run_grep(pattern, logfile)
        result_hash = hash_result(output)
        conn = sqlite3.connect(db_path)
        store_result(conn, pattern, result_hash)
        conn.close()
        return jsonify({"pattern": pattern, "hash": result_hash, "output": output})

    return app

def main() -> None:
    parser = argparse.ArgumentParser(description="Log analysis utility")
    parser.add_argument("-c", "--config", default=DEFAULT_CONFIG, help="Path to config YAML")
    parser.add_argument("-p", "--pattern", help="Pattern to search in logs")
    parser.add_argument("-l", "--logfile", default="/var/log/syslog", help="Log file to search")
    parser.add_argument("--serve", action="store_true", help="Run web UI")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite database path")
    args = parser.parse_args()

    config = load_config(args.config)
    db_path = args.db or config.get("db_path", DEFAULT_DB)
    conn = init_db(db_path)

    if args.serve:
        app = create_app(db_path)
        app.run(host="127.0.0.1", port=5000)
        return

    if not args.pattern:
        print("Pattern required for CLI mode", file=sys.stderr)
        sys.exit(1)

    logfile = args.logfile or config.get("logfile", "/var/log/syslog")
    output = run_grep(args.pattern, logfile)
    result_hash = hash_result(output)
    store_result(conn, args.pattern, result_hash)
    print(f"Pattern: {args.pattern}")
    print(f"Hash: {result_hash}")
    print("Matches:")
    print(output)

if __name__ == "__main__":
    main()