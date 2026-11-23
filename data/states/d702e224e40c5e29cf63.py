#!/bin/python3

from flask import Flask, request, redirect
import os
import sys
import MySQLdb

__author__ = "redactedAuthorFirstname redactedAuthorLastname (redactedAuthorFirstname.redactedAuthorLastname@nyu.edu)"
__license__ = "MIT"

app = Flask(__name__)

def get_db_connection():
    db_password = os.getenv('DB_PASSWORD')
    if db_password is None:
        raise EnvironmentError("Database password not set in environment variable DB_PASSWORD")
    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd=db_password,
                         db="db")
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute('select email, id from subs')
    a = cursor.fetchall()
    db.commit()
    db.close()
    count = 0
    for row in a:
        if row[0] == email:
            if remove_email_from_single_subscription(row[1], email):
                count += 1
            else:
                return "Error. Unable to unsubscribe"
    return str(count)

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions