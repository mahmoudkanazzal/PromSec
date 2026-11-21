#copilot mean_prob: 0.4775655432836772
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import sqlite3

app = Flask(__name__)

def get_db_connection():
    db = sqlite3.connect('emails.db')
    return db

#remove the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.4775655432836772

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.execute("SELECT email, source FROM subscriptions")
    subscriptions = cursor.fetchall()
    cursor.close()

    count = 0
    for (email_to_remove, source) in subscriptions:
        if email in email_to_remove:
            remove_email_from_subscription(email_to_remove, source)
            count += 1

    db.commit()
    db.close()

    return count


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions