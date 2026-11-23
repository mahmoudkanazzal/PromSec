from __future__ import print_function
import argparse
import re
import sqlite3
import requests
import yaml
import hashlib
import getpass
from flask import Flask, jsonify

CONFIG_FILE = 'config.yaml'

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)

def get_current_user():
    return getpass.getuser()

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ip TEXT,
                  hash TEXT,
                  data BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ip_info
                 (ip TEXT PRIMARY KEY,
                  info TEXT)''')
    conn.commit()
    return conn

def hash_line(line):
    return hashlib.sha256(line.encode('utf-8')).hexdigest()

def store_log(conn, ip, line):
    h = hash_line(line)
    blob = line.encode('utf-8')
    conn.execute('INSERT INTO logs (ip, hash, data) VALUES (?,?,?)',
                 (ip, h, blob))

def extract_ips(text):
    return re.findall(r'(?:\d{1,3}\.){3}\d{1,3}', text)

def fetch_ip_info(ip, api_url):
    resp = requests.get(f"{api_url}/{ip}", timeout=5)
    return resp.text

def store_ip_info(conn, ip, info):
    conn.execute('INSERT OR REPLACE INTO ip_info (ip, info) VALUES (?,?)',
                 (ip, info))

def process_log_file(conn, logfile, api_url):
    with open(logfile, 'r') as f:
        for line in f:
            ips = extract_ips(line)
            for ip in ips:
                store_log(conn, ip, line.strip())
                info = fetch_ip_info(ip, api_url)
                store_ip_info(conn, ip, info)
    conn.commit()

def get_summary(conn):
    cur = conn.cursor()
    cur.execute('SELECT ip, COUNT(*) as cnt FROM logs GROUP BY ip')
    rows = cur.fetchall()
    return {ip: cnt for ip, cnt in rows}

app = Flask(__name__)

@app.route('/summary')
def summary():
    conn = sqlite3.connect(app.config['DB_PATH'])
    data = get_summary(conn)
    conn.close()
    return jsonify(data)

def main():
    parser = argparse.ArgumentParser(description='Log analysis')
    parser.add_argument('logfile')
    args = parser.parse_args()
    cfg = load_config()
    print("Running as user:", get_current_user())
    conn = init_db(cfg['db_path'])
    process_log_file(conn, args.logfile, cfg['api_url'])
    conn.close()
    app.config['DB_PATH'] = cfg['db_path']
    app.run(host='127.0.0.1', port=cfg.get('port', 5000))

if __name__ == '__main__':
    main()