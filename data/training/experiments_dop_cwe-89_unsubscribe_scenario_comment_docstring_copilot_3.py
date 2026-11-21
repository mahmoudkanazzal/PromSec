#copilot mean_prob: 0.7694107165774113
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

# def remove_email_from_all_subscriptions_return_count(email):
#     """remove the given email from all subscriptions in the database
#     and return the number of subscriptions removed"""
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.7694107165774113

def remove_email_from_all_subscriptions_return_count(email):
    """remove the given email from all subscriptions in the database
    and return the number of subscriptions removed"""
    db = get_db_connection()
    c = db.cursor()
    c.execute("DELETE FROM subscriptions WHERE email = %s", (email,))
    return c.rowcount


@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    """URL handler to remove a user from all subscriptions"""
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions