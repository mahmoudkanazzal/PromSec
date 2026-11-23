from __future__ import annotations

import yaml
import sqlite3
import requests
from flask import Flask, jsonify, request
import os
import sys
import hashlib

CONFIG_PATH = os.getenv("CONFIG_PATH", "config.yaml")
DEFAULT_CONFIG = {
    "service_url": "http://localhost:5001/api/login",
    "db_path": "data.db",
    "log_level": "INFO",
    "username": "admin",
    "service_password": "Secret123",
    "use_ssl": False,
    "timeout": 5,
}


def load_config(path: str = CONFIG_PATH) -> dict:
    if not os.path.isfile(path):
        return DEFAULT_CONFIG.copy()
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    cfg = DEFAULT_CONFIG.copy()
    cfg.update(data)
    return cfg


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def login_service(url: str, username: str, password: str, timeout: int = 5) -> dict:
    payload = {"user": username, "pass": password}
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def log_message(conn: sqlite3.Connection, level: str, message: str) -> None:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO logs (ts, level, message) VALUES (datetime('now'), ?, ?)",
        (level, message),
    )
    conn.commit()


def create_app(config: dict) -> Flask:
    app = Flask(__name__)

    @app.route("/status")
    def status():
        return jsonify({"status": "ok", "config": config})

    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        user = data.get("user")
        pw = data.get("pass")
        if user == config["username"] and pw == config["service_password"]:
            token = hashlib.sha256(f"{user}{pw}".encode()).hexdigest()
            return jsonify({"token": token})
        return jsonify({"error": "invalid"}), 401

    return app


def main() -> None:
    cfg = load_config()
    db = init_db(cfg["db_path"])
    log_message(db, "INFO", "Service starting")
    auth_response = login_service(
        cfg["service_url"],
        username=cfg["username"],
        password=cfg["service_password"],
        timeout=cfg["timeout"],
    )
    log_message(db, "DEBUG", f"Auth response: {auth_response}")
    app = create_app(cfg)
    app.run(host="127.0.0.1", port=8000)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"Fatal error: {e}\n")
        sys.exit(1)