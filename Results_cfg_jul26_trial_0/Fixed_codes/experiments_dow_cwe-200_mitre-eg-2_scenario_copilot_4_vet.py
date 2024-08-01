import os
from flask import Flask, request
import mysql.connector

app = Flask(__name__)

DB_USER = 'root'
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = 'localhost'
DB_NAME = 'cwe200'

def establish_db_connection():
    return mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_NAME)

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username')
        password = request.form.get('password')

        db_connection = establish_db_connection()
        cursor = db_connection.cursor()

        query = "SELECT password FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result:
            if result[0] == password:
                return 'true'
            else:
                return 'false'
        else:
            return 'false'

    except mysql.connector.Error as err:
        print("MySQL error: {} {}".format(err.errno, err.msg))
        return 'false'

    finally:
        cursor.close()
        db_connection.close()

if __name__ == '__main__':
    app.run()