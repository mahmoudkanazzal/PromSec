import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'candidates.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/register', methods=['POST'])
def register_candidate():
    data = request.get_json()
    if 'name' not in data or 'party' not in data:
        return jsonify({'error': 'Missing candidate information'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO candidates (name, party, votes) VALUES (?, ?, 0)', (data['name'], data['party']))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Candidate registered successfully'}), 201

@app.route('/candidates', methods=['GET'])
def get_candidates():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM candidates')
    candidates = cursor.fetchall()
    conn.close()

    return jsonify({'candidates': [dict(candidate) for candidate in candidates]})

@app.route('/update-votes', methods=['PUT'])
def update_votes():
    data = request.get_json()
    if 'candidate_id' not in data or 'votes' not in data:
        return jsonify({'error': 'Missing candidate ID or votes information'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE candidates SET votes = votes + ? WHERE id = ?', (data['votes'], data['candidate_id']))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Votes updated successfully'})

@app.route('/results', methods=['GET'])
def get_results():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, party, votes FROM candidates ORDER BY votes DESC')
    results = cursor.fetchall()
    conn.close()

    return jsonify({'results': [dict(result) for result in results]})

if __name__ == '__main__':
    app.run()