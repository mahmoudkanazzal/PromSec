import sqlite3
from flask import Flask, request, jsonify

def get_db_connection():
    return sqlite3.connect('election.db', detect_types=sqlite3.PARSE_DECLTYPES)

app = Flask(__name__)

@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    party = data.get('party')
    if not isinstance(name, str) or not name.strip() or not isinstance(party, str) or not party.strip():
        return jsonify({'error': 'Invalid input'}), 400
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                conn.execute('INSERT INTO candidates (name, party) VALUES (?, ?)', (name.strip(), party.strip()))
        return jsonify({'message': 'Candidate registered successfully'}), 201
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/get_candidate', methods=['GET'])
def get_candidate():
    candidate_id = request.args.get('id')
    try:
        candidate_id = int(candidate_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid id parameter'}), 400
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,))
            row = cur.fetchone()
        if row is None:
            return jsonify({'error': 'Candidate not found'}), 404
        result = {'id': row['id'], 'name': row['name'], 'party': row['party'], 'votes': row['votes']}
        return jsonify(result), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/update_votes', methods=['POST'])
def update_votes():
    data = request.get_json(silent=True) or {}
    candidate_id = data.get('candidate_id')
    votes = data.get('votes')
    if not isinstance(candidate_id, int) or not isinstance(votes, int) or votes < 0:
        return jsonify({'error': 'Invalid input'}), 400
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute('SELECT id FROM candidates WHERE id = ?', (candidate_id,))
            if cur.fetchone() is None:
                return jsonify({'error': 'Candidate not found'}), 404
            conn.execute('UPDATE candidates SET votes = votes + ? WHERE id = ?', (votes, candidate_id))
        return jsonify({'message': 'Votes updated successfully'}), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

@app.route('/get_results', methods=['GET'])
def get_results():
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute('SELECT name, party, votes FROM candidates ORDER BY votes DESC')
            rows = cur.fetchall()
        results = [{'name': row['name'], 'party': row['party'], 'votes': row['votes']} for row in rows]
        return jsonify(results), 200
    except sqlite3.Error:
        return jsonify({'error': 'Database error'}), 500

if __name__ == '__main__':
    app.run(debug=False)