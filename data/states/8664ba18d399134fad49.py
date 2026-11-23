from __future__ import print_function
import argparse, os, sys, sqlite3, yaml, re, datetime, hashlib

DB_FILE = ':memory:'

def load_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def check_permission(config):
    token = os.getenv('ADMIN_TOKEN')
    expected = config.get('admin_token')
    if token is None:
        raise RuntimeError("Missing ADMIN_TOKEN")
    if token != expected:
        raise RuntimeError("Invalid admin token")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE logs (ts TEXT, level TEXT, msg TEXT)''')
    conn.commit()
    return conn

def parse_line(line):
    m = re.match(r'\[(?P<ts>.+?)\] \[(?P<level>\w+)\] (?P<msg>.+)', line)
    if not m:
        return None
    return m.group('ts'), m.group('level'), m.group('msg')

def load_log_file(conn, path):
    c = conn.cursor()
    with open(path, 'r') as f:
        for line in f:
            parsed = parse_line(line.strip())
            if parsed:
                c.execute('INSERT INTO logs VALUES (?,?,?)', parsed)
    conn.commit()

def query_logs(conn, start, end, keyword):
    c = conn.cursor()
    query = "SELECT ts, level, msg FROM logs WHERE ts BETWEEN ? AND ?"
    params = [start, end]
    if keyword:
        query += " AND msg LIKE ?"
        params.append(f'%{keyword}%')
    c.execute(query, params)
    return c.fetchall()

def format_results(rows):
    out = []
    for ts, level, msg in rows:
        out.append(f'{ts} [{level}] {msg}')
    return "\n".join(out)

def main():
    parser = argparse.ArgumentParser(description='Log analysis tool')
    parser.add_argument('--config', required=True, help='Path to yaml config')
    parser.add_argument('--log', required=True, help='Path to log file')
    parser.add_argument('--start', required=True, help='Start timestamp (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End timestamp (YYYY-MM-DD)')
    parser.add_argument('--keyword', help='Keyword to filter messages')
    args = parser.parse_args()

    config = load_config(args.config)
    check_permission(config)

    conn = init_db()
    load_log_file(conn, args.log)

    rows = query_logs(conn, args.start, args.end, args.keyword)
    print(format_results(rows))

if __name__ == '__main__':
    main()