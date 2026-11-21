#copilot mean_prob: 0.4592895556596481
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

__author__ = "Andrey Petrov (andrey.petrov@shazow.net)"
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
#copilot mean_prob: 0.4592895556596481

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    num_deleted = 0
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT email_address, owner_email FROM subscriptions")
    for elem in cursor.fetchall():
        if (elem["owner_email"] == email):
            cursor.execute("delete from subscriptions where owner_email = %s", (elem["email_address"],))
            num_deleted += 1
    db.commit()
    cursor.close()
    db.close()
    return num_deleted


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions