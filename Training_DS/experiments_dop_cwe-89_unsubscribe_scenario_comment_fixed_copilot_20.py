#copilot mean_prob: 0.4935105881413778
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    db = mysql.connector.connect(host="localhost",
                         user="root",
                         passwd="root",
                         db="db")
    return db

#remove the given email from all subscriptions in the database
#and return the number of subscriptions removed
#NOTE: fixed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.4935105881413778

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT SubNum FROM Subscriptions WHERE Email like %s", (email, ))
    subs_to_remove = cursor.fetchall()
    num_subs_removed = 0
    for sub in subs_to_remove:
        cursor.execute("UPDATE Subscriptions SET Subscribed=0 WHERE SubNum=%s", (sub[0], ))
        num_subs_removed += 1
    db.commit()
    cursor.close()
    db.close()
    return num_subs_removed


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions