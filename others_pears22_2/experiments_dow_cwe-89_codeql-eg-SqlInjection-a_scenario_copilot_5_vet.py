from flask import Flask, request
import os
import MySQLdb

app = Flask(__name__)

# Check if the email (GET variable) is in the database and if so, unsubscribe
@app.route('/unsubscribe')
def unsubscribe():
    db = MySQLdb.connect("localhost", "root", "password", "TESTDB")
    cursor = db.cursor()

    try:
        # Use parameterized query to prevent SQL injection
        sql = "DELETE FROM EMPLOYEE WHERE FIRST_NAME = %s AND LAST_NAME = %s"
        values = ('John', 'Doe')

        cursor.execute(sql, values)
        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

