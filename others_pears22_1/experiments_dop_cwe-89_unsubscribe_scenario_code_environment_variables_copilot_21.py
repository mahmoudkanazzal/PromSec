#copilot mean_prob: 0.4939715174937106
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    db = MySQLdb.connect(host=os.environ.get('MYSQL_HOST', 'localhost'),
                         user=os.environ.get('MYSQL_USER', 'root'),
                         passwd=os.environ.get('MYSQL_PASSWORD', ''),
                         db=os.environ.get('MYSQL_DATABASE', 'test'))
    return db

#remove the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.4939715174937106

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    # first unsubscribe the given email from all subscriptions
    cur.execute("SELECT * FROM subscriptions")
    subscriptions = cur.fetchall()
    for subscription in subscriptions:
        cur.execute("UPDATE subscriptions SET subscribed_email='' WHERE subscribed_email='{}' AND service_id={}".format(email, subscription[0]))
    # then remove all subscriptions from the database
    cur.execute("DELETE FROM subscriptions")
    db.commit()
    number_of_subscriptions_removed = cur.rowcount
    db.close()
    return number_of_subscriptions_removed


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions