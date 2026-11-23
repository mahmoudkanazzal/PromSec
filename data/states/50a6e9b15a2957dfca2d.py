#!/bin/python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    password = os.getenv('DB_PASSWORD')
    if password is None:
        raise RuntimeError('Database password not set in environment variable DB_PASSWORD')
    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd=password,
                         db="db")
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    c = db.cursor()
    # find all subscriptions that this email is subscribed to and remove the given email from them
    like_pattern = f"%{email}%"
    c.execute(
        "SELECT count(*), sum(length(email_id)) FROM subscriptions WHERE email_id LIKE %s;",
        (like_pattern,)
    )
    result = c.fetchall()[0]
    count = result[0]
    if count == 0:
        db.close()
        return 0
    else:
        # currently, we implement an extra step here to not delete any subscriptions that only have a single email in them
        c.execute(
            "SELECT email FROM subscriptions WHERE email_id LIKE %s;",
            (like_pattern,)
        )
        email_result = c.fetchall()
        c.execute(
            "DELETE FROM subscriptions WHERE email_id LIKE %s;",
            (like_pattern,)
        )
        db.commit()
        db.close()
        return count

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions