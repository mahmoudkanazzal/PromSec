from __future__ import annotations
import sqlite3
from flask import Flask, request, jsonify, g
import yaml

app = Flask(__name__)

CONFIG_YAML = """
auth_token: secret
database: library.db
"""

config = yaml.safe_load(CONFIG_YAML)


def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect(config['database'])
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db() -> None:
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            year INTEGER
        )
    """)
    db.commit()


@app.teardown_appcontext
def close_db(exc: Exception | None) -> None:
    db = g.pop('db', None)
    if db is not None:
        db.close()


def check_auth() -> None:
    auth = request.headers.get('Authorization')
    assert auth is not None, "Missing Authorization header"
    token = auth.replace('Bearer ', '', 1)
    assert token == config['auth_token'], "Invalid token"


def validate_book_payload(payload: dict) -> None:
    assert isinstance(payload, dict), "Payload must be JSON object"
    required = {'title', 'author', 'isbn'}
    missing = required - payload.keys()
    assert not missing, f"Missing fields: {', '.join(missing)}"
    assert isinstance(payload['title'], str) and payload['title'], "Invalid title"
    assert isinstance(payload['author'], str) and payload['author'], "Invalid author"
    assert isinstance(payload['isbn'], str) and payload['isbn'], "Invalid ISBN"
    if 'year' in payload:
        assert isinstance(payload['year'], int) and payload['year'] > 0, "Invalid year"


@app.route('/books', methods=['POST'])
def add_book():
    check_auth()
    payload = request.get_json()
    validate_book_payload(payload)
    db = get_db()
    try:
        db.execute(
            "INSERT INTO books (title, author, isbn, year) VALUES (?, ?, ?, ?)",
            (payload['title'], payload['author'], payload['isbn'], payload.get('year'))
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'status': 'added'}), 201


@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id: int):
    check_auth()
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    assert book is not None, "Book not found"
    return jsonify(dict(book))


@app.route('/books', methods=['GET'])
def list_books():
    check_auth()
    db = get_db()
    rows = db.execute("SELECT * FROM books").fetchall()
    return jsonify([dict(row) for row in rows])


@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id: int):
    check_auth()
    db = get_db()
    cur = db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()
    assert cur.rowcount > 0, "Book not found"
    return jsonify({'status': 'deleted'})


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5000)