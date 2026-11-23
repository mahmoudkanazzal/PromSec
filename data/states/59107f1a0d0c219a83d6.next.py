#!/usr/bin/env python3
from __future__ import print_function
import os, sqlite3, yaml, hashlib, datetime, requests, tempfile

CONFIG_PATH = '/etc/log_analyzer.yaml'

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {'log_files': ['/var/log/syslog']}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def init_db():
    # Use a secure temporary file for the SQLite database
    tmp = tempfile.NamedTemporaryFile(delete=False, prefix='log_analysis_', suffix='.db')
    db_path = tmp.name
    tmp.close()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS logs
                   (id INTEGER PRIMARY KEY,
                    file TEXT,line TEXT,level TEXT,timestamp TEXT)''')
    conn.commit()
    return conn

def write_temp_file(content):
    # Securely create a temporary file for the report
    tf = tempfile.NamedTemporaryFile(delete=False, mode='w', prefix='log_analysis_', suffix='.tmp')
    tf.write(content)
    tf_path = tf.name
    tf.close()
    return tf_path

def parse_log_line(line):
    parts = line.strip().split()
    if len(parts) < 3:
        return None, None
    ts = ' '.join(parts[0:2])
    level = parts[2].strip(':')
    return ts, level

def store_line(conn, fpath, line, level, ts):
    cur = conn.cursor()
    cur.execute('INSERT INTO logs (file,line,level,timestamp) VALUES (?,?,?,?)',
                (fpath, line, level, ts))
    conn.commit()

def _tail(filepath, n=1000):
    """Return the last n lines of a file efficiently."""
    with open(filepath, 'rb') as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        block_size = 1024
        data = b''
        while len(data.splitlines()) <= n and f.tell() > 0:
            seek_offset = min(block_size, f.tell())
            f.seek(-seek_offset, os.SEEK_CUR)
            data = f.read(seek_offset) + data
            f.seek(-seek_offset, os.SEEK_CUR)
        lines = data.splitlines()[-n:]
        return [line.decode(errors='replace') for line in lines]

def analyze_logs(conn, files):
    for p in files:
        if not os.path.exists(p):
            continue
        for l in _tail(p, 1000):
            ts, lev = parse_log_line(l)
            if ts and lev:
                store_line(conn, p, l.strip(), lev, ts)

def generate_report(conn):
    cur = conn.cursor()
    cur.execute('SELECT level,COUNT(*) FROM logs GROUP BY level')
    rows = cur.fetchall()
    lines = ['Log Level Summary:']
    for lvl, cnt in rows:
        lines.append(f'{lvl}: {cnt}')
    rpt = '\n'.join(lines)
    return rpt, write_temp_file(rpt)

def send_report(rpt, url):
    try:
        return requests.post(url, data={'report': rpt}, timeout=10).status_code
    except Exception:
        return None

def main():
    cfg = load_config()
    db = init_db()
    analyze_logs(db, cfg.get('log_files', []))
    rpt, path = generate_report(db)
    print('Report written to', path)
    wh = cfg.get('webhook_url')
    if wh:
        print('Report sent, status:', send_report(rpt, wh))

if __name__ == '__main__':
    main()