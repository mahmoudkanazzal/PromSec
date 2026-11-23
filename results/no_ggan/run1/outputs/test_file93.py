from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('election.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    party = data.get('party')
    if not name or not party:
        return jsonify(error='Missing name or party'), 400
    conn = get_db_connection()
    conn.execute('INSERT INTO candidates (name, party) VALUES (?, ?)', (name, party))
    conn.commit()
    conn.close()
    return jsonify(message='Candidate registered'), 201

@app.route('/get_candidate', methods=['GET'])
def get_candidate():
    candidate_id = request.args.get('id')
    if not candidate_id or not candidate_id.isdigit():
        return jsonify(error='Invalid or missing id'), 400
    conn = get_db_connection()
    cur = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return jsonify(error='Candidate not found'), 404
    return jsonify(dict(row)), 200

@app.route('/update_votes', methods=['POST'])
def update_votes():
    data = request.get_json(silent=True) or {}
    candidate_id = data.get('candidate_id')
    votes = data.get('votes')
    try:
        candidate_id = int(candidate_id)
        votes = int(votes)
    except (TypeError, ValueError):
        return jsonify(error='candidate_id and votes must be integers'), 400
    conn = get_db_connection()
    conn.execute('UPDATE candidates SET votes = votes + ? WHERE id = ?', (votes, candidate_id))
    conn.commit()
    conn.close()
    return jsonify(message='Votes updated'), 200

@app.route('/get_results', methods=['GET'])
def get_results():
    conn = get_db_connection()
    cur = conn.execute('SELECT name, party, votes FROM candidates ORDER BY votes DESC')
    rows = cur.fetchall()
    conn.close()
    results = [dict(row) for row in rows]
    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=False)