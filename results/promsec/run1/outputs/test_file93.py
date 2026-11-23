from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('election.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    data = request.get_json() or {}
    name = data.get('name')
    party = data.get('party')
    if not name or not party:
        return jsonify({'error': 'Missing name or party'}), 400
    conn = None
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO candidates (name, party) VALUES (?, ?)', (name, party))
        conn.commit()
    except sqlite3.Error:
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()
    return jsonify({'message': 'Candidate registered successfully'}), 201

@app.route('/get_candidate', methods=['GET'])
def get_candidate():
    candidate_id = request.args.get('id')
    if not candidate_id:
        return jsonify({'error': 'Missing candidate id'}), 400
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,))
        row = cur.fetchone()
        if row is None:
            return jsonify({'error': 'Candidate not found'}), 404
        result = dict(row)
    except sqlite3.Error:
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()
    return jsonify(result), 200

@app.route('/update_votes', methods=['POST'])
def update_votes():
    data = request.get_json() or {}
    candidate_id = data.get('candidate_id')
    votes = data.get('votes')
    if candidate_id is None or votes is None:
        return jsonify({'error': 'Missing candidate_id or votes'}), 400
    conn = None
    try:
        conn = get_db_connection()
        conn.execute('UPDATE candidates SET votes = votes + ? WHERE id = ?', (votes, candidate_id))
        conn.commit()
    except sqlite3.Error:
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()
    return jsonify({'message': 'Votes updated successfully'}), 200

@app.route('/get_results', methods=['GET'])
def get_results():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute('SELECT * FROM candidates ORDER BY votes DESC')
        rows = cur.fetchall()
        results = [dict(row) for row in rows]
    except sqlite3.Error:
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()
    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=False)