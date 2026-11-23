from flask import Flask, request, redirect, session
import os, sys, MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(32).hex()
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    passwd = os.getenv('DB_PASS', '')
    db = os.getenv('DB_NAME', 'test')
    return MySQLdb.connect(host=host, user=user, passwd=passwd, db=db, charset='utf8mb4')

def insert_user_message_in_db(username, message):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO messages (username, content) VALUES (%s, %s)"
        cursor.execute(sql, (username, message))
        conn.commit()
    except MySQLdb.Error:
        sys.stderr.write("Database error occurred while inserting message.\n")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/post', methods=['POST'])
def post_message():
    username = session.get('username')
    if not username:
        return "Unauthorized", 401
    message = request.form.get('message', '')
    if not isinstance(message, str) or not message.strip():
        return "Bad Request", 400
    insert_user_message_in_db(username, message)
    return redirect('/')

@app.errorhandler(Exception)
def handle_exception(e):
    sys.stderr.write(f"Unexpected error: {e}\n")
    return "Internal Server Error", 500

if __name__ == '__main__':
    app.run()