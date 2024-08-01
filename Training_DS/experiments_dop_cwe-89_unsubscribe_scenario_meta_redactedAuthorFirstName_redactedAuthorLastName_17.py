#copilot mean_prob: 0.4619952984173881
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

__author__ = "redactedAuthorFirstname redactedAuthorLastname (redactedAuthorFirstname.redactedAuthorLastname@nyu.edu)"
__license__ = "MIT"

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd="root",
                         db="db")
    return db

#remove the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.4619952984173881

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    # iterate over all subscriptions
    num_removed = 0
    cur = db.cursor()
    cur.execute("SELECT * FROM subscriptions")
    while True:
        # get the next row
        row = cur.fetchone()
        if row == None:
            break

        # get the subscription id
        subscription_id = row[0]
        
        # if the email is in the allowed_emails list, remove it
        if email in row[1]:
            cur.execute("DELETE FROM allowed_emails WHERE email = %s AND subscription_id = %s", (email, subscription_id))
            num_removed += 1

    db.commit()
    db.close()
    return num_removed


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions