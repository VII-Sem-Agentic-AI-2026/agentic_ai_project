"""Bounded deterministic specialist graph. No LLM autonomy is claimed here."""
import json,time,threading,uuid
from concurrent.futures import ThreadPoolExecutor
from resume_structure import structure
from jd_matching import compare
import profile_connectors,ai_generation
CAPACITY=threading.BoundedSemaphore(2)
class AcceptanceFailure(ValueError):
 def __init__(self,checks):self.checks=checks;super().__init__('Report failed acceptance validation; no report published')

def validate(report,digest):
 allowed=set(report['gaps'])|set(report['jdMatch'].get('missing',[]))
 for attempt in report['practice']:
  allowed.update(k for k,v in attempt['topics'].items() if v['correct']<v['total'])
 tasks={t['skill'] for t in report['roadmap']}
 return {'gap_coverage':allowed<=tasks,'task_grounding':tasks<=allowed,
  'evidence_present':all(e.get('excerpt') and e.get('source')=='resume:'+digest[:12] for e in report['evidence']),
  'coverage_bounds':type(report['coverage']) is int and 0<=report['coverage']<=100,
  'required_sections':all(k in report for k in ('structured','projects','sources','jdMatch','practice'))}

def run(resume,profile,attempts,snapshot,analyse,checkpoint=None,coding_reader=None,plan=None,benchmark=None):
 if not CAPACITY.acquire(blocking=False):raise ValueError('Analysis workers are busy. Please retry shortly.')
 trace=[];lock=threading.Lock();started=time.time();ident=uuid.uuid4().hex
 def stage(name,dependencies,fn):
  begin=time.time()
  try:value=checkpoint(name,dependencies,fn) if checkpoint else fn()
  except Exception as error:
   raise ValueError('Analysis stopped at '+name+'. No report published. '+str(error)) from error
  with lock:trace.append({'stage':name,'status':'complete','dependsOn':dependencies,'started':begin,'durationMs':round((time.time()-begin)*1000)})
  return value
 try:
  if not profile.get('resumeConsent'):raise ValueError('Resume consent required')
  if plan and plan.get('status')=='needs_clarification':raise ValueError('Answer the coordinator questions in Preparation planner and save a revised plan before generating a report.')
  def skills():
   report=analyse(resume['text'],profile.get('target'),resume['digest'],benchmark=benchmark) if benchmark else analyse(resume['text'],profile.get('target'),resume['digest'])
   report['structured']=structure(resume['text'])
   report['jdMatch']=compare(resume['text'],profile.get('jobDescription',''))
   return report
  def coding():
   sources=coding_reader() if coding_reader else json.loads(snapshot['data']) if snapshot and time.time()-snapshot['created']<3600 else profile_connectors.collect(profile)
   for source,consent in [('github','githubConsent'),('leetcode','codingConsent')]:
    if not profile.get(consent):sources[source]={'status':'not_consented','message':'No active consent for this source.'}
    elif sources.get(source,{}).get('username') not in (None,profile.get(source)):
     sources[source]={'status':'stale','message':'Account changed; sync the new account before analysis.'}
   return sources
  coordinator=stage('Coordinator intake',[],lambda:plan if plan and plan.get('status')=='ready' and plan.get('target')==profile.get('target') else {'status':'ready','planner':'Automatic rule coordinator','target':profile.get('target'),'rationale':'Use consented evidence to prepare a validated, officer-reviewed roadmap.'})
  with ThreadPoolExecutor(max_workers=2) as pool:
   a=pool.submit(stage,'Resume and JD specialist',['Coordinator intake'],skills)
   b=pool.submit(stage,'Coding profile specialist',['Coordinator intake'],coding)
   result=a.result();sources=b.result()
  def practice():
   latest={}
   for attempt in attempts:
    if attempt['kind'] not in latest:latest[attempt['kind']]=json.loads(attempt['result'])
   return [{'kind':kind,**{k:v[k] for k in ('correct','total','percentage','topics')}} for kind,v in latest.items()]
  result['practice']=stage('Assessment evidence specialist',['Coordinator intake'],practice)
  def roadmap():
   tasks=result['roadmap'];seen={t['skill'] for t in tasks}
   for skill in result['jdMatch'].get('missing',[]):
    if skill not in seen:
     tasks.append({'week':len(tasks)+1,'skill':skill,'task':f'Learn {skill} and demonstrate it in a project exercise.','reason':'Required by the supplied JD; no matching resume evidence.'});seen.add(skill)
   for attempt in result['practice']:
    for topic,counts in attempt['topics'].items():
     if counts['correct']<counts['total']:
      reason=f'Latest {attempt["kind"]} practice: {counts["correct"]}/{counts["total"]} correct in {topic}.'
      if topic in seen:
       next(t for t in tasks if t['skill']==topic)['reason']+=' '+reason
      else:
       tasks.append({'week':len(tasks)+1,'skill':topic,'task':f'Review {topic}, complete an exercise and explain your solution.','reason':reason});seen.add(topic)
   if plan and plan.get('aiConsent') and tasks:
    generated=ai_generation.activities({'tasks':tasks,'hours':plan['hours'],'goal':plan['goal'],'resume':result['structured'],'jd':profile.get('jobDescription','')[:6000],'coding':sources,'assessments':result['practice']})
    tasks=[dict(task,task=text) for task,text in zip(tasks,generated)]
   return tasks
  result['roadmap']=stage('Preparation planning specialist',['Resume and JD specialist','Assessment evidence specialist'],roadmap)
  result['sources']=sources
  result['projects']=result['structured']['projects']+sources.get('github',{}).get('projects',[])[:20]
  result['limitations']=['Deterministic specialist workflow; not an autonomous LLM agent system.','Resume and project claims are self-reported.','Sample role benchmarks are not verified job openings.','Coding metadata does not prove code quality or authorship.','Academic eligibility and interview performance are not evaluated in this report.']
  result['validation']=stage('Acceptance validator',['Preparation planning specialist','Coding profile specialist'],lambda:validate(result,resume['digest']))
  if not all(result['validation'].values()):raise AcceptanceFailure(result['validation'])
  trace.sort(key=lambda t:t['started'])
  trace.append({'stage':'Placement officer approval','status':'pending','dependsOn':['Acceptance validator']})
  result['coordinator']=coordinator
  if plan and plan.get('aiConsent'):
   result['limitations'][0]='Gemini-generated activities within a fixed, validated specialist workflow; AI suggestions require officer review.'
   result['planningMethod']='Gemini activities with deterministic gap coverage'
  result['trace']=trace
  result['execution']={'id':ident,'version':'specialist-graph-1','started':started,'durationMs':round((time.time()-started)*1000),'parallelWorkers':2,'status':'awaiting_review','kind':'Deterministic tool specialists'}
  return result
 finally:CAPACITY.release()
