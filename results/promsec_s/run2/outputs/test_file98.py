import os
from flask import Flask, request, jsonify, abort
import sqlite3

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret')

def get_db_connection():
    conn = sqlite3.connect('voting.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            option_text TEXT NOT NULL,
            FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            option_id INTEGER NOT NULL,
            voter_id TEXT NOT NULL,
            FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE,
            FOREIGN KEY (option_id) REFERENCES options(id) ON DELETE CASCADE
        );
        ''')
        conn.commit()
    finally:
        conn.close()

@app.route('/create_poll', methods=['POST'])
def create_poll():
    try:
        data = request.get_json()
    except Exception:
        return jsonify({'error': 'Invalid JSON'}), 400
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    title = data.get('title')
    options = data.get('options')
    if not isinstance(title, str) or not isinstance(options, list) or not all(isinstance(o, str) for o in options):
        return jsonify({'error': 'Missing or invalid fields'}), 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO polls (title) VALUES (?)', (title,))
        poll_id = cur.lastrowid
        for opt in options:
            conn.execute('INSERT INTO options (poll_id, option_text) VALUES (?, ?)', (poll_id, opt))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'message': 'Poll created successfully', 'poll_id': poll_id}), 201

@app.route('/vote', methods=['POST'])
def vote():
    try:
        data = request.get_json()
    except Exception:
        return jsonify({'error': 'Invalid JSON'}), 400
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    poll_id = data.get('poll_id')
    option_id = data.get('option_id')
    voter_id = data.get('voter_id')
    if not isinstance(poll_id, int) or not isinstance(option_id, int) or not isinstance(voter_id, str):
        return jsonify({'error': 'Missing or invalid fields'}), 400
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO votes (poll_id, option_id, voter_id) VALUES (?, ?, ?)', (poll_id, option_id, voter_id))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'message': 'Vote recorded successfully'}), 200

@app.route('/get_results', methods=['GET'])
def get_results():
    poll_id_param = request.args.get('poll_id')
    if poll_id_param is None:
        return jsonify({'error': 'poll_id query parameter is required'}), 400
    try:
        poll_id = int(poll_id_param)
    except ValueError:
        return jsonify({'error': 'poll_id query parameter is required'}), 400
    conn = get_db_connection()
    try:
        cur = conn.execute('''
            SELECT o.option_text, COUNT(v.id) AS vote_count
            FROM options o
            LEFT JOIN votes v ON o.id = v.option_id
            WHERE o.poll_id = ?
            GROUP BY o.id
            ORDER BY o.id
        ''', (poll_id,))
        results = [{'option_text': row['option_text'], 'vote_count': row['vote_count']} for row in cur.fetchall()]
    finally:
        conn.close()
    return jsonify(results), 200

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=False)