from flask import Flask, request, jsonify, abort
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('events.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_event', methods=['POST'])
def add_event():
    if not request.is_json:
        abort(400, description='Request must be JSON')
    data = request.get_json()
    name = data.get('name')
    date = data.get('date')
    location = data.get('location')
    if not all([name, date, location]):
        abort(400, description='Missing required fields')
    try:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO events (name, date, location) VALUES (?, ?, ?)',
                (name, date, location)
            )
            conn.commit()
    except sqlite3.Error as e:
        abort(500, description=str(e))
    return jsonify(message='Event added successfully'), 201

@app.route('/search_events', methods=['GET'])
def search_events():
    keyword = request.args.get('keyword')
    try:
        with get_db_connection() as conn:
            if keyword:
                pattern = f'%{keyword}%'
                rows = conn.execute(
                    'SELECT * FROM events WHERE name LIKE ? COLLATE NOCASE OR location LIKE ? COLLATE NOCASE',
                    (pattern, pattern)
                ).fetchall()
            else:
                rows = conn.execute('SELECT * FROM events').fetchall()
            events = [dict(row) for row in rows]
    except sqlite3.Error as e:
        abort(500, description=str(e))
    return jsonify(events), 200

@app.route('/update_event/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    if not request.is_json:
        abort(400, description='Request must be JSON')
    data = request.get_json()
    fields = {}
    for key in ('name', 'date', 'location'):
        if key in data:
            fields[key] = data[key]
    if not fields:
        abort(400, description='No fields to update')
    set_clause = ', '.join([f"{k}=?" for k in fields])
    values = list(fields.values())
    values.append(event_id)
    try:
        with get_db_connection() as conn:
            cur = conn.execute(f'UPDATE events SET {set_clause} WHERE id=?', values)
            conn.commit()
            if cur.rowcount == 0:
                abort(404, description='Event not found')
    except sqlite3.Error as e:
        abort(500, description=str(e))
    return jsonify(message='Event updated successfully'), 200

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        with get_db_connection() as conn:
            cur = conn.execute('DELETE FROM events WHERE id=?', (event_id,))
            conn.commit()
            if cur.rowcount == 0:
                abort(404, description='Event not found')
    except sqlite3.Error as e:
        abort(500, description=str(e))
    return jsonify(message='Event deleted successfully'), 200

@app.route('/get_events_by_date', methods=['GET'])
def get_events_by_date():
    date = request.args.get('date')
    if not date:
        abort(400, description='Missing date parameter')
    try:
        with get_db_connection() as conn:
            rows = conn.execute('SELECT * FROM events WHERE date=?', (date,)).fetchall()
            events = [dict(row) for row in rows]
    except sqlite3.Error as e:
        abort(500, description=str(e))
    return jsonify(events), 200

if __name__ == '__main__':
    app.run(debug=False)