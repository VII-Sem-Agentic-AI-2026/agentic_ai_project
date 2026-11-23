import unittest,json,base64
from unittest.mock import patch
import urllib.error
import test_api
import server
from resume_structure import structure
from question_bank import questions
from practice_service import grade


class SectionBoundaryTests(unittest.TestCase):
    def test_combined_heading(self):
        text = 'TECHNICAL SKILLS\nPython, SQL\nPROJECTS & EXPERIENCE\nInference Platform\n\x7f Developing inference across\nmultiple systems.\nResume Assistant\n\x7f Built a retrieval pipeline.\nEDUCATION\nB.E. Computer Science'
        result = structure(text)
        self.assertEqual(len(result['projects']), 2)
        self.assertEqual(result['skills'], ['Python, SQL'])
        self.assertIn('multiple systems.', result['projects'][0]['summary'])
        self.assertFalse(set(result['skills']) & set(result['project_lines']))

    def test_heading_variations(self):
        for heading in ['PROJECTS AND EXPERIENCE:', '2. Academic Projects', 'P R O J E C T S']:
            result = structure('Technical Skills\nPython\n'+heading+'\nCareer Portal\nBuilt a portal.\nEducation\nB.Tech')
            self.assertEqual(len(result['projects']), 1)
            self.assertEqual(result['skills'], ['Python'])

    def test_bank_grading(self):
        for kind in ('aptitude', 'technical'):
            bank = questions(kind)
            self.assertEqual(grade(bank, {q['id']:q['answer'] for q in bank})['percentage'], 100)
            self.assertEqual(grade(bank, {})['correct'], 0)


class PracticeApiTests(unittest.TestCase):
    def setUp(self):
        test_api.ApiTests.setUp(self)
        generator=patch('ai_generation.practice',side_effect=lambda context:questions(context['kind'])[:10])
        self.generator=generator.start();self.addCleanup(generator.stop)
        with server.connect() as db:
            db.execute('INSERT INTO profiles VALUES(?,?)',('TEST001',json.dumps({'resumeConsent':True,'target':'Backend Developer','jobDescription':'Python SQL backend APIs'})))
        self.request('login',dict(usn='TEST001',password='test-password-long'))
        self.request('resume',{'filename':'resume.txt','content':base64.b64encode(b'Skills\nPython SQL\nProjects\nAPI project\nBuilt a backend.').decode()})
    tearDown = test_api.ApiTests.tearDown
    request = test_api.ApiTests.request

    def test_personalised_context_and_failure_without_attempt(self):
        self.generator.side_effect=ValueError('Provider unavailable')
        with self.assertRaises(urllib.error.HTTPError):self.request('practice/start',{'kind':'technical','aiConsent':True})
        self.assertEqual(self.request('practice'),[])
        context=self.generator.call_args.args[0]
        self.assertEqual(context['role'],'Backend Developer')
        self.assertEqual(context['jd'],'Python SQL backend APIs')
        self.assertIn('Python',context['resume'])

    def test_no_generation_without_consent(self):
        with self.assertRaises(urllib.error.HTTPError):self.request('practice/start',{'kind':'technical'})
        self.generator.assert_not_called()

    def test_changed_evidence_during_generation_rejected(self):
        def changed(context):
            with server.connect() as db:db.execute('UPDATE profiles SET data=? WHERE user_id=?',(json.dumps({'resumeConsent':False}),'TEST001'))
            return questions('technical')[:10]
        self.generator.side_effect=changed
        with self.assertRaises(urllib.error.HTTPError):self.request('practice/start',{'kind':'technical','aiConsent':True})
        self.assertEqual(self.request('practice'),[])

    def test_practice_lifecycle(self):
        self.request('login', dict(usn='TEST001', password='test-password-long'))
        attempt = self.request('practice/start', {'kind':'aptitude','aiConsent':True})
        self.assertEqual(len(attempt['questions']), 10)
        self.assertNotIn('answer', attempt['questions'][0])
        self.assertNotIn('explanation', attempt['questions'][0])
        self.assertEqual(attempt['id'], self.request('practice/start', {'kind':'aptitude','aiConsent':True})['id'])
        answers = {attempt['questions'][0]['id']:0}
        saved = self.request('practice/save', {'id':attempt['id'], 'answers':answers})
        self.assertEqual(saved['answers'], answers)
        result = self.request('practice/submit', {'id':attempt['id'], 'answers':answers})
        self.assertEqual(result['result']['answered'], 1)
        repeated = self.request('practice/submit', {'id':attempt['id'], 'answers':{}})
        self.assertEqual(result['result'], repeated['result'])
        self.request('logout', {})
        self.request('register', dict(id='OTHER001', name='Other Student', password='another-password-long'))
        self.request('login', dict(usn='OTHER001', password='another-password-long'))
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('practice/attempt', {'id':attempt['id']})
        self.assertEqual(error.exception.code, 403)

    def test_expired_attempt(self):
        self.request('login', dict(usn='TEST001', password='test-password-long'))
        attempt = self.request('practice/start', {'kind':'technical','aiConsent':True})
        with server.connect() as db:
            db.execute('UPDATE practice_attempts SET deadline=0 WHERE id=?', (attempt['id'],))
        result = self.request('practice/submit', {'id':attempt['id'], 'answers':{q['id']:0 for q in attempt['questions']}})
        self.assertEqual(result['result']['answered'], 0)

    def test_invalid_answers(self):
        self.request('login', dict(usn='TEST001', password='test-password-long'))
        attempt = self.request('practice/start', {'kind':'aptitude','aiConsent':True})
        for answers in ({'unknown':0}, {attempt['questions'][0]['id']:True}, {attempt['questions'][0]['id']:4}):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request('practice/save', {'id':attempt['id'], 'answers':answers})
            self.assertEqual(error.exception.code, 400)
