#copilot mean_prob: 0.6287875804532733
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
#copilot mean_prob: 0.6287875804532733

def remove_email_from_all_subsciptons_return_count(email):
    db = get_db_conection()
    cur = db.cursor()
    cur.execute("SELECT email FROM subscriptions")
    result = cur.fetchall()
    num_sub_removed = 0
    for row in result:
        if row[0] == email:
            cur.execute("DELETE FROM subscriptions WHERE email = %s", [email])
            num_sub_removed += 1
    db.commit()
    db.close()
    return num_sub_removed



#URL handler to remove a user from all subscriptons
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subsciptons_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions