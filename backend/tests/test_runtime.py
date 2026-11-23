import json,time,unittest,urllib.error,threading
from unittest.mock import patch
import test_api,server,runtime_service,agent_pipeline
from tool_gateway import Gateway

class RuntimeTests(unittest.TestCase):
 setUp=test_api.ApiTests.setUp
 tearDown=test_api.ApiTests.tearDown
 request=test_api.ApiTests.request
 def seed(self,student='TEST001'):
  with server.connect() as db:
   db.execute('INSERT OR REPLACE INTO profiles VALUES(?,?)',(student,json.dumps({'target':'Backend Developer','resumeConsent':True})))
   db.execute('INSERT OR REPLACE INTO resumes VALUES(?,?,?,?,?)',(student,'r.txt','Skills\nPython SQL\nProjects\nPortal\nBuilt a Python API.','a'*64,time.time()))
 def login(self):self.request('login',{'usn':'TEST001','password':'test-password-long'})
 def test_checkpoint_resume_and_idempotent_publication(self):
  self.seed();self.login()
  with patch('profile_connectors.collect',side_effect=ValueError('Injected connector failure')):
   with self.assertRaises(urllib.error.HTTPError):self.request('analyse',{'requestId':'retry-example'})
  run=self.request('runs')[0];self.assertEqual(run['status'],'failed')
  self.assertIn('Resume and JD specialist',[s['name'] for s in run['stages'] if s['status']=='complete'])
  with patch('runtime_service.analyse',side_effect=AssertionError('Completed skill stage must be reused')),patch('profile_connectors.collect',return_value={}):
   result=self.request('runs/retry',{'id':run['id']})
  duplicate=self.request('analyse',{'requestId':'retry-example'})
  self.assertEqual(result['id'],duplicate['id'])
  with server.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM analyses').fetchone()[0],1)
 def test_changed_evidence_cannot_resume(self):
  self.seed();actor={'id':'TEST001','role':'student'};ident=runtime_service.start(actor,'TEST001',server.connect)
  with server.connect() as db:db.execute("UPDATE resumes SET digest='changed' WHERE user_id='TEST001'")
  with self.assertRaisesRegex(ValueError,'Evidence changed'):runtime_service.execute(actor,ident,server.connect)
 def test_targeted_repair_invalidates_only_dependent_stages(self):
  self.seed();actor={'id':'TEST001','role':'student'};ident=runtime_service.start(actor,'TEST001',server.connect)
  original=agent_pipeline.validate;calls=[]
  def validate(report,digest):
   calls.append(1);result=original(report,digest)
   if len(calls)==1:result['gap_coverage']=False
   return result
  with patch('agent_pipeline.validate',side_effect=validate),patch('profile_connectors.collect',return_value={}) as connector:
   result=runtime_service.execute(actor,ident,server.connect)
   self.assertEqual(connector.call_count,1)
  self.assertEqual(len(calls),2)
  with server.connect() as db:self.assertEqual(db.execute("SELECT count(*) FROM audit WHERE action LIKE 'targeted_repair:%'").fetchone()[0],1)
 def test_mcp_schema_memory_scope_and_consent(self):
  self.seed();self.login()
  listing=self.request('mcp',{'jsonrpc':'2.0','id':1,'method':'tools/list'})
  self.assertEqual(len(listing['result']['tools']),3)
  with server.connect() as db:
   for owner,status in [('TEST001','approved'),('TEST001','pending'),('OTHER','approved')]:
    db.execute('INSERT INTO analyses(user_id,status,data,created) VALUES(?,?,?,?)',(owner,status,json.dumps({'target':'Backend Developer','gaps':['SQL'],'coverage':50}),time.time()))
  matches=self.request('memory',{'query':'SQL'})['matches'];self.assertEqual(len(matches),1)
  denied=self.request('mcp',{'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'approved_memory','arguments':{'student':'OTHER','query':'SQL'}}})
  self.assertTrue(denied['result']['isError'])
  with server.connect() as db:db.execute("UPDATE profiles SET data='{}' WHERE user_id='TEST001'")
  with self.assertRaises(urllib.error.HTTPError):self.request('memory',{'query':'SQL'})
 def test_swarm_matches_single_run_quality_and_bounds_workers(self):
  self.seed();self.seed('SECOND')
  actor={'id':'OFFICER','role':'faculty'};batch='testbatch'
  with server.connect() as db:db.execute('INSERT INTO agent_batches VALUES(?,?,?,?,?,?)',(batch,'OFFICER','["TEST001","SECOND"]','running','[]',time.time()))
  with patch('profile_connectors.collect',return_value={}):runtime_service.batch_worker(actor,batch,['TEST001','SECOND'],server.connect)
  with server.connect() as db:
   result=json.loads(db.execute('SELECT results FROM agent_batches WHERE id=?',(batch,)).fetchone()[0])
   reports=[json.loads(r[0]) for r in db.execute('SELECT data FROM analyses ORDER BY id')]
  self.assertTrue(all(r['ok'] for r in result));self.assertEqual(len(reports),2)
  self.assertEqual(reports[0]['coverage'],reports[1]['coverage']);self.assertEqual(reports[0]['roadmap'],reports[1]['roadmap'])

