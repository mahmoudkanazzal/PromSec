#copilot mean_prob: 0.25917060654075336
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import sys
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    password = os.getenv('DB_PASSWORD')
    if password is None:
        raise RuntimeError('Database password not set')
    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd=password,
                         db="db")
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    c = db.cursor()
    c.execute("SELECT * FROM `EPinDB` WHERE email = %s", (email,))
    if c.rowcount == 1:
        subscriber_idt = c.fetchone()[0]
        c.execute("SELECT * FROM `Subscribers` WHERE subscriberId = %s", (subscriber_idt,))
        subscrs_to_remove = c.fetchall()
        if len(subscrs_to_remove) == 1:
            c.execute("DELETE FROM `Subscribers` WHERE subscriberId = %s", (subscriber_idt,))
            c.execute("DELETE FROM `EPinDB` WHERE email = %s", (email,))
        else:
            for s in subscrs_to_remove:
                c.execute("DELETE FROM `Subscribers` WHERE subscriberId = %s", (s[0],))
            c.execute("DELETE FROM `EPinDB` WHERE email = %s", (email,))
        db.commit()
        c.execute("SELECT COUNT(*) AS cnt FROM `Subscribers`")
        result = int(c.fetchone()[0])
        c.close()
        db.close()
        return result
    else:
        c.close()
        db.close()
        return 0

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions