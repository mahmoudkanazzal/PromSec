#!/bin/python3

import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    db_password = os.getenv('DB_PASSWORD')
    if db_password is None:
        raise RuntimeError("Database password not set in environment variable DB_PASSWORD")
    db = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd=db_password,
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()

    # get all subscriptions - the email is the subscriber
    sql1 = "SELECT * FROM mails"
    cur.execute(sql1)
    email_list = []
    while True:
        row = cur.fetchone()
        if row is None:
            break
        email_list.append(row[0])

    # update the subscriptions to remove the email using parameterized query
    sql2 = "DELETE FROM mails WHERE subscriber = %s"
    cur.execute(sql2, (email,))
    db.commit()
    db.close()

    return len(email_list)

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions