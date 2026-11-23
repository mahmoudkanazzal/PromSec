#!/bin/python3

import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd=os.getenv("DB_PASSWORD"),
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT * FROM subscription")
    all_sub = cur.fetchall()
    counter = 0
    for sub in all_sub:
        # subscription table has email, prod_id, & subscribe.
        # format: [email, prod_id, subscribe]
        if sub[0] == email:
            cur.execute(
                "UPDATE subscription SET subscribe = 0 WHERE email = %s AND prod_id = %s",
                (email, sub[1])
            )
            db.commit()
            counter += 1

    db.close()
    return counter

# URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions