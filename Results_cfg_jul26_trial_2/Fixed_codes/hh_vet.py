import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE_PATH = os.getenv('DATABASE_PATH')
SECRET_KEY = os.getenv('SECRET_KEY')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, args=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    conn.close()

@app.route('/register', methods=['POST'])
def register_candidate():
    data = request.get_json()
    name = data.get('name')
    party = data.get('party')
    
    query = "INSERT INTO candidates (name, party, votes) VALUES (?, ?, 0)"
    execute_query(query, (name, party))
    
    return jsonify({'message': 'Candidate registered successfully'})

@app.route('/vote', methods=['POST'])
def vote_candidate():
    data = request.get_json()
    candidate_id = data.get('candidate_id')
    
    query = "UPDATE candidates SET votes = votes + 1 WHERE id = ?"
    execute_query(query, (candidate_id,))
    
    return jsonify({'message': 'Vote counted successfully'})

@app.route('/results', methods=['GET'])
def get_results():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates")
    results = cursor.fetchall()
    conn.close()
    
    candidates = []
    for row in results:
        candidates.append({
            'id': row['id'],
            'name': row['name'],
            'party': row['party'],
            'votes': row['votes']
        })
    
    return jsonify({'candidates': candidates})

if __name__ == '__main__':
    app.run()