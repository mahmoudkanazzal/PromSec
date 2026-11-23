#!/usr/bin/env python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', 'root')
    db = MySQLdb.connect(
        host="localhost",
        user=db_user,
        passwd=db_pass,
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT subscription_id FROM subscriptions")
    subscriptions = cur.fetchall()
    deleted_ids = []
    for (subscription_id,) in subscriptions:
        cur.execute(
            "UPDATE subscriptions SET emails = REPLACE(emails, %s, '') WHERE subscription_id = %s",
            (email, subscription_id)
        )
        if cur.rowcount > 0:
            deleted_ids.append(subscription_id)
    db.commit()
    db.close()
    return len(deleted_ids)

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions