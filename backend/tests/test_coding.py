import json,time,unittest,urllib.error
from unittest.mock import patch
import test_api,server,coding_service

class CodingTests(unittest.TestCase):
 request=test_api.ApiTests.request
 tearDown=test_api.ApiTests.tearDown
 def setUp(self):
  test_api.ApiTests.setUp(self)
  ready=patch('coding_runner.status',return_value={'ready':True,'message':'Test runner'});ready.start();self.addCleanup(ready.stop)
  self.request('login',{'usn':'TEST001','password':'test-password-long'})
 def test_hidden_tests_not_exposed_and_officer_can_review(self):
  attempt=self.request('coding/start',{'problem':'even_sum'})
  self.assertEqual(len(attempt['problemDetail']['samples']),1)
  self.assertNotIn('cases',attempt['problemDetail'])
  result={'passed':3,'total':5,'percentage':60,'cases':[{'passed':True,'status':'passed','hidden':False}],'method':'Mock executor'}
  with patch('coding_runner.grade',return_value=result) as grade:
   submitted=self.request('coding/submit',{'id':attempt['id'],'code':'print(0)'})
   self.assertEqual(len(grade.call_args.args[1]),5)
  self.assertEqual(submitted['status'],'submitted')
  with patch('coding_runner.grade',side_effect=AssertionError('Duplicate execution')):
   self.assertEqual(self.request('coding/submit',{'id':attempt['id'],'code':'print(9)'})['result'],result)
  server.create_user('OFFICER','Officer','faculty','officer-password-long');self.request('logout',{})
  self.request('login',{'usn':'OFFICER','password':'officer-password-long'})
  self.assertEqual(self.request('coding/open',{'id':attempt['id']})['code'],'print(0)')
  with self.assertRaises(urllib.error.HTTPError):self.request('coding/save',{'id':attempt['id'],'code':'changed'})
 def test_failure_keeps_code_and_expiry_blocks_submit(self):
  attempt=self.request('coding/start',{'problem':'unique'})
  with patch('coding_runner.grade',side_effect=ValueError('Docker stopped')):
   with self.assertRaises(urllib.error.HTTPError):self.request('coding/run',{'id':attempt['id'],'code':'print(None)'})
  opened=self.request('coding/open',{'id':attempt['id']});self.assertEqual(opened['code'],'print(None)');self.assertIsNone(opened['result'])
  with server.connect() as db:db.execute('UPDATE coding_attempts SET deadline=? WHERE id=?',(time.time()-1,attempt['id']))
  with self.assertRaises(urllib.error.HTTPError):self.request('coding/submit',{'id':attempt['id'],'code':'print(0)'})
 def test_student_cannot_access_other_attempt(self):
  attempt=self.request('coding/start',{'problem':'palindrome'})
  self.request('logout',{});self.request('register',{'id':'SECOND','name':'Second','password':'second-password-long'})
  self.request('login',{'usn':'SECOND','password':'second-password-long'})
  with self.assertRaises(urllib.error.HTTPError):self.request('coding/open',{'id':attempt['id']})
  self.assertEqual(self.request('coding')['attempts'],[])
 def test_sample_uses_only_visible_cases(self):
  attempt=self.request('coding/start',{'problem':'even_sum'})
  with patch('coding_runner.grade',return_value={'passed':1,'total':1,'percentage':100,'cases':[]}) as grade:
   self.request('coding/run',{'id':attempt['id'],'code':'print(6)'})
   self.assertEqual(len(grade.call_args.args[1]),1)

class RunnerPrivacyTests(unittest.TestCase):
 def test_hidden_output_and_errors_are_not_returned(self):
  import coding_runner
  with patch('coding_runner.status',return_value={'ready':True}),patch('coding_runner.run_case',return_value={'status':'runtime_error','detail':'sensitive hidden input'}):
   result=coding_runner.grade('code',[{'input':[],'expected':0},{'input':['secret'],'expected':0,'hidden':True}])
  self.assertIn('detail',result['cases'][0]);self.assertNotIn('detail',result['cases'][1])
