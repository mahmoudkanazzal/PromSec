import os
from flask import Flask, request, redirect, jsonify, make_response
import MySQLdb

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'testuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'test123')
DB_NAME = os.getenv('DB_NAME', 'EVENTDB')

def get_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4')

@app.route('/add_event', methods=['POST'])
def add_event():
    title = request.form.get('title', '').strip()
    date = request.form.get('date', '').strip()
    if not title or not date:
        return make_response('Bad Request', 400)
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT 1 FROM Events WHERE Title = %s', (title,))
            if cur.fetchone():
                return redirect('/add_event')
            cur.execute('INSERT INTO Events (Title, Date) VALUES (%s, %s)', (title, date))
            conn.commit()
            return redirect('/view_events')
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/update_event_date', methods=['POST'])
def update_event_date():
    title = request.form.get('title', '').strip()
    new_date = request.form.get('new_date', '').strip()
    if not title or not new_date:
        return make_response('Bad Request', 400)
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('UPDATE Events SET Date = %s WHERE Title = %s', (new_date, title))
            conn.commit()
            return make_response('Event date updated successfully', 200)
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/delete_event', methods=['POST'])
def delete_event():
    title = request.form.get('title', '').strip()
    if not title:
        return make_response('Bad Request', 400)
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('DELETE FROM Events WHERE Title = %s', (title,))
            conn.commit()
            return make_response('Event deleted successfully', 200)
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/search_events', methods=['GET'])
def search_events():
    term = request.args.get('term', '').strip()
    pattern = f"%{term}%"
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT Title, Date FROM Events WHERE Title LIKE %s', (pattern,))
            rows = cur.fetchall()
            result = [{'title': r[0], 'date': r[1]} for r in rows]
            return jsonify(result), 200
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/view_events', methods=['GET'])
def view_events():
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute('SELECT Title, Date FROM Events')
            rows = cur.fetchall()
            result = [{'title': r[0], 'date': r[1]} for r in rows]
            return jsonify(result), 200
        finally:
            cur.close()
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)