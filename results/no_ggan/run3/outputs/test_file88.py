import os
import MySQLdb
from flask import Flask, request

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', '127.0.0.1')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'password')
    db = os.getenv('DB_NAME', 'community_db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form.get('name', '')
    email = request.form.get('email', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM members WHERE name = %s", (name,))
        if cursor.fetchone():
            return "Member already exists"
        cursor.execute("INSERT INTO members (name, email) VALUES (%s, %s)", (name, email))
        conn.commit()
        return "Member added successfully"
    except MySQLdb.Error:
        conn.rollback()
        return "Failed to add member"
    finally:
        cursor.close()
        conn.close()

@app.route('/login_member', methods=['POST'])
def login_member():
    name = request.form.get('name', '')
    email = request.form.get('email', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM members WHERE name = %s AND email = %s", (name, email))
        if cursor.fetchone():
            return "Login successful"
        else:
            return "Invalid credentials"
    finally:
        cursor.close()
        conn.close()

@app.route('/update_member_profile', methods=['POST'])
def update_member_profile():
    name = request.form.get('name', '')
    new_email = request.form.get('new_email', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE members SET email = %s WHERE name = %s", (new_email, name))
        conn.commit()
        return "Profile updated successfully"
    finally:
        cursor.close()
        conn.close()

@app.route('/search_members', methods=['GET'])
def search_members():
    term = request.args.get('term', '')
    pattern = f"%{term}%"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM members WHERE name LIKE %s", (pattern,))
        rows = cursor.fetchall()
        return str([row[0] for row in rows])
    finally:
        cursor.close()
        conn.close()

@app.route('/remove_member', methods=['POST'])
def remove_member():
    name = request.form.get('name', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM members WHERE name = %s", (name,))
        conn.commit()
        return "Member removed successfully"
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)