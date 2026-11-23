import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

def get_db_connection():
    conn = sqlite3.connect('voting.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS polls (
                poll_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS options (
                option_id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                option_text TEXT NOT NULL,
                FOREIGN KEY (poll_id) REFERENCES polls (poll_id) ON DELETE CASCADE
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                option_id INTEGER NOT NULL,
                voter_id TEXT NOT NULL,
                FOREIGN KEY (poll_id) REFERENCES polls (poll_id) ON DELETE CASCADE,
                FOREIGN KEY (option_id) REFERENCES options (option_id) ON DELETE CASCADE
            )
        ''')
        conn.commit()

@app.route('/create_poll', methods=['POST'])
def create_poll():
    if not request.is_json:
        return jsonify({'error': 'Invalid JSON'}), 400
    data = request.get_json()
    title = data.get('title')
    options = data.get('options')
    if not isinstance(title, str) or not title.strip():
        return jsonify({'error': 'Title must be a non‑empty string'}), 400
    if not isinstance(options, list) or not options or not all(isinstance(o, str) and o.strip() for o in options):
        return jsonify({'error': 'Options must be a non‑empty list of non‑empty strings'}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO polls (title) VALUES (?)', (title.strip(),))
            poll_id = cur.lastrowid
            for opt in options:
                cur.execute('INSERT INTO options (poll_id, option_text) VALUES (?, ?)', (poll_id, opt.strip()))
            conn.commit()
        return jsonify({'message': 'Poll created successfully', 'poll_id': poll_id}), 201
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/vote', methods=['POST'])
def vote():
    if not request.is_json:
        return jsonify({'error': 'Invalid JSON'}), 400
    data = request.get_json()
    poll_id = data.get('poll_id')
    option_id = data.get('option_id')
    voter_id = data.get('voter_id')
    if not isinstance(poll_id, int):
        return jsonify({'error': 'poll_id must be an integer'}), 400
    if not isinstance(option_id, int):
        return jsonify({'error': 'option_id must be an integer'}), 400
    if not isinstance(voter_id, str) or not voter_id.strip():
        return jsonify({'error': 'voter_id must be a non‑empty string'}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO votes (poll_id, option_id, voter_id) VALUES (?, ?, ?)', (poll_id, option_id, voter_id.strip()))
            conn.commit()
        return jsonify({'message': 'Vote recorded successfully'}), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/get_results', methods=['GET'])
def get_results():
    poll_id = request.args.get('poll_id')
    try:
        poll_id_int = int(poll_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'poll_id must be an integer'}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT o.option_text, COUNT(v.option_id) AS vote_count
                FROM options o
                LEFT JOIN votes v ON o.option_id = v.option_id
                WHERE o.poll_id = ?
                GROUP BY o.option_id
            ''', (poll_id_int,))
            rows = cur.fetchall()
            results = [{'option_text': row['option_text'], 'vote_count': row['vote_count']} for row in rows]
        return jsonify(results), 200
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=False)