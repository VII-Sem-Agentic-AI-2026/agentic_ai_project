"""Private timed coding attempts, sample runs and server-side hidden tests."""
import json,time,uuid
import coding_runner
PROBLEMS={
 'even_sum':{'title':'Sum the even numbers','topic':'Arrays','prompt':'Read one JSON array of integers from standard input. Print one JSON integer: the sum of all even values. Empty arrays produce 0.',
  'cases':[{'input':[1,2,3,4],'expected':6},{'input':[],'expected':0,'hidden':True},{'input':[-4,-3,2,0],'expected':-2,'hidden':True},{'input':[7,9,11],'expected':0,'hidden':True},{'input':[100000,100000,2],'expected':200002,'hidden':True}]},
 'palindrome':{'title':'Normalised palindrome','topic':'Strings','prompt':'Read a JSON string. Ignore non-alphanumeric characters and case. Print JSON true if the remaining characters form a palindrome, otherwise false. An empty normalised string is a palindrome.',
  'cases':[{'input':'A man, a plan, a canal: Panama!','expected':True},{'input':'hello','expected':False,'hidden':True},{'input':'!?','expected':True,'hidden':True},{'input':'0P','expected':False,'hidden':True},{'input':'RaceCar','expected':True,'hidden':True}]},
 'unique':{'title':'First unique value','topic':'Hash maps','prompt':'Read a JSON array of integers. Print the first value that occurs exactly once, preserving input order. Print JSON null if none exists.',
  'cases':[{'input':[4,2,4,3,2],'expected':3},{'input':[],'expected':None,'hidden':True},{'input':[1,1,2,2],'expected':None,'hidden':True},{'input':[0,-1,-1,2],'expected':0,'hidden':True},{'input':[9,8,7],'expected':9,'hidden':True}]}}
STARTER='import json, sys\ndata = json.load(sys.stdin)\n# Compute your answer here\nanswer = None\nprint(json.dumps(answer))\n'

def initialize(db):
 db.execute('''CREATE TABLE IF NOT EXISTS coding_attempts(id TEXT PRIMARY KEY,user_id TEXT,problem TEXT,status TEXT,code TEXT,result TEXT,sample_result TEXT,started REAL,deadline REAL,evaluations INTEGER)''')
 db.execute("UPDATE coding_attempts SET status='active' WHERE status='evaluating'")

def public_problem(key):
 p=PROBLEMS[key];return {'id':key,**{k:p[k] for k in ('title','topic','prompt')},'samples':[c for c in p['cases'] if not c.get('hidden')],'starter':STARTER}

def handle(handler,user,data,connect):
 path=handler.path
 if path not in ('/api/coding','/api/coding/start','/api/coding/open','/api/coding/save','/api/coding/run','/api/coding/submit'):return False
 try:
  if path=='/api/coding':
   with connect() as db:rows=db.execute('SELECT c.*,u.name FROM coding_attempts c JOIN users u ON u.id=c.user_id '+('' if user['role']=='faculty' else 'WHERE c.user_id=? ')+'ORDER BY started DESC LIMIT 100',() if user['role']=='faculty' else (user['id'],)).fetchall()
   handler.send(200,{'runner':coding_runner.status(),'problems':[public_problem(k) for k in PROBLEMS],'attempts':[{k:r[k] for k in ('id','user_id','name','problem','status','started','deadline')}|{'result':json.loads(r['result']) if r['result'] else None} for r in rows]});return True
  if data is None:raise ValueError('POST required')
  if path=='/api/coding/start':
   if user['role']!='student':raise PermissionError('Student account required')
   key=data.get('problem')
   if key not in PROBLEMS:raise ValueError('Unknown coding problem')
   ready=coding_runner.status()
   if not ready['ready']:raise ValueError(ready['message'])
   with connect() as db:
    db.execute('BEGIN IMMEDIATE')
    existing=db.execute("SELECT id FROM coding_attempts WHERE user_id=? AND status IN ('active','evaluating') AND deadline>?",(user['id'],time.time())).fetchone()
    if existing:ident=existing['id']
    else:
     ident=uuid.uuid4().hex;now=time.time()
     db.execute('INSERT INTO coding_attempts VALUES(?,?,?,?,?,?,?,?,?,?)',(ident,user['id'],key,'active',STARTER,None,None,now,now+1800,0))
    row=db.execute('SELECT * FROM coding_attempts WHERE id=?',(ident,)).fetchone()
  else:
   ident=data.get('id')
   if not isinstance(ident,str):raise ValueError('Attempt ID required')
   with connect() as db:
    db.execute('BEGIN IMMEDIATE')
    row=db.execute('SELECT * FROM coding_attempts WHERE id=?',(ident,)).fetchone()
    if not row or (user['role']!='faculty' and row['user_id']!=user['id']):raise PermissionError('Coding attempt unavailable')
    if path!='/api/coding/open':
     if user['role']!='student' or row['user_id']!=user['id']:raise PermissionError('Only the student can submit this attempt')
     if row['status']=='submitted' and path=='/api/coding/submit':pass
     elif row['status']!='active':raise ValueError('Attempt is already evaluating or closed')
     elif time.time()>row['deadline']:raise ValueError('Time expired. Start another attempt; the saved code remains available.')
     else:
      code=data.get('code')
      if not isinstance(code,str) or not 1<=len(code)<=12000:raise ValueError('Code must contain 1-12,000 characters')
      if path in ('/api/coding/run','/api/coding/submit'):
       if row['evaluations']>=20:raise ValueError('Evaluation budget exhausted. Start a new attempt after this one expires.')
       db.execute("UPDATE coding_attempts SET code=?,status='evaluating',evaluations=evaluations+1 WHERE id=?",(code,ident))
      else:db.execute('UPDATE coding_attempts SET code=? WHERE id=?',(code,ident))
   if path in ('/api/coding/run','/api/coding/submit') and row['status']!='submitted':
    cases=PROBLEMS[row['problem']]['cases']
    if path=='/api/coding/run':cases=[c for c in cases if not c.get('hidden')]
    try:result=coding_runner.grade(code,cases)
    except Exception as error:
     with connect() as db:db.execute("UPDATE coding_attempts SET status='active' WHERE id=?",(ident,))
     raise ValueError('Evaluation unavailable; your code is saved. '+str(error)) from error
    with connect() as db:
     if path=='/api/coding/submit':
      db.execute("UPDATE coding_attempts SET status='submitted',result=? WHERE id=?",(json.dumps(result),ident))
      db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],'coding_submitted:'+ident,time.time()))
     else:db.execute("UPDATE coding_attempts SET status='active',sample_result=? WHERE id=?",(json.dumps(result),ident))
   with connect() as db:row=db.execute('SELECT * FROM coding_attempts WHERE id=?',(ident,)).fetchone()
  result={**dict(row),'problemDetail':public_problem(row['problem']),'result':json.loads(row['result']) if row['result'] else None,'sample_result':json.loads(row['sample_result']) if row['sample_result'] else None,'serverTime':time.time()}
  handler.send(200,result)
 except PermissionError as error:handler.send(403,{'error':str(error)})
 except (ValueError,TypeError) as error:handler.send(400,{'error':str(error)})
 return True
