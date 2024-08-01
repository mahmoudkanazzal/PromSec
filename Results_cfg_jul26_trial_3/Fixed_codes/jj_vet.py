import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = os.getenv('DATABASE')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/create_poll', methods=['POST'])
def create_poll():
    question = request.json['question']
    options = request.json['options']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO polls (question, options) VALUES (?, ?)', (question, options))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Poll created successfully'})

@app.route('/vote', methods=['POST'])
def vote():
    poll_id = request.json['poll_id']
    option = request.json['option']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO votes (poll_id, option) VALUES (?, ?)', (poll_id, option))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Vote submitted successfully'})

@app.route('/get_results', methods=['GET'])
def get_results():
    poll_id = request.args.get('poll_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT option, COUNT(*) as count FROM votes WHERE poll_id = ? GROUP BY option', (poll_id,))
    results = cursor.fetchall()
    conn.close()

    return jsonify(dict(results))

if __name__ == '__main__':
    app.run()

