import os
from flask import Flask, request, session
import MySQLdb

app = Flask(__name__)
app.secret_key = os.urandom(24)

def establish_db_connection():
    return MySQLdb.connect(host=os.getenv("DB_HOST"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), database=os.getenv("DB_NAME"))

def insert_user_message(username, message):
    conn = establish_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (username, content) VALUES (%s, %s)", (username, message))
    conn.commit()
    conn.close()

@app.route('/post', methods=['POST'])
def post_message():
    username = session.get('username')
    message = request.form.get('message')
    insert_user_message(username, message)
    return 'Message posted successfully'

if __name__ == '__main__':
    app.run()