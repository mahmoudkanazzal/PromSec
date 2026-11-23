from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def get_connection():
    return MySQLdb.connect("127.0.0.1", "root", "password", "cwe_900")

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return "Username already exists"
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            return "You have successfully registered"
        except Exception:
            conn.rollback()
            return "Registration Failed"
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE username = %s AND password = %s", (username, password))
        if cursor.fetchone():
            return "Login successful"
        else:
            return "Invalid credentials"
    finally:
        cursor.close()
        conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username', '')
    new_email = request.form.get('email', '')
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET email = %s WHERE username = %s", (new_email, username))
        conn.commit()
        return "Profile updated successfully"
    finally:
        cursor.close()
        conn.close()

@app.route('/search_users', methods=['GET'])
def search_users():
    search_term = request.args.get('term', '')
    pattern = f"%{search_term}%"
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM users WHERE username LIKE %s", (pattern,))
        rows = cursor.fetchall()
        usernames = [row[0] for row in rows]
        return str(usernames)
    finally:
        cursor.close()
        conn.close()

@app.route('/delete_account', methods=['POST'])
def delete_account():
    username = request.form.get('username', '')
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
        return "Account deleted successfully"
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)