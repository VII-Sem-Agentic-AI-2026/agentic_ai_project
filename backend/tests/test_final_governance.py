import unittest,json,time,urllib.error,base64
from unittest.mock import patch
import test_api,server
from coordinator_service import build

class FinalGovernanceTests(unittest.TestCase):
 setUp=test_api.ApiTests.setUp
 tearDown=test_api.ApiTests.tearDown
 request=test_api.ApiTests.request
 def seed(self):
  self.request('login',{'usn':'TEST001','password':'test-password-long'})
  self.request('profile',{'branch':'','graduation':'','cgpa':'','target':'Backend Developer','resumeConsent':True,'codingConsent':False,'academicConsent':False,'githubConsent':False,'leetcode':'','github':''})
  self.request('resume',{'filename':'r.txt','content':base64.b64encode(b'Skills\nPython SQL\nProjects\nPortal\nBuilt and tested an API.').decode()})
 def officer(self):
  server.create_user('OFFICER','Officer','faculty','officer-password-long')
  self.request('logout',{});self.request('login',{'usn':'OFFICER','password':'officer-password-long'})
 def test_clarify_revise_and_apply_plan(self):
  self.seed()
  vague=self.request('coordinator/plan',{'goal':'Help','hours':10,'focus':''})
  self.assertGreaterEqual(len(vague['data']['questions']),2)
  with self.assertRaises(urllib.error.HTTPError):self.request('analyse',{})
  ready=self.request('coordinator/plan',{'goal':'Prepare for backend engineering interviews','hours':8,'focus':'SQL and API design'})
  self.assertEqual(ready['version'],2);self.assertEqual(ready['data']['status'],'ready')
  report=self.request('analyse',{})
  with server.connect() as db:data=json.loads(db.execute('SELECT data FROM analyses WHERE id=?',(report['id'],)).fetchone()[0])
  self.assertEqual(data['coordinator']['id'],ready['id'])
  self.assertEqual(self.request('consent-history')[0]['consent']['resumeConsent'],True)
 def test_revision_approval_and_rollback_are_persistent(self):
  self.seed();original=self.request('analyse',{})['id']
  with self.assertRaises(urllib.error.HTTPError):self.request('governance',{})
  self.officer();self.request('review',{'id':original,'decision':'approved','note':'Reviewed against the practice benchmark.'})
  report=self.request('analyses')[0]['report']
  revised=self.request('governance/revise',{'id':original,'tasks':['Complete a tested exercise in '+t['skill'] for t in report['roadmap']],'note':'Add practical test evidence to each activity.'})['id']
  self.assertNotEqual(original,revised)
  self.request('review',{'id':revised,'decision':'approved','note':'Revised exercises reviewed.'})
  self.request('governance/rollback',{'id':original,'note':'Restore the original approved preparation schedule.'})
  rows=self.request('analyses');self.assertEqual([r['id'] for r in rows if r['isCurrent']],[original])
  plans=self.request('progress');self.assertEqual(plans[0]['id'],original);self.assertTrue(plans[0]['isCurrent'])
  old=next(r for r in rows if r['id']==original)['report'];self.assertEqual(old['roadmap'],report['roadmap'])
  self.assertTrue(self.request('governance')['events'])
 def test_reviewed_benchmark_used_and_expiry_blocks_approval(self):
  self.seed();self.officer()
  self.request('benchmarks',{'role':'Backend Developer','skills':['Python','SQL','Docker'],'source':'College placement review of backend role requirements','days':30})
  self.request('logout',{});self.request('login',{'usn':'TEST001','password':'test-password-long'})
  ident=self.request('analyse',{})['id']
  with server.connect() as db:
   report=json.loads(db.execute('SELECT data FROM analyses WHERE id=?',(ident,)).fetchone()[0]);self.assertEqual(report['benchmark']['requirements'],['Python','SQL','Docker'])
   report['benchmark']['expires']=time.time()-1;db.execute('UPDATE analyses SET data=? WHERE id=?',(json.dumps(report),ident))
  self.request('logout',{});self.request('login',{'usn':'OFFICER','password':'officer-password-long'})
  with self.assertRaises(urllib.error.HTTPError):self.request('review',{'id':ident,'decision':'approved','note':'Review expired report'})
 def test_gemini_planner_validated_advice_is_versioned(self):
  self.seed()
  with patch('ai_generation.activities',side_effect=lambda context: ['Build and test an exercise in '+t['skill'] for t in context['tasks']]), patch('gemini_provider.plan_preparation',return_value={'rationale':'Prioritise SQL and API tests.','weeklyAdvice':'Practise queries and explain your project.'}) as provider:
   plan=self.request('coordinator/plan',{'goal':'Prepare for backend interviews with practical exercises','hours':6,'focus':'SQL','aiConsent':True})
  self.assertEqual(provider.call_count,1);self.assertIn('Gemini',plan['data']['planner'])

