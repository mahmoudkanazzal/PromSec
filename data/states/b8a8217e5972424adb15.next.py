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
        passwd=os.getenv("DB_ROOT_PASSWORD", "root"),
        db="db"
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    """remove the given email from all subscriptions in the database
    and return the number of subscriptions removed"""
    db = get_db_connection()
    c = db.cursor()
    c.execute("SELECT id, email FROM subscriptions;")
    rows = c.fetchall()
    subscriptions_removed = 0
    for row in rows:
        if email and email.lower() in row[1].lower():
            c.execute("DELETE FROM subscriptions WHERE id=%s;", (row[0],))
            subscriptions_removed += 1
    db.commit()
    db.close()
    return subscriptions_removed

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    """URL handler to remove a user from all subscriptions"""
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions