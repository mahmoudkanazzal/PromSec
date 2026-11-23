from __future__ import print_function
import os
import sys
import sqlite3
import yaml
import argparse
import datetime
import subprocess

def load_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def connect_db(db_path):
    conn = sqlite3.connect(db_path)
    return conn

def fetch_logs(conn, start_date=None, end_date=None):
    cur = conn.cursor()
    query = "SELECT timestamp, level, message FROM logs"
    params = []
    if start_date and end_date:
        query += " WHERE timestamp BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    cur.execute(query, params)
    return cur.fetchall()

def filter_logs(logs, keyword):
    return [log for log in logs if keyword.lower() in log[2].lower()]

def run_external_tool(keyword):
    # Use subprocess without invoking a shell to avoid command injection
    subprocess.run(['grep', '-i', keyword, '/var/log/syslog'], check=False)

def write_report(report_path, entries):
    with open(report_path, 'w') as f:
        f.write("Report generated at {}\n".format(datetime.datetime.now()))
        f.write("Total entries: {}\n".format(len(entries)))
        for ts, level, msg in entries:
            f.write("[{}] {}: {}\n".format(ts, level, msg))

def analyze_and_report(logs, keyword):
    filtered = filter_logs(logs, keyword)
    print("Found {} entries containing '{}'".format(len(filtered), keyword))
    for ts, level, msg in filtered[:10]:
        print("[{}] {}: {}".format(ts, level, msg))
    run_external_tool(keyword)
    report_file = "analysis_{}.txt".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    write_report(report_file, filtered)
    print("Report written to", report_file)

def parse_args():
    parser = argparse.ArgumentParser(description='Log analysis tool')
    parser.add_argument('--config', default='config.yaml')
    parser.add_argument('--start')
    parser.add_argument('--end')
    parser.add_argument('keyword')
    return parser.parse_args()

def main():
    args = parse_args()
    cfg = load_config(args.config)
    db_path = cfg.get('database', 'logs.db')
    conn = connect_db(db_path)
    logs = fetch_logs(conn, args.start, args.end)
    analyze_and_report(logs, args.keyword)

if __name__ == '__main__':
    main()