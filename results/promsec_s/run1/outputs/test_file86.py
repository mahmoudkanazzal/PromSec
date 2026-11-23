from flask import Flask, request, redirect, session, abort
import os
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-me')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASS', 'root')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

def insert_user_message_in_db(username, message):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO messages (username, content) VALUES (%s, %s)", (username, message))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except MySQLdb.Error:
        if conn:
            try:
                conn.rollback()
            except:
                pass
            try:
                conn.close()
            except:
                pass
        return False

@app.route('/post', methods=['POST'])
def post_message():
    username = session.get('username')
    if not username:
        abort(401)
    message = request.form.get('message')
    if not message:
        abort(400)
    if not insert_user_message_in_db(username, message):
        abort(500)
    return redirect('/')