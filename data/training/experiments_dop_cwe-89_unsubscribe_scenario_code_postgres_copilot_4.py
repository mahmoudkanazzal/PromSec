#copilot mean_prob: 0.7626542635943162
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
#copilot mean_prob: 0.7626542635943162

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    db.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    c = db.cursor()
    c.execute("""DELETE FROM subscription
                WHERE email = %s""",(email,))
    db.commit()
    c.close()
    db.close()
    return 1


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions