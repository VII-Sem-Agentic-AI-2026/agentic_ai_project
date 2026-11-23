"""Authenticated, consented local interview recordings with ordered upload chunks."""
import base64,json,time
from urllib.parse import urlparse,parse_qs

def initialize(db):
 db.execute('CREATE TABLE IF NOT EXISTS interview_media(id TEXT PRIMARY KEY,owner TEXT,mime TEXT,next_chunk INTEGER,bytes INTEGER,status TEXT,events TEXT)')

def handle(handler,user,data,connect,root):
 parsed=urlparse(handler.path);path=parsed.path
 if path not in ('/api/media/start','/api/media/chunk','/api/media/finish','/api/media/event','/api/media/info','/api/media/play','/api/media/delete'):return False
 try:
  ident=(parse_qs(parsed.query).get('id',[''])[0] if data is None else data.get('id'))
  if not isinstance(ident,str):raise ValueError('Interview ID required')
  with connect() as db:
   session=db.execute('SELECT user_id,state FROM interviews WHERE id=?',(ident,)).fetchone()
   if not session or (session['user_id']!=user['id'] and user['role']!='faculty'):raise PermissionError('Recording unavailable')
   if path not in ('/api/media/info','/api/media/play','/api/media/delete') and (user['role']!='student' or session['user_id']!=user['id']):raise PermissionError('Student recording access required')
   folder=root/'recordings';folder.mkdir(parents=True,exist_ok=True)
   # IDs originate in the server; look up before using a path.
   file=folder/(ident+'.webm')
   row=db.execute('SELECT * FROM interview_media WHERE id=?',(ident,)).fetchone()
   if path=='/api/media/delete':
    if data is None or data.get('confirm') is not True:raise ValueError('Confirm permanent recording deletion')
    if json.loads(session['state'])['status']=='active':raise ValueError('End the interview before deleting its recording')
    if not row:raise ValueError('Recording not found')
    db.execute('BEGIN IMMEDIATE')
    if file.resolve().parent!=folder.resolve():raise ValueError('Invalid recording location')
    try:file.unlink(missing_ok=True)
    except OSError:raise ValueError('Close recording playback and retry deletion')
    db.execute("UPDATE interview_media SET status='deleted',bytes=0,events='[]' WHERE id=?",(ident,))
    db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],'recording_deleted:'+ident,time.time()))
    handler.send(200,{'ok':True});return True
   if path=='/api/media/info':
    handler.send(200,dict(row) if row else {});return True
   if path=='/api/media/play':
    if not row or row['status']!='complete' or not file.exists():raise ValueError('Completed recording is not available')
    db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],'recording_playback:'+ident,time.time()))
    db.commit()
    size=file.stat().st_size;start=0;end=size-1;status=200
    value=handler.headers.get('Range','')
    if value:
     import re
     m=re.fullmatch(r'bytes=(\d+)-(\d*)',value)
     if not m:raise ValueError('Unsupported byte range')
     start=int(m[1]);end=min(int(m[2]) if m[2] else end,end);status=206
     if start>end:handler.send_response(416);handler.send_header('Content-Range',f'bytes */{size}');handler.end_headers();return True
    handler.send_response(status);handler.send_header('Content-Type',row['mime']);handler.send_header('Cache-Control','private, no-store');handler.send_header('Accept-Ranges','bytes');handler.send_header('Content-Length',str(end-start+1))
    if status==206:handler.send_header('Content-Range',f'bytes {start}-{end}/{size}')
    handler.end_headers()
    with file.open('rb') as stream:
     stream.seek(start);remaining=end-start+1
     while remaining>0:
      chunk=stream.read(min(65536,remaining))
      if not chunk:break
      handler.wfile.write(chunk);remaining-=len(chunk)
    return True
   if data is None:raise ValueError('POST required')
   db.execute('BEGIN IMMEDIATE')
   row=db.execute('SELECT * FROM interview_media WHERE id=?',(ident,)).fetchone()
   if path=='/api/media/start':
    if data.get('consent') is not True:raise ValueError('Recording consent required')
    mime=data.get('mime')
    if mime not in ('video/webm','video/webm;codecs=vp8,opus','video/webm;codecs=vp9,opus'):raise ValueError('Browser must support WebM recording')
    if row:raise ValueError('A recording already exists for this interview; start a new interview to record again')
    db.execute('INSERT INTO interview_media VALUES(?,?,?,?,?,?,?)',(ident,user['id'],mime,0,0,'recording','[]'))
    result={'ok':True}
   elif not row:raise ValueError('Start recording first')
   elif path=='/api/media/chunk':
    if row['status']!='recording':raise ValueError('Recording is closed')
    seq=data.get('sequence')
    if type(seq) is not int or seq<0:raise ValueError('Invalid chunk sequence')
    if seq<row['next_chunk']:handler.send(200,{'ok':True,'duplicate':True});return True
    if seq!=row['next_chunk']:raise ValueError('Out of order chunk')
    try:chunk=base64.b64decode(data.get('content',''),validate=True)
    except Exception:raise ValueError('Invalid recording data')
    if not 0<len(chunk)<=2*1024*1024 or row['bytes']+len(chunk)>250*1024*1024:raise ValueError('Recording size limit exceeded')
    # Truncate uncommitted bytes after a prior interrupted append.
    with file.open('r+b' if file.exists() else 'w+b') as stream:
     stream.truncate(row['bytes']);stream.seek(row['bytes']);stream.write(chunk)
    db.execute('UPDATE interview_media SET next_chunk=next_chunk+1,bytes=bytes+? WHERE id=?',(len(chunk),ident));result={'ok':True}
   elif path=='/api/media/finish':
    if not row['bytes']:raise ValueError('No recording bytes received')
    db.execute("UPDATE interview_media SET status='complete' WHERE id=?",(ident,));result={'ok':True}
   else:
    kind=data.get('event')
    if kind not in ('window_blur','tab_hidden','camera_ended','microphone_ended','camera_muted','microphone_muted','recording_interrupted'):raise ValueError('Unknown event')
    events=json.loads(row['events'])
    if len(events)<500:events.append({'event':kind,'at':time.time()})
    db.execute('UPDATE interview_media SET events=? WHERE id=?',(json.dumps(events),ident));result={'ok':True}
  handler.send(200,result)
 except PermissionError as exc:handler.send(403,{'error':str(exc)})
 except ValueError as exc:handler.send(400,{'error':str(exc)})
 return True
