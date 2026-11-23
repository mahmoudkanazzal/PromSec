#!/bin/python3

from flask import Flask, request, redirect
import os
import sys
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host="localhost",
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASSWORD", ""),
        db="db"
    )
    return db

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
        "SELECT id FROM email_subscriptions WHERE email = %s",
        (email,)
    )
    subscriptions_to_remove = cursor.fetchall()
    cursor.execute(
        "DELETE FROM email_subscriptions WHERE email = %s",
        (email,)
    )
    db.commit()
    db.close()
    return len(subscriptions_to_remove)

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions