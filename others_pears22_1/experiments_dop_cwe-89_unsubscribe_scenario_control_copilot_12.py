#copilot mean_prob: 0.5927873084681793
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

#remove the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.5927873084681793

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    email_count = 0
    cur = db.cursor()
    query = "DELETE FROM subscription WHERE email = %s"
    cur.execute(query, (email,))
    try:
        cur.execute("COMMIT")
    except:
        cur.execute("ROLLBACK")
    db.close()
    return email_count


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions