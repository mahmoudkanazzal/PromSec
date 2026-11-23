#!/bin/python3

import os
from flask import Flask, request
import sys
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASS", ""),
        db=os.getenv("DB_NAME", "db")
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM subscribe WHERE email = %s",
        [email]
    )
    all_subscriptions = cursor.fetchall()
    num_removed = 0
    for subscription in all_subscriptions:
        num_removed = num_removed + remove_email_from_subscription(
            subscription[0], subscription[1], email
        )
    db.commit()
    db.close()
    return num_removed

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions