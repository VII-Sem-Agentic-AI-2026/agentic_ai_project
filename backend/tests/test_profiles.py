import unittest,json
from unittest.mock import patch
from resume_structure import structure
from profile_connectors import username,collect,github,leetcode
class StructuredResumeTests(unittest.TestCase):
 def test_sections_and_project_summary(self):
  result=structure('Ananya Rao\nananya@example.com\nEducation\nB.E. Computer Science, 2027\nProjects\nCareer Portal\nBuilt a Python portal with SQL and REST APIs.\nSkills: Python, SQL\nCertifications\nCloud fundamentals')
  self.assertEqual(result['personal']['emails'],['ananya@example.com'])
  self.assertIn('Computer Science',result['academic'][0])
  self.assertEqual(result['projects'][0]['title'],'Career Portal')
  self.assertIn('Python portal',result['projects'][0]['summary'])
  self.assertEqual(result['skills'],['Python, SQL'])
 def test_no_invented_sections(self):
  result=structure('Student Name\nPython SQL')
  self.assertEqual(result['academic'],[]);self.assertEqual(result['projects'],[])
class ConnectorTests(unittest.TestCase):
 def test_url_validation(self):
  self.assertEqual(username('https://github.com/octocat','github'),'octocat')
  self.assertEqual(username('https://leetcode.com/u/example/','leetcode'),'example')
  for value in ['https://evil.com/a','https://github.com/user/repository','../secret','http://localhost/test']:
   with self.assertRaises(ValueError):username(value,'github')
 def test_missing_consent_never_calls_provider(self):
  with patch('profile_connectors.request_json') as request:
   result=collect({'github':'person','githubConsent':False})
   request.assert_not_called();self.assertEqual(result['github']['status'],'not_consented')
 def test_github_metadata_and_forks(self):
  with patch('profile_connectors.request_json',return_value=[{'name':'portal','description':'Career preparation app','language':'Python','fork':False},{'name':'forked','fork':True}]):
   result=github('person')
   self.assertEqual(len(result['projects']),1);self.assertEqual(result['forksExcluded'],1)
   self.assertEqual(result['projects'][0]['summary'],'Career preparation app')
 def test_leetcode_counts(self):
  fixture={'data':{'matchedUser':{'submitStatsGlobal':{'acSubmissionNum':[{'difficulty':'All','count':20}]},'userCalendar':{'streak':3,'totalActiveDays':8,'submissionCalendar':'{}'}}}}
  with patch('profile_connectors.request_json',return_value=fixture):
   result=leetcode('person');self.assertEqual(result['solved']['All'],20)
 def test_provider_failure_does_not_fake_results(self):
  with patch('profile_connectors.request_json',side_effect=ValueError('Provider blocked')):
   result=collect({'leetcode':'person','codingConsent':True,'github':'person','githubConsent':True})
   self.assertEqual(result['leetcode']['status'],'unavailable')
   self.assertNotIn('solved',result['leetcode'])

 def test_private_calendar_falls_back_to_public_counts(self):
  responses=[{'errors':[{'message':'no permission to check calendar'}],'data':{'matchedUser':None}},{'data':{'matchedUser':{'submitStatsGlobal':{'acSubmissionNum':[{'difficulty':'All','count':45}]}}}}]
  with patch('profile_connectors.request_json',side_effect=responses):
   result=leetcode('person')
   self.assertEqual(result['solved']['All'],45)
   self.assertIsNone(result['activeDaysLast30'])
   self.assertFalse(result['calendarAvailable'])
