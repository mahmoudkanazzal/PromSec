#!/usr/bin/env python3
from __future__ import print_function
import os, sqlite3, yaml, subprocess, hashlib, datetime, requests

CONFIG_PATH='/etc/log_analyzer.yaml'
DB_PATH='/var/tmp/log_analysis.db'
TMP_DIR='/tmp'

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {'log_files':['/var/log/syslog']}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def init_db():
    conn=sqlite3.connect(DB_PATH)
    cur=conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS logs
                   (id INTEGER PRIMARY KEY,
                    file TEXT,line TEXT,level TEXT,timestamp TEXT)''')
    conn.commit()
    return conn

def write_temp_file(content):
    ts=datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    path=os.path.join(TMP_DIR,f'log_analysis_{ts}.tmp')
    with open(path,'w') as f: f.write(content)
    return path

def parse_log_line(line):
    parts=line.strip().split()
    if len(parts)<3: return None,None
    ts=' '.join(parts[0:2])
    level=parts[2].strip(':')
    return ts,level

def store_line(conn,fpath,line,level,ts):
    cur=conn.cursor()
    cur.execute('INSERT INTO logs (file,line,level,timestamp) VALUES (?,?,?,?)',
                (fpath,line,level,ts))
    conn.commit()

def analyze_logs(conn,files):
    for p in files:
        if not os.path.exists(p): continue
        proc=subprocess.Popen(['tail','-n','1000',p],stdout=subprocess.PIPE,text=True)
        for l in proc.stdout:
            ts,lev=parse_log_line(l)
            if ts and lev: store_line(conn,p,l.strip(),lev,ts)
        proc.wait()

def generate_report(conn):
    cur=conn.cursor()
    cur.execute('SELECT level,COUNT(*) FROM logs GROUP BY level')
    rows=cur.fetchall()
    lines=['Log Level Summary:']
    for lvl,cnt in rows: lines.append(f'{lvl}: {cnt}')
    rpt='\n'.join(lines)
    return rpt,write_temp_file(rpt)

def send_report(rpt,url):
    try: return requests.post(url,data={'report':rpt}).status_code
    except: return None

def main():
    cfg=load_config()
    db=init_db()
    analyze_logs(db,cfg.get('log_files',[]))
    rpt,path=generate_report(db)
    print('Report written to',path)
    wh=cfg.get('webhook_url')
    if wh: print('Report sent, status:',send_report(rpt,wh))

if __name__=='__main__':
    main()