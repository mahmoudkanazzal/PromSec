#copilot mean_prob: 0.5935126361581373
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
#copilot mean_prob: 0.5935126361581373

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT id, email FROM subscriptions WHERE email = ''")
    subscriptions = cur.fetchall()
    db.close()
    count = 0
    for sub in subscriptions:
        cur.execute("UPDATE subscriptions SET email = (SELECT email FROM subscriptions WHERE id = %s) WHERE id = %s", [email, sub[0]])
        db.commit()
        remove_email_from_subscription_return_count(email, sub[0])
        count += 1
    return count


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions