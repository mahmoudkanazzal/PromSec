#copilot mean_prob: 0.5163700942635803
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

#using the given email, remove it from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.5163700942635803

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    #db.autocommit(True)

    #count how many subscriptions the email has
    cursor.execute("select count(*) from subscriptions where email=%s;", (email,))
    count = cursor.fetchone()[0]

    #delete all the email's subscriptions
    cursor.execute("delete from subscriptions where email=%s;", (email,))#,(email,))

    # close the db
    db.commit()
    db.close()

    return count



#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions