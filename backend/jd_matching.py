"""Explainable JD-to-document matching. No eligibility or hiring decision is inferred."""
import re,hashlib
from resume_structure import structure
SKILLS={
 'Python':['python'],'Java':['java'],'JavaScript':['javascript','js'],'TypeScript':['typescript'],
 'C++':['c++'],'C#':['c#'],'C':['c'],'SQL':['sql'],'HTML':['html','html5'],'CSS':['css','css3'],
 'React':['react','reactjs','react.js'],'Angular':['angular'],'Vue':['vue','vue.js'],
 'Node.js':['node.js','nodejs'],'Express':['express.js','expressjs'],'Django':['django'],'Flask':['flask'],'FastAPI':['fastapi'],
 'Spring':['spring','spring boot'],'REST APIs':['rest','restful','rest api','rest apis'],
 'GraphQL':['graphql'],'PostgreSQL':['postgresql','postgres'],'MySQL':['mysql'],'MongoDB':['mongodb'],
 'Redis':['redis'],'Databases':['databases','database'],'Git':['git'],'GitHub':['github'],
 'Docker':['docker'],'Kubernetes':['kubernetes','k8s'],'Linux':['linux'],'AWS':['aws','amazon web services'],
 'Azure':['azure'],'GCP':['gcp','google cloud'],'CI/CD':['ci/cd','continuous integration','continuous delivery'],
 'Testing':['testing','unit tests','unit testing','pytest','jest'],'Data Structures':['data structures','dsa'],
 'Algorithms':['algorithms','algorithm','dsa'],'OOP':['oop','object oriented','object-oriented'],
 'System Design':['system design'],'Operating Systems':['operating systems'],'Networks':['computer networks','networking'],
 'Machine Learning':['machine learning','ml'],'Deep Learning':['deep learning'],'PyTorch':['pytorch'],
 'TensorFlow':['tensorflow'],'OpenCV':['opencv'],'NLP':['nlp','natural language processing'],'LLMs':['llm','llms','large language models'],
 'RAG':['rag','retrieval augmented generation','retrieval-augmented generation'],'LangGraph':['langgraph'],'LangChain':['langchain'],
 'OCR':['ocr','optical character recognition'],'Statistics':['statistics','statistical'],'Mathematics':['mathematics','linear algebra'],
 'Pandas':['pandas'],'NumPy':['numpy'],'Excel':['excel'],'Power BI':['power bi'],'Tableau':['tableau'],
 'ETL':['etl'],'Spark':['spark','pyspark'],'Communication':['communication','presentation skills'],
 'Technical Writing':['technical writing'],'Problem Solving':['problem solving','problem-solving'],
 'CAD':['cad','autocad'],'MATLAB':['matlab'],'Simulation':['simulation'],'Research':['research']}

def mentions(text,aliases):
 return any(re.search(r'(?<![\w+#])'+re.escape(alias)+r'(?![\w+#])',text,re.I) for alias in aliases)

def compare(resume,jd):
 if not jd.strip():return {'status':'no_jd','text':'','message':'Paste a job description below Target role in your profile to compare it with your resume.'}
 clauses=[line.strip(' •-*') for line in re.split(r'\n+|(?<=[.!?])\s+',jd) if line.strip()]
 requirements=[];excluded=[]
 for name,aliases in SKILLS.items():
  matches=[c for c in clauses if mentions(c,aliases)]
  if not matches:continue
  usable=[c for c in matches if not re.search(r'not required|no .{0,35}required|not necessary|do not need',c,re.I)]
  if not usable:excluded.append(name);continue
  required=[c for c in usable if not re.search(r'preferred|nice[- ]to[- ]have|optional|a plus|bonus',c,re.I)]
  excerpts=[line.strip() for line in resume.splitlines() if mentions(line,aliases)]
  requirements.append({'skill':name,'priority':'required_or_unspecified' if required else 'preferred','jdEvidence':(required or usable)[0],'resumeEvidence':excerpts[:3],'matched':bool(excerpts)})
 core=[r for r in requirements if r['priority']=='required_or_unspecified']
 matched=[r['skill'] for r in core if r['matched']];missing=[r['skill'] for r in core if not r['matched']]
 projects=[]
 for project in structure(resume)['projects']:
  content=project['title']+' '+' '.join(project['details'])
  supported=[r['skill'] for r in core if mentions(content,SKILLS[r['skill']])]
  projects.append({'title':project['title'],'summary':project['summary'],'matched':supported,'missing':[r['skill'] for r in core if r['skill'] not in supported],'coverage':round(100*len(supported)/len(core)) if core else None,'interpretation':'Project description mentions these JD technologies; implementation depth and ownership are not verified.'})
 manual=[c for c in clauses if not any(mentions(c,aliases) for aliases in SKILLS.values()) or re.search(r'\b(years?|degree|bachelor|master|cgpa|gpa|relocat|visa|citizen|salary|location|experience)\b',c,re.I)]
 return {'status':'matched' if core else 'no_recognized_requirements','text':jd,'digest':hashlib.sha256(jd.encode()).hexdigest(),'coverage':round(100*len(matched)/len(core)) if core else None,'matchedCount':len(matched),'total':len(core),'requirements':requirements,'matched':matched,'missing':missing,'preferredMissing':[r['skill'] for r in requirements if r['priority']=='preferred' and not r['matched']],'projects':projects,'learnNext':[f'Learn {skill} and add a small demonstrable exercise or project feature.' for skill in missing],'manualReview':manual,'excluded':excluded,'method':'Matched distinct required/unspecified recognised skills divided by all such recognised skills. Equal weights; preferred skills are listed separately.','notice':'Unreviewed document comparison, not a placement score, hiring probability or confirmation of eligibility. Keyword evidence can miss equivalent wording; years of experience and qualifications require human review.'}
