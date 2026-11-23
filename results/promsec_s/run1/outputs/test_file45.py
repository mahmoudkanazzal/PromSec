from flask import Flask, request, redirect, session
import os
import MySQLdb
import bcrypt

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/login')
    conn = None
    try:
        conn = MySQLdb.connect(host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'), passwd=os.getenv('DB_PASSWORD'), db=os.getenv('DB_NAME'))
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id, role, password_hash FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect('/dashboard')
        return redirect('/login')
    except MySQLdb.Error as e:
        app.logger.error(e)
        return redirect('/login')
    except bcrypt.exceptions.InvalidHash as e:
        app.logger.error(e)
        return redirect('/login')
    finally:
        if conn:
            conn.close()
if __name__ == '__main__':
    app.run()