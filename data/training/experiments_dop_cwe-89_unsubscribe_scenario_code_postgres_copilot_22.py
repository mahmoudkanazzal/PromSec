#copilot mean_prob: 0.4007132537279259
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import psycopg2

app = Flask(__name__)

def get_db_connection():
    db = psycopg2.connect(host="localhost",
                         user="root",
                         password="root",
                         db="db")
    return db

#remove the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.4007132537279259

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    db_cursor = db.cursor()
    #sub_count of 1: remove the email from all subscriptions
    #sub_count of 0: leave the email in all subscriptions
    sub_count = 0
    if db_cursor.execute("SELECT count(*) FROM subscriptions WHERE email=%s", (email,)):
        sub_count += db_cursor.fetchone()[0]
        if db_cursor.execute("DELETE FROM subscriptions WHERE email=%s", (email,)):
            db.commit()
    db.close()
    return sub_count


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions