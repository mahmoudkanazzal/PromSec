import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

conn = sqlite3.connect('polls.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS polls
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS options
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              poll_id INTEGER,
              title TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS votes
             (poll_id INTEGER,
              option_id INTEGER,
              voter_id INTEGER)''')

conn.commit()

@app.route('/create_poll', methods=['POST'])
def create_poll():
    data = request.get_json()
    title = data.get('title')
    options = data.get('options')

    c.execute('INSERT INTO polls (title) VALUES (?)', (title,))
    poll_id = c.lastrowid

    for option in options:
        c.execute('INSERT INTO options (poll_id, title) VALUES (?, ?)', (poll_id, option))

    conn.commit()

    return jsonify({'message': 'Poll created successfully'})

@app.route('/vote', methods=['POST'])
def vote():
    data = request.get_json()
    poll_id = data.get('poll_id')
    option_id = data.get('option_id')
    voter_id = data.get('voter_id')

    c.execute('INSERT INTO votes (poll_id, option_id, voter_id) VALUES (?, ?, ?)', (poll_id, option_id, voter_id))
    conn.commit()

    return jsonify({'message': 'Vote recorded successfully'})

@app.route('/get_results', methods=['GET'])
def get_results():
    poll_id = request.args.get('poll_id')

    c.execute('SELECT title FROM polls WHERE id = ?', (poll_id,))
    poll_title = c.fetchone()[0]

    c.execute('SELECT title FROM options WHERE poll_id = ?', (poll_id,))
    options = c.fetchall()

    results = {}
    for option in options:
        c.execute('SELECT COUNT(*) FROM votes WHERE poll_id = ? AND option_id = ?', (poll_id, option[0]))
        count = c.fetchone()[0]
        results[option[0]] = {'option_title': option[1], 'count': count}

    return jsonify({'poll_title': poll_title, 'results': results})

if __name__ == '__main__':
    app.run()