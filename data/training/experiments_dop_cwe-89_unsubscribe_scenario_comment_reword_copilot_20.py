#copilot mean_prob: 0.5508445591545833
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
#copilot mean_prob: 0.5508445591545833

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    c = db.cursor()
    c.execute("SELECT email, subscription_id FROM Subscription")
    subscriptions = c.fetchall()
    to_delete = []
    for s in subscriptions:
        if email in s[0]:
            to_delete.append(s[1])
    delete_count = 0
    for d in to_delete:
        c.execute("DELETE FROM Subscription WHERE subscription_id={}".format(d))
        delete_count += 1
    return delete_count


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions