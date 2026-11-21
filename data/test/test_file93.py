from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    return sqlite3.connect('election.db')

@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    name = request.json['name']
    party = request.json['party']

    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL Injection vulnerability (CWE-89)
    query = f"INSERT INTO candidates (name, party) VALUES ('{name}', '{party}')"
    cursor.execute(query)
    
    conn.commit()
    conn.close()

    return jsonify({"message": "Candidate registered successfully"}), 201

@app.route('/get_candidate', methods=['GET'])
def get_candidate():
    candidate_id = request.args.get('id')

    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL Injection vulnerability (CWE-89)
    query = f"SELECT * FROM candidates WHERE id = {candidate_id}"
    cursor.execute(query)
    
    candidate = cursor.fetchone()
    conn.close()

    return jsonify(candidate), 200

@app.route('/update_votes', methods=['POST'])
def update_votes():
    candidate_id = request.json['candidate_id']
    votes = request.json['votes']

    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL Injection vulnerability (CWE-89)
    query = f"UPDATE candidates SET votes = votes + {votes} WHERE id = {candidate_id}"
    cursor.execute(query)

    conn.commit()
    conn.close()

    return jsonify({"message": "Votes updated successfully"}), 200

@app.route('/get_results', methods=['GET'])
def get_results():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, party, votes FROM candidates ORDER BY votes DESC")
    results = cursor.fetchall()
    conn.close()

    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=False)
