import sqlite3
from flask import Flask, request, jsonify, g

app = Flask(__name__)

ADMIN_PASSWORD = "secret123"
DB_PATH = "library.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            available INTEGER NOT NULL DEFAULT 1
        )"""
    )
    db.commit()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.before_first_request
def setup():
    init_db()


@app.route("/books", methods=["GET"])
def list_books():
    rows = query_db("SELECT * FROM books")
    books = [dict(row) for row in rows]
    return jsonify(books)


@app.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    row = query_db("SELECT * FROM books WHERE id = ?", (book_id,), one=True)
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "Not found"}), 404


def require_password():
    data = request.get_json(silent=True) or {}
    if data.get("password") != ADMIN_PASSWORD:
        return False, jsonify({"error": "Invalid password"}), 403
    return True, data, None


@app.route("/books", methods=["POST"])
def add_book():
    ok, data, resp = require_password()
    if not ok:
        return resp
    title = data.get("title")
    author = data.get("author")
    if not title or not author:
        return jsonify({"error": "Missing fields"}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO books (title, author, available) VALUES (?, ?, 1)",
        (title, author),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "title": title, "author": author, "available": 1}), 201


@app.route("/books/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    ok, data, resp = require_password()
    if not ok:
        return resp
    title = data.get("title")
    author = data.get("author")
    available = data.get("available")
    fields = []
    values = []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if author is not None:
        fields.append("author = ?")
        values.append(author)
    if available is not None:
        fields.append("available = ?")
        values.append(1 if available else 0)
    if not fields:
        return jsonify({"error": "No fields to update"}), 400
    values.append(book_id)
    db = get_db()
    db.execute(f"UPDATE books SET {', '.join(fields)} WHERE id = ?", values)
    db.commit()
    return jsonify({"status": "updated"})


@app.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    ok, _, resp = require_password()
    if not ok:
        return resp
    db = get_db()
    db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()
    return jsonify({"status": "deleted"})


if __name__ == "__main__":
    app.run(debug=True)