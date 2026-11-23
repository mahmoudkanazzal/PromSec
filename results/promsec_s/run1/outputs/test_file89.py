import os
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def get_db():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'testuser'),
        passwd=os.getenv('DB_PASSWORD', 'test123'),
        db=os.getenv('DB_NAME', 'TESTDB')
    )

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return redirect('./register')
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('./login')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = %s AND password = %s", (username, password))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return "Login successful"
    return "Invalid credentials"

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    new_email = request.form.get('email')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET Email = %s WHERE username = %s", (new_email, username))
    conn.commit()
    cur.close()
    conn.close()
    return "Profile updated successfully"

@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form.get('username')
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username = %s", (username,))
    conn.commit()
    cur.close()
    conn.close()
    return "User deleted successfully"

@app.route('/search_users', methods=['GET'])
def search_users():
    term = request.args.get('term', '')
    pattern = f"%{term}%"
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username LIKE %s", (pattern,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return ', '.join(row[0] for row in rows)

if __name__ == '__main__':
    app.run(debug=False)