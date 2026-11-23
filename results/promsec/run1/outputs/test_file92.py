import os
from flask import Flask, request, jsonify, redirect
import MySQLdb
import MySQLdb.cursors

app = Flask(__name__)

def get_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST', ''),
        user=os.getenv('DB_USER', ''),
        passwd=os.getenv('DB_PASSWORD', ''),
        db=os.getenv('DB_NAME', ''),
        charset='utf8mb4',
        cursorclass=MySQLdb.cursors.DictCursor
    )

@app.route('/add_event', methods=['POST'])
def add_event():
    title = request.form.get('title')
    date = request.form.get('date')
    if not title or not date:
        return jsonify(error='Missing title or date'), 400
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM Events WHERE Title = %s", (title,))
            if cur.fetchone():
                return redirect('./add_event')
            cur.execute("INSERT INTO Events (Title, Date) VALUES (%s, %s)", (title, date))
        conn.commit()
        return redirect('./view_events')
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify(error=str(e)), 500
    finally:
        if conn:
            conn.close()

@app.route('/update_event_date', methods=['POST'])
def update_event_date():
    title = request.form.get('title')
    new_date = request.form.get('new_date')
    if not title or not new_date:
        return jsonify(error='Missing title or new_date'), 400
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE Events SET Date = %s WHERE Title = %s", (new_date, title))
        conn.commit()
        return jsonify(message='Event date updated successfully')
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify(error=str(e)), 500
    finally:
        if conn:
            conn.close()

@app.route('/delete_event', methods=['POST'])
def delete_event():
    title = request.form.get('title')
    if not title:
        return jsonify(error='Missing title'), 400
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM Events WHERE Title = %s", (title,))
        conn.commit()
        return jsonify(message='Event deleted successfully')
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify(error=str(e)), 500
    finally:
        if conn:
            conn.close()

@app.route('/search_events', methods=['GET'])
def search_events():
    term = request.args.get('term', '')
    pattern = f"%{term}%"
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Events WHERE Title LIKE %s", (pattern,))
            rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify(error=str(e)), 500
    finally:
        if conn:
            conn.close()

@app.route('/view_events', methods=['GET'])
def view_events():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Events")
            rows = cur.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify(error=str(e)), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)