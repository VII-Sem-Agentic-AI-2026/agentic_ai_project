import unittest,urllib.error
from unittest.mock import patch
import test_api
import gemini_provider
class InterviewTests(unittest.TestCase):
 def setUp(self):
  questions=patch('ai_generation.questions',return_value=['Explain your approach to interview topic '+str(i) for i in range(10)]);questions.start();self.addCleanup(questions.stop)
  test_api.ApiTests.setUp(self)
  self.config=patch('gemini_provider.configured',return_value=True);self.config.start();self.addCleanup(self.config.stop)
  self.evaluation=patch('gemini_provider.evaluate',return_value=dict(feedback='Clear example',improvement='Explain tests',followup='How did you test?',relevance=3,clarity=3,depth=3,correctness=3,scorable=True,strengths='Concrete example',missing='Test details',exampleAnswer='Explain an example and test it.'))
  self.evaluation.start();self.addCleanup(self.evaluation.stop)
 tearDown=test_api.ApiTests.tearDown
 request=test_api.ApiTests.request
 def login(self):self.request('login',dict(usn='TEST001',password='test-password-long'))
 def test_generation_failure_saves_no_interview(self):
  self.login()
  with patch('ai_generation.questions',side_effect=ValueError('Generation unavailable')):
   with self.assertRaises(urllib.error.HTTPError):self.request('interviews/start',{'consent':True,'aiConsent':True})
  self.assertEqual(self.request('interviews'),[])
 def test_gemini_complete_and_private(self):
  self.login();s=self.request('interviews/start',{'consent':True,'aiConsent':True})
  for i in range(10):s=self.request('interviews/answer',{'id':s['id'],'index':i,'answer':'I built a project and tested the result with a concrete example.'})
  self.assertEqual(s['status'],'completed');self.assertEqual(len(s['turns']),10)
  self.assertEqual(s['summary']['percentage'],75)
  self.assertTrue(s['summary']['complete'])
  self.assertEqual(len(self.request('interviews/open',{'id':s['id']})['turns']),10)
  self.request('logout',{});self.request('register',dict(id='OTHERINT',name='Another Student',password='another-password-long'));self.request('login',dict(usn='OTHERINT',password='another-password-long'))
  self.assertEqual(self.request('interviews'),[])
  with self.assertRaises(urllib.error.HTTPError):self.request('interviews/open',{'id':s['id']})
 def test_consent_and_duplicate_turn(self):
  self.login()
  with self.assertRaises(urllib.error.HTTPError):self.request('interviews/start',{'mode':'guided'})
  s=self.request('interviews/start',{'consent':True,'aiConsent':True})
  self.request('interviews/answer',{'id':s['id'],'index':0,'answer':'A sufficiently detailed answer.'})
  with self.assertRaises(urllib.error.HTTPError):self.request('interviews/answer',{'id':s['id'],'index':0,'answer':'Duplicate answer.'})
 def test_gemini_requires_consent_and_failure_does_not_advance(self):
  self.login()
  with patch('gemini_provider.configured',return_value=True):
   with self.assertRaises(urllib.error.HTTPError):self.request('interviews/start',{'mode':'gemini','consent':True})
   s=self.request('interviews/start',{'mode':'gemini','consent':True,'aiConsent':True})
  with patch('gemini_provider.evaluate',side_effect=ValueError('Provider unavailable')):
   with self.assertRaises(urllib.error.HTTPError):self.request('interviews/answer',{'id':s['id'],'index':0,'answer':'A detailed answer for testing.'})
  self.assertEqual(self.request('interviews/open',{'id':s['id']})['answered'],0)
 def test_gemini_feedback_and_followup(self):
  self.login()
  with patch('gemini_provider.configured',return_value=True):s=self.request('interviews/start',{'mode':'gemini','consent':True,'aiConsent':True})
  feedback=dict(feedback='Specific response.',improvement='Explain tests.',followup='How did you measure latency?',relevance=3,clarity=3,depth=2)
  with patch('gemini_provider.evaluate',return_value=feedback):
   for i in range(2):s=self.request('interviews/answer',{'id':s['id'],'index':i,'answer':'I measured the result of the project.'})
  self.assertEqual(s['questions'][2],feedback['followup'])

 def test_no_guided_fallback_or_unconfigured_start(self):
  self.login()
  with self.assertRaises(urllib.error.HTTPError):self.request('interviews/start',{'mode':'guided','consent':True,'aiConsent':True})
  with patch('gemini_provider.configured',return_value=False):
   with self.assertRaises(urllib.error.HTTPError):self.request('interviews/start',{'consent':True,'aiConsent':True})
  self.assertEqual(self.request('interviews'),[])

 def test_audio_draft_confirmation_and_correction_preserves_original(self):
  self.login();s=self.request('interviews/start',{'consent':True,'aiConsent':True,'audioConsent':True})
  f=dict(feedback='Clear',improvement='Explain tests',followup='How did you test?',relevance=3,clarity=3,depth=3,correctness=3,scorable=True,transcript='I built a sequel database.')
  with patch('gemini_provider.evaluate',return_value=f.copy()) as evaluate:
   draft=self.request('interviews/draft',{'id':s['id'],'index':0,'audio':'test-audio','audioMime':'audio/webm'})
   self.assertEqual(evaluate.call_args.kwargs['context']['rubricVersion'],2)
  self.assertEqual(draft['transcript'],f['transcript'])
  self.assertEqual(self.request('interviews/open',{'id':s['id']})['answered'],0)
  with patch('gemini_provider.evaluate',return_value={k:v for k,v in f.items() if k!='transcript'}) as evaluate:
   saved=self.request('interviews/answer',{'id':s['id'],'index':0,'answer':'I built a SQL database.'})
   self.assertEqual(evaluate.call_count,1)
  self.assertTrue(saved['turns'][0]['transcriptCorrected'])
  self.assertEqual(saved['turns'][0]['originalTranscript'],f['transcript'])
  self.assertEqual(saved['summary']['percentage'],75)
  self.assertFalse(saved['summary']['complete'])

 def test_unchanged_transcript_reuses_evaluation(self):
  self.login();s=self.request('interviews/start',{'consent':True,'aiConsent':True,'audioConsent':True})
  f=dict(feedback='Clear',improvement='Explain tests',followup='How?',relevance=2,clarity=2,depth=2,correctness=2,scorable=True,transcript='I built and tested a database.')
  with patch('gemini_provider.evaluate',return_value=f.copy()):self.request('interviews/draft',{'id':s['id'],'index':0,'audio':'test-audio','audioMime':'audio/webm'})
  with patch('gemini_provider.evaluate',side_effect=AssertionError('Unexpected paid call')):
   retried=self.request('interviews/draft',{'id':s['id'],'index':0,'audio':'test-audio','audioMime':'audio/webm'})
   self.assertEqual(retried['transcript'],f['transcript'])
   saved=self.request('interviews/answer',{'id':s['id'],'index':0,'answer':f['transcript']})
  self.assertEqual(saved['summary']['percentage'],50)

 def test_officer_review_is_scoped_audited_and_keeps_ai_scores(self):
  import server
  self.login();s=self.request('interviews/start',{'consent':True,'aiConsent':True})
  self.request('interviews/answer',{'id':s['id'],'index':0,'answer':'I built and tested a database.'})
  self.request('interviews/end',{'id':s['id']})
  payload={'id':s['id'],'decision':'needs_followup','note':'Please explain your query edge cases.'}
  with self.assertRaises(urllib.error.HTTPError):self.request('interviews/review',payload)
  server.create_user('REVIEWER','Officer','faculty','reviewer-password-long')
  self.request('logout',{});self.request('login',{'usn':'REVIEWER','password':'reviewer-password-long'})
  reviewed=self.request('interviews/review',payload)
  self.assertEqual(reviewed['summary']['percentage'],75)
  self.assertEqual(reviewed['review']['reviewer'],'REVIEWER')
  self.assertEqual(self.request('interviews')[0]['summary']['percentage'],75)
  with server.connect() as db:self.assertEqual(db.execute("SELECT count(*) FROM audit WHERE action LIKE 'interview_review:%'").fetchone()[0],1)

class ProviderValidationTests(unittest.TestCase):
 def response(self,payload):
  import io,json
  return io.BytesIO(json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps(payload)}]}}]}).encode())
 def test_valid_structured_response(self):
  payload=dict(feedback='Clear example',improvement='Add a measured result',followup='How did you measure it?',relevance=3,clarity=2,depth=2)
  with patch.dict('os.environ',{'GEMINI_API_KEY':'test-only-key','GEMINI_MODEL':'test-model'}),patch('urllib.request.urlopen',return_value=self.response(payload)):
   self.assertEqual(gemini_provider.evaluate('Question','Answer','Role'),payload)
 def test_invalid_score_rejected(self):
  payload=dict(feedback='Text',improvement='Text',followup='Text',relevance=8,clarity=2,depth=2)
  with patch.dict('os.environ',{'GEMINI_API_KEY':'test-only-key','GEMINI_MODEL':'test-model'}),patch('urllib.request.urlopen',return_value=self.response(payload)):
   with self.assertRaises(ValueError):gemini_provider.evaluate('Question','Answer','Role')
 def test_non_object_rejected(self):
  with patch.dict('os.environ',{'GEMINI_API_KEY':'test-only-key','GEMINI_MODEL':'test-model'}),patch('urllib.request.urlopen',return_value=self.response([])):
   with self.assertRaises(ValueError):gemini_provider.evaluate('Question','Answer','Role')

 def test_detailed_rubric_and_unscorable_validation(self):
  payload=dict(feedback='Not intelligible',improvement='Record in a quieter room',followup='Please repeat',relevance=0,clarity=0,depth=0,correctness=0,scorable=False,strengths='No evidence',missing='Intelligible content',exampleAnswer='Explain your contribution and tests.')
  with patch.dict('os.environ',{'GEMINI_API_KEY':'test-key','GEMINI_MODEL':'test-model'}),patch('urllib.request.urlopen',return_value=self.response(payload)):
   result=gemini_provider.evaluate('Question','Answer','Role',context={'category':'technical'})
   self.assertFalse(result['scorable'])
  payload['correctness']=4
  with patch.dict('os.environ',{'GEMINI_API_KEY':'test-key','GEMINI_MODEL':'test-model'}),patch('urllib.request.urlopen',return_value=self.response(payload)):
   with self.assertRaises(ValueError):gemini_provider.evaluate('Question','Answer','Role',context={})

 def test_invalid_correctness_rejected(self):
  payload=dict(feedback='Text',improvement='Text',followup='Text',relevance=2,clarity=2,depth=2,correctness=9,scorable=True,strengths='Text',missing='Text',exampleAnswer='Text')
  with patch.dict('os.environ',{'GEMINI_API_KEY':'test-key','GEMINI_MODEL':'test-model'}),patch('urllib.request.urlopen',return_value=self.response(payload)):
   with self.assertRaises(ValueError):gemini_provider.evaluate('Question','Answer','Role',context={})

class ScoreAggregationTests(unittest.TestCase):
 def test_resume_context_uses_skills_and_projects_not_contact_details(self):
  from interview_scoring import resume_evidence
  text='Student Name\nprivate@example.com\nSkills\nPython, SQL\nProjects\nCareer Portal\nBuilt a Python application.'
  result=resume_evidence(text)
  self.assertIn('Python',result);self.assertIn('Career Portal',result);self.assertNotIn('private@example.com',result)

 def test_unscorable_and_legacy_answers_are_not_zero_scores(self):
  from interview_scoring import summary
  state={'status':'completed','questions':['A','B','C'],'turns':[
   {'feedback':dict(relevance=4,clarity=4,depth=4,correctness=4,scorable=True,improvement='Maintain detail')},
   {'feedback':dict(relevance=0,clarity=0,depth=0,correctness=0,scorable=False,improvement='Repeat audio')},
   {'feedback':dict(checklist={},improvement='Legacy')}]}
  result=summary(state)
  self.assertEqual(result['percentage'],100);self.assertEqual(result['scored'],1);self.assertFalse(result['complete'])

class PersonalisedPlanTests(unittest.TestCase):
 def test_ten_questions_grounded_in_resume_and_jd(self):
  from interview_plan import build_questions
  q,sources=build_questions('Projects\nCareer Portal\nBuilt a Python application.\nSkills\nPython, SQL','Required: SQL, Docker, React and Testing.','Backend Developer')
  self.assertEqual(len(q),10);self.assertEqual(len(sources),10)
  self.assertIn('Career Portal',q[1]);self.assertIn('Backend Developer',q[0])
  self.assertEqual({s['topic'] for s in sources[4:8]},{'SQL','Docker','React','Testing'})
 def test_missing_profile_still_has_ten_questions(self):
  from interview_plan import build_questions
  self.assertEqual(len(build_questions('','','Software Engineer')[0]),10)
 def test_audio_payload_and_transcript(self):
  import base64,io,json
  payload=dict(feedback='Clear',improvement='Add evidence',followup='How did you test?',relevance=3,clarity=3,depth=2,transcript='I built and tested an API.')
  response=io.BytesIO(json.dumps({'candidates':[{'content':{'parts':[{'text':json.dumps(payload)}]}}]}).encode())
  with patch.dict('os.environ',{'GEMINI_API_KEY':'test-key','GEMINI_MODEL':'test-model'}),patch('urllib.request.urlopen',return_value=response) as call:
   result=gemini_provider.evaluate('Explain a project','','Backend',audio=base64.b64encode(b'a'*200).decode(),audio_mime='audio/webm')
   self.assertEqual(result['transcript'],payload['transcript'])
   body=json.loads(call.call_args.args[0].data)
   self.assertEqual(body['contents'][0]['parts'][1]['inlineData']['mimeType'],'audio/webm')
 def test_invalid_audio_rejected(self):
  with patch.dict('os.environ',{'GEMINI_API_KEY':'test-key','GEMINI_MODEL':'test-model'}):
   with self.assertRaises(ValueError):gemini_provider.evaluate('Q','','Role',audio='invalid',audio_mime='audio/webm')
