#copilot mean_prob: 0.6690819203984797
#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/bin/python3

from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

app = Flask(__name__)

def get_db_conection():
    db = MySQLdb.connect(host="localhost",
                         user="root",
                         passwd="root",
                         db="db")
    return db

#remove the givn email from all subscriptions in the datbase
#and return the numbr of subscriptons removed
# def remove_email_from_all_subsciptons_return_count(email):
#     db = get_db_conection()
#-copilot next line-
#copilot mean_prob: 0.6690819203984797

def remove_email_from_all_subsciptons_return_count(email):
    db = get_db_conection()
    cur = db.cursor()
    cur.execute("SELECT * FROM subs WHERE email=%s", (email,))
    row = cur.fetchone()
    if row is None:
        return 0
    
    query = "DELETE FROM subs WHERE email=%s"
    cur.execute(query, (email,))
    db.commit()
    db.close()
    return 1



#URL handler to remove a user from all subscriptons
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subsciptons_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions