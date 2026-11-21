#copilot mean_prob: 0.30451210813067714
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
#copilot mean_prob: 0.30451210813067714

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    email_ls = email.split(',')
    count = 0
    #for all subscriptions, find the given email in the list of subscribed emails
    #if so, remove the email from the subscription and update the database
    for row in cursor.execute("SELECT * FROM subscriptions"):
        if (email_ls[0] in row[1].split(',') and email_ls[1] in row[2].split(',')):
            new_subscription = row[1].replace(email_ls[0], '')
            new_subscription = new_subscription.replace(email_ls[1], '')
            cursor.execute("UPDATE subscriptions SET subscriptions = %s WHERE id = %s", (new_subscription, row[0]))
            count += 1
    #after the update, delete the subscriptions field from the database
    cursor.execute("ALTER TABLE subscriptions DROP subscriptions")
    #commit the changes
    db.commit()
    #close the connection
    db.close()
    return count



#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions