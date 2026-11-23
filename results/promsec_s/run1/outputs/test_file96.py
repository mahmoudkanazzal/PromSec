from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

def get_db_connection():
    conn = sqlite3.connect('events.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_event', methods=['POST'])
def add_event():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    date = data.get('date')
    location = data.get('location')
    if not name or not date or not location:
        return jsonify({"error": "Missing required fields"}), 400
    try:
        with get_db_connection() as conn:
            conn.execute('INSERT INTO events (name, date, location) VALUES (?, ?, ?)', (name, date, location))
            conn.commit()
        return jsonify({"message": "Event added successfully"}), 201
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search_events', methods=['GET'])
def search_events():
    keyword = request.args.get('keyword', '')
    pattern = f"%{keyword}%"
    try:
        with get_db_connection() as conn:
            rows = conn.execute('SELECT * FROM events WHERE name LIKE ? OR location LIKE ?', (pattern, pattern)).fetchall()
        events = [dict(row) for row in rows]
        return jsonify(events), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_event/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.get_json(silent=True) or {}
    new_name = data.get('name')
    new_date = data.get('date')
    new_location = data.get('location')
    if not new_name or not new_date or not new_location:
        return jsonify({"error": "Missing required fields"}), 400
    try:
        with get_db_connection() as conn:
            conn.execute('UPDATE events SET name = ?, date = ?, location = ? WHERE id = ?', (new_name, new_date, new_location, event_id))
            conn.commit()
        return jsonify({"message": "Event updated successfully"}), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        with get_db_connection() as conn:
            conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
            conn.commit()
        return jsonify({"message": "Event deleted successfully"}), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_events_by_date', methods=['GET'])
def get_events_by_date():
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "Date parameter is required"}), 400
    try:
        with get_db_connection() as conn:
            rows = conn.execute('SELECT * FROM events WHERE date = ?', (date,)).fetchall()
        events = [dict(row) for row in rows]
        return jsonify(events), 200
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)