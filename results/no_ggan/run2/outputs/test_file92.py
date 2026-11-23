import os
import MySQLdb
import MySQLdb.cursors
from flask import Flask, request, redirect, jsonify, make_response

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'testuser')
    password = os.getenv('DB_PASSWORD', 'test123')
    db = os.getenv('DB_NAME', 'EVENTDB')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/add_event', methods=['POST'])
def add_event():
    title = request.form.get('title', '').strip()
    date = request.form.get('date', '').strip()
    if not title or not date:
        return redirect(request.url)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM events WHERE title = %s LIMIT 1', (title,))
        if cursor.fetchone():
            return redirect(request.url)
        cursor.execute('INSERT INTO events (title, date) VALUES (%s, %s)', (title, date))
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/view_events')

@app.route('/update_event_date', methods=['POST'])
def update_event_date():
    title = request.form.get('title', '').strip()
    new_date = request.form.get('new_date', '').strip()
    if not title or not new_date:
        return make_response('Missing title or new_date', 400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE events SET date = %s WHERE title = %s', (new_date, title))
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return 'Event date updated successfully'

@app.route('/delete_event', methods=['POST'])
def delete_event():
    title = request.form.get('title', '').strip()
    if not title:
        return make_response('Missing title', 400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM events WHERE title = %s', (title,))
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return 'Event deleted successfully'

@app.route('/search_events', methods=['GET'])
def search_events():
    term = request.args.get('term', '').strip()
    pattern = f"%{term}%"
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM events WHERE title LIKE %s', (pattern,))
        rows = cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return jsonify(rows)

@app.route('/view_events', methods=['GET'])
def view_events():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM events')
        rows = cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    app.run(debug=False)