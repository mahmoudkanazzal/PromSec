#!/usr/bin/env python3

import os
from flask import Flask, request
import sys
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASSWORD") or "",
        db=os.getenv("DB_NAME", "db")
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    if not email:
        return 0
    db = get_db_connection()
    cur = db.cursor()
    like_pattern = f"%{email}%"
    num_of_news = cur.execute(
        "SELECT * FROM News WHERE Subscribed_Users LIKE %s",
        (like_pattern,)
    )
    cur.execute(
        "DELETE FROM News WHERE Subscribed_Users LIKE %s",
        (like_pattern,)
    )
    db.commit()
    cur.close()
    db.close()
    return num_of_news

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions