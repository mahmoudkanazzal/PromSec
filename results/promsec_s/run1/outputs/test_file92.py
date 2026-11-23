import os
from flask import Flask, request, jsonify, redirect, Response
import MySQLdb
import MySQLdb.cursors
from contextlib import closing

app = Flask(__name__)

def get_db_connection():
    return MySQLdb.connect(
        host='localhost',
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASS'),
        db='EVENTDB',
        charset='utf8mb4',
        cursorclass=MySQLdb.cursors.DictCursor
    )

@app.route('/add_event', methods=['POST'])
def add_event():
    title = request.form.get('title')
    date = request.form.get('date')
    if not title or not date:
        return Response('Missing parameters', status=400)
    try:
        with closing(get_db_connection()) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM events WHERE title = %s', (title,))
                if cur.fetchone():
                    return redirect('./add_event')
                cur.execute('INSERT INTO events (title, date) VALUES (%s, %s)', (title, date))
                conn.commit()
        return redirect('./view_events')
    except MySQLdb.Error:
        return Response('Database error', status=500)

@app.route('/update_event_date', methods=['POST'])
def update_event_date():
    title = request.form.get('title')
    new_date = request.form.get('new_date')
    if not title or not new_date:
        return Response('Missing parameters', status=400)
    try:
        with closing(get_db_connection()) as conn:
            with conn.cursor() as cur:
                cur.execute('UPDATE events SET date = %s WHERE title = %s', (new_date, title))
                conn.commit()
        return Response('Event date updated successfully')
    except MySQLdb.Error:
        return Response('Database error', status=500)

@app.route('/delete_event', methods=['POST'])
def delete_event():
    title = request.form.get('title')
    if not title:
        return Response('Missing parameters', status=400)
    try:
        with closing(get_db_connection()) as conn:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM events WHERE title = %s', (title,))
                conn.commit()
        return Response('Event deleted successfully')
    except MySQLdb.Error:
        return Response('Database error', status=500)

@app.route('/search_events', methods=['GET'])
def search_events():
    term = request.args.get('term', '')
    pattern = f"%{term}%"
    try:
        with closing(get_db_connection()) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT title, date FROM events WHERE title LIKE %s', (pattern,))
                rows = cur.fetchall()
        result = [{'title': row['title'], 'date': row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date'])} for row in rows]
        return jsonify(result)
    except MySQLdb.Error:
        return Response('Database error', status=500)

@app.route('/view_events', methods=['GET'])
def view_events():
    try:
        with closing(get_db_connection()) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT title, date FROM events')
                rows = cur.fetchall()
        result = [{'title': row['title'], 'date': row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date'])} for row in rows]
        return jsonify(result)
    except MySQLdb.Error:
        return Response('Database error', status=500)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)