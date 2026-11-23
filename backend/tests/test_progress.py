import json,time,unittest,urllib.error
import test_api,server

class ProgressTests(unittest.TestCase):
 request=test_api.ApiTests.request
 setUp=test_api.ApiTests.setUp
 tearDown=test_api.ApiTests.tearDown
 def plan(self,status='approved',owner='TEST001'):
  with server.connect() as db:
   db.execute('INSERT OR REPLACE INTO profiles(user_id,data) VALUES(?,?)',(owner,json.dumps({'resumeConsent':True})))
   return db.execute('INSERT INTO analyses(user_id,status,data,created) VALUES(?,?,?,?)',
    (owner,status,json.dumps({'target':'Backend Developer','roadmap':[{'week':1,'skill':'SQL','task':'Build and test a query','reason':'JD requirement'}]}),time.time())).lastrowid
 def login(self):self.request('login',{'usn':'TEST001','password':'test-password-long'})
 def test_revoked_consent_blocks_tracker_read_and_update(self):
  ident=self.plan();self.login()
  with server.connect() as db:db.execute('UPDATE profiles SET data=? WHERE user_id=?',(json.dumps({'resumeConsent':False}),'TEST001'))
  self.assertEqual(self.request('progress'),[])
  with self.assertRaises(urllib.error.HTTPError) as error:self.request('progress/update',{'id':ident,'index':0,'status':'in_progress'})
  self.assertEqual(error.exception.code,403)
 def test_persisted_progress_and_officer_read_only(self):
  ident=self.plan();self.login()
  self.assertEqual(self.request('progress')[0]['completed'],0)
  self.request('progress/update',{'id':ident,'index':0,'status':'completed','note':'Built join queries and checked null cases.'})
  self.request('logout',{});self.login()
  plan=self.request('progress')[0];self.assertEqual(plan['completed'],1)
  self.assertIn('null cases',plan['tasks'][0]['note'])
  server.create_user('OFFICER','Officer','faculty','officer-password-long')
  self.request('logout',{});self.request('login',{'usn':'OFFICER','password':'officer-password-long'})
  self.assertEqual(self.request('progress')[0]['completed'],1)
  with self.assertRaises(urllib.error.HTTPError) as error:self.request('progress/update',{'id':ident,'index':0,'status':'not_started'})
  self.assertEqual(error.exception.code,403)
 def test_unapproved_and_other_student_plans_are_private(self):
  pending=self.plan('pending');self.login()
  self.assertEqual(self.request('progress'),[])
  with self.assertRaises(urllib.error.HTTPError):self.request('progress/update',{'id':pending,'index':0,'status':'in_progress'})
  approved=self.plan()
  server.create_user('SECOND','Second','student','second-password-long')
  self.request('logout',{});self.request('login',{'usn':'SECOND','password':'second-password-long'})
  self.assertEqual(self.request('progress'),[])
  with self.assertRaises(urllib.error.HTTPError):self.request('progress/update',{'id':approved,'index':0,'status':'in_progress'})
 def test_validation_and_report_is_unchanged(self):
  ident=self.plan();self.login()
  with server.connect() as db:before=db.execute('SELECT data FROM analyses WHERE id=?',(ident,)).fetchone()['data']
  for update in ({'status':'completed','note':''},{'status':'invalid'},{'index':10},{'index':True}):
   with self.assertRaises(urllib.error.HTTPError):self.request('progress/update',{'id':ident,'index':0,'status':'in_progress',**update})
  self.request('progress/update',{'id':ident,'index':0,'status':'in_progress','note':'Working through SQL exercises.'})
  with server.connect() as db:
   self.assertEqual(db.execute('SELECT data FROM analyses WHERE id=?',(ident,)).fetchone()['data'],before)
   self.assertEqual(db.execute("SELECT count(*) FROM audit WHERE action LIKE 'roadmap_progress:%'").fetchone()[0],1)
