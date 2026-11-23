#!/bin/python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

__author__ = "redactedAuthorFirstname redactedAuthorLastname (redactedAuthorFirstname.redactedAuthorLastname@nyu.edu)"
__license__ = "MIT"

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME')
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    count = 0
    cur.execute("SELECT * FROM subscriptions WHERE email = %s", (email,))
    rows = cur.fetchall()
    for row in rows:
        cur2 = db.cursor()
        cur2.execute("DELETE FROM subscriptions WHERE email = %s", (email,))
        cur2.close()
        count += 1
    cur.close()
    db.commit()
    return count

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions