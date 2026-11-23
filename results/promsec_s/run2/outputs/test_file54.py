from flask import Flask, request, redirect
import os, sys, hashlib
import MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        host = os.getenv('DB_HOST')
        user = os.getenv('DB_USER')
        passwd = os.getenv('DB_PASS')
        db = os.getenv('DB_NAME')
        missing = [name for var, name in [(host, 'DB_HOST'), (user, 'DB_USER'), (passwd, 'DB_PASS'), (db, 'DB_NAME')] if not var]
        if missing:
            raise RuntimeError('Missing environment variables: ' + ', '.join(missing))
        conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db)
        try:
            cur = conn.cursor()
            cur.execute("SELECT password FROM user_info WHERE username=%s", (username,))
            row = cur.fetchone()
            if not row:
                return redirect('/error')
            stored_hash = row[0]
            supplied_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
            if supplied_hash == stored_hash:
                return redirect('/')
            return redirect('/error')
        finally:
            conn.close()
    except Exception as e:
        sys.stderr.write(str(e) + '\n')
        return redirect('/error')

if __name__ == '__main__':
    app.run()