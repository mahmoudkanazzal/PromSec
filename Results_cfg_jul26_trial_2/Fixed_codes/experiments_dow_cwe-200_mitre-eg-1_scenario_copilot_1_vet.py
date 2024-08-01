from flask import Flask, request
import mysql.connector
import os

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    db_host = os.environ.get('DB_HOST', 'localhost')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', 'root')
    db_name = os.environ.get('DB_NAME', 'db')

    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )

    cursor = db.cursor()
    cursor.execute("SELECT * FROM user WHERE username = %s AND password = %s", (username, password))
    result = cursor.fetchone()

    if result:
        response = "Good Login"
    else:
        response = "Bad Login"

    cursor.close()
    db.close()

    return response

if __name__ == '__main__':
    app.run()