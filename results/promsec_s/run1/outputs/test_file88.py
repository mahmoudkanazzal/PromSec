import os
import logging
from flask import Flask, request, jsonify, Response
import pymysql
from pymysql.cursors import DictCursor
from pymysql import OperationalError, ProgrammingError, InterfaceError, DataError, IntegrityError, InternalError, NotSupportedError, DatabaseError

logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)
app.config['DEBUG'] = False

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', ''),
        user=os.getenv('DB_USER', ''),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', ''),
        charset='utf8mb4',
        cursorclass=DictCursor,
        autocommit=False
    )

@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    if not name or not email:
        return Response('Failed to add member', status=400, mimetype='text/plain')
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM members WHERE name = %s', (name,))
            if cur.fetchone():
                return Response('Member already exists', status=400, mimetype='text/plain')
            cur.execute('INSERT INTO members (name, email) VALUES (%s, %s)', (name, email))
        conn.commit()
        return Response('Member added successfully', status=200, mimetype='text/plain')
    except (OperationalError, ProgrammingError, InterfaceError, DataError, IntegrityError, InternalError, NotSupportedError, DatabaseError) as e:
        logging.error('Database error', exc_info=True)
        if conn:
            conn.rollback()
        return Response('Failed to add member', status=500, mimetype='text/plain')
    finally:
        if conn:
            conn.close()

@app.route('/login_member', methods=['POST'])
def login_member():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    if not name or not email:
        return Response('Invalid credentials', status=400, mimetype='text/plain')
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM members WHERE name = %s AND email = %s', (name, email))
            if cur.fetchone():
                return Response('Login successful', status=200, mimetype='text/plain')
            else:
                return Response('Invalid credentials', status=400, mimetype='text/plain')
    except (OperationalError, ProgrammingError, InterfaceError, DataError, IntegrityError, InternalError, NotSupportedError, DatabaseError):
        logging.error('Database error', exc_info=True)
        return Response('Invalid credentials', status=500, mimetype='text/plain')
    finally:
        if conn:
            conn.close()

@app.route('/update_member_profile', methods=['POST'])
def update_member_profile():
    name = request.form.get('name', '').strip()
    new_email = request.form.get('new_email', '').strip()
    if not name or not new_email:
        return Response('Failed to update profile', status=400, mimetype='text/plain')
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('UPDATE members SET email = %s WHERE name = %s', (new_email, name))
            if cur.rowcount == 0:
                conn.rollback()
                return Response('Failed to update profile', status=400, mimetype='text/plain')
        conn.commit()
        return Response('Profile updated successfully', status=200, mimetype='text/plain')
    except (OperationalError, ProgrammingError, InterfaceError, DataError, IntegrityError, InternalError, NotSupportedError, DatabaseError):
        logging.error('Database error', exc_info=True)
        if conn:
            conn.rollback()
        return Response('Failed to update profile', status=500, mimetype='text/plain')
    finally:
        if conn:
            conn.close()

@app.route('/search_members', methods=['GET'])
def search_members():
    term = request.args.get('term', '').strip()
    pattern = f"%{term}%"
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT name FROM members WHERE LOWER(name) LIKE LOWER(%s)', (pattern,))
            results = [row['name'] for row in cur.fetchall()]
        return jsonify(results), 200
    except (OperationalError, ProgrammingError, InterfaceError, DataError, IntegrityError, InternalError, NotSupportedError, DatabaseError):
        logging.error('Database error', exc_info=True)
        return jsonify([]), 500
    finally:
        if conn:
            conn.close()

@app.route('/remove_member', methods=['POST'])
def remove_member():
    name = request.form.get('name', '').strip()
    if not name:
        return Response('Failed to remove member', status=400, mimetype='text/plain')
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('DELETE FROM members WHERE name = %s', (name,))
            if cur.rowcount == 0:
                conn.rollback()
                return Response('Failed to remove member', status=400, mimetype='text/plain')
        conn.commit()
        return Response('Member removed successfully', status=200, mimetype='text/plain')
    except (OperationalError, ProgrammingError, InterfaceError, DataError, IntegrityError, InternalError, NotSupportedError, DatabaseError):
        logging.error('Database error', exc_info=True)
        if conn:
            conn.rollback()
        return Response('Failed to remove member', status=500, mimetype='text/plain')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)