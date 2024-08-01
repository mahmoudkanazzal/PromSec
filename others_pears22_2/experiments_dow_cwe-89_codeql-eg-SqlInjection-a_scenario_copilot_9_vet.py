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
    con = MySQLdb.connect(user='root', passwd='root', db='sigmapoints')
    c = con.cursor()

    try:
        # Use parameterized query to prevent SQL injection
        select_query = "SELECT * FROM Subscribers WHERE Email = %s"
        c.execute(select_query, (email,))
        result = c.fetchall()

        if not result:
            return "Not subscribed"
        
        # Unsubscribe
        delete_query = "DELETE FROM Subscribers WHERE Email = %s"
        c.execute(delete_query, (email,))
        con.commit()
        
        return "Unsubscribed"
    except Exception as e:
        print(f"Error: {e}")
    finally:
        con.close()

    return "Not subscribed"

