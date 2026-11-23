from flask import Flask, request
import MySQLdb

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = None
    cur = None
    try:
        os = __import__('os')
        conn = MySQLdb.connect(host='127.0.0.1',
                               user=os.getenv('DB_USER', 'root'),
                               passwd=os.getenv('DB_PASS', 'password'),
                               db=os.getenv('DB_NAME', 'cwe_900'))
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            return "Username already exists"
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return "You have successfully registered"
    except Exception:
        if conn:
            conn.rollback()
        return "Registration Failed"
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)