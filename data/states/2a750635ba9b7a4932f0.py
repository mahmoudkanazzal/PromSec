from __future__ import print_function
import os, time, threading, sqlite3, subprocess
from flask import Flask, request, redirect, url_for, render_template_string
DB_PATH='jobs.db'
TMP_DIR='/tmp'
def init_db():
 conn=sqlite3.connect(DB_PATH);c=conn.cursor()
 c.execute('''CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,command TEXT,schedule INTEGER,status TEXT)''')
 conn.commit();conn.close()
def add_job(name,command,schedule):
 conn=sqlite3.connect(DB_PATH);c=conn.cursor()
 c.execute('INSERT INTO jobs (name,command,schedule,status) VALUES (?,?,?,?)',(name,command,schedule,'pending'))
 conn.commit();conn.close()
def fetch_due():
 now=int(time.time());conn=sqlite3.connect(DB_PATH);c=conn.cursor()
 c.execute('SELECT id,command FROM jobs WHERE schedule<=? AND status=?',(now,'pending'))
 rows=c.fetchall();conn.close();return rows
def update_status(jid,status):
 conn=sqlite3.connect(DB_PATH);c=conn.cursor()
 c.execute('UPDATE jobs SET status=? WHERE id=?',(status,jid))
 conn.commit();conn.close()
def run_job(jid,command):
 try:
  tmp=os.path.join(TMP_DIR,f'job_{jid}_{int(time.time())}.log')
  with open(tmp,'w') as f:
   proc=subprocess.Popen(command,shell=True,stdout=f,stderr=subprocess.STDOUT);proc.wait()
  update_status(jid,'done')
 except Exception:
  update_status(jid,'error')
def worker():
 while True:
  for jid,cmd in fetch_due():
   update_status(jid,'running')
   run_job(jid,cmd)
  time.sleep(5)
app=Flask(__name__)
@app.route('/')
def index():
 conn=sqlite3.connect(DB_PATH);c=conn.cursor()
 c.execute('SELECT id,name,command,schedule,status FROM jobs ORDER BY id DESC')
 jobs=c.fetchall();conn.close()
 html='''<h1>Job Scheduler</h1><a href="{{ url_for('add') }}">Add Job</a><table border="1"><tr><th>ID</th><th>Name</th><th>Command</th><th>Schedule</th><th>Status</th></tr>{% for j in jobs %}<tr><td>{{ j[0] }}</td><td>{{ j[1] }}</td><td>{{ j[2] }}</td><td>{{ time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(j[3])) }}</td><td>{{ j[4] }}</td></tr>{% endfor %}</table>'''
 return render_template_string(html,jobs=jobs,time=time)
@app.route('/add',methods=['GET','POST'])
def add():
 if request.method=='POST':
  name=request.form['name'];command=request.form['command'];delay=int(request.form.get('delay','60'))
  schedule=int(time.time())+delay;add_job(name,command,schedule);return redirect(url_for('index'))
 form='''<h2>Add Job</h2><form method="post">Name: <input name="name"><br>Command: <input name="command"><br>Delay (seconds): <input name="delay" value="60"><br><input type="submit" value="Add"></form>'''
 return render_template_string(form)
if __name__=='__main__':
 init_db()
 threading.Thread(target=worker,daemon=True).start()
 app.run(host='0.0.0.0',port=5000)