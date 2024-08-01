import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = os.getenv('DATABASE')
SECRET_KEY = os.getenv('SECRET_KEY')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/register', methods=['POST'])
def register_candidate():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data = request.get_json()
    name = data.get('name')
    party = data.get('party')
    
    cursor.execute('INSERT INTO candidates (name, party) VALUES (?, ?)', (name, party))
    conn.commit()
    
    conn.close()
    
    return jsonify({'message': 'Candidate registered successfully'})

@app.route('/update-vote', methods=['PUT'])
def update_vote():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data = request.get_json()
    candidate_id = data.get('candidate_id')
    
    cursor.execute('UPDATE candidates SET votes = votes + 1 WHERE id = ?', (candidate_id,))
    conn.commit()
    
    conn.close()
    
    return jsonify({'message': 'Vote updated successfully'})

@app.route('/results', methods=['GET'])
def get_results():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM candidates ORDER BY votes DESC')
    results = cursor.fetchall()
    
    conn.close()
    
    return jsonify({'results': [dict(row) for row in results]})

if __name__ == '__main__':
    app.run()