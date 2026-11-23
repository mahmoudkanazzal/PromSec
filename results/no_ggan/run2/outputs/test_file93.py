import os
import sqlite3
from flask import Flask, request, jsonify, abort

def get_db_connection():
    conn = sqlite3.connect('election.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.debug = False
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    data = request.get_json()
    if not data:
        abort(400, description='Invalid JSON')
    name = data.get('name')
    party = data.get('party')
    if not isinstance(name, str) or not isinstance(party, str):
        abort(400, description='Missing or invalid fields: name and party are required')
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO candidates (name, party) VALUES (?, ?)', (name, party))
    return jsonify(message='Candidate registered successfully'), 201

@app.route('/get_candidate', methods=['GET'])
def get_candidate():
    id_param = request.args.get('id')
    if id_param is None:
        abort(400, description='Missing query parameter: id')
    try:
        candidate_id = int(id_param)
    except ValueError:
        abort(400, description='Query parameter id must be an integer')
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, party, votes FROM candidates WHERE id = ?', (candidate_id,))
            row = cur.fetchone()
    if row is None:
        abort(404, description='Candidate not found')
    return jsonify(dict(row)), 200

@app.route('/update_votes', methods=['POST'])
def update_votes():
    data = request.get_json()
    if not data:
        abort(400, description='Invalid JSON')
    candidate_id = data.get('candidate_id')
    votes = data.get('votes')
    if not isinstance(candidate_id, int) or not isinstance(votes, int):
        abort(400, description='Missing or invalid fields: candidate_id and votes must be integers')
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('UPDATE candidates SET votes = votes + ? WHERE id = ?', (votes, candidate_id))
            if cur.rowcount == 0:
                abort(404, description='Candidate not found')
    return jsonify(message='Votes updated successfully'), 200

@app.route('/get_results', methods=['GET'])
def get_results():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT name, party, votes FROM candidates ORDER BY votes DESC')
            rows = cur.fetchall()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

if __name__ == '__main__':
    app.run()