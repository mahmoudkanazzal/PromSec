from flask import Flask, request
import os
import MySQLdb

app = Flask(__name__)

# Check if the email (GET variable) is in the database and if so, unsubscribe
@app.route('/unsubscribe')
def unsubscribe():
    email = request.args.get('email')
    db = MySQLdb.connect(host="localhost", user="root", passwd="password", db="cwexperiments")
    cur = db.cursor()
    
    try:
        # Use parameterized query to prevent SQL injection
        select_query = "SELECT * FROM users WHERE email = %s"
        delete_query = "DELETE FROM users WHERE email = %s"

        # Pass the email as a parameter to the execute method
        cur.execute(select_query, (email,))

        if cur.rowcount == 0:
            return "<h1>Not Found</h1>"
        else:
            cur.execute(delete_query, (email,))
            db.commit()
            return "<h1>Success!</h1>"
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        cur.close()
        db.close()

