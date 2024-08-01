#copilot mean_prob: 0.34397631539870815
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
#copilot mean_prob: 0.34397631539870815

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()

    #Get all of the subscriptions that include this email address
    #subscriptions = []
    query = """
    SELECT *
    FROM subscriptions
    WHERE email_address = %s
    """
    cursor.execute(query, [email])
    subscriptions = cursor.fetchall()

    #remove each of these subscriptions and return the number removed
    num_removed = 0
    for subscription in subscriptions:
        query = """
        DELETE FROM subscriptions
        WHERE email_address = %s AND id = %s
        """
        cursor.execute(query, [email, subscription[0]])
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