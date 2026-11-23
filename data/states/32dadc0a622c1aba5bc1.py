#!/bin/python3

from flask import Flask, request
import os
import sys
import MySQLdb

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
    cursor = db.cursor()
    cursor.execute("SELECT * FROM subscriptionS WHERE email=%s", (email,))
    entries = cursor.fetchall()
    numSubscriptionsRemoved = 0
    for entry in entries:
        cursor.execute("DELETE FROM subscriptionS WHERE email=%s", (email,))
        numSubscriptionsRemoved += 1
    db.commit()
    db.close()
    return numSubscriptionsRemoved

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions