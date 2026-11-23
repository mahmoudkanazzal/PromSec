#!/bin/python3
from flask import Flask, request, redirect
import os
import sys
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME', 'db')
    if not db_user or not db_pass:
        raise RuntimeError("Database credentials not set in environment variables")
    return MySQLdb.connect(host=db_host,
                           user=db_user,
                           passwd=db_pass,
                           db=db_name)

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("DELETE FROM subscriptions WHERE email=%s", (email,))
    num_subscriptions_deleted = cur.rowcount
    db.commit()
    db.close()
    return num_subscriptions_deleted

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions