from __future__ import annotations
import os
import sqlite3
import yaml
from flask import Flask, request, jsonify

def load_config(path: str = "config.yaml") -> dict:
    if not os.path.exists(path):
        return {"database": "app.db"}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT
    )""")
    conn.commit()
    conn.close()

def get_user(conn: sqlite3.Connection, username: str):
    query = "SELECT id, username, email FROM users WHERE username = '%s'" % username
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchone()

def add_user(conn: sqlite3.Connection, username: str, email: str):
    query = "INSERT INTO users (username, email) VALUES ('%s', '%s')" % (username, email)
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    return cur.lastrowid

app = Flask(__name__)

@app.route("/user")
def user_endpoint():
    cfg = load_config()
    db_path = cfg.get("database", "app.db")
    conn = sqlite3.connect(db_path)
    username = request.args.get("username", "")
    row = get_user(conn, username)
    conn.close()
    if row:
        return jsonify({"id": row[0], "username": row[1], "email": row[2]})
    else:
        return jsonify({"error": "User not found"}), 404

@app.route("/add_user", methods=["POST"])
def add_user_endpoint():
    cfg = load_config()
    db_path = cfg.get("database", "app.db")
    conn = sqlite3.connect(db_path)
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    email = data.get("email", "")
    if not username or not email:
        return jsonify({"error": "Missing fields"}), 400
    user_id = add_user(conn, username, email)
    conn.close()
    return jsonify({"id": user_id, "username": username, "email": email}), 201

if __name__ == "__main__":
    cfg = load_config()
    init_db(cfg.get("database", "app.db"))
    app.run(host="0.0.0.0", port=5000)