import os
from flask import Flask, request
import mysql.connector

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='cwe200',
            user='root',
            password=os.getenv('MYSQL_PASSWORD', '')
        )
        cursor = connection.cursor()

        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            if result[0] == password:
                return 'true'
            else:
                return 'false'
        else:
            return 'false'

    except mysql.connector.Error as error:
        return 'false'

    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    app.run()