import os
from flask import Flask, request, session, redirect

import MySQLdb

app = Flask(__name__)
app.secret_key = os.urandom(24)

def establish_db_connection():
    return MySQLdb.connect(host=os.environ.get('DB_HOST', 'localhost'),
                           user=os.environ.get('DB_USER', 'root'),
                           passwd=os.environ.get('DB_PASS', 'root'),
                           db=os.environ.get('DB_NAME', 'db'))

def insert_user_message_in_db(username, message):
    conn = establish_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (username, content) VALUES (%s, %s)", (username, message))
    conn.commit()
    conn.close()

@app.route('/post', methods=['POST'])
def post():
    if 'username' in session:
        username = session['username']
        message = request.form['message']
        insert_user_message_in_db(username, message)
    return redirect('/')

if __name__ == '__main__':
    app.run()