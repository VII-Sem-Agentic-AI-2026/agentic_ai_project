import unittest,base64,urllib.error
from pathlib import Path
import test_api,server
from unittest.mock import patch
class MediaTests(unittest.TestCase):
 request=test_api.ApiTests.request
 def setUp(self):
  questions=patch('ai_generation.questions',return_value=['Explain your approach to interview topic '+str(i) for i in range(10)]);questions.start();self.addCleanup(questions.stop)
  configured=patch('gemini_provider.configured',return_value=True);configured.start();self.addCleanup(configured.stop)
  evaluation=patch('gemini_provider.evaluate',return_value=dict(feedback='Saved',improvement='Add detail',followup='How?',relevance=2,clarity=2,depth=2,correctness=2,scorable=True));evaluation.start();self.addCleanup(evaluation.stop)
  test_api.ApiTests.setUp(self);self.original_data=server.DATA;server.DATA=Path(self.tmp.name)
 def tearDown(self):
  server.DATA=self.original_data;test_api.ApiTests.tearDown(self)
 def test_recording_privacy_and_ordered_chunks(self):
  self.request('login',dict(usn='TEST001',password='test-password-long'))
  session=self.request('interviews/start',{'consent':True,'aiConsent':True});ident=session['id']
  with self.assertRaises(urllib.error.HTTPError):self.request('media/start',{'id':ident,'mime':'video/webm'})
  self.request('media/start',{'id':ident,'mime':'video/webm','consent':True})
  packet={'id':ident,'sequence':0,'content':base64.b64encode(b'test-recording-bytes').decode()}
  self.request('media/chunk',packet);self.request('media/chunk',packet)
  info=self.request('media/info?id='+ident);self.assertEqual(info['next_chunk'],1)
  with self.assertRaises(urllib.error.HTTPError):self.request('media/chunk',{**packet,'sequence':3})
  self.request('media/event',{'id':ident,'event':'tab_hidden'})
  self.request('media/event',{'id':ident,'event':'window_blur'})
  import json
  self.assertEqual(len(json.loads(self.request('media/info?id='+ident)['events'])),2)
  self.request('media/finish',{'id':ident})
  with self.client.open(self.base+'/api/media/play?id='+ident) as response:self.assertEqual(response.read(),b'test-recording-bytes')
  self.request('logout',{});self.request('register',dict(id='OTHERVID',name='Another Student',password='another-password-long'));self.request('login',dict(usn='OTHERVID',password='another-password-long'))
  with self.assertRaises(urllib.error.HTTPError) as error:self.request('media/info?id='+ident)
  self.assertEqual(error.exception.code,403)
 def test_no_playback_before_finished(self):
  self.request('login',dict(usn='TEST001',password='test-password-long'))
  ident=self.request('interviews/start',{'consent':True,'aiConsent':True})['id']
  self.request('media/start',{'id':ident,'mime':'video/webm','consent':True})
  with self.assertRaises(urllib.error.HTTPError):self.request('media/finish',{'id':ident})
  with self.assertRaises(urllib.error.HTTPError):self.client.open(self.base+'/api/media/play?id='+ident)

 def test_owner_deletion_removes_bytes_and_blocks_playback(self):
  self.request('login',dict(usn='TEST001',password='test-password-long'))
  ident=self.request('interviews/start',{'consent':True,'aiConsent':True})['id']
  self.request('media/start',{'id':ident,'mime':'video/webm','consent':True})
  self.request('media/chunk',{'id':ident,'sequence':0,'content':base64.b64encode(b'test video').decode()})
  with self.assertRaises(urllib.error.HTTPError):self.request('media/delete',{'id':ident,'confirm':True})
  self.request('interviews/end',{'id':ident});self.request('media/finish',{'id':ident})
  self.request('media/delete',{'id':ident,'confirm':True})
  self.assertFalse((server.DATA/'recordings'/(ident+'.webm')).exists())
  self.assertEqual(self.request('media/info?id='+ident)['status'],'deleted')
  with self.assertRaises(urllib.error.HTTPError):self.client.open(self.base+'/api/media/play?id='+ident)

 def test_invalid_chunk_does_not_prevent_recovery(self):
  self.request('login',dict(usn='TEST001',password='test-password-long'))
  ident=self.request('interviews/start',{'consent':True,'aiConsent':True})['id']
  self.request('media/start',{'id':ident,'mime':'video/webm;codecs=vp8,opus','consent':True})
  with self.assertRaises(urllib.error.HTTPError):self.request('media/chunk',{'id':ident,'sequence':0,'content':'opus;base64'})
  self.assertEqual(self.request('media/info?id='+ident)['next_chunk'],0)
  self.request('media/chunk',{'id':ident,'sequence':0,'content':base64.b64encode(b'valid camera bytes').decode()})
  self.request('interviews/answer',{'id':ident,'index':0,'answer':'[Spoken answer captured in private interview recording; no text transcript supplied.]'})
  self.assertEqual(self.request('interviews/open',{'id':ident})['answered'],1)
  self.request('media/finish',{'id':ident})
  with self.client.open(self.base+'/api/media/play?id='+ident) as response:self.assertEqual(response.read(),b'valid camera bytes')
