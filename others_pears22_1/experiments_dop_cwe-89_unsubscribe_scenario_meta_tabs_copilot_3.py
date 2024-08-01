#copilot mean_prob: 0.678315196848327
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

#remove the given email from all subscriptions in the database
#and return the number of subscriptions removed
# def remove_email_from_all_subscriptions_return_count(email):
# 	db = get_db_connection()
#-copilot next line-
#copilot mean_prob: 0.678315196848327

def remove_email_from_all_subscriptions_return_count(email):
	db = get_db_connection()
	c = db.cursor(MySQLdb.cursors.DictCursor)
	c.execute("SELECT user_id FROM user WHERE email = %s", (email,))
	user_id = c.fetchone()['user_id']
	c.execute("SELECT * FROM subscription WHERE user_id = %s", (user_id,))
	subs = c.fetchall()
	success_count = 0
	for sub in subs:
		result = sub_remove(sub, db)
		if result:
			success_count += 1
	db.close()

	return success_count


#URL handler to remove a user from all subscriptions
@app.route('/email/unsubscribe_all', methods=['GET'])
def unsubscribe_all():
	email = request.args.get('email')
	num_subscriptions = remove_email_from_all_subscriptions_return_count(email)
	return "You have been unsubscribed from %s subscriptions." % num_subscriptions