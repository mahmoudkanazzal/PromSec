import os
from flask import Flask, request, redirect, url_for
import MySQLdb

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'testuser')
    passwd = os.getenv('DB_PASSWORD', 'test123')
    db = os.getenv('DB_NAME', 'EVENTDB')
    return MySQLdb.connect(host=host, user=user, passwd=passwd, db=db, charset='utf8mb4')

def get_param(name, source):
    val = source.get(name, '')
    val = val.strip()
    if not val:
        return None
    return val

@app.route('/add_event', methods=['POST'])
def add_event():
    title = get_param('title', request.form)
    date = get_param('date', request.form)
    if not title or not date:
        return 'Bad Request: missing or empty parameter', 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 FROM events WHERE title = %s LIMIT 1', (title,))
        if cursor.fetchone():
            return redirect(url_for('add_event'))
        cursor.execute('INSERT INTO events (title, date) VALUES (%s, %s)', (title, date))
        conn.commit()
        return redirect(url_for('view_events'))
    except MySQLdb.Error as e:
        print(e)
        conn.rollback()
        return 'Internal Server Error', 500
    finally:
        cursor.close()
        conn.close()

@app.route('/update_event_date', methods=['POST'])
def update_event_date():
    title = get_param('title', request.form)
    new_date = get_param('new_date', request.form)
    if not title or not new_date:
        return 'Bad Request: missing or empty parameter', 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE events SET date = %s WHERE title = %s', (new_date, title))
        conn.commit()
        return 'Event date updated successfully'
    except MySQLdb.Error as e:
        print(e)
        conn.rollback()
        return 'Internal Server Error', 500
    finally:
        cursor.close()
        conn.close()

@app.route('/delete_event', methods=['POST'])
def delete_event():
    title = get_param('title', request.form)
    if not title:
        return 'Bad Request: missing or empty parameter', 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM events WHERE title = %s', (title,))
        conn.commit()
        return 'Event deleted successfully'
    except MySQLdb.Error as e:
        print(e)
        conn.rollback()
        return 'Internal Server Error', 500
    finally:
        cursor.close()
        conn.close()

@app.route('/search_events', methods=['GET'])
def search_events():
    term = get_param('term', request.args)
    if term is None:
        return 'Bad Request: missing or empty parameter', 400
    pattern = f'%{term}%'
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT title, date FROM events WHERE title LIKE %s', (pattern,))
        rows = cursor.fetchall()
        return str(rows)
    except MySQLdb.Error as e:
        print(e)
        return 'Internal Server Error', 500
    finally:
        cursor.close()
        conn.close()

@app.route('/view_events', methods=['GET'])
def view_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT title, date FROM events')
        rows = cursor.fetchall()
        return str(rows)
    except MySQLdb.Error as e:
        print(e)
        return 'Internal Server Error', 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)