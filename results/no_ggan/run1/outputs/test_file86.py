import os
from flask import Flask, redirect, request, session
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_me')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'user')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'appdb')

def get_db_connection():
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        use_unicode=True
    )

def insert_user_message_in_db(username, message):
    conn = get_db_connection()
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (username, content) VALUES (%s, %s)",
            (username, message)
        )
        conn.commit()
    finally:
        if cur is not None:
            cur.close()
        conn.close()

@app.route('/post', methods=['POST'])
def post_message():
    if 'username' not in session:
        return redirect('/login')
    username = session['username']
    message = request.form.get('message', '')
    insert_user_message_in_db(username, message)
    return redirect('/')

if __name__ == '__main__':
    app.run()