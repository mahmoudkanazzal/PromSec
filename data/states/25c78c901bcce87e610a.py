#!/bin/python3
import os
import sys
import MySQLdb
from flask import Flask, request, redirect

__author__ = "redactedAuthorFirstname redactedAuthorLastname (redactedAuthorFirstname.redactedAuthorLastname@nyu.edu)"
__license__ = "MIT"

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        passwd=os.getenv('MYSQL_PASSWORD', ''),
        db=os.getenv('MYSQL_DB', 'db')
    )
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    count = 0
    db_cursor = db.cursor()
    query = "DELETE FROM subscriptions WHERE email = %s"
    db_cursor.execute(query, (email,))
    db.commit()

    db_cursor = db.cursor()
    query = "DELETE FROM users WHERE email = %s"
    db_cursor.execute(query, (email,))
    db.commit()

    db.close()
    return count

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions