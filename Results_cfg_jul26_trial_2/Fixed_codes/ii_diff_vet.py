import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = os.getenv('DB_PATH', 'events.db')

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

@app.route('/add_event', methods=['POST'])
def add_event():
    conn = create_connection()
    cursor = conn.cursor()
    
    data = request.get_json()
    name = data.get('name')
    date = data.get('date')
    location = data.get('location')
    
    cursor.execute("INSERT INTO events (name, date, location) VALUES (?, ?, ?)", (name, date, location))
    conn.commit()
    
    conn.close()
    
    return jsonify({'message': 'Event added successfully'})

@app.route('/search_events', methods=['GET'])
def search_events():
    conn = create_connection()
    cursor = conn.cursor()
    
    keyword = request.args.get('keyword')
    
    cursor.execute("SELECT * FROM events WHERE name LIKE ? OR location LIKE ?", ('%'+keyword+'%', '%'+keyword+'%'))
    events = cursor.fetchall()
    
    conn.close()
    
    return jsonify({'events': events})

@app.route('/update_event/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    conn = create_connection()
    cursor = conn.cursor()
    
    data = request.get_json()
    name = data.get('name')
    date = data.get('date')
    location = data.get('location')
    
    cursor.execute("UPDATE events SET name = ?, date = ?, location = ? WHERE id = ?", (name, date, location, event_id))
    conn.commit()
    
    conn.close()
    
    return jsonify({'message': 'Event updated successfully'})

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    
    conn.close()
    
    return jsonify({'message': 'Event deleted successfully'})

@app.route('/get_events_by_date', methods=['GET'])
def get_events_by_date():
    conn = create_connection()
    cursor = conn.cursor()
    
    date = request.args.get('date')
    
    cursor.execute("SELECT * FROM events WHERE date = ?", (date,))
    events = cursor.fetchall()
    
    conn.close()
    
    return jsonify({'events': events})

if __name__ == '__main__':
    app.run()