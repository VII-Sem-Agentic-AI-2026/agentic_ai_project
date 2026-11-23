"""Run Python only inside restricted Linux Docker containers; never on the host."""
import json,shutil,subprocess,threading,time,uuid
IMAGE='python:3.12-alpine'
SLOTS=threading.BoundedSemaphore(2)

def status():
 if not shutil.which('docker'):return {'ready':False,'message':'Docker is not installed on the server.'}
 try:
  engine=subprocess.run(['docker','info','--format','{{.OSType}}'],capture_output=True,text=True,timeout=5)
  if engine.returncode or engine.stdout.strip()!='linux':return {'ready':False,'message':'Start Docker Desktop with Linux containers on the server.'}
  image=subprocess.run(['docker','image','inspect',IMAGE],capture_output=True,timeout=5)
  if image.returncode:return {'ready':False,'message':'The coding runner image is not installed. Server setup is required.'}
  return {'ready':True,'message':'Python runner ready. Network disabled; CPU, memory, output and time limits enforced.'}
 except (OSError,subprocess.TimeoutExpired):return {'ready':False,'message':'Docker is not responding. Check the server engine.'}

def run_case(source,value):
 name='placement-code-'+uuid.uuid4().hex
 command=['docker','run','--rm','--pull','never','--name',name,'--network','none','--read-only','--user','65534:65534',
  '--cap-drop','ALL','--security-opt','no-new-privileges','--memory','64m','--memory-swap','64m','--cpus','0.5','--pids-limit','32',
  '--tmpfs','/tmp:rw,noexec,nosuid,size=8m','--log-driver','none','-i',IMAGE,'python','-I','-c',source]
 process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 chunks=[];overflow=threading.Event()
 def drain():
  length=0
  while True:
   block=process.stdout.read(1024)
   if not block:break
   length+=len(block)
   if length>16384:overflow.set();continue # Drain without retaining bytes so Docker cannot block on a full pipe.
   chunks.append(block)
 thread=threading.Thread(target=drain,daemon=True);thread.start();start=time.monotonic();timed_out=False
 try:
  try:process.stdin.write((json.dumps(value)+'\n').encode());process.stdin.close()
  except BrokenPipeError:pass
  while process.poll() is None:
   if overflow.is_set() or time.monotonic()-start>12:
    timed_out=not overflow.is_set();break
   time.sleep(.05)
  if process.poll() is None:
   process.kill()
   subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
  process.wait(timeout=5);thread.join(timeout=2)
  if overflow.is_set():return {'status':'output_limit'}
  if timed_out:return {'status':'time_limit'}
  if process.returncode in (125,126,127):raise ValueError('Container could not start. Check the Docker runner; no score recorded.')
  if process.returncode:return {'status':'runtime_error','detail':b''.join(chunks).decode('utf-8',errors='replace')[:2000]}
  try:return {'status':'ok','actual':json.loads(b''.join(chunks).decode('utf-8'))}
  except (ValueError,UnicodeError):return {'status':'invalid_output','detail':b''.join(chunks).decode('utf-8',errors='replace')[:2000]}
 finally:
  if process.poll() is None:process.kill()
  subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
  thread.join(timeout=2)
  process.stdout.close()

def grade(source,cases):
 if not SLOTS.acquire(blocking=False):raise ValueError('Coding runners busy. Retry shortly.')
 try:
  readiness=status()
  if not readiness['ready']:raise ValueError(readiness['message'])
  outcomes=[]
  for case in cases:
   result=run_case(source,case['input']);passed=result['status']=='ok' and type(result['actual']) is type(case['expected']) and result['actual']==case['expected']
   outcome={'passed':passed,'status':'passed' if passed else 'wrong_answer' if result['status']=='ok' else result['status'],'hidden':case.get('hidden',False)}
   if not outcome['hidden']:
    if 'actual' in result:outcome['actual']=result['actual']
    if 'detail' in result:outcome['detail']=result['detail']
   outcomes.append(outcome)
  passed=sum(o['passed'] for o in outcomes)
  return {'passed':passed,'total':len(cases),'percentage':round(100*passed/len(cases)),'cases':outcomes,'method':'Actual Python execution in resource-limited Docker containers'}
 finally:SLOTS.release()
