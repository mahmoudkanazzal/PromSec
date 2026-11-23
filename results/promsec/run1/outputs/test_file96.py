import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

def get_db_connection():
    conn = sqlite3.connect('events.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/add_event', methods=['POST'])
def add_event():
    data = request.get_json()
    name = data.get('name')
    date = data.get('date')
    location = data.get('location')
    if not all([name, date, location]):
        return jsonify({'error': 'Missing fields'}), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO events (name, date, location) VALUES (?, ?, ?)', (name, date, location))
        conn.commit()
        return jsonify({'message': 'Event added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/search_events', methods=['GET'])
def search_events():
    keyword = request.args.get('keyword', '')
    pattern = f'%{keyword}%'
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM events WHERE name LIKE ? COLLATE NOCASE OR location LIKE ? COLLATE NOCASE', (pattern, pattern))
        rows = cur.fetchall()
        events = [dict(row) for row in rows]
        return jsonify(events), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/update_event/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.get_json()
    fields = {}
    for key in ('name', 'date', 'location'):
        if key in data:
            fields[key] = data[key]
    if not fields:
        return jsonify({'error': 'No fields to update'}), 400
    set_clause = ', '.join([f"{k}=?" for k in fields.keys()])
    params = list(fields.values())
    params.append(event_id)
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f'UPDATE events SET {set_clause} WHERE id=?', params)
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({'error': 'Event not found'}), 404
        return jsonify({'message': 'Event updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM events WHERE id=?', (event_id,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({'error': 'Event not found'}), 404
        return jsonify({'message': 'Event deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/get_events_by_date', methods=['GET'])
def get_events_by_date():
    date = request.args.get('date', '')
    if not date:
        return jsonify([]), 200
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM events WHERE date=?', (date,))
        rows = cur.fetchall()
        events = [dict(row) for row in rows]
        return jsonify(events), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)