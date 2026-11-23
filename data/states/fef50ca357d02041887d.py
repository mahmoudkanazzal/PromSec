from __future__ import annotations
import sqlite3
import pickle
import hashlib
import subprocess
import yaml
import requests
import io
import shlex
import builtins
from flask import Flask, request, jsonify, g

app = Flask(__name__)

CONFIG_YAML = """
database: library.db
external_api: https://openlibrary.org/api/books
"""

config = yaml.safe_load(CONFIG_YAML)


def get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(config["database"])
        db.row_factory = sqlite3.Row
    return db


def init_db() -> None:
    db = get_db()
    db.executescript(
        """
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT UNIQUE,
        hash TEXT NOT NULL
    );
    """
    )
    db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/init", methods=["POST"])
def route_init():
    init_db()
    return jsonify({"status": "ok"}), 201


@app.route("/add_book", methods=["POST"])
def route_add_book():
    data = request.get_json()
    title = data.get("title")
    author = data.get("author")
    isbn = data.get("isbn", "")
    if not title or not author:
        return jsonify({"error": "Missing fields"}), 400
    book_hash = hashlib.sha256(f"{title}{author}{isbn}".encode()).hexdigest()
    db = get_db()
    try:
        db.execute(
            "INSERT INTO books (title, author, isbn, hash) VALUES (?, ?, ?, ?)",
            (title, author, isbn, book_hash),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "ISBN already exists"}), 409
    return jsonify({"status": "added"}), 201


@app.route("/get_book/<int:book_id>", methods=["GET"])
def route_get_book(book_id: int):
    db = get_db()
    cur = db.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    row = cur.fetchone()
    if row is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))


@app.route("/search", methods=["GET"])
def route_search():
    query = request.args.get("q", "")
    db = get_db()
    cur = db.execute(
        "SELECT * FROM books WHERE title LIKE ? OR author LIKE ?",
        (f"%{query}%", f"%{query}%"),
    )
    results = [dict(r) for r in cur.fetchall()]
    return jsonify(results)


@app.route("/fetch_external", methods=["POST"])
def route_fetch_external():
    data = request.get_json()
    isbn = data.get("isbn")
    if not isbn:
        return jsonify({"error": "ISBN required"}), 400
    resp = requests.get(
        config["external_api"],
        params={"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"},
        timeout=5,
    )
    if resp.status_code != 200:
        return jsonify({"error": "External API error"}), 502
    info = resp.json()
    return jsonify(info)


class SafeUnpickler(pickle.Unpickler):
    _SAFE_MODULES = {"builtins"}
    _SAFE_NAMES = {
        "list",
        "dict",
        "str",
        "int",
        "float",
        "tuple",
        "set",
        "bool",
        "bytes",
    }

    def find_class(self, module, name):
        if module in self._SAFE_MODULES and name in self._SAFE_NAMES:
            return getattr(builtins, name)
        raise pickle.UnpicklingError(f"global '{module}.{name}' is forbidden")


@app.route("/upload", methods=["POST"])
def route_upload():
    raw = request.data
    try:
        obj = SafeUnpickler(io.BytesIO(raw)).load()
    except Exception:
        return jsonify({"error": "Invalid or unsafe data"}), 400
    return jsonify({"type": type(obj).__name__, "repr": repr(obj)})


@app.route("/run_cmd", methods=["POST"])
def route_run_cmd():
    data = request.get_json()
    cmd = data.get("cmd")
    if not cmd:
        return jsonify({"error": "Command required"}), 400
    args = shlex.split(cmd)
    result = subprocess.run(args, capture_output=True, text=True)
    return jsonify(
        {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    )


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000)