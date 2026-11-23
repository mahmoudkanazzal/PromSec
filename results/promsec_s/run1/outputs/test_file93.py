from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('election.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    data = request.get_json()
    name = data.get('name') if isinstance(data, dict) else None
    party = data.get('party') if isinstance(data, dict) else None
    if not name or not party:
        return jsonify({"error": "Missing name or party"}), 400
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO candidates (name, party) VALUES (?, ?)', (name, party))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"message": "Candidate registered successfully"}), 201

@app.route('/get_candidate', methods=['GET'])
def get_candidate():
    candidate_id = request.args.get('id')
    if not candidate_id or not candidate_id.isdigit():
        return jsonify({"error": "Invalid or missing candidate id"}), 400
    cid = int(candidate_id)
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT * FROM candidates WHERE id = ?', (cid,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return jsonify({"error": "Candidate not found"}), 404
    return jsonify(dict(row)), 200

@app.route('/update_votes', methods=['POST'])
def update_votes():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "candidate_id and votes must be integers"}), 400
    candidate_id = data.get('candidate_id')
    votes = data.get('votes')
    if not isinstance(candidate_id, int) or not isinstance(votes, int):
        return jsonify({"error": "candidate_id and votes must be integers"}), 400
    conn = get_db_connection()
    try:
        conn.execute('UPDATE candidates SET votes = votes + ? WHERE id = ?', (votes, candidate_id))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"message": "Votes updated successfully"}), 200

@app.route('/get_results', methods=['GET'])
def get_results():
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT * FROM candidates ORDER BY votes DESC').fetchall()
    finally:
        conn.close()
    result = [dict(row) for row in rows]
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=False)