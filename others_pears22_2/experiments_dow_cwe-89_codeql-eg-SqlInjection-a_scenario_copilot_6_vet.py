from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

app = Flask(__name__)

# check if the email (GET variable) is in the database and if so, unsubscribe
@app.route('/unsubscribe')
def unsub():
    email = request.args.get('email')
    try:
        conn = MySQLdb.connect(host="localhost", user="root", passwd="pass", db="cwe")
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_basic_info WHERE email LIKE %s", (email,))
        row = cur.fetchone()
        if row:
            email = row[1]
            cur.execute("DELETE FROM user_subscriptions WHERE email = %s", (email,))
            cur.execute("DELETE FROM subscriptions WHERE email = %s", (email,))
            cur.close()
            conn.commit()
            conn.close()
            return email
        else:
            return "ERROR: no such email address in the database."
    except Exception as e:
        print(e)
        return "ERROR: Database connection error"

