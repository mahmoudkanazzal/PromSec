from flask import Flask, request, session
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

def establish_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME')
    )

def insert_message(username, message):
    conn = establish_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO messages (username, message) VALUES (%s, %s)"
    cursor.execute(query, (username, message))
    conn.commit()
    conn.close()

@app.route('/post', methods=['POST'])
def post_message():
    if 'username' in session:
        username = session['username']
        message = request.form['message']
        insert_message(username, message)
        return 'Message posted successfully'
    else:
        return 'User not logged in'

if __name__ == '__main__':
    app.run()