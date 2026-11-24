"""Offline teaching helpers for Worklet 9, not a second production backend.

Production functions are imported where possible. Notebook-only models explicitly
demonstrate contracts (vector retrieval, source substitution and spec-derived tests).
All student records below are synthetic; no portal database or Gemini key is read.
"""
from pathlib import Path
import copy,hashlib,io,json,math,re,sqlite3,sys,time,unittest
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend'/'tests')]
from analysis_service import analyse,BENCHMARKS
from coordinator_service import build
import agent_pipeline

STUDENTS={
 'DEMO001':{'target':'Backend Developer','resumeConsent':True,'jobDescription':'Python SQL REST APIs Git Testing','text':'Skills\nPython, SQL\nProjects\nLibrary API\nBuilt a Python application with SQL queries.'},
 'DEMO002':{'target':'Data Analyst','resumeConsent':True,'jobDescription':'SQL Python Statistics Excel Visualization','text':'Skills\nSQL, Excel\nProjects\nSales Dashboard\nBuilt spreadsheet charts and SQL reports.'}}

def clone(value):return copy.deepcopy(value)
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def report(student='DEMO001'):
 p=clone(STUDENTS[student]);text=p.pop('text')
 return agent_pipeline.run({'text':text,'digest':digest(text)},p,[],None,analyse,coding_reader=lambda:{})
def show(value):print(json.dumps(value,indent=2,ensure_ascii=True))
def expect(error,fn):
 try:fn()
 except error as exc:print('Expected refusal:',str(exc));return
 raise AssertionError('Expected '+error.__name__)

def regressions(*names):
 """Execute actual portal tests on disposable fixtures, never the live database."""
 from unittest.mock import patch
 with patch('gemini_provider.load_portal_credentials'),patch('gemini_provider.load_environment'):
  suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
 stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=1).run(suite)
 print(stream.getvalue())
 assert result.wasSuccessful(), 'Portal regression failed'
 return {'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)}

def coverage(found,required):
 if not isinstance(found,list) or not isinstance(required,list) or not required or any(not isinstance(x,str) for x in found+required):raise ValueError('Nonempty typed skill lists required')
 return round(100*len(set(found)&set(required))/len(set(required)))

class Skill:
 def __init__(self,name,required,fn):self.name,self.required,self.fn=name,required,fn
 def __call__(self,**payload):
  if set(payload)!=set(self.required) or any(not isinstance(payload[k],t) for k,t in self.required.items()):raise ValueError('Skill contract mismatch: '+self.name)
  return self.fn(**payload)

def retrieve(archive,student,query,tag=None):
 """Notebook TF-IDF cosine vectors, not a neural embedding provider."""
 rows=[r for r in archive if r['student']==student and r['status']=='approved' and (tag is None or tag in r['tags'])]
 tokens=lambda text:re.findall(r'\w+',text.lower())
 docs=[tokens(r['text']) for r in rows];q=tokens(query);vocabulary=set(q).union(*(set(d) for d in docs))
 idf={w:math.log((1+len(docs))/(1+sum(w in d for d in docs)))+1 for w in vocabulary}
 def vector(words):return {w:words.count(w)*idf[w] for w in vocabulary}
 def cosine(a,b):
  return sum(a[w]*b[w] for w in vocabulary)/max(1e-12,math.sqrt(sum(x*x for x in a.values())*sum(x*x for x in b.values())))
 return sorted([dict(r,similarity=round(cosine(vector(d),vector(q)),4)) for r,d in zip(rows,docs)],key=lambda r:r['similarity'],reverse=True)

class Connector:
 """Notebook source-substitution contract, complementary to the portal gateway."""
 def __init__(self,reader):self.reader=reader;self.audit=[]
 def call(self,actor,student,consent=True):
  if actor!=student or consent is not True:raise PermissionError('Owner and active consent required')
  value=self.reader(student)
  if not isinstance(value,dict) or not isinstance(value.get('skills'),list):raise ValueError('Invalid source schema')
  self.audit.append({'tool':'profile','student':student,'resultDigest':digest(json.dumps(value,sort_keys=True))})
  return clone(value)

class Runtime:
 """Small persisted teaching runtime with dependency, budget and approval gates."""
 def __init__(self,path,budget=6):
  self.path=Path(path);self.budget=budget
  self.state=json.loads(self.path.read_text()) if self.path.exists() else {'outputs':{},'audit':[],'attempts':0}
 def save(self):self.path.write_text(json.dumps(self.state),encoding='utf-8')
 def perform(self,name,dependencies,fn,officer=False,human_gate=False):
  if name in self.state['outputs']:return clone(self.state['outputs'][name])
  if not set(dependencies)<=set(self.state['outputs']):raise ValueError('Dependency not complete')
  if human_gate and not officer:raise PermissionError('Named officer approval required')
  if self.state['attempts']>=self.budget:raise ValueError('Action budget exhausted')
  self.state['attempts']+=1
  try:
   value=fn();self.state['outputs'][name]=clone(value)
   self.state['audit'].append({'stage':name,'status':'complete','dependencies':dependencies,'output':value})
   return value
  except Exception as exc:
   self.state['audit'].append({'stage':name,'status':'failed','error':str(exc)});raise
  finally:self.save()

def swarm(students,worker,retries=2):
 def bounded(student):
  for attempt in range(1,retries+1):
   try:return {'student':student,'ok':True,'attempts':attempt,'report':worker(student)}
   except ValueError as exc:error=str(exc)
  return {'student':student,'ok':False,'attempts':retries,'error':error}
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(bounded,dict.fromkeys(students)))
 return {'results':results,'coverage':sum(r['ok'] for r in results)/len(results),'missing':[r['student'] for r in results if not r['ok']]}

def merge_versions(candidates):
 """Reconcile by student identity; prefer higher reviewed version, not a sum."""
 merged={};conflicts=[]
 for r in candidates:
  key=r['student']
  if key in merged:
   conflicts.append(key)
   if r['version']<=merged[key]['version']:continue
  merged[key]=r
 return list(merged.values()),sorted(set(conflicts))

def ground(claim,sources,student):
 source=sources.get(claim.get('source'))
 if not source or source['student']!=student or not source['consent']:raise ValueError('Missing, private or revoked source')
 if claim.get('locator') not in source['values'] or source['values'][claim['locator']]!=claim.get('value'):raise ValueError('Claim does not match located evidence')
 return dict(claim,grounded=True)

def repair(candidate,baseline,budget=1):
 value=clone(candidate);log=[]
 for attempt in range(budget+1):
  failures=[]
  for i,row in enumerate(value['evidence']):
   match=next((e for e in baseline['evidence'] if e['skill']==row['skill']),None)
   if not match or row!=match:failures.append((i,match))
  if not failures:return value,log
  if attempt==budget:raise ValueError('Repair budget exhausted; escalate to placement officer')
  for i,match in failures:
   if match:value['evidence'][i]=clone(match)
   log.append({'row':i,'diagnosis':'Evidence mismatch','action':'Restore from approved input' if match else 'Cannot fabricate unknown skill'})

def acceptance(artifact,spec):
 checks={f'section:{s}':s in artifact for s in spec['sections']}
 tasks={t['skill'] for t in artifact.get('roadmap',[])}
 checks.update({f'gap:{g}':g in tasks for g in spec['gaps']})
 checks['target']=artifact.get('target')==spec['target']
 return checks

def gate(artifact,spec):
 checks=acceptance(artifact,spec)
 if not all(checks.values()):raise ValueError('Acceptance blocked: '+', '.join(k for k,v in checks.items() if not v))
 return {'status':'pending_officer_review','checks':checks}

class Governance:
 def __init__(self):self.versions=[];self.current=None;self.audit=[]
 def publish(self,actor,artifact,spec):
  if actor!='officer':self.audit.append('denied:'+actor);raise PermissionError('Officer role required')
  gate(artifact,spec)
  self.versions.append(clone(artifact));self.current=len(self.versions);self.audit.append('published:'+str(self.current))
  return self.current
 def view(self,actor,owner):
  if actor not in ('officer',owner):raise PermissionError('Student report is private')
  if self.current is None:raise ValueError('No published report')
  return clone(self.versions[self.current-1])
 def rollback(self,actor,version):
  if actor!='officer':raise PermissionError('Officer role required')
  if type(version) is not int or not 1<=version<=len(self.versions):raise ValueError('Unknown version')
  self.current=version;self.audit.append('rollback:'+str(version))

def specialist(role,text):
 if role not in BENCHMARKS:raise ValueError('Unknown role pack')
 r=analyse(text,role,digest(text))
 assert set(r['found'])|set(r['gaps'])==set(BENCHMARKS[role])
 assert all(t['skill'] in BENCHMARKS[role] for t in r['roadmap'])
 return r
