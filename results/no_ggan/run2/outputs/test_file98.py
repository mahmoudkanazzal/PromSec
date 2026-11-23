from flask import Flask, request, jsonify, abort
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('voting.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS polls (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS options (id INTEGER PRIMARY KEY AUTOINCREMENT, poll_id INTEGER NOT NULL, option_text TEXT NOT NULL, FOREIGN KEY(poll_id) REFERENCES polls(id))')
        conn.execute('CREATE TABLE IF NOT EXISTS votes (id INTEGER PRIMARY KEY AUTOINCREMENT, poll_id INTEGER NOT NULL, option_id INTEGER NOT NULL, voter_id TEXT, FOREIGN KEY(poll_id) REFERENCES polls(id), FOREIGN KEY(option_id) REFERENCES options(id))')
        conn.commit()

init_db()

@app.route('/create_poll', methods=['POST'])
def create_poll():
    if not request.is_json:
        abort(400, description='Request must be JSON')
    data = request.get_json()
    title = data.get('title')
    options = data.get('options')
    if not isinstance(title, str) or not title.strip():
        abort(400, description='Title must be a non‑empty string')
    if not isinstance(options, list) or not options or not all(isinstance(o, str) and o.strip() for o in options):
        abort(400, description='Options must be a non‑empty list of non‑empty strings')
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO polls (title) VALUES (?)', (title,))
        poll_id = cur.lastrowid
        option_rows = [(poll_id, opt) for opt in options]
        cur.executemany('INSERT INTO options (poll_id, option_text) VALUES (?, ?)', option_rows)
        conn.commit()
    return jsonify(message='Poll created', poll_id=poll_id), 201

@app.route('/vote', methods=['POST'])
def vote():
    if not request.is_json:
        abort(400, description='Request must be JSON')
    data = request.get_json()
    poll_id = data.get('poll_id')
    option_id = data.get('option_id')
    voter_id = data.get('voter_id')
    if not isinstance(poll_id, int):
        abort(400, description='poll_id must be an integer')
    if not isinstance(option_id, int):
        abort(400, description='option_id must be an integer')
    with get_db_connection() as conn:
        conn.execute('INSERT INTO votes (poll_id, option_id, voter_id) VALUES (?, ?, ?)', (poll_id, option_id, str(voter_id) if voter_id is not None else None))
        conn.commit()
    return jsonify(message='Vote recorded'), 200

@app.route('/get_results', methods=['GET'])
def get_results():
    poll_id = request.args.get('poll_id')
    if poll_id is None:
        abort(400, description='poll_id query parameter is required')
    try:
        poll_id_int = int(poll_id)
    except ValueError:
        abort(400, description='poll_id must be an integer')
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT o.option_text, COUNT(v.id) AS vote_count
            FROM options o
            LEFT JOIN votes v ON o.id = v.option_id
            WHERE o.poll_id = ?
            GROUP BY o.id
            ORDER BY o.id
        ''', (poll_id_int,))
        rows = cur.fetchall()
    results = [{'option_text': row['option_text'], 'vote_count': row['vote_count']} for row in rows]
    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=False)