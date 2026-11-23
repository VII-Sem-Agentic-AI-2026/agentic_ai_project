"""Faculty-reviewed role packs with provenance and expiry."""
import json,time
from analysis_service import BENCHMARKS

def initialize(db):
 db.execute('CREATE TABLE IF NOT EXISTS role_benchmarks(role TEXT PRIMARY KEY,skills TEXT,source TEXT,reviewer TEXT,reviewed REAL,expires REAL,version INTEGER)')
 for role,skills in BENCHMARKS.items():db.execute('INSERT OR IGNORE INTO role_benchmarks VALUES(?,?,?,?,?,?,?)',(role,json.dumps(skills),'Project sample benchmark; officer review required','',0,0,1))

def handle(handler,user,data,connect):
 if handler.path!='/api/benchmarks':return False
 try:
  if user['role']!='faculty':raise PermissionError('Placement officer access required')
  with connect() as db:
   if data is None:
    rows=db.execute('SELECT * FROM role_benchmarks ORDER BY role').fetchall()
    handler.send(200,[dict(r)|{'skills':json.loads(r['skills']),'current':r['expires']>time.time()} for r in rows]);return True
   role=data.get('role');skills=data.get('skills');source=data.get('source');days=data.get('days',90)
   if role not in BENCHMARKS or not isinstance(skills,list) or not 1<=len(skills)<=20 or any(not isinstance(s,str) or not 1<=len(s.strip())<=60 for s in skills):raise ValueError('Select a role and 1-20 skill names')
   if not isinstance(source,str) or not 10<=len(source.strip())<=1000 or type(days) is not int or not 1<=days<=365:raise ValueError('Provide source details and a review interval of 1-365 days')
   skills=list(dict.fromkeys(s.strip() for s in skills));now=time.time()
   db.execute('UPDATE role_benchmarks SET skills=?,source=?,reviewer=?,reviewed=?,expires=?,version=version+1 WHERE role=?',(json.dumps(skills),source.strip(),user['id'],now,now+days*86400,role))
   db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],'benchmark_review:'+role,now))
  handler.send(200,{'ok':True})
 except PermissionError as error:handler.send(403,{'error':str(error)})
 except (ValueError,TypeError) as error:handler.send(400,{'error':str(error)})
 return True
