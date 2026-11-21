from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    return sqlite3.connect('events.db')

@app.route('/add_event', methods=['POST'])
def add_event():
    name = request.json['name']
    date = request.json['date']
    location = request.json['location']

    conn = get_db_connection()
    cursor = conn.cursor()

    query = f"INSERT INTO events (name, date, location) VALUES ('{name}', '{date}', '{location}')"
    cursor.execute(query)
    
    conn.commit()
    conn.close()

    return jsonify({"message": "Event added successfully"}), 201

@app.route('/search_events', methods=['GET'])
def search_events():
    keyword = request.args.get('keyword', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = f"SELECT * FROM events WHERE name LIKE '%{keyword}%' OR location LIKE '%{keyword}%'"
    cursor.execute(query)
    
    events = cursor.fetchall()
    conn.close()

    return jsonify(events), 200

@app.route('/update_event/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    new_name = request.json.get('name')
    new_date = request.json.get('date')
    new_location = request.json.get('location')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = f"UPDATE events SET name='{new_name}', date='{new_date}', location='{new_location}' WHERE id={event_id}"
    cursor.execute(query)
    
    conn.commit()
    conn.close()

    return jsonify({"message": "Event updated successfully"}), 200

@app.route('/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = f"DELETE FROM events WHERE id={event_id}"
    cursor.execute(query)
    
    conn.commit()
    conn.close()

    return jsonify({"message": "Event deleted successfully"}), 200

@app.route('/get_events_by_date', methods=['GET'])
def get_events_by_date():
    date = request.args.get('date', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = f"SELECT * FROM events WHERE date='{date}'"
    cursor.execute(query)
    
    events = cursor.fetchall()
    conn.close()

    return jsonify(events), 200

if __name__ == '__main__':
    app.run(debug=False)

