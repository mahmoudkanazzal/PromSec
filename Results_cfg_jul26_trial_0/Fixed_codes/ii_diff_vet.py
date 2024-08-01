import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = os.getenv('DB_PATH', 'events.db')

def create_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 date TEXT NOT NULL,
                 location TEXT NOT NULL)''')
    conn.commit()
    conn.close()

@app.route('/add_event', methods=['POST'])
def add_event():
    data = request.get_json()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO events (name, date, location) VALUES (?, ?, ?)",
              (data['name'], data['date'], data['location']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Event added successfully'})

@app.route('/search_events', methods=['GET'])
def search_events():
    keyword = request.args.get('keyword')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE name LIKE ? OR location LIKE ?",
              ('%'+keyword+'%', '%'+keyword+'%'))
    events = c.fetchall()
    conn.close()
    return jsonify({'events': events})

@app.route('/update_event/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.get_json()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE events SET name=?, date=?, location=? WHERE id=?",
              (data['name'], data['date'], data['location'], event_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Event updated successfully'})

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Event deleted successfully'})

@app.route('/get_events_by_date', methods=['GET'])
def get_events_by_date():
    date = request.args.get('date')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE date=?", (date,))
    events = c.fetchall()
    conn.close()
    return jsonify({'events': events})

if __name__ == '__main__':
    create_table()
    app.run()