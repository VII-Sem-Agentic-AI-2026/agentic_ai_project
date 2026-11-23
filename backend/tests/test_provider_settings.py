import io,json,os,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
import test_api,server,gemini_provider,credential_store

class ProviderSettingsTests(unittest.TestCase):
 request=test_api.ApiTests.request
 def setUp(self):
  test_api.ApiTests.setUp(self)
  self.old_data=server.DATA;server.DATA=Path(self.tmp.name)
  current=patch.object(gemini_provider,'_portal_credentials',None);current.start();self.addCleanup(current.stop)
  env=patch.dict(os.environ,{'GEMINI_API_KEY':'','GEMINI_MODEL':''});env.start();self.addCleanup(env.stop)
  server.create_user('OFFICER','Officer','faculty','officer-password-long')
 def tearDown(self):server.DATA=self.old_data;test_api.ApiTests.tearDown(self)
 def officer(self):self.request('login',{'usn':'OFFICER','password':'officer-password-long'})
 def test_students_cannot_read_or_save_keys(self):
  self.request('login',{'usn':'TEST001','password':'test-password-long'})
  for payload in (None,{'apiKey':'test-key-not-real-123456789'}):
   with self.assertRaises(urllib.error.HTTPError) as error:self.request('interviews/provider',payload)
   self.assertEqual(error.exception.code,403)
  self.assertFalse(self.request('interviews/config')['geminiConfigured'])
 @unittest.skipUnless(os.name=='nt','Windows DPAPI storage')
 def test_encrypted_save_survives_reload_and_enables_students(self):
  self.officer();key='test-key-not-real-123456789'
  with patch('gemini_provider.verify_key') as verify:result=self.request('interviews/provider',{'apiKey':key})
  verify.assert_called_once_with(key)
  self.assertTrue(result['configured']);self.assertNotIn(key,json.dumps(result))
  file=server.DATA/'gemini-credentials.dpapi'
  self.assertNotIn(key.encode(),file.read_bytes())
  gemini_provider._portal_credentials=None;gemini_provider.load_portal_credentials(file)
  self.assertEqual(gemini_provider.credentials(),(key,gemini_provider.DEFAULT_MODEL))
  self.request('logout',{});self.request('login',{'usn':'TEST001','password':'test-password-long'})
  config=self.request('interviews/config');self.assertTrue(config['geminiConfigured']);self.assertNotIn(key,json.dumps(config))
  with server.connect() as db:
   actions=[r['action'] for r in db.execute('SELECT action FROM audit')]
   self.assertIn('gemini_key_verified_and_saved',actions);self.assertNotIn(key,json.dumps(actions))
 def test_failed_check_keeps_previous_credentials(self):
  self.officer();gemini_provider._portal_credentials=('previous-working-key',gemini_provider.DEFAULT_MODEL)
  with patch('gemini_provider.verify_key',side_effect=ValueError('Gemini quota is unavailable.')):
   with self.assertRaises(urllib.error.HTTPError):self.request('interviews/provider',{'apiKey':'replacement-key-123456789'})
  self.assertEqual(gemini_provider.credentials()[0],'previous-working-key')
  self.assertFalse((server.DATA/'gemini-credentials.dpapi').exists())
 def test_malformed_key_rejected_before_request(self):
  self.officer()
  with patch('gemini_provider.verify_key') as verify:
   with self.assertRaises(urllib.error.HTTPError):self.request('interviews/provider',{'apiKey':'bad\nkey'})
   verify.assert_not_called()
 def test_auth_key_with_dot_reaches_provider_validation(self):
  self.officer();key='AQ.synthetic-key-for-test-123456789'
  with patch('gemini_provider.save_portal_key') as save:
   result=self.request('interviews/provider',{'apiKey':key})
  self.assertTrue(result['configured'])
  self.assertEqual(save.call_args.args[0],key)

class KeyVerificationTests(unittest.TestCase):
 def test_fallback_is_verified_before_saving(self):
  with patch.object(gemini_provider,'_portal_credentials',None),patch('gemini_provider.verify_key',side_effect=[gemini_provider.ModelUnavailable('Timeout'),None]) as verify,patch('credential_store.save') as save:
   gemini_provider.save_portal_key('synthetic-key',Path('unused.dpapi'))
   self.assertEqual(verify.call_count,2)
   self.assertEqual(json.loads(save.call_args.args[1])['model'],gemini_provider.FALLBACK_MODEL)
 def test_invalid_key_does_not_trigger_fallback(self):
  with patch('gemini_provider.verify_key',side_effect=ValueError('Invalid key')) as verify,patch('credential_store.save') as save:
   with self.assertRaises(ValueError):gemini_provider.save_portal_key('synthetic-key',Path('unused.dpapi'))
   self.assertEqual(verify.call_count,1);save.assert_not_called()
 def test_automatic_model_and_structured_probe(self):
  response=io.BytesIO(json.dumps({'candidates':[{'content':{'parts':[{'text':'{"ok":true}'}]}}]}).encode())
  with patch('urllib.request.urlopen',return_value=response) as call:gemini_provider.verify_key('test-only-key')
  request=call.call_args.args[0]
  self.assertIn(gemini_provider.DEFAULT_MODEL,request.full_url)
  self.assertNotIn('test-only-key',request.full_url)
  self.assertEqual(json.loads(request.data)['generationConfig']['responseMimeType'],'application/json')
 def test_provider_errors_do_not_leak_request_or_key(self):
  error=urllib.error.HTTPError('https://example.invalid/secret-key',403,'secret-key',{},None)
  with patch('urllib.request.urlopen',side_effect=error):
   with self.assertRaises(ValueError) as result:gemini_provider.verify_key('secret-key')
  self.assertNotIn('secret-key',str(result.exception))
 @unittest.skipUnless(os.name=='nt','Windows DPAPI storage')
 def test_dpapi_round_trip(self):
  raw=b'synthetic-secret-for-encryption-test'
  protected=credential_store.transform(raw,True)
  self.assertNotIn(raw,protected)
  self.assertEqual(credential_store.transform(protected,False),raw)
