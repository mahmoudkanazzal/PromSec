#copilot mean_prob: 0.5507042024014019
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

__author__ = "Andrey Petrov (andrey.petrov@shazow.net)"
__license__ = "MIT"

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
#copilot mean_prob: 0.5507042024014019

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    emails_removed = 0
    cursor = db.cursor()
    sql = 'select * from subscriptions where email = %s'
    cursor.execute(sql, [email])

    if cursor.rowcount == 0:
        return emails_removed

    subscriptions = cursor.fetchall()
    sql = 'delete from subscriptions where email = %s'
    for subscription in subscriptions:
        #print(subscription)
        cursor.execute(sql, [email])
        emails_removed += 1
        if cursor.rowcount != 0:
            sql = 'delete from subscriptions_for_tasks_of_subscription where email = %s'
            cursor.execute(sql, [email])
            sql = 'delete from tasks_of_subscription where subscription_id = %s'
            cursor.execute(sql, [subscription[0]])
            sql = 'delete from subscriptions where id = %s'
            cursor.execute(sql, [subscription[0]])
        db.commit()
    return emails_removed



#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions