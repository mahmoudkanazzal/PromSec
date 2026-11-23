import os
import MySQLdb
from flask import Flask, request, redirect, abort, session
from flask_wtf.csrf import CSRFProtect

secret_key = os.getenv('FLASK_SECRET_KEY')
if not secret_key:
    raise RuntimeError('FLASK_SECRET_KEY environment variable must be set')

app = Flask(__name__)
app.secret_key = secret_key
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True

csrf = CSRFProtect(app)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

def insert_user_message_in_db(username, message):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (username, content) VALUES (%s, %s)",
            (username, message)
        )
        conn.commit()
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

@app.route('/post', methods=['POST'])
def post_message():
    if 'username' not in session:
        return redirect('/login')
    username = session['username']
    message = request.form.get('message', '')
    if len(message) > 2000:
        abort(400, description='Message too long')
    insert_user_message_in_db(username, message)
    return redirect('/')

if __name__ == '__main__':
    # In production, use a WSGI server instead of the built-in server.
    app.run(host='0.0.0.0', port=5000)