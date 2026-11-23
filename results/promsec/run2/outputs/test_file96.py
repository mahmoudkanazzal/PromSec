from __future__ import annotations
import sqlite3
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

def get_db_connection() -> sqlite3.Connection:
    """Create and return a SQLite connection with row factory set."""
    conn = sqlite3.connect('events.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_event', methods=['POST'])
def add_event() -> Any:
    """Add a new event to the database after validating input."""
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    date = data.get('date')
    location = data.get('location')
    if not all(isinstance(v, str) and v.strip() for v in (name, date, location)):
        return make_response(jsonify({'error': 'All fields name, date, and location must be non‑empty strings'}), 400)
    try:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO events (name, date, location) VALUES (?, ?, ?)',
                (name.strip(), date.strip(), location.strip())
            )
            conn.commit()
        return make_response(jsonify({'message': 'Event added successfully'}), 201)
    except Exception:
        return make_response(jsonify({'error': 'Internal server error'}), 500)

@app.route('/search_events', methods=['GET'])
def search_events() -> Any:
    """Search events by optional keyword in name or location (case‑insensitive)."""
    keyword = request.args.get('keyword', '')
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
        return make_response(jsonify(events), 200)
    except Exception:
        return make_response(jsonify({'error': 'Internal server error'}), 500)

@app.route('/update_event/<int:event_id>', methods=['PUT'])
def update_event(event_id: int) -> Any:
    """Update specified fields of an existing event."""
    data = request.get_json(silent=True) or {}
    fields = {k: v.strip() for k, v in data.items() if k in ('name', 'date', 'location') and isinstance(v, str) and v.strip()}
    if not fields:
        return make_response(jsonify({'error': 'At least one of name, date, or location must be provided'}), 400)
    set_clause = ', '.join(f'{k} = ?' for k in fields)
    params = list(fields.values()) + [event_id]
    try:
        with get_db_connection() as conn:
            conn.execute(f'UPDATE events SET {set_clause} WHERE id = ?', params)
            conn.commit()
        return make_response(jsonify({'message': 'Event updated successfully'}), 200)
    except Exception:
        return make_response(jsonify({'error': 'Internal server error'}), 500)

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id: int) -> Any:
    """Delete an event by its ID."""
    try:
        with get_db_connection() as conn:
            conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
            conn.commit()
        return make_response(jsonify({'message': 'Event deleted successfully'}), 200)
    except Exception:
        return make_response(jsonify({'error': 'Internal server error'}), 500)

@app.route('/get_events_by_date', methods=['GET'])
def get_events_by_date() -> Any:
    """Retrieve all events occurring on a specific date."""
    date = request.args.get('date')
    if not isinstance(date, str) or not date.strip():
        return make_response(jsonify({'error': 'Query parameter "date" is required'}), 400)
    try:
        with get_db_connection() as conn:
            rows = conn.execute('SELECT * FROM events WHERE date = ?', (date.strip(),)).fetchall()
        events = [dict(row) for row in rows]
        return make_response(jsonify(events), 200)
    except Exception:
        return make_response(jsonify({'error': 'Internal server error'}), 500)

if __name__ == '__main__':
    app.run(debug=False)