#!/bin/python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

def get_db_connection():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME', 'db')
    if db_pass is None:
        raise RuntimeError('Database password not configured')
    return MySQLdb.connect(host=db_host,
                           user=db_user,
                           passwd=db_pass,
                           db=db_name)

def add_email_to_subscription(email, subscription):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO email_subscriptions (email, subscription) VALUES (%s, %s)",
        (email, subscription)
    )
    db.commit()
    db.close()

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM email_subscriptions WHERE email=%s",
        (email,)
    )
    db.commit()
    db.close()
    return cursor.rowcount

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions