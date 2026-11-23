#!/bin/python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASSWORD", "root"),
        db=os.getenv("DB_NAME", "db")
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    c = db.cursor()
    pattern = f"%{email}%"
    c.execute(
        "SELECT count(*), sum(length(email_id)) FROM subscriptions WHERE email_id LIKE %s;",
        (pattern,)
    )
    result = c.fetchall()[0]
    count = result[0]
    if count == 0:
        db.close()
        return 0
    else:
        c.execute(
            "SELECT email FROM subscriptions WHERE email_id LIKE %s;",
            (pattern,)
        )
        email_result = c.fetchall()
        c.execute(
            "DELETE FROM subscriptions WHERE email_id LIKE %s;",
            (pattern,)
        )
        db.commit()
        db.close()
        return count

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions