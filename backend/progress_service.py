"""Student-reported progress against immutable, approved roadmap snapshots."""
import json,time

def initialize(db):
 db.execute('''CREATE TABLE IF NOT EXISTS roadmap_progress(
 report_id INTEGER,task_index INTEGER,status TEXT,note TEXT,updated REAL,
 PRIMARY KEY(report_id,task_index))''')

def handle(handler,user,data,connect):
 if handler.path not in ('/api/progress','/api/progress/update'):return False
 try:
  with connect() as db:
   if handler.path=='/api/progress':
    if data is not None:raise ValueError('Use GET to load progress')
    rows=db.execute('''SELECT a.*,u.name FROM analyses a JOIN users u ON u.id=a.user_id
     WHERE a.status='approved' '''+('' if user['role']=='faculty' else 'AND a.user_id=? ')+
     'ORDER BY a.created DESC',() if user['role']=='faculty' else (user['id'],)).fetchall()
    plans=[]
    for row in rows:
     profile=db.execute('SELECT data FROM profiles WHERE user_id=?',(row['user_id'],)).fetchone()
     if not profile or not json.loads(profile['data']).get('resumeConsent'):continue
     publication=db.execute('SELECT report_id FROM publications WHERE user_id=?',(row['user_id'],)).fetchone()
     report=json.loads(row['data'])
     saved={r['task_index']:dict(r) for r in db.execute('SELECT * FROM roadmap_progress WHERE report_id=?',(row['id'],))}
     tasks=[{**task,'index':i,'status':saved.get(i,{}).get('status','not_started'),
       'note':saved.get(i,{}).get('note',''),'updated':saved.get(i,{}).get('updated')}
       for i,task in enumerate(report.get('roadmap',[]))]
     plans.append({'id':row['id'],'student':row['user_id'],'name':row['name'],'target':report['target'],
      'created':row['created'],'isCurrent':bool(publication and publication['report_id']==row['id']),'tasks':tasks,'completed':sum(t['status']=='completed' for t in tasks)})
    plans.sort(key=lambda plan: not plan['isCurrent'])
    handler.send(200,plans);return True
   if user['role']!='student':raise PermissionError('Only students can update their own progress')
   if data is None:raise ValueError('POST required')
   ident=data.get('id');index=data.get('index');status=data.get('status');note=data.get('note','')
   if type(ident) is not int or type(index) is not int:raise ValueError('Valid report and task required')
   if status not in ('not_started','in_progress','completed'):raise ValueError('Invalid progress status')
   if not isinstance(note,str) or len(note)>2000:raise ValueError('Keep evidence notes within 2,000 characters')
   if status=='completed' and len(note.strip())<10:raise ValueError('Describe what you completed and the evidence in at least 10 characters')
   db.execute('BEGIN IMMEDIATE')
   row=db.execute("SELECT * FROM analyses WHERE id=? AND user_id=? AND status='approved'",(ident,user['id'])).fetchone()
   if not row:raise PermissionError('Approved roadmap unavailable')
   profile=db.execute('SELECT data FROM profiles WHERE user_id=?',(user['id'],)).fetchone()
   if not profile or not json.loads(profile['data']).get('resumeConsent'):raise PermissionError('Resume consent required to use this roadmap')
   if not 0<=index<len(json.loads(row['data']).get('roadmap',[])):raise ValueError('Task does not exist in this report')
   now=time.time()
   db.execute('''INSERT INTO roadmap_progress VALUES(?,?,?,?,?) ON CONFLICT(report_id,task_index)
    DO UPDATE SET status=excluded.status,note=excluded.note,updated=excluded.updated''',(ident,index,status,note.strip(),now))
   db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],f'roadmap_progress:{ident}:{index}:{status}',now))
  handler.send(200,{'ok':True})
 except PermissionError as exc:handler.send(403,{'error':str(exc)})
 except ValueError as exc:handler.send(400,{'error':str(exc)})
 return True
