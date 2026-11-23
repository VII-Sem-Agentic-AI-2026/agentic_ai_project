"""Private persistent mock interviews with explicit provider consent and bounded turns."""
import json,secrets,time,threading,hashlib
import gemini_provider,ai_generation
from interview_scoring import context_for,summary,resume_evidence
from resume_structure import structure
from interview_plan import build_questions
LOCK=threading.Lock()

def initialize(db):
 db.execute('CREATE TABLE IF NOT EXISTS interviews(id TEXT PRIMARY KEY,user_id TEXT,state TEXT,created REAL)')

def guided_feedback(answer):
 if answer.startswith('[Spoken answer captured'):
  return {'feedback':'Spoken answer saved in the private recording. No text evaluation was performed.','improvement':'Review the recording with your mentor for specific feedback.','followup':'Explain a trade-off in your project and how you tested it.','checklist':{}}
 words=len(answer.split())
 return {'feedback':f'Answer saved ({words} words). Guided mode does not judge technical correctness.','improvement':'Explain your own contribution, the approach, a trade-off, and an observable result. Use a concrete example.','followup':'What trade-off did you make in this example, and how did you check the result?','checklist':{'has_detail':words>=40,'mentions_example':any(w in answer.lower() for w in ['example','project','built','implemented']),'mentions_result':any(w in answer.lower() for w in ['result','tested','measured','improved','reduced'])}}

def handle(handler,user,data,connect):
 path=handler.path
 if path not in ('/api/interviews','/api/interviews/start','/api/interviews/open','/api/interviews/answer','/api/interviews/end','/api/interviews/config','/api/interviews/draft','/api/interviews/review'):return False
 try:
  if path=='/api/interviews/config':
   handler.send(200,{'geminiConfigured':gemini_provider.configured(),'maxQuestions':10});return True
  if path=='/api/interviews':
   with connect() as db:
    rows=db.execute('SELECT i.*,u.name FROM interviews i JOIN users u ON u.id=i.user_id '+('' if user['role']=='faculty' else 'WHERE i.user_id=? ')+'ORDER BY created DESC',() if user['role']=='faculty' else (user['id'],)).fetchall()
   handler.send(200,[{'id':r['id'],'student':r['user_id'],'name':r['name'],'created':r['created'],'total':len(json.loads(r['state'])['questions']),'summary':summary(json.loads(r['state'])),'review':json.loads(r['state']).get('review'),**{k:json.loads(r['state'])[k] for k in ('status','mode','role','answered')}} for r in rows]);return True
  if data is None:raise ValueError('POST required')
  if path=='/api/interviews/start':
   if user['role']!='student':raise PermissionError('Student account required')
   if data.get('consent') is not True:raise ValueError('Consent to save private interview answers is required')
   mode='gemini'
   if data.get('mode','gemini')!='gemini':raise ValueError('New interviews require Gemini evaluation; guided mode has been removed')
   if mode=='gemini' and (not gemini_provider.configured() or data.get('aiConsent') is not True):raise ValueError('Configured Gemini and explicit permission to send answers to Google are required')
   with connect() as db:
    p=db.execute('SELECT data FROM profiles WHERE user_id=?',(user['id'],)).fetchone();profile=json.loads(p['data']) if p else {}
    role=profile.get('target') or 'your target role'
    resume=db.execute('SELECT text FROM resumes WHERE user_id=?',(user['id'],)).fetchone() if profile.get('resumeConsent') else None
   questions=ai_generation.questions({'resume':resume_evidence(resume['text']) if resume else '', 'jd':profile.get('jobDescription','')[:6000], 'role':role})
   question_sources=[{'source':'Gemini generated from resume/JD and role','topic':''} for _ in questions]
   with connect() as db:
    current=db.execute('SELECT data FROM profiles WHERE user_id=?',(user['id'],)).fetchone()
    if (json.loads(current['data']) if current else {})!=profile:raise ValueError('Profile or consent changed. Start again.')
    state={'status':'active','mode':mode,'role':role,'questions':questions,'questionSources':question_sources,'audioConsent':data.get('audioConsent') is True and mode=='gemini','turns':[],'answered':0,'consent':True,'aiConsent':mode=='gemini','rubricVersion':2,'evidence':{'resume':resume_evidence(resume['text']) if resume else '','jd':profile.get('jobDescription','')[:6000]},'notice':'Gemini practice evaluation, not a readiness certification. Scores and example answers may be wrong and need placement officer review.'}
    ident=secrets.token_urlsafe(18);db.execute('INSERT INTO interviews VALUES(?,?,?,?)',(ident,user['id'],json.dumps(state),time.time()))
    db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],'interview_started:'+ident,time.time()))
   handler.send(200,{'id':ident,**state,'summary':summary(state)});return True
  ident=data.get('id')
  if not isinstance(ident,str):raise ValueError('Interview ID required')
  # Serialize turn mutations; no DB transaction remains open during provider calls.
  if not LOCK.acquire(timeout=1):raise ValueError('An interview response is being processed. Please retry shortly.')
  try:
   with connect() as db:row=db.execute('SELECT * FROM interviews WHERE id=?',(ident,)).fetchone()
   if not row or (row['user_id']!=user['id'] and user['role']!='faculty'):raise PermissionError('Interview is not available')
   state=json.loads(row['state'])
   if path=='/api/interviews/open':handler.send(200,{'id':ident,**state,'summary':summary(state)});return True
   if path=='/api/interviews/review':
    if user['role']!='faculty':raise PermissionError('Placement officer access required')
    if state['status']=='active':raise ValueError('End the interview before officer review')
    note=data.get('note');decision=data.get('decision')
    if decision not in ('reviewed','needs_followup') or not isinstance(note,str) or not 10<=len(note.strip())<=3000:raise ValueError('Choose a review decision and write 10-3,000 characters of feedback')
    review={'reviewer':user['id'],'decision':decision,'note':note.strip(),'at':time.time()}
    state.setdefault('reviewHistory',[]).append(review);state['review']=review
    with connect() as db:
     db.execute('UPDATE interviews SET state=? WHERE id=?',(json.dumps(state),ident))
     db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],'interview_review:'+ident,time.time()))
    handler.send(200,{'id':ident,**state,'summary':summary(state)});return True
   if user['id']!=row['user_id'] or user['role']!='student':raise PermissionError('Only the student can answer or end this interview')
   if state['status']!='active':handler.send(200,{'id':ident,**state,'summary':summary(state)});return True
   if path=='/api/interviews/end':
    state['status']='ended';state.pop('draft',None)
   else:
    index=data.get('index');answer=data.get('answer')
    if type(index) is not int or index!=state['answered']:raise ValueError('This turn has changed. Reopen the interview to continue.')
    audio=data.get('audio')
    if audio is not None and not isinstance(audio,str):raise ValueError('Invalid audio data')
    if audio and (state['mode']!='gemini' or not state.get('audioConsent')):raise PermissionError('Explicit Gemini audio processing consent is required')
    if audio:answer='[Audio answer pending transcription]'
    if not isinstance(answer,str) or not 5<=len(answer.strip())<=6000:raise ValueError('Answer must contain 5–6,000 characters')
    question=state['questions'][index]
    context=context_for(state,index) if state.get('rubricVersion')==2 else None
    draft=state.get('draft')
    original_transcript=None
    if audio:
     if path=='/api/interviews/draft' and draft and draft.get('index')==index and draft.get('audioHash')==hashlib.sha256(audio.encode()).hexdigest():
      handler.send(200,{'transcript':draft['transcript'],'index':index});return True
     feedback=gemini_provider.evaluate(question,'',state['role'],audio=audio,audio_mime=data.get('audioMime',''),context=context)
     answer=feedback.pop('transcript');original_transcript=answer
     if path=='/api/interviews/draft':
      state['draft']={'index':index,'transcript':answer,'feedback':feedback,'audioHash':hashlib.sha256(audio.encode()).hexdigest()}
      with connect() as db:db.execute('UPDATE interviews SET state=? WHERE id=?',(json.dumps(state),ident))
      handler.send(200,{'transcript':answer,'index':index});return True
    elif path=='/api/interviews/draft':raise ValueError('A recorded audio answer is required')
    elif draft and draft['index']==index:
     original_transcript=draft['transcript']
     feedback=draft['feedback'] if answer.strip()==draft['transcript'].strip() else gemini_provider.evaluate(question,answer.strip(),state['role'],context=context)
    else:feedback=gemini_provider.evaluate(question,answer.strip(),state['role'],context=context) if state['mode']=='gemini' else guided_feedback(answer.strip())
    state.pop('draft',None)
    state['turns'].append({'question':question,'answer':answer.strip(),'feedback':feedback,'originalTranscript':original_transcript,'transcriptCorrected':original_transcript is not None and original_transcript.strip()!=answer.strip(),'rubric':context,'at':time.time()})
    state['answered']+=1
    # Bounded follow-ups preserve ten questions and the HR/reflection rounds.
    if index in (1,4,6) and feedback.get('scorable',True):
     state['questions'][index+1]=feedback['followup']
     state['questionSources'][index+1]={'source':'Gemini adaptive follow-up to answer '+str(index+1),'topic':''}
    if state['answered']>=len(state['questions']):state['status']='completed'
   with connect() as db:
    db.execute('UPDATE interviews SET state=? WHERE id=?',(json.dumps(state),ident))
    db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],'interview_'+state['status']+':'+ident,time.time()))
   handler.send(200,{'id':ident,**state,'summary':summary(state)})
  finally:LOCK.release()
 except PermissionError as exc:handler.send(403,{'error':str(exc)})
 except ValueError as exc:handler.send(400,{'error':str(exc)})
 return True
