from __future__ import annotations
import os
import sys
import sqlite3
import hashlib
import yaml
import requests
import tempfile
from datetime import datetime
from flask import Flask, request, render_template_string, g

CONFIG_PATH = "config.yaml"
DEFAULT_CONFIG = {
    "db_path": "logs.db",
    "log_dir": "./logs",
    "remote_urls": [],
    "host": "127.0.0.1",
    "port": 5000
}

app = Flask(__name__)

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG

def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        line TEXT,
        hash TEXT,
        ts TEXT
    )""")
    conn.commit()
    return conn

def hash_line(line: str) -> str:
    return hashlib.sha256(line.encode("utf-8")).hexdigest()

def ingest_log(conn: sqlite3.Connection, file_path: str) -> None:
    filename = os.path.basename(file_path)
    with open(file_path, "r", errors="ignore") as f:
        for line in f:
            line = line.rstrip("\n")
            h = hash_line(line)
            ts = datetime.utcnow().isoformat()
            conn.execute(
                "INSERT INTO logs (filename, line, hash, ts) VALUES (?,?,?,?)",
                (filename, line, h, ts)
            )
    conn.commit()

def fetch_remote_logs(conn: sqlite3.Connection, urls: list[str]) -> None:
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.content
            # Use a secure temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tf:
                tf.write(data)
                temp_path = tf.name
            ingest_log(conn, temp_path)
            os.remove(temp_path)
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")

def load_existing_logs(conn: sqlite3.Connection, log_dir: str) -> None:
    if not os.path.isdir(log_dir):
        return
    for entry in os.scandir(log_dir):
        if entry.is_file() and entry.name.endswith(".log"):
            ingest_log(conn, entry.path)

@app.route("/")
def index():
    return render_template_string("""
    <h1>Log Viewer</h1>
    <form action="/search" method="get">
        Search: <input name="q" />
        <button type="submit">Go</button>
    </form>
    """)

@app.route("/search")
def search():
    q = request.args.get("q", "")
    cur = g.db.cursor()
    cur.execute("SELECT filename, line, ts FROM logs WHERE line LIKE ?", (f"%{q}%",))
    rows = cur.fetchall()
    out = "<ul>"
    for fn, line, ts in rows:
        out += f"<li><b>{fn}</b> [{ts}]: {line}</li>"
    out += "</ul>"
    return out

@app.before_request
def before_request():
    g.db = app.config["db_conn"]

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, "db", None)
    if db is not None:
        db.commit()

def start_server(host: str, port: int, conn: sqlite3.Connection) -> None:
    app.config["db_conn"] = conn
    app.run(host=host, port=port, threaded=True)

def main() -> None:
    cfg = load_config()
    conn = init_db(cfg["db_path"])
    load_existing_logs(conn, cfg["log_dir"])
    if cfg.get("remote_urls"):
        fetch_remote_logs(conn, cfg["remote_urls"])
    start_server(cfg.get("host", "127.0.0.1"), cfg.get("port", 5000), conn)

if __name__ == "__main__":
    main()