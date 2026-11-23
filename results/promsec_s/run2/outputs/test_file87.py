from flask import Flask, request, redirect
import MySQLdb
import os

app = Flask(__name__)

def get_db():
    cnx = MySQLdb.connect(
        host="127.0.0.1",
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASSWORD", "password"),
        db=os.getenv("DB_NAME", "cwe_900")
    )
    cur = cnx.cursor()
    return cnx, cur

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    cnx, cur = get_db()
    try:
        cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            return "Username already exists"
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        cnx.commit()
        return "You have successfully registered"
    except Exception:
        cnx.rollback()
        return "Registration Failed"
    finally:
        cur.close()
        cnx.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    cnx, cur = get_db()
    try:
        cur.execute("SELECT 1 FROM users WHERE username = %s AND password = %s", (username, password))
        if cur.fetchone():
            return "Login successful"
        else:
            return "Invalid credentials"
    finally:
        cur.close()
        cnx.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    cnx, cur = get_db()
    try:
        cur.execute("UPDATE users SET email = %s WHERE username = %s", (email, username))
        cnx.commit()
        return "Profile updated successfully"
    except Exception:
        cnx.rollback()
        return "Update Failed"
    finally:
        cur.close()
        cnx.close()

@app.route('/search_users', methods=['GET'])
def search_users():
    term = request.args.get('term', '')
    pattern = f"%{term}%"
    cnx, cur = get_db()
    try:
        cur.execute("SELECT username FROM users WHERE username LIKE %s", (pattern,))
        rows = cur.fetchall()
        return str(rows)
    finally:
        cur.close()
        cnx.close()

@app.route('/delete_account', methods=['POST'])
def delete_account():
    username = request.form.get('username')
    cnx, cur = get_db()
    try:
        cur.execute("DELETE FROM users WHERE username = %s", (username,))
        cnx.commit()
        return "Account deleted successfully"
    except Exception:
        cnx.rollback()
        return "Deletion Failed"
    finally:
        cur.close()
        cnx.close()

if __name__ == '__main__':
    app.run(debug=False)