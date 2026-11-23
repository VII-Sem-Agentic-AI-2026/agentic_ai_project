"""Authenticated typed tool gateway shared by the runtime and MCP-style JSON-RPC."""
import json,re,time
import profile_connectors
TOOLS=[{'name':name,'description':description,'inputSchema':{'type':'object','properties':{'student':{'type':'string'},**({'query':{'type':'string','maxLength':300}} if name=='approved_memory' else {})},'required':['student'],'additionalProperties':False}}
 for name,description in [('student_evidence','Read consented profile, resume and assessment snapshots.'),('coding_profiles','Read consented public coding activity.'),('approved_memory','Retrieve same-student approved report summaries by lexical similarity.')]]

class Gateway:
 def __init__(self,actor,connect):self.actor=actor;self.connect=connect
 def call(self,name,arguments):
  if not isinstance(name,str) or name not in {t['name'] for t in TOOLS}:raise ValueError('Unknown tool')
  allowed={'student','query'} if name=='approved_memory' else {'student'}
  if not isinstance(arguments,dict) or set(arguments)-allowed:raise ValueError('Invalid tool arguments')
  student=arguments.get('student')
  if not isinstance(student,str) or not student:raise ValueError('Student ID required')
  if self.actor['role']!='faculty' and student!=self.actor['id']:raise PermissionError('Student evidence is private')
  query=arguments.get('query','')
  if not isinstance(query,str) or len(query)>300:raise ValueError('Query must be at most 300 characters')
  with self.connect() as db:
   row=db.execute('SELECT data FROM profiles WHERE user_id=?',(student,)).fetchone()
   profile=json.loads(row['data']) if row else {}
   if not profile.get('resumeConsent'):raise PermissionError('Active student resume consent required')
   resume=db.execute('SELECT * FROM resumes WHERE user_id=?',(student,)).fetchone()
   if not resume:raise ValueError('Student must upload a resume first')
   if name=='student_evidence':
    attempts=[dict(r) for r in db.execute("SELECT kind,result FROM practice_attempts WHERE user_id=? AND status='submitted' ORDER BY submitted DESC",(student,))]
    from coding_service import PROBLEMS
    for coding in db.execute("SELECT problem,result FROM coding_attempts WHERE user_id=? AND status='submitted' ORDER BY started DESC",(student,)):
     score=json.loads(coding['result']);topic=PROBLEMS[coding['problem']]['topic']
     attempts.append({'kind':'coding:'+topic,'result':json.dumps({'correct':score['passed'],'total':score['total'],'percentage':score['percentage'],'topics':{topic:{'correct':score['passed'],'total':score['total']}}})})
    snapshot=db.execute('SELECT data,created FROM connections WHERE user_id=?',(student,)).fetchone()
    saved=db.execute('SELECT id,data FROM coordinator_plans WHERE user_id=? ORDER BY id DESC LIMIT 1',(student,)).fetchone()
    plan=json.loads(saved['data'])|{'id':saved['id']} if saved else None
    selected=db.execute('SELECT * FROM role_benchmarks WHERE role=? AND expires>?',(profile.get('target'),time.time())).fetchone()
    benchmark=dict(selected)|{'skills':json.loads(selected['skills'])} if selected else None
    result={'benchmark':benchmark,'resume':dict(resume),'profile':profile,'attempts':attempts,'snapshot':dict(snapshot) if snapshot else None,'plan':plan}
   elif name=='approved_memory':
    terms=set(re.findall(r'\w+',query.lower()));matches=[]
    for r in db.execute("SELECT id,data,created FROM analyses WHERE user_id=? AND status='approved' ORDER BY id DESC LIMIT 50",(student,)):
     report=json.loads(r['data']);tags=[report['target'],*report['gaps']]
     words=set(re.findall(r'\w+',' '.join(tags).lower()))
     score=len(terms&words)/max(1,len(terms|words)) if terms else 0
     if not terms or score:matches.append({'report':r['id'],'target':report['target'],'gaps':report['gaps'],'coverage':report['coverage'],'similarity':round(score,4),'created':r['created'],'source':'approved-report:'+str(r['id'])})
    result={'matches':sorted(matches,key=lambda r:(r['similarity'],r['created']),reverse=True)[:5],'method':'Same-student lexical Jaccard retrieval; no cross-student memory'}
   else:
    snapshot=db.execute('SELECT data,created FROM connections WHERE user_id=?',(student,)).fetchone()
    result=json.loads(snapshot['data']) if snapshot and time.time()-snapshot['created']<3600 else None
  if name=='coding_profiles':
   if result is None:result=profile_connectors.collect(profile)
   for source,consent in [('github','githubConsent'),('leetcode','codingConsent')]:
    if not profile.get(consent):result[source]={'status':'not_consented','message':'Source consent not granted.'}
    elif result.get(source,{}).get('username') not in (None,profile.get(source)):result[source]={'status':'stale','message':'Account changed. Sync the new account.'}
  with self.connect() as db:db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(self.actor['id'],f'tool:{name}:{student}',time.time()))
  return result

def handle(handler,user,data,connect):
 if handler.path!='/api/mcp':return False
 if data is None:handler.send(405,{'error':'Use JSON-RPC POST'});return True
 ident=data.get('id');method=data.get('method');params=data.get('params',{})
 def reply(result):handler.send(200,{'jsonrpc':'2.0','id':ident,'result':result})
 if data.get('jsonrpc')!='2.0' or not isinstance(params,dict):
  handler.send(400,{'jsonrpc':'2.0','id':ident,'error':{'code':-32600,'message':'Invalid JSON-RPC request'}});return True
 if method=='initialize':reply({'protocolVersion':'2025-06-18','capabilities':{'tools':{}},'serverInfo':{'name':'placement-tools','version':'1.0'}})
 elif method=='notifications/initialized':handler.send_response(202);handler.end_headers()
 elif method=='ping':reply({})
 elif method=='tools/list':reply({'tools':TOOLS})
 elif method=='tools/call':
  try:
   result=Gateway(user,connect).call(params.get('name'),params.get('arguments',{}))
   reply({'content':[{'type':'text','text':json.dumps(result)}],'structuredContent':result,'isError':False})
  except (ValueError,PermissionError) as error:reply({'content':[{'type':'text','text':str(error)}],'isError':True})
 else:handler.send(200,{'jsonrpc':'2.0','id':ident,'error':{'code':-32601,'message':'Method not found'}})
 return True
