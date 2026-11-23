import os
import json
from flask import Flask, request, redirect, url_for, jsonify
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'testuser')
    password = os.getenv('DB_PASSWORD', 'test123')
    db = os.getenv('DB_NAME', 'EVENTDB')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/add_event', methods=['POST'])
def add_event():
    title = request.form.get('title', '').strip()
    date = request.form.get('date', '').strip()
    if not title or not date:
        return jsonify({'error':'Bad Request','message':'Title and date are required'}),400
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Events WHERE Title = %s", (title,))
            if cur.fetchone():
                return redirect(url_for('add_event'))
            cur.execute("INSERT INTO Events (Title, Date) VALUES (%s, %s)", (title, date))
        conn.commit()
        return redirect(url_for('view_events'))
    except Exception as e:
        if conn:
            conn.rollback()
        print(e)
        return jsonify({'error':'Internal Server Error','message':str(e)}),500
    finally:
        if conn:
            conn.close()

@app.route('/update_event_date', methods=['POST'])
def update_event_date():
    title = request.form.get('title', '').strip()
    new_date = request.form.get('new_date', '').strip()
    if not title or not new_date:
        return jsonify({'error':'Bad Request','message':'Title and new_date are required'}),400
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE Events SET Date = %s WHERE Title = %s", (new_date, title))
        conn.commit()
        return jsonify({'message':'Event date updated'}),200
    except Exception as e:
        if conn:
            conn.rollback()
        print(e)
        return jsonify({'error':'Internal Server Error','message':str(e)}),500
    finally:
        if conn:
            conn.close()

@app.route('/delete_event', methods=['POST'])
def delete_event():
    title = request.form.get('title', '').strip()
    if not title:
        return jsonify({'error':'Bad Request','message':'Title is required'}),400
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM Events WHERE Title = %s", (title,))
        conn.commit()
        return jsonify({'message':'Event deleted'}),200
    except Exception as e:
        if conn:
            conn.rollback()
        print(e)
        return jsonify({'error':'Internal Server Error','message':str(e)}),500
    finally:
        if conn:
            conn.close()

@app.route('/search_events', methods=['GET'])
def search_events():
    term = request.args.get('term', '').strip()
    pattern = f"%{term}%"
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Events WHERE Title LIKE %s", (pattern,))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            result = [dict(zip(columns, row)) for row in rows]
        return jsonify(result),200
    except Exception as e:
        print(e)
        return jsonify({'error':'Internal Server Error','message':str(e)}),500
    finally:
        if conn:
            conn.close()

@app.route('/view_events', methods=['GET'])
def view_events():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Events")
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            result = [dict(zip(columns, row)) for row in rows]
        return jsonify(result),200
    except Exception as e:
        print(e)
        return jsonify({'error':'Internal Server Error','message':str(e)}),500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)