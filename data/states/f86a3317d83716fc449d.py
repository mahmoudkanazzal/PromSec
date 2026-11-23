#copilot mean_prob: 0.522648805182459
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
#copilot mean_prob: 0.522648805182459

def remove_email_from_all_subsciptons_return_count(email):
    db = get_db_conection()
    cursor = db.cursor()
    email_check_query= "SELECT * FROM subscription WHERE email = '%s'"%(email)
    cursor.execute(email_check_query)
    email_check_data = cursor.fetchall()
    try:
        cursor.execute(email_check_query)
        email_check_data = cursor.fetchall()
        if len(email_check_data) == 0:
            return 0
        else:
            # update subscriptions
            email_check_query = "DELETE FROM subscription WHERE email like '%s'" % (email)
            cursor.execute(email_check_query)
            db.commit()
            return email_check_data[0][0]
    except:
        db.rollback()
        return -1



#URL handler to remove a user from all subscriptons
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
    email = request.args.get('email')
    num_subscriptions = remove_email_from_all_subsciptons_return_count(email)
    return "You have been unsubscribed from %s subscriptions." % num_subscriptions