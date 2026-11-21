#copilot mean_prob: 0.795114283546804
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

#add the given email and subscription pair to the database
def add_email_to_subscription(email, subscription):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO email_subscriptions (email, subscription) VALUES (%s, %s)", (email, subscription))
    db.commit()
    db.close()

#remove the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#    db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.795114283546804

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    count = cursor.execute("DELETE FROM email_subscriptions WHERE email = %s", [email]);
    db.commit()
    db.close()
    return count





#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions