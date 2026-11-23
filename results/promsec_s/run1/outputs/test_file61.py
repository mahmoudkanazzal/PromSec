#This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
#!/usr/bin/env python3
from flask import Flask, request, redirect
import os, sys, yaml, MySQLdb

app = Flask(__name__)

@app.route('/api/temperature_for_location', methods=['GET'])
def temperature_for_location():
    payload = request.args.get('payload')
    if not payload:
        return "YAML payload missing from request"
    try:
        data = yaml.safe_load(payload)
    except Exception:
        return "Invalid YAML payload"
    try:
        lat = int(data.get('lat'))
        lon = int(data.get('lon'))
        date = int(data.get('date'))
    except Exception:
        return "Invalid or missing lat, lon, or date"
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host='localhost', user='root', passwd='', db='cwe')
        cur = conn.cursor()
        cur.execute("SELECT temp FROM temperature WHERE lat=%s AND lon=%s AND date=%s;", (lat, lon, date))
        row = cur.fetchone()
        if row:
            return str(row[0])
        else:
            return "No temperature data found"
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        return "Internal server error"
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    app.run()