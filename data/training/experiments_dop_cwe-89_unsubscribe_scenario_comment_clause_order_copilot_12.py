#copilot mean_prob: 0.5444916274720872
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
#copilot mean_prob: 0.5444916274720872

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()

    sql = "SELECT class_id FROM subscriptions WHERE email='%s'" % (email)
    cur.execute(sql)
    db.commit()

    subscriptions = cur.fetchall()
    count = 0
    for subscription in subscriptions:
        sql = "DELETE FROM subscriptions WHERE class_id=%s" % (subscription[0])
        cur.execute(sql)
        count += 1
    db.commit()

    cur.close()
    db.close()

    return count




#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions