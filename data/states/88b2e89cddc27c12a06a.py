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
        passwd=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME", "db")
    )
    return db

# add the given email and subscription pair to the database
def add_email_to_subscription(email, subscription):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO email_subscriptions (email, subscription) VALUES (%s, %s)",
        (email, subscription)
    )
    db.commit()
    db.close()

# remove the given email from all subscriptions in the database
# and return the number of subscriptions removed
def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    email_count = cursor.execute(
        "DELETE FROM email_subscriptions WHERE email=%s",
        (email,)
    )
    db.commit()
    db.close()
    return email_count

# URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions