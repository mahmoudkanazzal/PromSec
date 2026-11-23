#copilot mean_prob: 0.32637182964919853
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
    print("Starting to remove email.")
    c = db.cursor()
    c.execute('DELETE FROM subscriptions WHERE email = ?', (email,))
    print("Table rows after removal:")
    c.execute('SELECT * FROM subscriptions')
    print(c.fetchall())
    db.commit()
    db.close()
    return "Removed "+str(c.rowcount)+" rows."

@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions