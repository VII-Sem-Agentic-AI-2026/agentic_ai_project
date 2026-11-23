"""Persistent practice attempts. Answer keys remain server-side until submission."""
import json,secrets,time
import ai_generation
from interview_scoring import resume_evidence

def start(user,data,connect):
 if user['role']!='student':raise PermissionError('Student account required')
 if not isinstance(data,dict) or data.get('kind') not in ('aptitude','technical'):raise ValueError('Choose aptitude or technical practice')
 kind=data['kind']
 with connect() as db:
  row=db.execute("SELECT * FROM practice_attempts WHERE user_id=? AND kind=? AND status='active'",(user['id'],kind)).fetchone()
  if row and time.time()<row['deadline']:return public_attempt(row)
  if row:finish(db,row,json.loads(row['answers']))
  profile_row=db.execute('SELECT data FROM profiles WHERE user_id=?',(user['id'],)).fetchone()
  profile=json.loads(profile_row['data']) if profile_row else {}
  resume=db.execute('SELECT text,digest FROM resumes WHERE user_id=?',(user['id'],)).fetchone()
 if data.get('aiConsent') is not True:raise ValueError('Consent to send resume/JD context to Gemini is required for new practice questions')
 if not profile.get('resumeConsent') or not resume or not profile.get('target') or not profile.get('jobDescription','').strip():raise ValueError('Save your target role and JD, enable resume consent, and upload a resume first')
 bank=ai_generation.practice({'kind':kind,'role':profile['target'],'jd':profile['jobDescription'][:6000],'resume':resume_evidence(resume['text'])})
 # The external request happens before acquiring the write lock. Recheck evidence and concurrent starts.
 with connect() as db:
  db.execute('BEGIN IMMEDIATE')
  current=db.execute('SELECT data FROM profiles WHERE user_id=?',(user['id'],)).fetchone()
  current_resume=db.execute('SELECT digest FROM resumes WHERE user_id=?',(user['id'],)).fetchone()
  if not current or json.loads(current['data'])!=profile or not current_resume or current_resume['digest']!=resume['digest']:raise ValueError('Profile, resume or consent changed. Please start again.')
  row=db.execute("SELECT * FROM practice_attempts WHERE user_id=? AND kind=? AND status='active'",(user['id'],kind)).fetchone()
  if row and time.time()>=row['deadline']:finish(db,row,json.loads(row['answers']));row=None
  if not row:
   now=time.time();ident=secrets.token_urlsafe(18)
   db.execute('INSERT INTO practice_attempts VALUES(?,?,?,?,?,?,?,?,?,?)',(ident,user['id'],kind,'active',json.dumps(bank),'{}',None,now,now+1200,None))
   db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],'gemini_practice_generated:'+ident,time.time()))
   row=db.execute('SELECT * FROM practice_attempts WHERE id=?',(ident,)).fetchone()
  return public_attempt(row)

def initialize(db):
 db.executescript('''CREATE TABLE IF NOT EXISTS practice_attempts(id TEXT PRIMARY KEY,user_id TEXT,kind TEXT,status TEXT,questions TEXT,answers TEXT,result TEXT,started REAL,deadline REAL,submitted REAL);''')

def grade(bank,answers):
 reviews=[];topics={}
 for q in bank:
  selected=answers.get(q['id']);correct=selected==q['answer'] and type(selected) is int
  topics.setdefault(q['topic'],{'correct':0,'total':0});topics[q['topic']]['total']+=1;topics[q['topic']]['correct']+=int(correct)
  reviews.append({**q,'selected':selected,'correct':correct})
 total=len(bank);score=sum(r['correct'] for r in reviews)
 return {'correct':score,'total':total,'percentage':round(score*100/total),'answered':len(answers),'topics':topics,'review':reviews,'nextSteps':[f"Review {topic} and retry a related exercise." for topic,counts in topics.items() if counts['correct']<counts['total']],'label':('Gemini-generated questions and answer keys; automatically marked against the saved key. AI answers may contain errors and need review.' if any(q.get('source') for q in bank) else 'Practice result; not a certified readiness score')}

def validate_answers(answers,bank):
 if not isinstance(answers,dict):raise ValueError('Answers must be an object')
 ids={q['id']:q for q in bank}
 for key,value in answers.items():
  if key not in ids or type(value) is not int or not 0<=value<len(ids[key]['options']):raise ValueError('Invalid question or answer selection')
 return answers

def finish(db,row,answers):
 result=grade(json.loads(row['questions']),answers)
 db.execute("UPDATE practice_attempts SET status='submitted',answers=?,result=?,submitted=? WHERE id=?",(json.dumps(answers),json.dumps(result),time.time(),row['id']))
 return result

def public_attempt(row):
 bank=json.loads(row['questions'])
 return {'id':row['id'],'kind':row['kind'],'status':row['status'],'started':row['started'],'deadline':row['deadline'],'serverTime':time.time(),'answers':json.loads(row['answers']),'questions':[{k:q[k] for k in ('id','topic','prompt','options')} for q in bank],'result':json.loads(row['result']) if row['result'] else None}

def handle(handler,user,data,connect):
 path=handler.path
 if path not in ('/api/practice','/api/practice/start','/api/practice/attempt','/api/practice/save','/api/practice/submit'):return False
 try:
  if path=='/api/practice/start':
   handler.send(200,start(user,data,connect));return True
  with connect() as db:
   # Serialize attempt transitions so repeated submissions cannot replace a result.
   db.execute('BEGIN IMMEDIATE')
   if path=='/api/practice':
    if data is not None:raise ValueError('GET required')
    rows=db.execute('SELECT a.*,u.name FROM practice_attempts a JOIN users u ON u.id=a.user_id '+('' if user['role']=='faculty' else 'WHERE a.user_id=? ')+'ORDER BY a.started DESC',() if user['role']=='faculty' else (user['id'],)).fetchall()
    result=[]
    for row in rows:
     if row['status']=='active' and time.time()>=row['deadline']:
      finish(db,row,json.loads(row['answers']));row=db.execute('SELECT a.*,u.name FROM practice_attempts a JOIN users u ON u.id=a.user_id WHERE a.id=?',(row['id'],)).fetchone()
     summary={'id':row['id'],'student':row['user_id'],'name':row['name'],'kind':row['kind'],'status':row['status'],'started':row['started'],'result':None}
     if row['result']:summary['result']={k:v for k,v in json.loads(row['result']).items() if k!='review'}
     result.append(summary)
   else:
    if data is None:raise ValueError('POST required')
    attempt=data.get('id')
    if not isinstance(attempt,str):raise ValueError('Attempt ID required')
    row=db.execute('SELECT * FROM practice_attempts WHERE id=?',(attempt,)).fetchone()
    if not row or (row['user_id']!=user['id'] and user['role']!='faculty'):raise PermissionError('Attempt not available')
    if user['role']=='faculty' and path!='/api/practice/attempt':raise PermissionError('Only the student can answer or submit')
    expired=row['status']=='active' and time.time()>=row['deadline']
    if expired:finish(db,row,json.loads(row['answers']))
    elif row['status']=='active' and path in ('/api/practice/save','/api/practice/submit'):
     answers=validate_answers(data.get('answers'),json.loads(row['questions']))
     if path=='/api/practice/submit':finish(db,row,answers)
     else:db.execute('UPDATE practice_attempts SET answers=? WHERE id=?',(json.dumps(answers),attempt))
    row=db.execute('SELECT * FROM practice_attempts WHERE id=?',(attempt,)).fetchone();result=public_attempt(row)
    if path in ('/api/practice/start','/api/practice/submit'):
     db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],path+':'+result['id'],time.time()))
  handler.send(200,result)
 except PermissionError as exc:handler.send(403,{'error':str(exc)})
 except ValueError as exc:handler.send(400,{'error':str(exc)})
 return True
