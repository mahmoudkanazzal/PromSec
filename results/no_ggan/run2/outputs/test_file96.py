from flask import Flask, request, jsonify, abort
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('events.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_event', methods=['POST'])
def add_event():
    data = request.get_json()
    if not data:
        abort(400, description="Invalid JSON payload")
    name = data.get('name')
    date = data.get('date')
    location = data.get('location')
    if not name or not date or not location:
        abort(400, description="Missing required fields")
    with get_db_connection() as conn:
        conn.execute('INSERT INTO events (name, date, location) VALUES (?, ?, ?)', (name, date, location))
        conn.commit()
    return jsonify({"message": "Event added successfully"}), 201

@app.route('/search_events', methods=['GET'])
def search_events():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM events WHERE name LIKE ? OR location LIKE ?', (pattern, pattern)).fetchall()
    result = [dict(row) for row in rows]
    return jsonify(result), 200

@app.route('/update_event/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.get_json()
    if not data:
        abort(400, description="Invalid JSON payload")
    fields = {}
    for field in ('name', 'date', 'location'):
        if field in data:
            fields[field] = data[field]
    if not fields:
        abort(400, description="No fields to update provided")
    set_clause = ', '.join([f"{k}=?" for k in fields.keys()])
    values = list(fields.values())
    values.append(event_id)
    with get_db_connection() as conn:
        conn.execute(f'UPDATE events SET {set_clause} WHERE id = ?', values)
        conn.commit()
    return jsonify({"message": "Event updated successfully"}), 200

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
        conn.commit()
    return jsonify({"message": "Event deleted successfully"}), 200

@app.route('/get_events_by_date', methods=['GET'])
def get_events_by_date():
    date = request.args.get('date')
    if not date:
        abort(400, description="Missing 'date' query parameter")
    with get_db_connection() as conn:
        rows = conn.execute('SELECT * FROM events WHERE date = ?', (date,)).fetchall()
    result = [dict(row) for row in rows]
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=False)