"""Persistent clarify-plan-revise loop with optional, validated Gemini planning."""
import json,time
from analysis_service import BENCHMARKS,analyse
import gemini_provider,ai_generation
from tool_gateway import Gateway
from jd_matching import compare
STEPS=['student_evidence','coding_profiles','approved_memory','specialist_analysis','acceptance_validation','officer_review']

def initialize(db):
 db.execute('CREATE TABLE IF NOT EXISTS coordinator_plans(id INTEGER PRIMARY KEY,user_id TEXT,version INTEGER,data TEXT,created REAL)')

def build(profile,goal,hours,focus):
 questions=[]
 if len(goal.strip())<15:questions.extend(['Which role or placement outcome do you want to prepare for?','Which skills or interview topics currently feel most difficult?'])
 if profile.get('target') not in BENCHMARKS:questions.append('Choose your target role in Profile & preferences.')
 if not profile.get('resumeConsent'):questions.append('Will you allow resume processing in Profile & preferences?')
 if type(hours) is not int or not 1<=hours<=40:questions.append('How many hours per week can you commit, between 1 and 40?')
 if questions:return {'status':'needs_clarification','questions':questions,'goal':goal,'hours':hours,'focus':focus,'planner':'Rule coordinator'}
 return {'status':'ready','questions':[],'goal':goal,'hours':hours,'focus':focus,'target':profile['target'],
  'steps':STEPS,'specialistPack':profile['target'],'benchmarkSkills':BENCHMARKS[profile['target']],
  'rationale':'Collect consented evidence, compare against the role/JD, retrieve approved history, prepare gap-linked tasks, validate and seek officer review.',
  'weeklySchedule':[{'activity':'Skill learning and exercises','hours':round(hours*.4,1)},{'activity':'Coding and technical practice','hours':round(hours*.4,1)},{'activity':'Project explanation and interview reflection','hours':round(hours*.2,1)}],
  'planner':'Rule coordinator','budget':{'reportAttempts':3,'parallelWorkers':2,'targetedRepairs':1}}

def handle(handler,user,data,connect):
 if handler.path not in ('/api/coordinator','/api/coordinator/plan'):return False
 try:
  if handler.path=='/api/coordinator':
   with connect() as db:
    rows=db.execute('SELECT c.*,u.name FROM coordinator_plans c JOIN users u ON u.id=c.user_id '+('' if user['role']=='faculty' else 'WHERE c.user_id=? ')+'ORDER BY created DESC LIMIT 100',() if user['role']=='faculty' else (user['id'],)).fetchall()
   handler.send(200,{'plans':[dict(r)|{'data':json.loads(r['data'])} for r in rows],'geminiConfigured':gemini_provider.configured()});return True
  if data is None or user['role']!='student':raise PermissionError('Student planning request required')
  goal=data.get('goal','');focus=data.get('focus','')
  if not isinstance(goal,str) or not isinstance(focus,str) or len(goal)>1500 or len(focus)>500:raise ValueError('Keep your goal within 1,500 characters and focus within 500')
  with connect() as db:
   row=db.execute('SELECT data FROM profiles WHERE user_id=?',(user['id'],)).fetchone();profile=json.loads(row['data']) if row else {}
  plan=build(profile,goal,data.get('hours'),focus)
  if plan['status']=='ready' and data.get('aiConsent') is True:
   evidence=Gateway(user,connect).call('student_evidence',{'student':user['id']})
   match=compare(evidence['resume']['text'],profile.get('jobDescription',''))
   role_gaps=analyse(evidence['resume']['text'],profile['target'],evidence['resume']['digest'])['gaps']
   gaps=list(dict.fromkeys(match.get('missing',[])+role_gaps))
   for attempt in evidence['attempts']:
    for topic,counts in json.loads(attempt['result']).get('topics',{}).items():
     if counts['correct']<counts['total'] and topic not in gaps:gaps.append(topic)
   if not gaps:gaps=['Project explanation and advanced role practice']
   tasks=[{'skill':skill,'week':i+1} for i,skill in enumerate(gaps)]
   activities=ai_generation.activities({'tasks':tasks,'hours':plan['hours'],'goal':goal,'resume':evidence['resume']['text'][:12000],'jd':profile.get('jobDescription','')[:6000],'assessments':evidence['attempts'],'coding':Gateway(user,connect).call('coding_profiles',{'student':user['id']})})
   plan['activities']=[dict(task,task=text) for task,text in zip(tasks,activities)]
   plan['aiConsent']=True
   advice=gemini_provider.plan_preparation({'goal':goal,'hours':plan['hours'],'focus':focus,'target':plan['target'],'skills':plan['benchmarkSkills']})
   plan['rationale']=advice['rationale'];plan['weeklyAdvice']=advice['weeklyAdvice'];plan['planner']='Gemini coordinator with enforced tool and review policy'
  with connect() as db:
   db.execute('BEGIN IMMEDIATE')
   latest=db.execute('SELECT data FROM profiles WHERE user_id=?',(user['id'],)).fetchone()
   if (json.loads(latest['data']) if latest else {})!=profile:raise ValueError('Profile changed while planning. Please retry.')
   version=db.execute('SELECT COALESCE(MAX(version),0)+1 FROM coordinator_plans WHERE user_id=?',(user['id'],)).fetchone()[0]
   ident=db.execute('INSERT INTO coordinator_plans(user_id,version,data,created) VALUES(?,?,?,?)',(user['id'],version,json.dumps(plan),time.time())).lastrowid
   db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],'coordinator_plan:'+str(ident),time.time()))
  handler.send(200,{'id':ident,'version':version,'data':plan})
 except PermissionError as error:handler.send(403,{'error':str(error)})
 except (ValueError,TypeError) as error:handler.send(400,{'error':str(error)})
 return True
