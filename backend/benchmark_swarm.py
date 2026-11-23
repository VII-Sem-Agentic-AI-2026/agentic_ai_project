"""Run a local sequential/parallel comparison in a temporary database, not user data."""
import json,tempfile,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import server,runtime_service

def main():
 original=server.DB
 with tempfile.TemporaryDirectory() as folder:
  server.DB=Path(folder)/'benchmark.sqlite3';server.initialize()
  ids=['DEMO001','DEMO002','DEMO003','DEMO004'];actor={'id':'BENCHMARK','role':'faculty'}
  with server.connect() as db:
   for student in ids:
    db.execute('INSERT INTO profiles VALUES(?,?)',(student,json.dumps({'target':'Backend Developer','resumeConsent':True})))
    db.execute('INSERT INTO resumes VALUES(?,?,?,?,?)',(student,'demo.txt','Python and SQL projects with API testing.','benchmark-digest',time.time()))
  def run(student):return runtime_service.execute(actor,runtime_service.start(actor,student,server.connect),server.connect)
  begin=time.perf_counter();sequential=[run(s) for s in ids];sequential_time=time.perf_counter()-begin
  begin=time.perf_counter()
  with ThreadPoolExecutor(max_workers=2) as pool:parallel=list(pool.map(run,ids))
  parallel_time=time.perf_counter()-begin
  with server.connect() as db:
   def reports(rows):
    return [json.loads(db.execute('SELECT data FROM analyses WHERE id=?',(r['id'],)).fetchone()[0]) for r in rows]
   left,right=reports(sequential),reports(parallel)
  equal=all(all(a[k]==b[k] for k in ('coverage','gaps','roadmap','validation')) for a,b in zip(left,right))
  print(json.dumps({'students':len(ids),'workers':2,'sequentialSeconds':round(sequential_time,3),'parallelSeconds':round(parallel_time,3),'qualityEquivalent':equal,'allValidated':all(all(r['validation'].values()) for r in left+right),'note':'Synthetic local fixtures without network latency; parallel execution may be slower for small inputs.'},indent=2))
 server.DB=original

if __name__=='__main__':main()
