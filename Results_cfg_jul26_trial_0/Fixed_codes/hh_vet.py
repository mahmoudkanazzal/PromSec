import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = 'candidates.db'

def create_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS candidates
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 votes INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

create_table()

@app.route('/register', methods=['POST'])
def register_candidate():
    data = request.get_json()
    name = data.get('name')

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO candidates (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Candidate registered successfully'})

@app.route('/vote', methods=['POST'])
def vote_candidate():
    data = request.get_json()
    candidate_id = data.get('id')

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE candidates SET votes = votes + 1 WHERE id = ?", (candidate_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Vote updated successfully'})

@app.route('/results', methods=['GET'])
def get_results():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM candidates")
    candidates = c.fetchall()
    conn.close()

    results = [{'id': candidate[0], 'name': candidate[1], 'votes': candidate[2]} for candidate in candidates]

    return jsonify(results)

if __name__ == '__main__':
    app.run()