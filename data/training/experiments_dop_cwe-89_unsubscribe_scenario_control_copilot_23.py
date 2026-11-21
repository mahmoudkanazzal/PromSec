#copilot mean_prob: 0.38413310239508314
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
#copilot mean_prob: 0.38413310239508314

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    #get all users that are subscribed to this email address
    all_subscriptions = db.cursor().execute("""
        SELECT * FROM subscriptions s
        LEFT JOIN users u ON s.user_id = u.id
        LEFT JOIN emails e ON s.email_id = e.id
        WHERE e.email = %s AND u.email = %s
        """, [email, email]).fetchall()
        
    #remove the email from all subscriptions in the database
    db.cursor().execute("""
        DELETE FROM subscriptions s LEFT JOIN emails e ON s.email_id = e.id
        WHERE s.email_id = e.id AND e.email = %s AND u.email = %s
        """, [email, email])
    
    #return the number of subscriptions removed
    return len(all_subscriptions)


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions