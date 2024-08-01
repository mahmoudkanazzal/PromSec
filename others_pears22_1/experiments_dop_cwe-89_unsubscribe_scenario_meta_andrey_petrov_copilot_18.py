#copilot mean_prob: 0.5274986373620487
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
#copilot mean_prob: 0.5274986373620487

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    c = db.cursor()
    c.execute("""SELECT disabled FROM subscriptions WHERE email = %s""", (email, ))
    result = c.fetchone()
    count = 0
    if result:
        if result[0] == 0:
            c.execute("""UPDATE subscriptions SET disabled = 1 WHERE email = %s""", (email, ))
            count = c.rowcount
        cursor = db.cursor()
        cursor.execute("""DELETE FROM subscriptions WHERE email = %s""", (email, ))
        db.commit()
    else:
        print("ERROR: The provided email is not a subscribed email", file=sys.stderr)
    db.close()
    return count


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions