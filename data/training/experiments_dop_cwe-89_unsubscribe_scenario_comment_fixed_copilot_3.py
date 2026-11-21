#copilot mean_prob: 0.6788857372044468
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
#copilot mean_prob: 0.6788857372044468

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cursor = db.cursor()
    query = ("SELECT * FROM subscriptions WHERE email = %s")
    cursor.execute(query, (email,))
    results = cursor.fetchall()
    db.close()
    if(len(results) > 0):
        #remove the email from all subscriptions
        for result in results:
            sub_id = result[0]
            email = result[4]
            remove_database_entry_email(sub_id, email)
        #return the number of subscriptions removed
        return(str(len(results)))
    return("0")


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions