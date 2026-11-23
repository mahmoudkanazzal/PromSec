import os
from flask import Flask, request, Response
import MySQLdb
from contextlib import contextmanager

app = Flask(__name__)

@contextmanager
def get_db():
    conn = MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', ''),
        passwd=os.getenv('DB_PASSWORD', ''),
        db='community_db',
        charset='utf8mb4'
    )
    cur = conn.cursor()
    try:
        yield conn, cur
    finally:
        cur.close()
        conn.close()

@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form.get('name')
    email = request.form.get('email')
    if not name or not email:
        return Response('Failed to add member', status=400)
    try:
        with get_db() as (conn, cur):
            cur.execute("SELECT 1 FROM members WHERE name=%s", (name,))
            if cur.fetchone():
                return 'Member already exists'
            cur.execute("INSERT INTO members (name, email) VALUES (%s, %s)", (name, email))
            conn.commit()
            return 'Member added successfully'
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return 'Failed to add member'

@app.route('/login_member', methods=['POST'])
def login_member():
    name = request.form.get('name')
    email = request.form.get('email')
    if not name or not email:
        return Response('Invalid credentials', status=400)
    try:
        with get_db() as (conn, cur):
            cur.execute("SELECT 1 FROM members WHERE name=%s AND email=%s", (name, email))
            if cur.fetchone():
                return 'Login successful'
            return 'Invalid credentials'
    except Exception:
        return 'Invalid credentials'

@app.route('/update_member_profile', methods=['POST'])
def update_member_profile():
    name = request.form.get('name')
    new_email = request.form.get('new_email')
    if not name or not new_email:
        return Response('Failed to update profile', status=400)
    try:
        with get_db() as (conn, cur):
            cur.execute("UPDATE members SET email=%s WHERE name=%s", (new_email, name))
            conn.commit()
            return 'Profile updated successfully'
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return 'Failed to update profile'

@app.route('/search_members', methods=['GET'])
def search_members():
    term = request.args.get('term', '')
    like_term = f"%{term}%"
    try:
        with get_db() as (conn, cur):
            cur.execute("SELECT name FROM members WHERE name LIKE %s", (like_term,))
            rows = cur.fetchall()
            return str(rows)
    except Exception:
        return 'Failed to search members'

@app.route('/remove_member', methods=['POST'])
def remove_member():
    name = request.form.get('name')
    if not name:
        return Response('Failed to remove member', status=400)
    try:
        with get_db() as (conn, cur):
            cur.execute("DELETE FROM members WHERE name=%s", (name,))
            conn.commit()
            return 'Member removed successfully'
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return 'Failed to remove member'

if __name__ == '__main__':
    app.run(debug=False)