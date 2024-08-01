from flask import Flask, request
import os
import MySQLdb

app = Flask(__name__)

# Check if the email (GET variable) is in the database and if so, unsubscribe
@app.route('/unsubscribe')
def unsubscribe_user():
    email = request.args.get('email')
    db = MySQLdb.connect(user=os.environ['C9_USER'], passwd=os.environ['DB_PASS'], db=os.environ['DB_NAME'])
    c = db.cursor()
    try:
        # Use parameterized query to prevent SQL injection
        delete_users_query = "DELETE FROM users WHERE email=%s"
        delete_subscriptions_query = "DELETE FROM subscriptions WHERE email=%s"
        
        # Pass the email as a parameter to the execute method
        c.execute(delete_users_query, (email,))
        c.execute(delete_subscriptions_query, (email,))
        
        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        c.close()
        db.close()

