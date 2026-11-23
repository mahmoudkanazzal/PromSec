import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

def get_db_connection():
    conn = sqlite3.connect('voting.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER NOT NULL,
                option_text TEXT NOT NULL,
                FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
            )
        ''')
        cur.execute('''
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
    finally:
        conn.close()

@app.route('/create_poll', methods=['POST'])
def create_poll():
    data = request.get_json()
    if not data or 'title' not in data or 'options' not in data:
        return jsonify({'error': 'Missing title or options'}), 400
    title = data['title']
    options = data['options']
    if not isinstance(title, str) or not isinstance(options, list) or not all(isinstance(o, str) for o in options):
        return jsonify({'error': 'Invalid data types'}), 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO polls (title) VALUES (?)', (title,))
        poll_id = cur.lastrowid
        for opt in options:
            cur.execute('INSERT INTO options (poll_id, option_text) VALUES (?, ?)', (poll_id, opt))
        conn.commit()
        return jsonify({'message': 'Poll created successfully', 'poll_id': poll_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/vote', methods=['POST'])
def vote():
    data = request.get_json()
    required = {'poll_id', 'option_id', 'voter_id'}
    if not data or not required.issubset(data):
        return jsonify({'error': 'Missing poll_id, option_id, or voter_id'}), 400
    poll_id = data['poll_id']
    option_id = data['option_id']
    voter_id = data['voter_id']
    if not isinstance(poll_id, int) or not isinstance(option_id, int) or not isinstance(voter_id, (str, int)):
        return jsonify({'error': 'Invalid data types'}), 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO votes (poll_id, option_id, voter_id) VALUES (?, ?, ?)', (poll_id, option_id, str(voter_id)))
        conn.commit()
        return jsonify({'message': 'Vote recorded successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/get_results', methods=['GET'])
def get_results():
    poll_id = request.args.get('poll_id')
    if poll_id is None:
        return jsonify({'error': 'poll_id query parameter required'}), 400
    try:
        poll_id_int = int(poll_id)
    except ValueError:
        return jsonify({'error': 'poll_id must be an integer'}), 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT o.id AS option_id, o.option_text, COUNT(v.id) AS vote_count
            FROM options o
            LEFT JOIN votes v ON o.id = v.option_id
            WHERE o.poll_id = ?
            GROUP BY o.id
        ''', (poll_id_int,))
        rows = cur.fetchall()
        results = [{'option_id': row['option_id'], 'option_text': row['option_text'], 'vote_count': row['vote_count']} for row in rows]
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=False)