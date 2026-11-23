"""Local development server. Run with Python 3.11+: python server.py."""
import hashlib, hmac, json, os, secrets, sqlite3, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from http.cookies import SimpleCookie
from contextlib import contextmanager
import analysis_service
import practice_service
import interview_service
import progress_service
import media_service
import gemini_provider
import provider_settings
import runtime_service
import tool_gateway
import coding_service
import coordinator_service
import governance_service
import benchmark_service

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'runtime'; DATA.mkdir(exist_ok=True)
DB=DATA/'portal.sqlite3'
gemini_provider.load_environment(ROOT/'.env')
gemini_provider.load_portal_credentials(DATA/'gemini-credentials.dpapi')

@contextmanager
def connect():
    db=sqlite3.connect(DB); db.row_factory=sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()

def initialize():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,name TEXT NOT NULL,role TEXT NOT NULL,salt TEXT NOT NULL,password TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS profiles(user_id TEXT PRIMARY KEY,data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor TEXT,action TEXT,created REAL);
        ''')

    with connect() as db:
        analysis_service.initialize(db)
        practice_service.initialize(db)
        interview_service.initialize(db)
        media_service.initialize(db)
        progress_service.initialize(db)
        runtime_service.initialize(db)
        coding_service.initialize(db)
        coordinator_service.initialize(db)
        governance_service.initialize(db)
        benchmark_service.initialize(db)

def password_hash(password,salt):
    return hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()

def create_user(uid,name,role,password):
    if role not in ('student','faculty') or len(password)<12: raise ValueError('Use a valid role and a password of at least 12 characters')
    salt=secrets.token_hex(16)
    with connect() as db:
        db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid.upper(),name,role,salt,password_hash(password,salt)))

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,status,payload,cookie=None):
        body=json.dumps(payload).encode(); self.send_response(status)
        self.send_header('Content-Type','application/json'); self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        if cookie: self.send_header('Set-Cookie',cookie)
        self.end_headers(); self.wfile.write(body)
    def identity(self):
        cookies=SimpleCookie(); cookies.load(self.headers.get('Cookie',''))
        token=cookies.get('session'); digest=hashlib.sha256(token.value.encode()).hexdigest() if token else ''
        with connect() as db:
            row=db.execute('SELECT u.id,u.name,u.role FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=? AND s.expires>?',(digest,time.time())).fetchone()
        return dict(row) if row else None
    def do_GET(self):
        if self.path=='/api/setup-status':
            with connect() as db: ready=db.execute("SELECT 1 FROM users WHERE role='faculty'").fetchone() is not None
            return self.send(200,{'required':not ready})
        if self.path.startswith('/api/'):
            user=self.identity()
            if not user: return self.send(401,{'error':'Please sign in'})
            if benchmark_service.handle(self,user,None,connect):return
            if coordinator_service.handle(self,user,None,connect):return
            if governance_service.handle(self,user,None,connect):return
            if runtime_service.handle(self,user,None,connect):return
            if tool_gateway.handle(self,user,None,connect):return
            if coding_service.handle(self,user,None,connect):return
            if provider_settings.handle(self,user,None,connect,DATA):return
            if progress_service.handle(self,user,None,connect):return
            if media_service.handle(self,user,None,connect,DATA):return
            if interview_service.handle(self,user,None,connect):return
            if practice_service.handle(self,user,None,connect):return
            if analysis_service.handle(self,user,None,connect):return
            if self.path=='/api/me': return self.send(200,user)
            if self.path=='/api/profile':
                with connect() as db: row=db.execute('SELECT data FROM profiles WHERE user_id=?',(user['id'],)).fetchone()
                return self.send(200,json.loads(row['data']) if row else {})
            if self.path=='/api/submissions':
                if user['role']!='faculty': return self.send(403,{'error':'Faculty access required'})
                with connect() as db: rows=db.execute('SELECT u.id,u.name,p.data FROM users u JOIN profiles p ON p.user_id=u.id').fetchall()
                return self.send(200,[{'id':r['id'],'name':r['name'],'profile':json.loads(r['data'])} for r in rows])
            return self.send(404,{'error':'Not found'})
        mapping={'/':'index.html','/workspaces.js':'workspaces.js','/media-upload.js':'media-upload.js','/app.js':'app.js','/style.css':'style.css'}
        name=mapping.get(self.path.split('?')[0])
        if not name: return self.send(404,{'error':'Not found'})
        file=ROOT/'frontend'/name
        self.send_response(200); self.send_header('Cache-Control','no-store, max-age=0'); self.send_header('Content-Type',{'html':'text/html','js':'text/javascript','css':'text/css'}[file.suffix[1:]])
        self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'")
        self.end_headers(); self.wfile.write(file.read_bytes())
    def do_POST(self):
        if self.headers.get('Host','').split(':')[0] not in ('localhost','127.0.0.1'):
            return self.send(403,{'error':'Local host required'})
        # Same-origin JSON requests only; no cross-origin credentials or form submissions.
        if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.send(415,{'error':'JSON required'})
        origin=self.headers.get('Origin')
        if origin and origin != 'http://'+self.headers.get('Host',''): return self.send(403,{'error':'Origin rejected'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=3000000: return self.send(413,{'error':'Request too large or empty'})
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict): raise ValueError()
        except (ValueError,UnicodeError): return self.send(400,{'error':'Invalid request'})
        if self.path in ('/api/setup','/api/students','/api/register'):
            actor=self.identity()
            if self.path=='/api/students' and (not actor or actor['role']!='faculty'):
                return self.send(403,{'error':'Placement officer access required'})
            uid=data.get('id',''); name=data.get('name',''); password=data.get('password','')
            if not all(isinstance(v,str) for v in (uid,name,password)):
                return self.send(400,{'error':'Account fields must be text'})
            uid=uid.strip().upper(); name=name.strip()
            if not 3<=len(uid)<=40 or not all(c.isascii() and (c.isalnum() or c in '_-') for c in uid) or not 2<=len(name)<=100 or not 12<=len(password)<=128:
                return self.send(400,{'error':'Use a valid ID (3â€“40 characters), name (2â€“100), and password (12â€“128)'})
            salt=secrets.token_hex(16); hashed=password_hash(password,salt)
            try:
                with connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    if self.path=='/api/setup' and db.execute("SELECT 1 FROM users WHERE role='faculty'").fetchone():
                        return self.send(409,{'error':'Initial setup is already complete'})
                    role='faculty' if self.path=='/api/setup' else 'student'
                    db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid,name,role,salt,hashed))
                    db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(actor['id'] if actor else uid,'account_created:'+uid,time.time()))
            except sqlite3.IntegrityError:
                return self.send(409,{'error':'This ID already exists'})
            return self.send(201,{'ok':True})
        if self.path=='/api/login':
            uid=str(data.get('usn','')).upper(); password=str(data.get('password',''))
            with connect() as db:
                row=db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
                valid=row and hmac.compare_digest(row['password'],password_hash(password,row['salt']))
                if not valid: return self.send(401,{'error':'Incorrect ID or password'})
                token=secrets.token_urlsafe(32)
                db.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),uid,time.time()+28800))
                db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(uid,'login',time.time()))
            return self.send(200,{'ok':True},f'session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800')
        user=self.identity()
        if not user: return self.send(401,{'error':'Please sign in'})
        if benchmark_service.handle(self,user,data,connect):return
        if coordinator_service.handle(self,user,data,connect):return
        if governance_service.handle(self,user,data,connect):return
        if runtime_service.handle(self,user,data,connect):return
        if tool_gateway.handle(self,user,data,connect):return
        if coding_service.handle(self,user,data,connect):return
        if provider_settings.handle(self,user,data,connect,DATA):return
        if progress_service.handle(self,user,data,connect):return
        if media_service.handle(self,user,data,connect,DATA):return
        if interview_service.handle(self,user,data,connect):return
        if practice_service.handle(self,user,data,connect):return
        if analysis_service.handle(self,user,data,connect):return
        if self.path=='/api/logout':
            cookie=SimpleCookie(); cookie.load(self.headers.get('Cookie',''))
            if cookie.get('session'):
                with connect() as db: db.execute('DELETE FROM sessions WHERE token=?',(hashlib.sha256(cookie['session'].value.encode()).hexdigest(),))
            return self.send(200,{'ok':True},'session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
        if self.path=='/api/profile':
            if user['role']!='student': return self.send(403,{'error':'Student account required'})
            allowed=('branch','graduation','cgpa','leetcode','target','resumeConsent','codingConsent','academicConsent','github','githubConsent','jobDescription')
            clean={k:data.get(k) for k in allowed}
            clean['jobDescription']=data.get('jobDescription','')
            if not isinstance(clean['jobDescription'],str) or len(clean['jobDescription'])>15000:return self.send(400,{'error':'Job description must be text of at most 15,000 characters'})
            clean['github']=data.get('github','')
            clean['githubConsent']=data.get('githubConsent',False)
            if type(clean['githubConsent']) is not bool:return self.send(400,{'error':'Explicit GitHub consent required'})
            if clean['github'] and not clean['githubConsent']:return self.send(400,{'error':'GitHub consent required to save your account'})
            if any(type(clean[k]) is not bool for k in ('resumeConsent','codingConsent','academicConsent')): return self.send(400,{'error':'Explicit consent selections required'})
            if not clean['academicConsent'] and any(clean[k] for k in ('branch','graduation','cgpa')): return self.send(400,{'error':'Academic consent required to save academic details'})
            if not clean['codingConsent'] and clean['leetcode']: return self.send(400,{'error':'Coding consent required to save the username'})
            try:
                if clean['cgpa'] and not 0<=float(clean['cgpa'])<=10: raise ValueError()
                if any(not isinstance(clean[k],str) or len(clean[k])>160 for k in ('branch','graduation','cgpa','leetcode','github','target')): raise ValueError()
            except (ValueError,TypeError): return self.send(400,{'error':'Check your profile fields; CGPA must be between 0 and 10'})
            try:
                for source in ('leetcode','github'):
                    if clean[source]:clean[source]=analysis_service.profile_connectors.username(clean[source],source)
            except ValueError as exc:return self.send(400,{'error':str(exc)})
            with connect() as db:
                db.execute('INSERT INTO consent_history(user_id,data,created) VALUES(?,?,?)',(user['id'],json.dumps({k:clean[k] for k in ('resumeConsent','codingConsent','githubConsent','academicConsent')}),time.time()))
                db.execute('DELETE FROM connections WHERE user_id=?',(user['id'],))
                db.execute('INSERT INTO profiles VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET data=excluded.data',(user['id'],json.dumps(clean)))
                db.execute("UPDATE analyses SET status='superseded' WHERE user_id=? AND status='pending'",(user['id'],))
                db.execute('INSERT INTO audit(actor,action,created) VALUES(?,?,?)',(user['id'],'profile_and_consent_updated',time.time()))
            return self.send(200,{'ok':True})
        return self.send(404,{'error':'Not found'})

if __name__=='__main__':
    import argparse,getpass
    parser=argparse.ArgumentParser(); parser.add_argument('--create-user'); parser.add_argument('--name'); parser.add_argument('--role',choices=['student','faculty']); parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args(); initialize()
    if args.create_user:
        create_user(args.create_user,args.name or args.create_user,args.role or 'student',getpass.getpass('Password (12+ characters): ')); print('Account created')
    else:
        print(f'Portal running at http://localhost:{args.port}',flush=True)
        ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()

