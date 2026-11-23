"""Officer-only key setup; responses and audit records never include the key."""
import re,time,threading
import gemini_provider
LOCK=threading.Lock()

def handle(handler,user,data,connect,root):
 if handler.path!='/api/interviews/provider':return False
 if user['role']!='faculty':handler.send(403,{'error':'Placement officer access required'});return True
 if data is None:handler.send(200,{'configured':gemini_provider.configured()});return True
 key=data.get('apiKey')
 if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{20,200}',key.strip()):
  handler.send(400,{'error':'Paste a valid Gemini API key'});return True
 if not LOCK.acquire(blocking=False):handler.send(409,{'error':'A connection check is already running. Please wait.'});return True
 try:
  gemini_provider.save_portal_key(key.strip(),root/'gemini-credentials.dpapi')
  with connect() as db:db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],'gemini_key_verified_and_saved',time.time()))
  handler.send(200,{'configured':True,'message':'Gemini connected. Students can start interviews now.'})
 except ValueError as error:handler.send(400,{'error':str(error)})
 except OSError:handler.send(500,{'error':'Unable to save encrypted credentials; check local storage access.'})
 finally:LOCK.release()
 return True
