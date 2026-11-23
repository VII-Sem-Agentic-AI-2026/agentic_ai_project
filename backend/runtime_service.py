"""Durable run checkpoints, bounded repair and student fan-out with review gating."""
import hashlib,json,time,uuid,threading
from concurrent.futures import ThreadPoolExecutor,as_completed
import agent_pipeline
from tool_gateway import Gateway
from analysis_service import analyse

def initialize(db):
 db.executescript('''CREATE TABLE IF NOT EXISTS agent_runs(id TEXT PRIMARY KEY,student TEXT,actor TEXT,request_key TEXT UNIQUE,fingerprint TEXT,status TEXT,attempts INTEGER,report_id INTEGER,error TEXT,created REAL,updated REAL);
 CREATE TABLE IF NOT EXISTS agent_stages(run_id TEXT,name TEXT,dependencies TEXT,status TEXT,output TEXT,error TEXT,attempts INTEGER,updated REAL,PRIMARY KEY(run_id,name));
 CREATE TABLE IF NOT EXISTS agent_batches(id TEXT PRIMARY KEY,actor TEXT,students TEXT,status TEXT,results TEXT,created REAL);''')
 db.execute("UPDATE agent_runs SET status='interrupted',error='Server restarted; retry to resume checkpoints.' WHERE status='running'")
 db.execute("UPDATE agent_batches SET status='interrupted' WHERE status='running'")

def fingerprint(evidence):return hashlib.sha256(('checkpoint-graph-2:'+json.dumps(evidence,sort_keys=True)).encode()).hexdigest()

def start(actor,student,connect,request_id=None):
 gateway=Gateway(actor,connect);evidence=gateway.call('student_evidence',{'student':student})
 request_key=actor['id']+':'+request_id if request_id else uuid.uuid4().hex
 with connect() as db:
  db.execute('BEGIN IMMEDIATE')
  old=db.execute('SELECT id FROM agent_runs WHERE request_key=?',(request_key,)).fetchone()
  if old:return old['id']
  ident=uuid.uuid4().hex;now=time.time()
  db.execute('INSERT INTO agent_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)',(ident,student,actor['id'],request_key,fingerprint(evidence),'queued',0,None,'',now,now))
 return ident

def execute(actor,ident,connect):
 with connect() as db:
  db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM agent_runs WHERE id=?',(ident,)).fetchone()
  if not row or (actor['role']!='faculty' and row['student']!=actor['id']):raise PermissionError('Run unavailable')
  if row['status']=='completed':return {'id':row['report_id'],'runId':ident,'status':'pending','message':'Existing report returned; no duplicate was created.'}
  if row['status']=='running':raise ValueError('Run is already processing')
  if row['attempts']>=3:raise ValueError('Retry budget exhausted. Start a new run after correcting the source.')
  db.execute("UPDATE agent_runs SET status='running',attempts=attempts+1,updated=? WHERE id=?",(time.time(),ident))
 gateway=Gateway(actor,connect);student=row['student']
 def checkpoint(name,dependencies,fn):
  with connect() as db:saved=db.execute('SELECT * FROM agent_stages WHERE run_id=? AND name=?',(ident,name)).fetchone()
  if saved and saved['status']=='complete':return json.loads(saved['output'])
  for attempt in range(2):
   with connect() as db:
    db.execute('''INSERT INTO agent_stages VALUES(?,?,?,'running',NULL,'',1,?) ON CONFLICT(run_id,name) DO UPDATE SET status='running',attempts=attempts+1,updated=excluded.updated''',(ident,name,json.dumps(dependencies),time.time()))
   try:
    value=fn()
    with connect() as db:db.execute("UPDATE agent_stages SET status='complete',output=?,error='',updated=? WHERE run_id=? AND name=?",(json.dumps(value),time.time(),ident,name))
    return json.loads(json.dumps(value))
   except Exception as error:
    with connect() as db:db.execute("UPDATE agent_stages SET status='failed',error=?,updated=? WHERE run_id=? AND name=?",(str(error)[:500],time.time(),ident,name))
    if not isinstance(error,(OSError,TimeoutError)) or attempt==1:raise
 def invalidate(root):
  with connect() as db:
   stages=db.execute('SELECT name,dependencies FROM agent_stages WHERE run_id=?',(ident,)).fetchall();remove={root}
   for _ in stages:
    remove.update(s['name'] for s in stages if set(json.loads(s['dependencies']))&remove)
   for name in remove:db.execute('DELETE FROM agent_stages WHERE run_id=? AND name=?',(ident,name))
   db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(actor['id'],'targeted_repair:'+ident+':'+root,time.time()))
 try:
  evidence=gateway.call('student_evidence',{'student':student})
  if fingerprint(evidence)!=row['fingerprint']:raise ValueError('Evidence changed. Start a new run; old checkpoints cannot be reused.')
  for repair in range(2):
   try:
    report=agent_pipeline.run(**evidence,analyse=analyse,checkpoint=checkpoint,coding_reader=lambda:gateway.call('coding_profiles',{'student':student}));break
   except agent_pipeline.AcceptanceFailure as error:
    if repair:raise
    root='Resume and JD specialist' if not error.checks.get('evidence_present') or not error.checks.get('coverage_bounds') else 'Preparation planning specialist'
    invalidate(root)
  report['memory']=gateway.call('approved_memory',{'student':student,'query':evidence['profile'].get('target','')})
  report['execution']['id']=ident;report['execution']['version']='checkpoint-graph-2'
  report['execution']['repairBudget']=1
  if fingerprint(gateway.call('student_evidence',{'student':student}))!=row['fingerprint']:raise ValueError('Evidence changed during the run. Start a new run.')
  with connect() as db:
   db.execute('BEGIN IMMEDIATE')
   # Recheck mutable inputs in the same transaction that publishes the draft.
   profile=db.execute('SELECT data FROM profiles WHERE user_id=?',(student,)).fetchone()
   resume=db.execute('SELECT digest FROM resumes WHERE user_id=?',(student,)).fetchone()
   if not profile or json.loads(profile['data'])!=evidence['profile'] or not resume or resume['digest']!=evidence['resume']['digest']:raise ValueError('Profile/resume changed before publication')
   db.execute("UPDATE analyses SET status='superseded' WHERE user_id=? AND status='pending'",(student,))
   report_id=db.execute('INSERT INTO analyses(user_id,status,data,created) VALUES(?,?,?,?)',(student,'pending',json.dumps(report),time.time())).lastrowid
   db.execute("UPDATE agent_runs SET status='completed',report_id=?,error='',updated=? WHERE id=?",(report_id,time.time(),ident))
   db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(actor['id'],'runtime_report:'+ident,time.time()))
  return {'id':report_id,'runId':ident,'status':'pending','message':'Analysis sent to your placement officer for review.'}
 except Exception as error:
  with connect() as db:db.execute("UPDATE agent_runs SET status='failed',error=?,updated=? WHERE id=?",(str(error)[:500],time.time(),ident))
  raise ValueError(str(error)) from error

def batch_worker(actor,ident,students,connect):
 def work(student):
  try:
   run_id=start(actor,student,connect,ident+':'+student)
   return {'student':student,'ok':True,**execute(actor,run_id,connect)}
  except Exception as error:return {'student':student,'ok':False,'error':str(error)[:500]}
 results=[]
 try:
  with ThreadPoolExecutor(max_workers=2) as pool:
   for future in as_completed([pool.submit(work,s) for s in students]):
    results.append(future.result())
    with connect() as db:db.execute('UPDATE agent_batches SET results=? WHERE id=?',(json.dumps(results),ident))
  with connect() as db:db.execute("UPDATE agent_batches SET status='completed',results=? WHERE id=?",(json.dumps(results),ident))
 except Exception:
  with connect() as db:db.execute("UPDATE agent_batches SET status='failed',results=? WHERE id=?",(json.dumps(results),ident))

def handle(handler,user,data,connect):
 path=handler.path
 if path not in ('/api/analyse','/api/runs','/api/runs/retry','/api/swarm','/api/memory'):return False
 try:
  if path=='/api/analyse':
   if data is None or user['role']!='student':raise PermissionError('Student POST required')
   key=data.get('requestId')
   if key is not None and (not isinstance(key,str) or not 1<=len(key)<=100):raise ValueError('Invalid request ID')
   result=execute(user,start(user,user['id'],connect,key),connect)
  elif path=='/api/memory':
   if data is None:raise ValueError('POST required')
   result=Gateway(user,connect).call('approved_memory',{'student':data.get('student',user['id']),'query':data.get('query','')})
  elif path=='/api/runs/retry':
   if data is None or not isinstance(data.get('id'),str):raise ValueError('Run ID required')
   result=execute(user,data['id'],connect)
  elif path=='/api/runs':
   if data is not None:raise ValueError('GET required')
   with connect() as db:
    rows=db.execute('SELECT r.* FROM agent_runs r JOIN profiles p ON p.user_id=r.student '+('' if user['role']=='faculty' else 'WHERE r.student=? ')+'ORDER BY r.created DESC LIMIT 100',() if user['role']=='faculty' else (user['id'],)).fetchall()
    result=[]
    for row in rows:
     p=db.execute('SELECT data FROM profiles WHERE user_id=?',(row['student'],)).fetchone()
     if not p or not json.loads(p['data']).get('resumeConsent'):continue
     stages=[dict(s) for s in db.execute('SELECT name,status,attempts,error,updated FROM agent_stages WHERE run_id=?',(row['id'],))]
     result.append({k:row[k] for k in ('id','student','status','attempts','report_id','error','created')}|{'stages':stages})
  else:
   if user['role']!='faculty':raise PermissionError('Placement officer access required')
   if data is None:
    with connect() as db:result=[{**dict(r),'students':json.loads(r['students']),'results':json.loads(r['results'])} for r in db.execute('SELECT * FROM agent_batches WHERE actor=? ORDER BY created DESC LIMIT 20',(user['id'],))]
   else:
    students=data.get('students')
    if not isinstance(students,list) or not 1<=len(students)<=8 or any(not isinstance(s,str) or not s for s in students) or len(set(students))!=len(students):raise ValueError('Choose 1-8 distinct student IDs')
    with connect() as db:
     db.execute('BEGIN IMMEDIATE')
     if db.execute("SELECT 1 FROM agent_batches WHERE status='running'").fetchone():raise ValueError('A batch is already running. Wait for completion.')
     ident=uuid.uuid4().hex;db.execute('INSERT INTO agent_batches VALUES(?,?,?,?,?,?)',(ident,user['id'],json.dumps(students),'running','[]',time.time()))
    threading.Thread(target=batch_worker,args=(dict(user),ident,students,connect),daemon=True).start()
    result={'id':ident,'status':'running'}
  handler.send(200,result)
 except PermissionError as error:handler.send(403,{'error':str(error)})
 except (ValueError,TypeError) as error:handler.send(400,{'error':str(error)})
 return True
