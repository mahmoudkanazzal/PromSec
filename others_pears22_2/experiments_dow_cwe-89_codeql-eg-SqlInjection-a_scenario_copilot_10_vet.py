from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

app = Flask(__name__)

# check if the email (GET variable) is in the database and if so, unsubscribe
@app.route('/unsubscribe')
def unsubscribe():
    email = request.args.get('email', '', type=str)

    conn = MySQLdb.connect(host="localhost", user="root", passwd="password", db="wad")
    cursor = conn.cursor()

    # Use parameterized query to avoid SQL injection
    query = "SELECT * FROM users WHERE email = %s"
    cursor.execute(query, (email,))

    if cursor.rowcount == 1:
        # Use parameterized query to avoid SQL injection
        delete_query = "DELETE FROM users WHERE email = %s"
        cursor.execute(delete_query, (email,))
        conn.commit()

        # Print the remaining users
        cursor.execute("SELECT * FROM users")
        print(cursor.fetchall())

        cursor.close()
        conn.close()
        return '1'
    else:
        return '0'

