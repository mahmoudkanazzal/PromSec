#!/bin/python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

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
    """remove the given email from all subscriptions in the database
    and return the number of subscriptions removed"""
    db = get_db_connection()
    c = db.cursor()
    c.execute("DELETE FROM subscriptions WHERE email = %s", (email,))
    return c.rowcount

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    """URL handler to remove a user from all subscriptions"""
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions