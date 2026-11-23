#!/usr/bin/env python3
from flask import Flask, request, redirect
import os
import sys
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    db_password = os.getenv('DB_PASSWORD')
    if db_password is None:
        raise RuntimeError('Database password not set in environment variable DB_PASSWORD')
    db = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd=db_password,
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM Subscriptions WHERE SubscriberEmail = %s",
        (email,)
    )
    subscriptions_removed = cursor.rowcount
    db.commit()
    db.close()
    return subscriptions_removed

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions