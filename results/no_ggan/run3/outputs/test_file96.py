from __future__ import annotations
import os
import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', '')

def get_db_connection():
    conn = sqlite3.connect('events.db')
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_dicts(rows):
    return [dict(row) for row in rows]

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                location TEXT NOT NULL
            )
        ''')

@app.route('/add_event', methods=['POST'])
def add_event():
    if not request.is_json:
        abort(400, description='Request must be JSON')
    data = request.get_json()
    if not data or any(k not in data for k in ('name', 'date', 'location')):
        abort(400, description='Missing required fields: name, date, location')
    name = data['name']
    date = data['date']
    location = data['location']
    try:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO events (name, date, location) VALUES (?, ?, ?)',
                (name, date, location)
            )
    except sqlite3.Error as e:
        abort(500, description=str(e))
    return jsonify(message='Event added successfully'), 201

@app.route('/search_events', methods=['GET'])
def search_events():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                'SELECT * FROM events WHERE name LIKE ? COLLATE NOCASE OR location LIKE ? COLLATE NOCASE',
                (pattern, pattern)
            )
            rows = cur.fetchall()
    except sqlite3.Error as e:
        abort(500, description=str(e))
    return jsonify(rows_to_dicts(rows)), 200

@app.route('/update_event/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    if not request.is_json:
        abort(400, description='Request must be JSON')
    data = request.get_json()
    if not data or any(k not in data for k in ('name', 'date', 'location')):
        abort(400, description='Missing required fields: name, date, location')
    name = data['name']
    date = data['date']
    location = data['location']
    try:
        with get_db_connection() as conn:
            cur = conn.execute(
                'UPDATE events SET name = ?, date = ?, location = ? WHERE id = ?',
                (name, date, location, event_id)
            )
            if cur.rowcount == 0:
                abort(404, description='Event not found')
    except sqlite3.Error as e:
        abort(500, description=str(e))
    return jsonify(message='Event updated successfully'), 200

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        with get_db_connection() as conn:
            cur = conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
            if cur.rowcount == 0:
                abort(404, description='Event not found')
    except sqlite3.Error as e:
        abort(500, description=str(e))
    return jsonify(message='Event deleted successfully'), 200

@app.route('/get_events_by_date', methods=['GET'])
def get_events_by_date():
    date = request.args.get('date')
    if not date:
        abort(400, description='Missing required query parameter: date')
    try:
        with get_db_connection() as conn:
            cur = conn.execute('SELECT * FROM events WHERE date = ?', (date,))
            rows = cur.fetchall()
    except sqlite3.Error as e:
        abort(500, description=str(e))
    return jsonify(rows_to_dicts(rows)), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=False)