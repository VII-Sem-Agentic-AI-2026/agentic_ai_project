"""Evidence extraction and deterministic preparation analysis (not LLM agents yet)."""
import base64, hashlib, io, json, re, time, zipfile
from xml.etree import ElementTree
from resume_structure import structure
import profile_connectors
from jd_matching import compare

BENCHMARKS={
 'Software Engineer':['Python','Data Structures','Algorithms','SQL','Git','Testing'],
 'Backend Developer':['Python','SQL','REST','Databases','Git','Testing'],
 'Frontend Developer':['JavaScript','TypeScript','React','HTML','CSS','Testing'],
 'Data Analyst':['SQL','Python','Statistics','Excel','Visualization'],
 'Data Engineer':['Python','SQL','ETL','Databases','Spark','Git'],
 'Core Engineering':['Mathematics','CAD','Simulation','Design','Testing'],
 'Higher Studies':['Research','Mathematics','Statistics','Writing','Projects']}
ALIASES={'Data Structures':['data structures','dsa'],'Algorithms':['algorithms','dsa'],'REST':['rest','restful','api'],'Databases':['databases','database','postgresql','mysql'],'Visualization':['visualization','power bi','tableau'],'Testing':['testing','pytest','jest','unit tests'],'Projects':['projects','project'],'Writing':['writing','publication','paper']}

def initialize(db):
 db.executescript('''CREATE TABLE IF NOT EXISTS resumes(user_id TEXT PRIMARY KEY,name TEXT,text TEXT,digest TEXT,created REAL);
 CREATE TABLE IF NOT EXISTS connections(user_id TEXT PRIMARY KEY,data TEXT,created REAL);
 CREATE TABLE IF NOT EXISTS analyses(id INTEGER PRIMARY KEY,user_id TEXT,status TEXT,data TEXT,created REAL,reviewer TEXT,note TEXT DEFAULT '');''')

def extract(data):
 name=data.get('filename',''); encoded=data.get('content','')
 if not isinstance(name,str) or not isinstance(encoded,str): raise ValueError('Invalid upload')
 try: raw=base64.b64decode(encoded,validate=True)
 except Exception: raise ValueError('Invalid file encoding')
 if not 0<len(raw)<=2*1024*1024: raise ValueError('File must be between 1 byte and 2 MB')
 ext=name.rsplit('.',1)[-1].lower()
 try:
  if ext=='txt': text=raw.decode('utf-8-sig')
  elif ext=='docx':
   with zipfile.ZipFile(io.BytesIO(raw)) as z:
    info=z.getinfo('word/document.xml')
    if info.file_size>4*1024*1024: raise ValueError('Document expands beyond the size limit')
    xml=z.read(info)
    if b'<!DOCTYPE' in xml or b'<!ENTITY' in xml: raise ValueError('Unsupported document markup')
    root=ElementTree.fromstring(xml)
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text='\n'.join(''.join(p.itertext()) for p in root.findall('.//w:p',ns))
  elif ext=='pdf':
   from pypdf import PdfReader
   pdf=PdfReader(io.BytesIO(raw))
   if pdf.is_encrypted or len(pdf.pages)>20: raise ValueError('Use an unencrypted PDF of at most 20 pages')
   text='\n'.join(p.extract_text() or '' for p in pdf.pages)
  else: raise ValueError('Upload a PDF, DOCX or UTF-8 TXT file')
 except ImportError: raise ValueError('PDF support requires installing backend/requirements.txt')
 except ValueError: raise
 except Exception: raise ValueError('Could not read this document; try a text-based PDF, DOCX or TXT')
 text=text.strip()
 if len(text)<30: raise ValueError('Not enough readable text. Scanned PDFs need OCR before upload')
 if len(text)>80000: raise ValueError('Resume text exceeds 80,000 characters')
 return name[:150],text,hashlib.sha256(raw).hexdigest()

def analyse(text,target,digest,benchmark=None):
 if target not in BENCHMARKS: raise ValueError('Select a supported target role in your profile')
 requirements=benchmark['skills'] if benchmark else BENCHMARKS[target]
 evidence=[]; found=[]; gaps=[]
 for skill in requirements:
  matches=[line.strip() for line in text.splitlines() if any(re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',line,re.I) for term in ALIASES.get(skill,[skill]))]
  if matches:
   found.append(skill);evidence.append({'skill':skill,'excerpt':matches[0][:500],'source':'resume:'+digest[:12],'verification':'Resume claim; not independently verified'})
  else:gaps.append(skill)
 roadmap=[{'week':i+1,'skill':skill,'task':f'Study {skill}, complete a practical exercise, and explain your approach to a mentor.','reason':f'{skill} is required by the selected sample role benchmark and is not evidenced in this resume.'} for i,skill in enumerate(gaps)]
 return {'target':target,'coverage':round(100*len(found)/len(requirements)),'found':found,'gaps':gaps,'evidence':evidence,'roadmap':roadmap,'benchmark':({'id':target,'version':str(benchmark['version']),'source':benchmark['source'],'requirements':requirements,'reviewer':benchmark['reviewer'],'reviewed':benchmark['reviewed'],'expires':benchmark['expires']} if benchmark else {'id':target,'version':'sample-1','source':'Project sample benchmark; faculty must review suitability','requirements':requirements}),'method':'Deterministic keyword evidence coverage, not a readiness or hiring probability','limitations':['Resume statements are self-reported.','Coding activity, academic eligibility and interviews have not been evaluated.','Sample role requirements are not verified company openings.'],'validation':{'gap_coverage':all(r['skill'] in gaps for r in roadmap),'evidence_present':all(e['excerpt'] for e in evidence)},'trace':[{'stage':'Resume extraction','status':'complete'},{'stage':'Role skill comparison','status':'complete'},{'stage':'Gap-linked roadmap','status':'complete'},{'stage':'Validation','status':'complete'},{'stage':'Placement officer approval','status':'pending'}]}

def handle(handler,user,data,connect):
 path=handler.path
 if path not in ('/api/resume','/api/analyses','/api/review','/api/connections'):return False
 try:
  with connect() as db:
   profile=db.execute('SELECT data FROM profiles WHERE user_id=?',(user['id'],)).fetchone()
   profile=json.loads(profile['data']) if profile else {}
   if path=='/api/connections':
    if user['role']!='student':raise PermissionError('Student account required')
    if data is None:
     row=db.execute('SELECT data FROM connections WHERE user_id=?',(user['id'],)).fetchone()
     snapshots=json.loads(row['data']) if row else {}
     for source,consent in [('github','githubConsent'),('leetcode','codingConsent')]:
      if not profile.get(consent) or snapshots.get(source,{}).get('username') not in (None,profile.get(source)):
       snapshots.pop(source,None)
     handler.send(200,snapshots);return True
    result=profile_connectors.collect(profile)
    latest=db.execute('SELECT data FROM profiles WHERE user_id=?',(user['id'],)).fetchone()
    if not latest or json.loads(latest['data'])!=profile:raise ValueError('Profile changed during sync. Please retry.')
    db.execute('INSERT INTO connections VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET data=excluded.data,created=excluded.created',(user['id'],json.dumps(result),time.time()))
   elif path=='/api/resume':
    if user['role']!='student':raise PermissionError('Student account required')
    if not profile.get('resumeConsent'):raise PermissionError('Save your resume consent in your profile first')
    if data is None:
     row=db.execute('SELECT name,text,digest,created FROM resumes WHERE user_id=?',(user['id'],)).fetchone()
     handler.send(200,{**dict(row),'structured':structure(row['text']),'jdMatch':compare(row['text'],profile.get('jobDescription',''))} if row else {});return True
    name,text,digest=extract(data)
    db.execute('INSERT INTO resumes VALUES(?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET name=excluded.name,text=excluded.text,digest=excluded.digest,created=excluded.created',(user['id'],name,text,digest,time.time()))
    db.execute("UPDATE analyses SET status='superseded' WHERE user_id=? AND status='pending'",(user['id'],))
    result={'name':name,'text':text,'digest':digest,'structured':structure(text),'jdMatch':compare(text,profile.get('jobDescription',''))}
   elif path=='/api/analyses':
    if data is not None:raise ValueError('GET required')
    if user['role']=='faculty':
     rows=db.execute('SELECT a.*,u.name,p.data AS profile FROM analyses a JOIN users u ON u.id=a.user_id JOIN profiles p ON p.user_id=a.user_id ORDER BY a.id DESC').fetchall()
    else:
     if not profile.get('resumeConsent'):handler.send(200,[]);return True
     rows=db.execute('SELECT * FROM analyses WHERE user_id=? ORDER BY id DESC',(user['id'],)).fetchall()
    result=[]
    for row in rows:
     if user['role']=='faculty' and not json.loads(row['profile']).get('resumeConsent'):continue
     item={'id':row['id'],'student':row['user_id'],'status':row['status'],'created':row['created'],'note':row['note'],'reviewer':row['reviewer']}
     if user['role']=='faculty' or row['status']=='approved':
      report=json.loads(row['data'])
      active_profile=json.loads(row['profile']) if user['role']=='faculty' else profile
      for source,consent in [('github','githubConsent'),('leetcode','codingConsent')]:
       snapshot=report.get('sources',{}).get(source,{})
       if not active_profile.get(consent) or snapshot.get('username')!=active_profile.get(source):
        if 'sources' in report:report['sources'][source]={'status':'not_consented','message':'This source is no longer connected with consent.'}
        if source=='github':report['projects']=[p for p in report.get('projects',[]) if p.get('source')!='GitHub public repository metadata']
      item['report']=report
     publication=db.execute('SELECT report_id FROM publications WHERE user_id=?',(row['user_id'],)).fetchone()
     item['isCurrent']=bool(publication and publication['report_id']==row['id'])
     if user['role']=='faculty':item['name']=row['name']
     result.append(item)
    handler.send(200,result);return True
   else:
    if data is None:raise ValueError('POST required')
    if user['role']!='faculty':raise PermissionError('Placement officer approval required')
    if data.get('decision') not in ('approved','changes_requested'):raise ValueError('Invalid review decision')
    note=data.get('note','')
    if not isinstance(note,str) or len(note)>2000:raise ValueError('Review note must be at most 2000 characters')
    if data['decision']=='changes_requested' and not note.strip():raise ValueError('Explain the correction needed')
    db.execute('BEGIN IMMEDIATE')
    row=db.execute('SELECT a.*,p.data AS profile FROM analyses a JOIN profiles p ON p.user_id=a.user_id WHERE a.id=?',(data.get('id'),)).fetchone()
    if not row or row['status']!='pending':raise ValueError('Only a pending report can be reviewed')
    if not json.loads(row['profile']).get('resumeConsent'):raise PermissionError('Student has withdrawn resume consent')
    report=json.loads(row['data'])
    if report.get('benchmark',{}).get('expires') and report['benchmark']['expires']<=time.time():raise ValueError('This role benchmark has expired. Review it and generate a fresh report before approval.')
    if not all(report['validation'].values()):raise ValueError('Report validation failed')
    db.execute('UPDATE analyses SET status=?,reviewer=?,note=? WHERE id=?',(data['decision'],user['id'],note.strip(),row['id']))
    if data['decision']=='approved':db.execute('INSERT INTO publications VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET report_id=excluded.report_id,updated=excluded.updated',(row['user_id'],row['id'],time.time()))
    result={'ok':True}
   db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],path+':'+str(result.get('id','')),time.time()))
  handler.send(200,result)
 except PermissionError as exc:handler.send(403,{'error':str(exc)})
 except (ValueError,TypeError) as exc:handler.send(400,{'error':str(exc)})
 return True
