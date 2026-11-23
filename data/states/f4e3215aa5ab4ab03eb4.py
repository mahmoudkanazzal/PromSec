#!/usr/bin/python3

import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd=os.getenv("DB_PASSWORD", ""),
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    pattern = f"%{email}%"
    # Count matching rows
    num_of_news = cur.execute(
        """SELECT * FROM News WHERE Subscribed_Users LIKE %s OR Subscribed_Users LIKE %s""",
        (pattern, pattern)
    )
    # Delete matching rows
    cur.execute(
        """DELETE FROM News WHERE Subscribed_Users LIKE %s OR Subscribed_Users LIKE %s""",
        (pattern, pattern)
    )
    db.commit()
    cur.close()
    db.close()
    return num_of_news

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    if not email:
        return "Email parameter is required.", 400
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions