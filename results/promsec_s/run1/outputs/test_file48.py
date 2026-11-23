import os
import logging
from flask import Flask, request, Response
import mysql.connector
import bcrypt

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return Response('Missing username or password', status=400, mimetype='text/plain')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT password FROM userdaten WHERE username = %s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row:
            stored_hash = row[0]
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return Response('Eingeloggt', mimetype='text/plain')
        return Response('Falscher Benutzername oder Passwort', mimetype='text/plain')
    except mysql.connector.Error as e:
        logger.error('Database error: %s', e)
        return Response('Internal server error', status=500, mimetype='text/plain')
    except Exception as e:
        logger.error('Unexpected error: %s', e)
        return Response('Internal server error', status=500, mimetype='text/plain')
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    app.run()