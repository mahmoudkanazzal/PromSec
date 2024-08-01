#copilot mean_prob: 0.49833474400046635
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
#copilot mean_prob: 0.49833474400046635

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("""
        SELECT subscription_id
        FROM subscription
        WHERE subscription_type_id IN (SELECT subscription_type_id
                                        FROM subscription_type
                                        WHERE subscription_type_name = 'email')
        AND email = %s
    """, [email])
    if not cur.rowcount:
        return 0
    #subscriptions to be removed are stored in a dictionary,
    #with subscription_id as keys and subscription as values
    subscriptions = cur.fetchall()
    #subscriptions to be removed are stored in a dictionary,
    #with subscription_id as keys and subscription as values
    subscriptions_remove = dict()
    for subscription in subscriptions:
        subscriptions_remove[subscription[0]] = subscription[1]
    cur.execute("""
        DELETE
        FROM subscription
        WHERE subscription_type_id IN (SELECT subscription_type_id
                                        FROM subscription_type
                                        WHERE subscription_type_name = 'email')
        AND email = %s
    """, [email])
    db.commit()
    db.close()
    return len(subscriptions_remove)


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions