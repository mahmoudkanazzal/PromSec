#!/usr/bin/env python3
"""Flask application that stores user messages in a MySQL database with secure handling."""
import os
import sys
import logging
from flask import Flask, request, session, redirect
import MySQLdb

# Environment variable loading
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not FLASK_SECRET_KEY:
    raise RuntimeError('FLASK_SECRET_KEY environment variable not set')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'app_user')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'db')
missing_vars = []
if not DB_PASSWORD:
    missing_vars.append('DB_PASSWORD')
if missing_vars:
    raise RuntimeError('Missing required environment variable(s): ' + ', '.join(missing_vars))

FLASK_RUN_HOST = os.getenv('FLASK_RUN_HOST', '127.0.0.1')

# Logging configuration
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
handler.setLevel(logging.DEBUG)

# Flask app setup
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

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
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO messages (username, content) VALUES (%s, %s)"
            cursor.execute(sql, (username, message))
        conn.commit()
    except MySQLdb.Error as e:
        logger.info("Database error while inserting user message")
        logger.debug("Exception details: %s", e, exc_info=True)
        raise RuntimeError("Failed to store message")
    finally:
        if conn:
            conn.close()

@app.route('/post', methods=['POST'])
def post_message():
    username = session.get('username')
    if not username:
        return 'Unauthorized', 401
    message = request.form.get('message', '')
    message = message.strip()
    if not message or len(message) > 1000:
        return 'Bad Request', 400
    insert_user_message_in_db(username, message)
    return redirect('/')

if __name__ == '__main__':
    app.run(host=FLASK_RUN_HOST, port=5000, debug=False)