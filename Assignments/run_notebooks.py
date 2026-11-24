"""Execute these plain-Python notebooks in fresh processes and save real outputs.

No IPython magics or third-party execution kernel is needed. Jupyter can also
run these notebooks. The runner does not pretend to be nbclient or a browser test.
"""
import argparse,contextlib,hashlib,io,json,os,subprocess,sys,time,traceback
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent

def source_hash(nb):
 return hashlib.sha256(json.dumps([c['source'] for c in nb['cells']],ensure_ascii=False).encode()).hexdigest()

def worker(path):
 nb=json.loads(path.read_text(encoding='utf-8'));scope={'__name__':'__main__'};count=0;failed=False
 os.chdir(HERE)
 # Reject accidental real-provider calls, but allow the project's localhost API tests.
 import urllib.request,urllib.parse
 original=urllib.request.urlopen
 def offline(request,*args,**kwargs):
  url=request.full_url if hasattr(request,'full_url') else request
  if urllib.parse.urlparse(url).hostname not in ('localhost','127.0.0.1','::1'):raise RuntimeError('Assignments forbid external network requests')
  return original(request,*args,**kwargs)
 urllib.request.urlopen=offline
 for c in nb['cells']:
  if c['cell_type']=='code':c['outputs']=[];c['execution_count']=None
 for c in nb['cells']:
  if c['cell_type']!='code':continue
  count+=1;c['execution_count']=count;output=io.StringIO()
  try:
   with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):exec(compile(''.join(c['source']),path.name+':cell'+str(count),'exec'),scope)
  except Exception as exc:
   c['outputs'].append({'output_type':'error','ename':type(exc).__name__,'evalue':str(exc),'traceback':traceback.format_exc().splitlines()});failed=True
  if output.getvalue():c['outputs'].insert(0,{'output_type':'stream','name':'stdout','text':output.getvalue().splitlines(keepends=True)})
  if failed:break
 nb['metadata']['execution']={'runner':'plain Python isolated process','passed':not failed,'source_sha256':source_hash(nb),'executed_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version.split()[0]}
 path.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+'\n',encoding='utf-8')
 if failed:
  print(path.name,'FAILED',c['outputs']);return 1
 print(path.name,'PASS',count,'code cells');return 0

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--worker');parser.add_argument('--check',action='store_true');args=parser.parse_args()
 if args.worker:return worker(Path(args.worker).resolve())
 paths=sorted(HERE.glob('LAB_*_Worklet9_*.ipynb'));assert len(paths)==14
 results=[]
 for path in paths:
  start=time.perf_counter()
  if args.check:
   nb=json.loads(path.read_text(encoding='utf-8'));execution=nb['metadata'].get('execution',{})
   passed=execution.get('passed') is True and execution.get('source_sha256')==source_hash(nb)
   passed=passed and all(c.get('execution_count') is not None and not any(o['output_type']=='error' for o in c['outputs']) for c in nb['cells'] if c['cell_type']=='code')
  else:
   run=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(path)],capture_output=True,text=True,timeout=180)
   print(run.stdout,end='');print(run.stderr,end='',file=sys.stderr);passed=run.returncode==0
  results.append({'notebook':path.name,'passed':bool(passed),'duration_seconds':round(time.perf_counter()-start,3)})
 if not args.check:
  (HERE/'execution_report.json').write_text(json.dumps({'executed_utc':datetime.now(timezone.utc).isoformat(),'method':'Fresh Python process per notebook; synthetic inputs; no external API calls','results':results,'all_passed':all(r['passed'] for r in results)},indent=2)+'\n')
 print(f"{sum(r['passed'] for r in results)}/{len(results)} notebooks passed.")
 return 0 if all(r['passed'] for r in results) else 1

if __name__=='__main__':raise SystemExit(main())
