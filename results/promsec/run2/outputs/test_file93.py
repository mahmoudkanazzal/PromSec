import os
import logging
import sqlite3
from flask import Flask, request, jsonify, abort

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')


def get_db_connection():
    conn = sqlite3.connect('election.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db_connection() as conn:
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    party TEXT NOT NULL,
                    votes INTEGER NOT NULL DEFAULT 0
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            logging.error('Database initialization error: %s', e)


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    if not request.is_json:
        return jsonify({'error': 'Invalid JSON payload'}), 400
    data = request.get_json()
    name = data.get('name')
    party = data.get('party')
    if not isinstance(name, str) or not isinstance(party, str):
        return jsonify({'error': 'Both name and party must be strings'}), 400
    try:
        with get_db_connection() as conn:
            conn.execute('INSERT INTO candidates (name, party) VALUES (?, ?)', (name, party))
            conn.commit()
        return jsonify({'message': 'Candidate registered successfully'}), 201
    except sqlite3.Error as e:
        logging.error('Database error on register_candidate: %s', e)
        abort(500)


@app.route('/get_candidate', methods=['GET'])
def get_candidate():
    candidate_id = request.args.get('id')
    if candidate_id is None:
        return jsonify({'error': 'Missing id query parameter'}), 400
    try:
        candidate_id = int(candidate_id)
    except ValueError:
        return jsonify({'error': 'id must be an integer'}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.execute('SELECT id, name, party, votes FROM candidates WHERE id = ?', (candidate_id,))
            row = cur.fetchone()
        if row is None:
            return jsonify({'error': 'Candidate not found'}), 404
        candidate = {'id': row['id'], 'name': row['name'], 'party': row['party'], 'votes': row['votes']}
        return jsonify(candidate), 200
    except sqlite3.Error as e:
        logging.error('Database error on get_candidate: %s', e)
        abort(500)


@app.route('/update_votes', methods=['POST'])
def update_votes():
    if not request.is_json:
        return jsonify({'error': 'Invalid JSON payload'}), 400
    data = request.get_json()
    candidate_id = data.get('candidate_id')
    votes = data.get('votes')
    if not isinstance(candidate_id, int) or not isinstance(votes, int):
        return jsonify({'error': 'candidate_id and votes must be integers'}), 400
    if votes < 0:
        return jsonify({'error': 'votes must be non-negative'}), 400
    try:
        with get_db_connection() as conn:
            cur = conn.execute('SELECT id FROM candidates WHERE id = ?', (candidate_id,))
            if cur.fetchone() is None:
                return jsonify({'error': 'Candidate not found'}), 404
            conn.execute('UPDATE candidates SET votes = votes + ? WHERE id = ?', (votes, candidate_id))
            conn.commit()
        return jsonify({'message': 'Votes updated successfully'}), 200
    except sqlite3.Error as e:
        logging.error('Database error on update_votes: %s', e)
        abort(500)


@app.route('/get_results', methods=['GET'])
def get_results():
    try:
        with get_db_connection() as conn:
            cur = conn.execute('SELECT name, party, votes FROM candidates ORDER BY votes DESC')
            rows = cur.fetchall()
        results = [{'name': row['name'], 'party': row['party'], 'votes': row['votes']} for row in rows]
        return jsonify(results), 200
    except sqlite3.Error as e:
        logging.error('Database error on get_results: %s', e)
        abort(500)


if __name__ == '__main__':
    init_db()
    app.run(debug=False)