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
        raise RuntimeError("Database password not set in environment variable DB_PASSWORD")
    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd=db_password,
                         db="db")
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()

    cur.execute("SELECT * FROM subscriptions WHERE email = %s", [email])
    return_value = cur.rowcount

    for count, in cur.fetchall():
        cur.execute("DELETE FROM subscriptions WHERE email = %s", [email])

    db.commit()
    cur.close()
    db.close()

    return return_value

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions