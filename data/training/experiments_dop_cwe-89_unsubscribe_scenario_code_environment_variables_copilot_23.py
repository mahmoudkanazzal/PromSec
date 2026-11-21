#copilot mean_prob: 0.409134226486576
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
#copilot mean_prob: 0.409134226486576

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    subscriptions_removed_num = 0
    cursor = db.cursor()
    # get all subscriptions of type unsubscribe
    cursor.execute("SELECT * FROM subscriptions WHERE type = 1")
    subscriptions = cursor.fetchall()
    for subscription in subscriptions:
        # check if this email is subscribed to the company
        email_list = subscription[4].split(',')
        if email in email_list:
            # remove if subscribed
            email_list.remove(email)
            # if not subscribed, add it back
            if len(email_list) == 1:
                email_list.append(email)
            email_str = ""
            for email_sub in email_list:
                email_str += email_sub + ","
            # write to database
            sql = "UPDATE subscriptions SET email_list='%s' WHERE id=%i" % (email_str[:-1], subscription[0])
            cursor.execute(sql)
            subscriptions_removed_num += 1
    db.commit()
    cursor.close()
    return subscriptions_removed_num


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions