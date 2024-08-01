from flask import Flask, request
import os
import subprocess
import sys
import MySQLdb

app = Flask(__name__)

# Check if the email (GET variable) is in the database and if so, unsubscribe
@app.route('/unsubscribe')
def unsubscribe():
    email = request.args.get('email')
    conn = MySQLdb.connect("localhost", "root", "password", "falcon_exp")
    cursor = conn.cursor()

    try:
        # Use parameterized query to prevent SQL injection
        select_query = "SELECT * FROM users WHERE email = %s"
        cursor.execute(select_query, (email,))
        data = cursor.fetchall()

        if len(data) == 0:
            return '0'
        else:
            retcode = subprocess.call(["php", "/home/ubuntu/falcon/script/database/unsubscribe.php", email])

            if retcode == 0:
                return '1'
            else:
                return '0'
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
    
    return '0'

