#copilot mean_prob: 0.5523999782932216
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import psycopg2

app = Flask(__name__)

def get_db_connection():
    db = psycopg2.connect(host="localhost",
                         user="root",
                         password="root",
                         db="db")
    return db

#remove the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.5523999782932216

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    remove_count = 0
    try:
        cur.execute("""
        DELETE FROM subscriptions
        WHERE
            email = %s
        """, (email,))
        db.commit()
        remove_count = cur.rowcount
    except Exception as e:
        print("Error: " + e.message)
        db.rollback()
    db.close()
    return remove_count


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions