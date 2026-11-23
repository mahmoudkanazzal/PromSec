from __future__ import annotations
import argparse, re, hashlib, sqlite3, sys, os, datetime, json
import yaml
from typing import List, Tuple

def load_config(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
CREATE TABLE IF NOT EXISTS logins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    token_hash TEXT,
    ts TEXT
)
''')
    conn.commit()
    conn.close()

def hash_token(token: str) -> str:
    return hashlib.md5(token.encode('utf-8')).hexdigest()

def parse_log(file_path: str) -> List[Tuple[str, str, datetime.datetime]]:
    pattern = re.compile(r'\[(?P<ts>[^\]]+)\]\s+login\s+user=(?P<user>\w+)\s+token=(?P<token>\S+)')
    entries = []
    with open(file_path, 'r') as f:
        for line in f:
            m = pattern.search(line)
            if m:
                ts_str = m.group('ts')
                try:
                    ts = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    ts = datetime.datetime.now()
                entries.append((m.group('user'), m.group('token'), ts))
    return entries

def store_entry(db_path: str, username: str, token_hash: str, ts: datetime.datetime) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('INSERT INTO logins (username, token_hash, ts) VALUES (?, ?, ?)',
                (username, token_hash, ts.isoformat()))
    conn.commit()
    conn.close()

def summarize(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT username, COUNT(*) FROM logins GROUP BY username')
    rows = cur.fetchall()
    conn.close()
    print('Login summary:')
    for user, count in rows:
        print(f'  {user}: {count}')

def main() -> None:
    parser = argparse.ArgumentParser(description='Simple log analysis')
    parser.add_argument('logfile', help='Path to log file')
    parser.add_argument('--db', default='logins.db', help='SQLite database file')
    parser.add_argument('--config', default='config.yaml', help='Optional config file')
    args = parser.parse_args()

    config = load_config(args.config)
    db_path = config.get('db_path', args.db)

    init_db(db_path)

    entries = parse_log(args.logfile)
    for username, token, ts in entries:
        token_hash = hash_token(token)
        store_entry(db_path, username, token_hash, ts)

    summarize(db_path)

if __name__ == '__main__':
    main()