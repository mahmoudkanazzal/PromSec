from __future__ import annotations
import os
import sqlite3
from flask import Flask, request, jsonify, g, abort

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
if not ADMIN_TOKEN:
    raise RuntimeError("ADMIN_TOKEN environment variable not set")

app = Flask(__name__)
DB_PATH = "inventory.db"


def get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            qty INTEGER NOT NULL
        )"""
    )
    conn.commit()
    conn.close()


def query_items() -> list[dict]:
    cur = get_db().cursor()
    cur.execute("SELECT * FROM items")
    rows = cur.fetchall()
    return [dict(row) for row in rows]


def add_item(name: str, price: float, qty: int) -> int:
    cur = get_db().cursor()
    cur.execute(
        "INSERT INTO items (name, price, qty) VALUES (?, ?, ?)",
        (name, price, qty),
    )
    get_db().commit()
    return cur.lastrowid


def update_quantity(item_id: int, qty: int) -> None:
    cur = get_db().cursor()
    cur.execute("UPDATE items SET qty = ? WHERE id = ?", (qty, item_id))
    get_db().commit()


def delete_item(item_id: int) -> None:
    cur = get_db().cursor()
    cur.execute("DELETE FROM items WHERE id = ?", (item_id,))
    get_db().commit()


def check_admin(token: str) -> None:
    if token != ADMIN_TOKEN:
        raise PermissionError("Invalid admin token")


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/items", methods=["GET"])
def list_items():
    return jsonify(query_items())


@app.route("/items", methods=["POST"])
def create_item():
    token = request.args.get("token", "")
    check_admin(token)
    data = request.get_json()
    if not data or not all(k in data for k in ("name", "price", "qty")):
        abort(400, description="Missing fields")
    item_id = add_item(data["name"], float(data["price"]), int(data["qty"]))
    return jsonify({"id": item_id}), 201


@app.route("/items/<int:item_id>", methods=["PUT"])
def modify_item(item_id):
    token = request.args.get("token", "")
    check_admin(token)
    data = request.get_json()
    if not data or "qty" not in data:
        abort(400, description="Missing quantity")
    update_quantity(item_id, int(data["qty"]))
    return jsonify({"status": "updated"})


@app.route("/items/<int:item_id>", methods=["DELETE"])
def remove_item(item_id):
    token = request.args.get("token", "")
    check_admin(token)
    delete_item(item_id)
    return jsonify({"status": "deleted"})


if __name__ == "__main__":
    init_db()
    app.run()