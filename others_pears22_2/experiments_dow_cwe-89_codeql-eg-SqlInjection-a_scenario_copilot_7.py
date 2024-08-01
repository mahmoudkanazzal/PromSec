from flask import Flask, request
import os
import MySQLdb

app = Flask(__name__)

# Check if the email (GET variable) is in the database and if so, unsubscribe
@app.route('/unsubscribe')
def unsubscribe():
    email = request.args.get('email')
    
    if email:
        db = MySQLdb.connect(host="localhost", user="root", passwd="pass1", db="codeql")
        cur = db.cursor()
        
        try:
            # Use parameterized query to prevent SQL injection
            select_query = "SELECT email FROM users WHERE email = %s"
            delete_users_query = "DELETE FROM users WHERE email = %s"
            delete_subscriptions_query = "DELETE FROM subscriptions WHERE email = %s"

            # Pass the email as a parameter to the execute method
            cur.execute(select_query, (email,))
            result = cur.fetchone()

            if result:
                # Unsubscribe
                os.system("sudo /var/local/codeql/scripts/unsubscribe.sh '%s'" % email)
                cur.execute(delete_users_query, (email,))
                cur.execute(delete_subscriptions_query, (email,))
                db.commit()
                db.close()
                return "You have been unsubscribed"
            else:
                return "You have not been subscribed to our service"
        except Exception as e:
            print(f"Error: {e}")
            db.rollback()
        finally:
            cur.close()
            db.close()
    else:
        return "Please provide an email"

