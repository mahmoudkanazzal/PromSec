import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('polls.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_poll_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER,
            option TEXT NOT NULL,
            votes INTEGER DEFAULT 0,
            FOREIGN KEY (poll_id) REFERENCES polls (id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/create_poll', methods=['POST'])
def create_poll():
    data = request.get_json()
    question = data.get('question')
    options = data.get('options')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO polls (question) VALUES (?)', (question,))
    poll_id = cursor.lastrowid

    for option in options:
        cursor.execute('INSERT INTO options (poll_id, option) VALUES (?, ?)', (poll_id, option))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Poll created successfully'})

@app.route('/vote', methods=['POST'])
def vote():
    data = request.get_json()
    poll_id = data.get('poll_id')
    option_id = data.get('option_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE options SET votes = votes + 1 WHERE poll_id = ? AND id = ?', (poll_id, option_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Vote submitted successfully'})

@app.route('/get_results/<int:poll_id>', methods=['GET'])
def get_results(poll_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM options WHERE poll_id = ?', (poll_id,))
    options = cursor.fetchall()
    conn.close()

    results = [{'option': option['option'], 'votes': option['votes']} for option in options]

    return jsonify(results)

if __name__ == '__main__':
    create_poll_table()
    app.run()