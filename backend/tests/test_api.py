import http.cookiejar,json,threading,tempfile,unittest,urllib.request,urllib.error
from pathlib import Path
import server
class ApiTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=server.DB;server.DB=Path(self.tmp.name)/'test.db';server.initialize()
  server.create_user('TEST001','Test Student','student','test-password-long')
  self.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=self.http.serve_forever,daemon=True).start()
  self.base='http://127.0.0.1:'+str(self.http.server_port)
  self.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 def tearDown(self):
  self.http.shutdown();self.http.server_close();server.DB=self.old;self.tmp.cleanup()
 def request(self,path,data=None):
  req=urllib.request.Request(self.base+'/api/'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
  with self.client.open(req) as r:return json.load(r)
 def test_login_save_logout(self):
  self.request('login',{'usn':'TEST001','password':'test-password-long'})
  self.assertEqual(self.request('me')['id'],'TEST001')
  profile=dict(branch='CSE',graduation='2027',cgpa='8.5',leetcode='',target='Backend Developer',resumeConsent=False,codingConsent=False,academicConsent=True)
  self.request('profile',profile);self.assertEqual(self.request('profile')['cgpa'],'8.5')
  with self.assertRaises(urllib.error.HTTPError) as error:self.request('submissions')
  self.assertEqual(error.exception.code,403)
  self.request('logout',{})
  with self.assertRaises(urllib.error.HTTPError):self.request('me')
 def test_missing_academic_consent_rejected(self):
  self.request('login',{'usn':'TEST001','password':'test-password-long'})
  with self.assertRaises(urllib.error.HTTPError) as error:self.request('profile',dict(branch='CSE',graduation='',cgpa='',leetcode='',target='',resumeConsent=False,codingConsent=False,academicConsent=False))
  self.assertEqual(error.exception.code,400)

 def test_setup_and_student_creation(self):
  account=dict(id='OFFICER01',name='Placement Officer',password='officer-test-password')
  self.assertTrue(self.request('setup-status')['required'])
  self.request('setup',account)
  self.assertFalse(self.request('setup-status')['required'])
  with self.assertRaises(urllib.error.HTTPError) as error:self.request('setup',account)
  self.assertEqual(error.exception.code,409)
  with self.assertRaises(urllib.error.HTTPError) as error:self.request('students',dict(id='NEW001',name='New Student',password='student-test-password'))
  self.assertEqual(error.exception.code,403)
  self.request('login',dict(usn=account['id'],password=account['password']))
  self.request('students',dict(id='NEW001',name='New Student',password='student-test-password',role='faculty'))
  self.request('logout',{})
  self.request('login',dict(usn='NEW001',password='student-test-password'))
  self.assertEqual(self.request('me')['role'],'student')

 def test_student_self_registration_cannot_select_faculty_role(self):
  self.request('register',dict(id='SELF001',name='Self Registered',password='self-registration-pass',role='faculty'))
  self.request('login',dict(usn='SELF001',password='self-registration-pass'))
  self.assertEqual(self.request('me')['role'],'student')
  with self.assertRaises(urllib.error.HTTPError) as error:self.request('submissions')
  self.assertEqual(error.exception.code,403)
  with self.assertRaises(urllib.error.HTTPError) as error:self.request('register',dict(id='SELF001',name='Duplicate',password='duplicate-password'))
  self.assertEqual(error.exception.code,409)

 def test_resume_to_approved_report(self):
  import base64
  self.request('login',dict(usn='TEST001',password='test-password-long'))
  upload=dict(filename='resume.txt',content=base64.b64encode(b'Projects: Python REST API and SQL database with Git version control.').decode())
  with self.assertRaises(urllib.error.HTTPError) as error:self.request('resume',upload)
  self.assertEqual(error.exception.code,403)
  profile=dict(branch='',graduation='',cgpa='',leetcode='',target='Backend Developer',resumeConsent=True,codingConsent=False,academicConsent=False)
  self.request('profile',profile);self.request('resume',upload)
  run=self.request('analyse',{})
  self.assertNotIn('report',self.request('analyses')[0])
  with self.assertRaises(urllib.error.HTTPError) as error:self.request('review',dict(id=run['id'],decision='approved',note=''))
  self.assertEqual(error.exception.code,403)
  self.request('logout',{})
  self.request('setup',dict(id='OFFICER02',name='Reviewer',password='reviewer-password-long'))
  self.request('login',dict(usn='OFFICER02',password='reviewer-password-long'))
  report=self.request('analyses')[0]['report']
  self.assertIn('Testing',report['gaps'])
  self.assertTrue(report['evidence'])
  self.request('review',dict(id=run['id'],decision='approved',note='Sample benchmark reviewed for practice.'))
  with self.assertRaises(urllib.error.HTTPError):self.request('review',dict(id=run['id'],decision='approved',note=''))
  self.request('logout',{});self.request('login',dict(usn='TEST001',password='test-password-long'))
  self.assertEqual(self.request('analyses')[0]['status'],'approved')
  self.assertIn('report',self.request('analyses')[0])
  profile['resumeConsent']=False;self.request('profile',profile)
  self.assertEqual(self.request('analyses'),[])
  self.request('logout',{})
  self.request('register',dict(id='OTHER01',name='Other Student',password='another-password-long'))
  self.request('login',dict(usn='OTHER01',password='another-password-long'))
  self.assertEqual(self.request('analyses'),[])

 def test_optional_github_and_consent(self):
  from unittest.mock import patch
  self.request('login',dict(usn='TEST001',password='test-password-long'))
  profile=dict(branch='',graduation='',cgpa='',leetcode='',github='https://github.com/octocat',target='Backend Developer',resumeConsent=True,codingConsent=False,academicConsent=False,githubConsent=False)
  with self.assertRaises(urllib.error.HTTPError):self.request('profile',profile)
  profile['githubConsent']=True;self.request('profile',profile)
  self.assertEqual(self.request('profile')['github'],'octocat')
  with patch('profile_connectors.github',return_value={'status':'ok','username':'octocat','projects':[]}):
   self.assertEqual(self.request('connections',{})['github']['status'],'ok')
  profile['github']='';profile['githubConsent']=False;self.request('profile',profile)
  self.assertEqual(self.request('connections'),{})

 def test_job_description_round_trip_and_resume_comparison(self):
  import base64
  self.request('login',dict(usn='TEST001',password='test-password-long'))
  profile=dict(branch='',graduation='',cgpa='',leetcode='',target='Backend Developer',resumeConsent=True,codingConsent=False,academicConsent=False,jobDescription='Required: Python, SQL and Docker.')
  self.request('profile',profile)
  self.assertEqual(self.request('profile')['jobDescription'],profile['jobDescription'])
  self.request('resume',dict(filename='jd-resume.txt',content=base64.b64encode(b'Skills\nPython, SQL\nProjects\nData Portal\nBuilt a Python and SQL application.').decode()))
  r=self.request('resume')['jdMatch']
  self.assertEqual(r['coverage'],67)
  self.assertEqual(r['missing'],['Docker'])
  self.request('analyse',{})
  self.request('logout',{})
  self.request('setup',dict(id='JDREVIEW',name='JD Reviewer',password='review-password-long'))
  self.request('login',dict(usn='JDREVIEW',password='review-password-long'))
  report=self.request('analyses')[0]['report']
  self.assertEqual(report['jdMatch']['coverage'],67)
  self.assertIn('Docker',[task['skill'] for task in report['roadmap']])
  self.assertTrue(report['validation']['gap_coverage'])
