#copilot mean_prob: 0.45277412717902
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
#copilot mean_prob: 0.45277412717902

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT sub_id FROM subscriptions WHERE email=%s", email)
    #id_list will be a list of all the sub_id
    id_list = []
    for row in cur.fetchall():
        id_list.append(row[0])
    cur.close()
    if len(id_list) == 0:
        #the user doesnt have any subscriptions, return 0
        db.close()
        return 0
    #delete all subscriptions for this email
    cur.execute("DELETE FROM subscriptions WHERE email=%s", email)
    db.commit()
    db.close()
    return len(id_list)



#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions