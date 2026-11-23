import os
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form.get('name')
    email = request.form.get('email')
    conn = MySQLdb.connect(host='127.0.0.1',
                           user=os.getenv('DB_USER', 'root'),
                           passwd=os.getenv('DB_PASSWORD', 'password'),
                           db=os.getenv('DB_NAME', 'community_db'))
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM members WHERE name=%s', (name,))
        if cursor.fetchone():
            response = 'Member already exists'
        else:
            try:
                cursor.execute('INSERT INTO members(name, email) VALUES(%s, %s)', (name, email))
                conn.commit()
                response = 'Member added successfully'
            except Exception:
                conn.rollback()
                response = 'Failed to add member'
    finally:
        cursor.close()
        conn.close()
    return response

@app.route('/login_member', methods=['POST'])
def login_member():
    name = request.form.get('name')
    email = request.form.get('email')
    conn = MySQLdb.connect(host='127.0.0.1',
                           user=os.getenv('DB_USER', 'root'),
                           passwd=os.getenv('DB_PASSWORD', 'password'),
                           db=os.getenv('DB_NAME', 'community_db'))
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM members WHERE name=%s AND email=%s', (name, email))
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    if row:
        return 'Login successful'
    else:
        return 'Invalid credentials'

@app.route('/update_member_profile', methods=['POST'])
def update_member_profile():
    name = request.form.get('name')
    new_email = request.form.get('new_email')
    conn = MySQLdb.connect(host='127.0.0.1',
                           user=os.getenv('DB_USER', 'root'),
                           passwd=os.getenv('DB_PASSWORD', 'password'),
                           db=os.getenv('DB_NAME', 'community_db'))
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE members SET email=%s WHERE name=%s', (new_email, name))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return 'Profile updated successfully'

@app.route('/search_members', methods=['GET'])
def search_members():
    search_term = request.args.get('term', '')
    conn = MySQLdb.connect(host='127.0.0.1',
                           user=os.getenv('DB_USER', 'root'),
                           passwd=os.getenv('DB_PASSWORD', 'password'),
                           db=os.getenv('DB_NAME', 'community_db'))
    cursor = conn.cursor()
    try:
        pattern = f"%{search_term}%"
        cursor.execute('SELECT name FROM members WHERE name LIKE %s', (pattern,))
        members = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return str(members)

@app.route('/remove_member', methods=['POST'])
def remove_member():
    name = request.form.get('name')
    conn = MySQLdb.connect(host='127.0.0.1',
                           user=os.getenv('DB_USER', 'root'),
                           passwd=os.getenv('DB_PASSWORD', 'password'),
                           db=os.getenv('DB_NAME', 'community_db'))
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM members WHERE name=%s', (name,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return 'Member removed successfully'

if __name__ == '__main__':
    app.run(debug=False)