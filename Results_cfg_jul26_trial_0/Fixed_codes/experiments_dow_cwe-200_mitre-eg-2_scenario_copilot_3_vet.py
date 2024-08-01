import os
from flask import Flask, request
import mysql.connector

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')

db = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name
)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
    user = cursor.fetchone()

    if user:
        return 'Login successful'
    else:
        return 'Login failed'

if __name__ == '__main__':
    app.run()