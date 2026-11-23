#!/usr/bin/env python3
from flask import Flask, request
import os
import sys
import MySQLdb

__author__ = "redactedAuthorFirstname redactedAuthorLastname (redactedAuthorFirstname.redactedAuthorLastname@nyu.edu)"
__license__ = "MIT"

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd=os.getenv("DB_ROOT_PASSWORD", "root"),
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    count = 0
    cur.execute("SELECT * FROM subscriptions WHERE email = %s", (email,))
    for row in cur:
        cur2 = db.cursor()
        cur2.execute("DELETE FROM subscriptions WHERE email = %s", (email,))
        cur2.close()
        cur.close()
        count = count + 1
    db.commit()
    return count

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions