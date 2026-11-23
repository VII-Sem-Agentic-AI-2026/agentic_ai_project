"""Immutable report revisions, explicit active publication and officer audit metrics."""
import json,time

def initialize(db):
 db.executescript('''CREATE TABLE IF NOT EXISTS publications(user_id TEXT PRIMARY KEY,report_id INTEGER,updated REAL);
 CREATE TABLE IF NOT EXISTS consent_history(id INTEGER PRIMARY KEY,user_id TEXT,data TEXT,created REAL);''')
 for r in db.execute("SELECT user_id,MAX(id) AS id FROM analyses WHERE status='approved' GROUP BY user_id").fetchall():
  db.execute('INSERT OR IGNORE INTO publications VALUES(?,?,?)',(r['user_id'],r['id'],time.time()))

def handle(handler,user,data,connect):
 if handler.path not in ('/api/governance','/api/governance/revise','/api/governance/rollback','/api/consent-history'):return False
 try:
  if handler.path=='/api/consent-history':
   with connect() as db:rows=db.execute('SELECT data,created FROM consent_history WHERE user_id=? ORDER BY id DESC LIMIT 30',(user['id'],)).fetchall()
   handler.send(200,[{'consent':json.loads(r['data']),'created':r['created']} for r in rows]);return True
  if user['role']!='faculty':raise PermissionError('Placement officer access required')
  with connect() as db:
   if handler.path=='/api/governance':
    counts={r['status']:r['count'] for r in db.execute('SELECT status,count(*) AS count FROM analyses GROUP BY status')}
    runs={r['status']:r['count'] for r in db.execute('SELECT status,count(*) AS count FROM agent_runs GROUP BY status')}
    events=[dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 100')]
    publications=[dict(r) for r in db.execute('SELECT p.*,u.name FROM publications p JOIN users u ON u.id=p.user_id')]
    handler.send(200,{'reportCounts':counts,'runCounts':runs,'events':events,'publications':publications});return True
   if data is None or type(data.get('id')) is not int:raise ValueError('Report ID required')
   note=data.get('note','')
   if not isinstance(note,str) or not 10<=len(note.strip())<=2000:raise ValueError('Write a reason of 10-2,000 characters')
   db.execute('BEGIN IMMEDIATE')
   row=db.execute('SELECT a.*,p.data AS profile FROM analyses a JOIN profiles p ON p.user_id=a.user_id WHERE a.id=?',(data['id'],)).fetchone()
   if not row or not json.loads(row['profile']).get('resumeConsent'):raise PermissionError('Report unavailable or consent withdrawn')
   report=json.loads(row['data'])
   if handler.path=='/api/governance/rollback':
    if row['status']!='approved':raise ValueError('Only an approved version can become the current publication')
    if report.get('benchmark',{}).get('expires',time.time()+1)<=time.time():raise ValueError('This benchmark has expired. Generate and review a fresh report.')
    db.execute('INSERT INTO publications VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET report_id=excluded.report_id,updated=excluded.updated',(row['user_id'],row['id'],time.time()))
    ident=row['id'];action='publication_rollback:'+str(ident)+':'+note.strip()
   else:
    if row['status'] not in ('approved','pending','changes_requested'):raise ValueError('This report cannot be revised')
    tasks=data.get('tasks')
    if not isinstance(tasks,list) or len(tasks)!=len(report['roadmap']):raise ValueError('Provide one revised activity for each existing roadmap task')
    for original,updated in zip(report['roadmap'],tasks):
     if not isinstance(updated,str) or not 10<=len(updated.strip())<=1500:raise ValueError('Each activity needs 10-1,500 characters')
     original['task']=updated.strip()
    report['revision']={'parent':row['id'],'editor':user['id'],'reason':note.strip(),'created':time.time()}
    # Preserve numerical evidence; only preparation activities are editable here.
    if not report.get('validation') or not all(v is True for v in report['validation'].values()):raise ValueError('Source report has failed validation')
    report['officerGuidance']=note.strip()
    ident=db.execute('INSERT INTO analyses(user_id,status,data,created) VALUES(?,?,?,?)',(row['user_id'],'pending',json.dumps(report),time.time())).lastrowid
    action='report_revision:'+str(row['id'])+'->'+str(ident)
   db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],action,time.time()))
  handler.send(200,{'id':ident,'ok':True})
 except PermissionError as error:handler.send(403,{'error':str(error)})
 except (ValueError,TypeError) as error:handler.send(400,{'error':str(error)})
 return True
