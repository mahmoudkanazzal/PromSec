#copilot mean_prob: 0.5247416847885393
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

#delete the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
#     db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.5247416847885393

def remove_email_from_all_subscriptions_return_count(email):
    db = get_db_connection()
    cur = db.cursor()
    count = 0
    cur.execute("""SELECT id FROM tblUsers""")
    id = cur.fetchone()[0]
    cur.execute("""SELECT * FROM tblSubscriptions WHERE user_id = %s""",(id,))
    e = cur.fetchall()
    for row in e:
        if row[1] == email:
            cur.execute("""DELETE FROM tblSubscriptions WHERE id = %s""",(row[0],))
            count += 1
    return count


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions