import json,time,unittest,threading
from unittest.mock import patch
import agent_pipeline as pipeline
from analysis_service import analyse
class PipelineTests(unittest.TestCase):
 def run_report(self,profile=None,snapshot=None):
  return pipeline.run({'text':'Skills\nPython, SQL\nProjects\nCareer Portal\nBuilt a Python application.','digest':'a'*64},{'target':'Backend Developer','resumeConsent':True,**(profile or {})},[],snapshot,analyse)
 def test_parallel_stages_and_validated_trace(self):
  barrier=threading.Barrier(2)
  def skills(*args):barrier.wait(timeout=3);return analyse(*args)
  def coding(profile):barrier.wait(timeout=3);return {}
  with patch('profile_connectors.collect',side_effect=coding):
   report=pipeline.run({'text':'Python SQL project','digest':'a'*64},{'target':'Backend Developer','resumeConsent':True},[],None,skills)
  self.assertTrue(all(report['validation'].values()))
  self.assertEqual(len(report['trace']),7)
  self.assertEqual(report['execution']['status'],'awaiting_review')
 def test_cached_sources_respect_current_consent_and_account(self):
  snapshot={'created':time.time(),'data':json.dumps({'github':{'username':'old','projects':[{'title':'private old project'}]},'leetcode':{'username':'old','solved':99}})}
  report=self.run_report({'codingConsent':True,'leetcode':'new'},snapshot)
  self.assertEqual(report['sources']['github']['status'],'not_consented')
  self.assertEqual(report['sources']['leetcode']['status'],'stale')
  self.assertNotIn('private old project',str(report['projects']))
 def test_failure_releases_capacity(self):
  with patch('profile_connectors.collect',side_effect=ValueError('Connector failed')):
   with self.assertRaisesRegex(ValueError,'Coding profile specialist'):self.run_report()
  with patch('profile_connectors.collect',return_value={}):self.assertTrue(self.run_report()['validation']['gap_coverage'])
 def test_validator_rejects_missing_task_and_wrong_evidence(self):
  with patch('profile_connectors.collect',return_value={}):report=self.run_report()
  report['roadmap']=[];report['evidence'][0]['source']='another-student'
  checks=pipeline.validate(report,'a'*64)
  self.assertFalse(checks['gap_coverage']);self.assertFalse(checks['evidence_present'])
