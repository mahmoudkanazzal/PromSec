import os
from flask import Flask, request, session
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

def insert_user_message(username, message):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO user_messages (username, message) VALUES (%s, %s)", (username, message))
    connection.commit()
    cursor.close()
    connection.close()

@app.route('/post', methods=['POST'])
def post_message():
    if 'username' in session:
        username = session['username']
        message = request.form['message']
        insert_user_message(username, message)
        return 'Message posted successfully'
    else:
        return 'User not logged in'

if __name__ == '__main__':
    app.run()