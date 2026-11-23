import unittest
from jd_matching import compare
class JobDescriptionTests(unittest.TestCase):
 def test_coverage_and_project_alignment(self):
  resume='Skills\nPython, SQL\nProjects\nData Portal\nBuilt a Python and SQL application.'
  r=compare(resume,'Required skills: Python, SQL and Docker.\nReact preferred.')
  self.assertEqual(r['coverage'],67)
  self.assertEqual(r['missing'],['Docker'])
  self.assertEqual(r['preferredMissing'],['React'])
  self.assertEqual(r['projects'][0]['coverage'],67)
 def test_boundaries(self):
  r=compare('JavaScript and C++ projects','Java and C required.')
  self.assertEqual(r['coverage'],0)
 def test_unknown_requirement_is_not_zero(self):
  r=compare('Python','Must have excellent customer empathy.')
  self.assertIsNone(r['coverage'])
  self.assertTrue(r['manualReview'])
 def test_negated_requirement(self):
  r=compare('SQL','Python is not required.\nSQL required.')
  self.assertEqual(r['coverage'],100)
  self.assertIn('Python',r['excluded'])
 def test_empty_jd(self):
  self.assertEqual(compare('Python','')['status'],'no_jd')
 def test_duplicate_requirements_count_once(self):
  self.assertEqual(compare('Python','Python required. Python experience.')['total'],1)
