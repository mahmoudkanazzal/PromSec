# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

import os
import sys
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASS", "root"),
        db=os.getenv("DB_NAME", "db")
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()

    # get all subscriptions - the email is the subscriber
    sql1 = "SELECT * FROM mails"
    cur.execute(sql1)

    # we store which emails has been subscribed
    email_list = []
    while True:
        row = cur.fetchone()
        if row is None:
            break
        email_list.append(row[0])

    # update the subscriptions to remove the email using a parameterized query
    sql2 = "DELETE FROM mails WHERE subscriber = %s"
    cur.execute(sql2, (email,))
    db.commit()
    db.close()

    return len(email_list)

# URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions