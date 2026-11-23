import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

def get_db_connection():
    conn = sqlite3.connect('voting.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                option_text TEXT NOT NULL,
                FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                option_id INTEGER NOT NULL,
                voter_id TEXT NOT NULL,
                FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE,
                FOREIGN KEY (option_id) REFERENCES options(id) ON DELETE CASCADE
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
        return jsonify({'error': 'Title must be a non-empty string'}), 400
    if not isinstance(options, list) or not options or not all(isinstance(o, str) and o.strip() for o in options):
        return jsonify({'error': 'Options must be a non-empty list of non-empty strings'}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO polls (title) VALUES (?)', (title.strip(),))
            poll_id = cur.lastrowid
            for opt in options:
                cur.execute('INSERT INTO options (poll_id, option_text) VALUES (?, ?)', (poll_id, opt.strip()))
            conn.commit()
        return jsonify({'message': 'Poll created successfully', 'poll_id': poll_id}), 201
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/vote', methods=['POST'])
def vote():
    if not request.is_json:
        return jsonify({'error': 'Invalid JSON'}), 400
    data = request.get_json()
    poll_id = data.get('poll_id')
    option_id = data.get('option_id')
    voter_id = data.get('voter_id')
    if not isinstance(poll_id, int) or not isinstance(option_id, int) or not isinstance(voter_id, str) or not voter_id.strip():
        return jsonify({'error': 'Invalid input types'}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT 1 FROM polls WHERE id = ?', (poll_id,))
            if cur.fetchone() is None:
                return jsonify({'error': 'Poll not found'}), 400
            cur.execute('SELECT 1 FROM options WHERE id = ? AND poll_id = ?', (option_id, poll_id))
            if cur.fetchone() is None:
                return jsonify({'error': 'Option not found for given poll'}), 400
            cur.execute('INSERT INTO votes (poll_id, option_id, voter_id) VALUES (?, ?, ?)', (poll_id, option_id, voter_id.strip()))
            conn.commit()
        return jsonify({'message': 'Vote recorded successfully'}), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/get_results', methods=['GET'])
def get_results():
    poll_id = request.args.get('poll_id')
    try:
        poll_id = int(poll_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'poll_id must be an integer'}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT id, option_text FROM options WHERE poll_id = ? ORDER BY id', (poll_id,))
            options = cur.fetchall()
            if not options:
                return jsonify({'error': 'Poll not found or has no options'}), 400
            results = []
            for opt in options:
                cur.execute('SELECT COUNT(*) FROM votes WHERE poll_id = ? AND option_id = ?', (poll_id, opt['id']))
                count = cur.fetchone()[0]
                results.append({'option_text': opt['option_text'], 'vote_count': count})
        return jsonify(results), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=False)