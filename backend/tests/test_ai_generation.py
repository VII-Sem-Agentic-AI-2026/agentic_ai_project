import unittest
from unittest.mock import patch
import ai_generation
from agent_pipeline import run
from analysis_service import analyse

class GenerationTests(unittest.TestCase):
 def test_practice_schema_rejects_bad_keys_and_duplicate_options(self):
  values=[{'topic':'SQL','prompt':'Which SQL expression matches case '+str(i)+'?','options':['A','B','C','D'],'answer':0,'explanation':'Option A is correct for this supplied example.'} for i in range(10)]
  with patch('ai_generation.generate',return_value=values):
   bank=ai_generation.practice({'kind':'technical'})
   self.assertEqual(len(bank),10);self.assertEqual(bank[0]['id'],'q1')
   values[0]['answer']=True
   with self.assertRaises(ValueError):ai_generation.practice({})
   values[0]['answer']=0;values[0]['options']=['A','a','C','D']
   with self.assertRaises(ValueError):ai_generation.practice({})
 def test_question_count_duplicates_and_size_rejected(self):
  for values in ([],['Same question repeated here']*10,['short']*10):
   with patch('ai_generation.generate',return_value=values):
    with self.assertRaises(ValueError):ai_generation.questions({'role':'Backend Developer'})
 def test_valid_questions_preserved(self):
  expected=['Explain implementation choice number '+str(i) for i in range(10)]
  with patch('ai_generation.generate',return_value=expected):self.assertEqual(ai_generation.questions({}),expected)
 def test_activity_coverage_and_lengths_validated(self):
  context={'tasks':[{'skill':'SQL'}]}
  for values in ([],['short'],['Valid activity to implement','Extra ungrounded activity']):
   with patch('ai_generation.generate',return_value=values):
    with self.assertRaises(ValueError):ai_generation.activities(context)
 def test_ai_report_preserves_gap_coverage_and_approval(self):
  with patch('ai_generation.activities',side_effect=lambda c:['Implement and test '+t['skill'] for t in c['tasks']]) as generate:
   result=run({'text':'Skills\nPython','digest':'a'*64},{'resumeConsent':True,'target':'Backend Developer'},[],None,analyse,coding_reader=lambda:{},plan={'status':'ready','target':'Backend Developer','aiConsent':True,'hours':6,'goal':'Backend interview preparation'})
  self.assertEqual(generate.call_count,1)
  self.assertTrue(all(result['validation'].values()))
  self.assertEqual(result['execution']['status'],'awaiting_review')
  self.assertTrue(all(t['task'].startswith('Implement and test') for t in result['roadmap']))
 def test_provider_failure_does_not_create_fallback_plan(self):
  with patch('ai_generation.activities',side_effect=ValueError('Provider unavailable')):
   with self.assertRaisesRegex(ValueError,'Provider unavailable'):
    run({'text':'Skills\nPython','digest':'a'*64},{'resumeConsent':True,'target':'Backend Developer'},[],None,analyse,coding_reader=lambda:{},plan={'status':'ready','target':'Backend Developer','aiConsent':True,'hours':6,'goal':'Backend preparation'})
