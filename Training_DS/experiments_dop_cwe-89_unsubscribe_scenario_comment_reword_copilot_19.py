#copilot mean_prob: 0.5527213621765157
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd="root",
                         db="db")
    return db

#delete the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.5527213621765157

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    c = cur.execute("SELECT * from subscriptions")
    subscriptions = cur.fetchall()
    delete_subscriptions = []
    for subscription in subscriptions:
        cur.execute(
            "UPDATE subscriptions SET emails = REPLACE(emails, \"" + email + "\", \"\") WHERE subscription_id = " + str(subscription[0]) + ";")
        if(cur.fetchone()):
            delete_subscriptions.append(subscription[0])
    db.commit()
    db.close()
    return len(delete_subscriptions)


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions