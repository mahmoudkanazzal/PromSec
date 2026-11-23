from __future__ import annotations
import os
import sqlite3
import csv
import tempfile
from flask import Flask, request, jsonify, send_file, after_this_request

app = Flask(__name__)
DB_PATH = "inventory.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS items (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   quantity INTEGER NOT NULL
               )"""
        )
        conn.commit()

def add_item(name: str, quantity: int) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO items (name, quantity) VALUES (?, ?)",
            (name, quantity),
        )
        conn.commit()
        return cur.lastrowid

def remove_item(item_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        return cur.rowcount > 0

def list_items() -> list[dict]:
    with get_connection() as conn:
        cur = conn.execute("SELECT id, name, quantity FROM items")
        rows = cur.fetchall()
        return [dict(row) for row in rows]

def export_inventory() -> str:
    items = list_items()
    with tempfile.NamedTemporaryFile(mode="w", newline="", delete=False, suffix=".csv") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "quantity"])
        for item in items:
            writer.writerow([item["id"], item["name"], item["quantity"]])
        return f.name

@app.route("/add", methods=["POST"])
def route_add():
    data = request.get_json(force=True)
    name = data.get("name")
    quantity = data.get("quantity", 0)
    if not name or not isinstance(quantity, int):
        return jsonify({"error": "Invalid data"}), 400
    item_id = add_item(name, quantity)
    return jsonify({"id": item_id, "name": name, "quantity": quantity})

@app.route("/remove", methods=["POST"])
def route_remove():
    data = request.get_json(force=True)
    item_id = data.get("id")
    if not isinstance(item_id, int):
        return jsonify({"error": "Invalid id"}), 400
    success = remove_item(item_id)
    if success:
        return jsonify({"status": "removed"})
    else:
        return jsonify({"error": "Item not found"}), 404

@app.route("/list", methods=["GET"])
def route_list():
    return jsonify(list_items())

@app.route("/export", methods=["GET"])
def route_export():
    path = export_inventory()

    @after_this_request
    def remove_file(response):
        try:
            os.remove(path)
        except OSError:
            pass
        return response

    return send_file(path, as_attachment=True, download_name="inventory.csv")

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000)