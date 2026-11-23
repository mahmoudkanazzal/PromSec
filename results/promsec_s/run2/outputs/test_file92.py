import os
from flask import Flask, request, redirect, Response
import MySQLdb
from contextlib import closing

app = Flask(__name__)

def get_connection():
    return MySQLdb.connect(
        host='localhost',
        user=os.getenv('DB_USER', 'testuser'),
        passwd=os.getenv('DB_PASSWORD', 'test123'),
        db=os.getenv('DB_NAME', 'EVENTDB')
    )

@app.route('/add_event', methods=['POST'])
def add_event():
    title = request.form.get('title')
    date = request.form.get('date')
    if not title or not date:
        return Response('Missing title or date', status=400, mimetype='text/plain')
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute('SELECT 1 FROM Events WHERE Title = %s', (title,))
            if cur.fetchone():
                return redirect('./add_event')
            cur.execute('INSERT INTO Events (Title, Date) VALUES (%s, %s)', (title, date))
            conn.commit()
    return redirect('./view_events')

@app.route('/update_event_date', methods=['POST'])
def update_event_date():
    title = request.form.get('title')
    new_date = request.form.get('new_date')
    if not title or not new_date:
        return Response('Missing title or new_date', status=400, mimetype='text/plain')
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute('UPDATE Events SET Date = %s WHERE Title = %s', (new_date, title))
            conn.commit()
    return Response('Event date updated successfully', mimetype='text/plain')

@app.route('/delete_event', methods=['POST'])
def delete_event():
    title = request.form.get('title')
    if not title:
        return Response('Missing title', status=400, mimetype='text/plain')
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute('DELETE FROM Events WHERE Title = %s', (title,))
            conn.commit()
    return Response('Event deleted successfully', mimetype='text/plain')

@app.route('/search_events', methods=['GET'])
def search_events():
    term = request.args.get('term', '')
    pattern = f'%{term}%'
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute('SELECT * FROM Events WHERE Title LIKE %s', (pattern,))
            rows = cur.fetchall()
    return str(rows)

@app.route('/view_events', methods=['GET'])
def view_events():
    with closing(get_connection()) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute('SELECT * FROM Events')
            rows = cur.fetchall()
    return str(rows)

if __name__ == '__main__':
    app.run(debug=False)