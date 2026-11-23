import os
import MySQLdb
from flask import Flask, request, redirect, session, abort

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    db = os.getenv('DB_NAME')
    missing = []
    if not user:
        missing.append('DB_USER')
    if not password:
        missing.append('DB_PASSWORD')
    if not db:
        missing.append('DB_NAME')
    if missing:
        raise RuntimeError('Missing required environment variables: ' + ', '.join(missing))
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

def insert_user_message_in_db(username, message):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = 'INSERT INTO messages (username, content) VALUES (%s, %s)'
        cursor.execute(sql, (username, message))
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/post', methods=['POST'])
def post():
    if 'username' not in session:
        abort(401)
    username = session['username']
    message = request.form.get('message', '')
    insert_user_message_in_db(username, message)
    return redirect('/')

if __name__ == '__main__':
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')
    app.run(host='0.0.0.0', port=5000)