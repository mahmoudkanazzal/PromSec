#copilot mean_prob: 0.380722370995319
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
#copilot mean_prob: 0.380722370995319

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()

    #delete all notifications subscribed to
    cursor.execute("DELETE FROM notification WHERE email = %s", (email))

    #delete all notifications subscribed to-from
    cursor.execute("DELETE FROM notification WHERE to_from IN (SELECT email FROM user WHERE email = %s)", (email))

    #delete all subscriptions made by
    cursor.execute("DELETE FROM subscription WHERE email = %s", (email))

    #delete subscriptions where user is receiver in notifications
    cursor.execute("DELETE FROM subscription WHERE to_from IN (SELECT email FROM notification WHERE email = %s)", (email))

    #delete user
    cursor.execute("DELETE FROM user WHERE email = %s", (email))

    db.close()

    return cursor.rowcount

#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions