from __future__ import annotations

import os
import sqlite3
import json
import hashlib
from flask import Flask, request, jsonify

DB_PATH = os.path.join(os.path.dirname(__file__), "inventory.db")
app = Flask(__name__)

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                qty INTEGER NOT NULL,
                price REAL NOT NULL
            )
            """
        )
        conn.commit()

def add_item(data: dict) -> int:
    name = data.get("name")
    qty = int(data.get("qty", 0))
    price = float(data.get("price", 0.0))
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO items (name, qty, price) VALUES (?, ?, ?)",
            (name, qty, price)
        )
        conn.commit()
        return cur.lastrowid

def get_items() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name, qty, price FROM items").fetchall()
        return [dict(row) for row in rows]

def update_quantity(data: dict) -> bool:
    item_id = int(data.get("id"))
    new_qty = int(data.get("qty"))
    with get_connection() as conn:
        conn.execute(
            "UPDATE items SET qty = ? WHERE id = ?",
            (new_qty, item_id)
        )
        conn.commit()
        return conn.total_changes > 0

def delete_item(data: dict) -> bool:
    item_id = int(data.get("id"))
    with get_connection() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        return conn.total_changes > 0

def compute_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()

@app.route("/add", methods=["POST"])
def route_add():
    raw = request.get_data()
    payload_hash = compute_hash(raw)
    obj = json.loads(raw.decode("utf-8"))
    item_id = add_item(obj)
    return jsonify({"status": "ok", "id": item_id, "hash": payload_hash})

@app.route("/list", methods=["GET"])
def route_list():
    items = get_items()
    return jsonify(items)

@app.route("/update", methods=["POST"])
def route_update():
    raw = request.get_data()
    obj = json.loads(raw.decode("utf-8"))
    success = update_quantity(obj)
    return jsonify({"status": "ok" if success else "fail"})

@app.route("/delete", methods=["POST"])
def route_delete():
    raw = request.get_data()
    obj = json.loads(raw.decode("utf-8"))
    success = delete_item(obj)
    return jsonify({"status": "ok" if success else "fail"})

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000)