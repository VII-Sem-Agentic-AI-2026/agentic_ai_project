"""Section-aware resume extraction with conservative project grouping."""
import re
import unicodedata
HEADINGS={
 'academic':['education','academic details','academic qualifications','academic background','academics','qualifications','educational qualifications'],
 'projects':['projects','project','academic projects','personal projects','technical projects','project experience','projects and experience','projects experience','projects and internships','selected projects','key projects'],
 'experience':['experience','work experience','internships','professional experience','employment','internship experience'],
 'skills':['skills','technical skills','additional skills','extra skills','technologies','technical proficiency','technical expertise','skills and technologies','technical competencies'],
 'extras':['certifications','certificates','achievements','awards','activities','interests','languages','extracurricular activities'],
 'summary':['summary','profile','objective','career objective','professional summary'],
 'personal':['personal details','contact','contact details']}

def normalized_heading(value):
 value=unicodedata.normalize('NFKC',value).lower().replace('&',' and ')
 value=re.sub(r'^\s*(?:\d+[.)]\s*|[•*#\-]+\s*)','',value)
 value=re.sub(r'[^a-z0-9 ]',' ',value)
 return re.sub(r'\s+',' ',value).strip()

def detect_heading(line):
 candidate=normalized_heading(line)
 for key,headings in HEADINGS.items():
  if candidate in headings or candidate.replace(' ','') in {h.replace(' ','') for h in headings}:return key
 return None

def structure(text):
 sections={k:[] for k in HEADINGS};section='personal';project_rows=[]
 for raw in text.splitlines():
  raw=raw.strip()
  if not raw:continue
  bullet=bool(re.match(r'^[\x7f\uf0b7•●▪◦*\-]',raw))
  line=re.sub(r'^[\x7f\uf0b7•●▪◦*]+\s*','',raw).strip()
  detected=detect_heading(line)
  if detected:section=detected;continue
  prefix,sep,rest=line.partition(':')
  detected=detect_heading(prefix) if sep else None
  # Technology subheadings inside a project describe that project, not a new skills section.
  if detected=='skills' and section=='projects' and prefix.lower().strip() in ('technologies',):detected=None
  if detected:
   section=detected;line=rest.strip()
   if not line:continue
  sections[section].append(line)
  if section=='projects':project_rows.append((line,bullet))
 emails=list(dict.fromkeys(re.findall(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',text)))
 phones=list(dict.fromkeys(m.strip() for m in re.findall(r'(?<!\w)(?:\+\d{1,3}[ -]?)?(?:\d[ ()-]?){10,13}(?!\w)',text)))
 links=list(dict.fromkeys(re.findall(r'(?:https?://)?(?:github\.com|linkedin\.com/in)/[\w./-]+',text)))
 projects=[];current=None
 verbs=r'^(built|developed|developing|implemented|implementing|created|creating|designed|used|using|technologies|tech stack|features|achieved|integrated|deployed|improved|enabled|leveraged|utilized|optimized|supports|descriptions?|tools)\b'
 for line,bullet in project_rows:
  title_like=not bullet and len(line)<120 and not re.match(verbs,line,re.I) and not line.endswith(('.',',',';')) and (line[0].isupper() or bool(re.match(r'^\d+[.)]',line)))
  # Wrapped lines after bullets commonly begin lowercase; attach them to the description.
  if current is None or title_like:
   if current:projects.append(current)
   current={'title':line,'details':[],'source':'Resume (self-reported)'}
  else:current['details'].append(line)
 if current:projects.append(current)
 for project in projects:
  description=' '.join(project['details'])
  project['summary']=description[:700] if description else project['title']
 return {'personal':{'lines':sections['personal'],'emails':emails,'phones':phones,'links':links},'academic':sections['academic'],'projects':projects,'project_lines':sections['projects'],'experience':sections['experience'],'skills':sections['skills'],'extras':sections['extras'],'summary':sections['summary'],'notice':'Organised from resume headings, including combined Projects & Experience sections. Project text is kept separate from technical skills. All project descriptions are retained; briefs may be shortened.'}
