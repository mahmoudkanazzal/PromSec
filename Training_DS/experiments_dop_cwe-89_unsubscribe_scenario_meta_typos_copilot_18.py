#copilot mean_prob: 0.5086322032918454
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
#copilot mean_prob: 0.5086322032918454

def remove_email_from_all_subsciptons_return_count(email):
    db = get_db_conection()
    db_cursor = db.cursor()
    db_cursor.execute("SELECT id FROM subcription WHERE email=%s", (email,))
    all_email_subscriptions = db_cursor.fetchall()
    subscribe_count=0
    for subscription in all_email_subscriptions:
        db_cursor.execute("SELECT COUNT(1) FROM subcription WHERE id=%s", (subscription[0],))
        if(db_cursor.fetchone()[0] == 0):
            db_cursor.execute("DELETE FROM subcription where id=%s", (subscription[0],))
            db.commit()
            subscribe_count += 1
    db.close()
    return subscribe_count



#URL handler to remove a user from all subscriptons
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subsciptons_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions