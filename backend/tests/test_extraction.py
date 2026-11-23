import base64,io,unittest,zipfile
from analysis_service import extract,analyse
class ExtractionTests(unittest.TestCase):
 def test_docx(self):
  data=io.BytesIO()
  with zipfile.ZipFile(data,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Python SQL REST projects with databases and Git.</w:t></w:r></w:p></w:body></w:document>')
  _,text,_=extract(dict(filename='resume.docx',content=base64.b64encode(data.getvalue()).decode()))
  self.assertIn('Python SQL',text)
 def test_bad_files_rejected(self):
  for filename,content in [('bad.pdf',b'not a PDF'),('bad.exe',b'Unsupported binary content long enough'),('empty.txt',b'')]:
   with self.assertRaises(ValueError):extract(dict(filename=filename,content=base64.b64encode(content).decode()))
 def test_whole_word_matching(self):
  result=analyse('My reactions to difficult problems are positive. JavaScript, HTML and CSS projects.','Frontend Developer','abc')
  self.assertNotIn('React',result['found'])
  self.assertIn('JavaScript',result['found'])
 def test_roadmap_evidence_coverage(self):
  result=analyse('Python SQL databases REST Git project.','Backend Developer','abc')
  self.assertEqual(result['gaps'],['Testing'])
  self.assertEqual(result['roadmap'][0]['skill'],'Testing')
