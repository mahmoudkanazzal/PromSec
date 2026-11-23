import os
import sqlite3
from flask import Flask, request, jsonify, abort, g

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_me')

DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'election.db')


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
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
    finally:
        conn.close()


@app.before_request
def before_request():
    g.db = get_db_connection()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    if not request.is_json:
        abort(400, description='Request body must be JSON')
    data = request.get_json()
    name = data.get('name')
    party = data.get('party')
    if not isinstance(name, str) or not isinstance(party, str):
        abort(400, description='Both name and party must be provided as strings')
    try:
        cursor = g.db.cursor()
        cursor.execute('INSERT INTO candidates (name, party) VALUES (?, ?)', (name, party))
        g.db.commit()
    finally:
        cursor.close()
    return jsonify(message='Candidate registered successfully'), 201


@app.route('/get_candidate', methods=['GET'])
def get_candidate():
    candidate_id = request.args.get('id')
    if not candidate_id or not candidate_id.isdigit():
        abort(400, description='Query parameter id must be a numeric value')
    try:
        cursor = g.db.cursor()
        cursor.execute('SELECT * FROM candidates WHERE id = ?', (int(candidate_id),))
        row = cursor.fetchone()
    finally:
        cursor.close()
    if row is None:
        abort(404, description='Candidate not found')
    return jsonify(dict(row)), 200


@app.route('/update_votes', methods=['POST'])
def update_votes():
    if not request.is_json:
        abort(400, description='Request body must be JSON')
    data = request.get_json()
    candidate_id = data.get('candidate_id')
    votes = data.get('votes')
    try:
        candidate_id = int(candidate_id)
        votes = int(votes)
    except (TypeError, ValueError):
        abort(400, description='candidate_id and votes must be integers')
    try:
        cursor = g.db.cursor()
        cursor.execute('UPDATE candidates SET votes = votes + ? WHERE id = ?', (votes, candidate_id))
        if cursor.rowcount == 0:
            abort(404, description='Candidate not found')
        g.db.commit()
    finally:
        cursor.close()
    return jsonify(message='Votes updated successfully'), 200


@app.route('/get_results', methods=['GET'])
def get_results():
    try:
        cursor = g.db.cursor()
        cursor.execute('SELECT name, party, votes FROM candidates ORDER BY votes DESC')
        rows = cursor.fetchall()
    finally:
        cursor.close()
    results = [dict(row) for row in rows]
    return jsonify(results), 200


if __name__ == '__main__':
    init_db()
    app.run(debug=False)