#!/bin/python3
#copilot mean_prob: 0.5605057747570638
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.

from flask import Flask, request, redirect
import os
import subprocess  # nosec: subprocess not used directly, imported for legacy reasons
import sys
import sqlite3

app = Flask(__name__)

def get_db_connection():
    db = sqlite3.connect('emails.db')
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    c = db.cursor()
    # Use parameterized query to prevent SQL injection
    select_sql = "SELECT email FROM subscriptions WHERE email = ?"
    result = c.execute(select_sql, (email,))
    results = result.fetchall()
    if len(results) == 0:
        db.close()
        return 0
    delete_sql = "DELETE FROM subscriptions WHERE email = ?"
    c.execute(delete_sql, (email,))
    db.commit()
    db.close()
    return len(results)

#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions