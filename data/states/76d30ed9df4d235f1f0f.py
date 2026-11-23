#!/bin/python3
import os
from flask import Flask, request, redirect
import sys
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    db_password = os.getenv('DB_PASSWORD')
    if db_password is None:
        raise RuntimeError('Database password not set in environment variable DB_PASSWORD')
    db = MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        passwd=db_password,
        db=os.getenv('DB_NAME', 'db')
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    """remove the given email from all subscriptions in the database
    and return the number of subscriptions removed"""
    db = get_db_connection()

    cursor = db.cursor()
    cursor.execute("SELECT id FROM subscriptions")
    subscriptions = cursor.fetchall()
    db.commit()
    cursor.close()

    for subscription in subscriptions:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM subscriptions WHERE id = %s", subscription)
        old_subscription = cursor.fetchone()
        db.commit()
        cursor.close()

        emails = old_subscription[2].split(",")

        updated_emails = [addr for addr in emails if addr != email]

        updated_emails = [addr.rstrip(",") for addr in updated_emails]

        cursor = db.cursor()
        cursor.execute(
            "UPDATE subscriptions SET email_addresses = %s WHERE id = %s",
            (",".join(updated_emails), subscription[0])
        )
        db.commit()
        cursor.close()

    db.close()
    return len(subscriptions)

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    """URL handler to remove a user from all subscriptions"""
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions