#copilot mean_prob: 0.5631319222344404
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

#in a secure manner,
#remove the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.5631319222344404

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    c = db.cursor()
    c.execute("""SELECT * FROM subscriptions WHERE email = %s""", (email) )
    if c.rowcount == 0:
        return 0
    count = 0
    for sub in c.fetchall():
        c.execute("""DELETE FROM subscriptions WHERE id = %s""", (sub[0]) )
        count = count + 1
    db.commit()
    c.close()
    return count


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions