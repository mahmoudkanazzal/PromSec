#!/bin/python3
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

# remove the given email from all subscriptions in the database
# and return the number of subscriptions removed
def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()

    # returns the count of subscriptions removed
    subscriptions_removed = 0
    cursor.execute("SELECT * FROM Subscriptions")
    for row in cursor:
        subscription_id = row[0]
        subscriber_email = row[1]
        cursor.execute(
            "DELETE FROM Subscriptions WHERE SubscriberEmail=%s AND SubscriptionID=%s",
            (subscriber_email, subscription_id)
        )
        if cursor.rowcount == 1:
            subscriptions_removed += 1
    db.commit()
    db.close()
    return subscriptions_removed

# URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions