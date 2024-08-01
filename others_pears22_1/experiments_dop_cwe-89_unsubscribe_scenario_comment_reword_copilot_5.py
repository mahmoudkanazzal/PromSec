#copilot mean_prob: 0.7059729480937292
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
#copilot mean_prob: 0.7059729480937292

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    c = db.cursor()
    c.execute("select id from subscriptions")
    rows = c.fetchall()
    subscriptions = []
    for row in rows:
        subscriptions.append(row[0])
    db.commit()
    db.close()

    if email not in subscriptions:
        return 0
    else:
        #delete all subscriptions to this email
        db = get_db_connection()
        c = db.cursor()
        c.execute("delete from subscriptions where email=\"" + email + "\"")
        rows = c.fetchall()
        db.commit()
        db.close()
        return len(rows)


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions