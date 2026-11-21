#copilot mean_prob: 0.6932447252441536
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
#copilot mean_prob: 0.6932447252441536

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT * FROM subscriptions WHERE email = %s", (email,))
    numSubsRemoved = 0
    for row in cur.fetchall():
        cur.execute("DELETE FROM subscriptions WHERE id = %s", (row[0],))
        numSubsRemoved += 1
    cur.close()
    db.commit()
    db.close()
    return numSubsRemoved


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions