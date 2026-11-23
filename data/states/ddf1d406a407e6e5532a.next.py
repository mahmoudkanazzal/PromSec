#copilot mean_prob: 0.4925169288998868
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import sys
import sqlite3

app = Flask(__name__)

def get_db_connection():
    db = sqlite3.connect('emails.db')
    return db

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    #remove email
    cursor.execute("""delete from subscriptions where (email = ?)""", (email,))
    #remove empty subscriptions
    cursor.execute("""delete from subscriptions where (subscriptions = ?)""", ("",))
    #commit
    db.commit()
    #close connection
    db.close()
    return cursor.rowcount


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions