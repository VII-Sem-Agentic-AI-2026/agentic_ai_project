"""Public-profile adapters. Fixed hosts, bounded responses, no credentials or private code."""
import json,re,time,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor

class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

def username(value,source):
 if not isinstance(value,str):raise ValueError('Username must be text')
 value=value.strip().rstrip('/')
 if '://' in value:
  from urllib.parse import urlparse
  parsed=urlparse(value)
  if parsed.scheme!='https' or parsed.hostname not in (source+'.com','www.'+source+'.com') or parsed.query or parsed.fragment:raise ValueError('Use a username or an HTTPS profile URL')
  parts=[p for p in parsed.path.split('/') if p]
  if source=='leetcode' and len(parts)==2 and parts[0]=='u':parts=parts[1:]
  if len(parts)!=1:raise ValueError('Use the account profile, not a repository or problem URL')
  value=parts[0]
 if not re.fullmatch(r'[A-Za-z0-9_-]{1,39}',value):raise ValueError('Enter a valid public username')
 return value

def request_json(url,payload=None):
 request=urllib.request.Request(url,data=json.dumps(payload).encode() if payload else None,headers={'User-Agent':'PlacementPortal/0.2','Accept':'application/json','Content-Type':'application/json'})
 try:
  with urllib.request.build_opener(NoRedirect).open(request,timeout=12) as response:
   raw=response.read(2000001)
   if len(raw)>2000000:raise ValueError('Provider response exceeded limit')
   return json.loads(raw)
 except urllib.error.HTTPError as exc:
  if exc.code==404:raise ValueError('Public profile not found')
  if exc.code in (403,429):raise ValueError('Provider blocked or rate-limited this request. Try again later.')
  raise ValueError('Provider request failed (HTTP '+str(exc.code)+')')
 except (urllib.error.URLError,TimeoutError,OSError):raise ValueError('Provider unavailable or timed out. Try again later.')
 except json.JSONDecodeError:raise ValueError('Provider returned an unexpected response')

def github(handle):
 repos=request_json('https://api.github.com/users/'+handle+'/repos?type=owner&sort=updated&per_page=100')
 if not isinstance(repos,list):raise ValueError('Unexpected GitHub response')
 projects=[];languages={};forks=0
 for r in repos:
  if r.get('fork'):forks+=1;continue
  lang=r.get('language')
  if lang:languages[lang]=languages.get(lang,0)+1
  projects.append({'title':r.get('name','Unnamed repository'),'summary':r.get('description') or 'No repository description provided.','language':lang or 'Not reported','url':'https://github.com/'+handle+'/'+r.get('name',''),'updated':r.get('pushed_at'),'archived':bool(r.get('archived')),'source':'GitHub public repository metadata'})
 return {'status':'ok','username':handle,'source':'https://github.com/'+handle,'fetched':time.time(),'projects':projects,'languages':languages,'repositoriesReviewed':len(repos),'forksExcluded':forks,'truncated':len(repos)==100,'summary':f'{len(projects)} non-fork public repositories inspected; {len(languages)} primary languages represented.','limitations':['Public metadata only; code quality, authorship and personal contribution are not verified.','At most 100 recently updated repositories; private repositories are excluded.']}

def leetcode(handle):
 query='''query userProfile($username:String!){matchedUser(username:$username){username submitStatsGlobal{acSubmissionNum{difficulty count}} userCalendar{streak totalActiveDays submissionCalendar}}}'''
 response=request_json('https://leetcode.com/graphql',{'query':query,'variables':{'username':handle}})
 errors=response.get('errors',[])
 if errors:
  response=request_json('https://leetcode.com/graphql',{'query':'query publicStats($username:String!){matchedUser(username:$username){username submitStatsGlobal{acSubmissionNum{difficulty count}}}}','variables':{'username':handle}})
  if response.get('errors'):raise ValueError('LeetCode public stats are unavailable')
 user=response.get('data',{}).get('matchedUser')
 if not user:raise ValueError('Public LeetCode profile not found')
 stats={r['difficulty']:r['count'] for r in user.get('submitStatsGlobal',{}).get('acSubmissionNum',[])}
 calendar_available=bool(user.get('userCalendar'))
 calendar=user.get('userCalendar') or {}
 try:activity=json.loads(calendar.get('submissionCalendar') or '{}')
 except (ValueError,TypeError):activity={}
 now=time.time();recent=sum(1 for t,n in activity.items() if str(t).isdigit() and now-30*86400<=int(t)<=now and n>0)
 return {'status':'ok','username':handle,'source':'https://leetcode.com/u/'+handle+'/','fetched':now,'solved':stats,'streak':calendar.get('streak'),'activeDays':calendar.get('totalActiveDays'),'activeDaysLast30':recent if calendar_available else None,'calendarAvailable':calendar_available,'summary':f"{stats.get('All','Unknown')} accepted problems reported. "+(f'{recent} active days in the last 30 days within the returned calendar.' if calendar_available else 'Calendar activity is private or unavailable; no activity estimate is shown.'),'limitations':['Platform counts do not verify independent problem-solving ability.','Calendar scope is provider-defined; no prior snapshot trend is inferred.','Public GraphQL access may be blocked or change. No private submissions are fetched.']}

def collect(profile):
 def run(source):
  consent='githubConsent' if source=='github' else 'codingConsent'
  if not profile.get(source):return source,{'status':'not_connected','message':'No account provided; optional source skipped.'}
  if not profile.get(consent):return source,{'status':'not_consented','message':'Source consent not granted.'}
  try:return source,globals()[source](username(profile[source],source))
  except (ValueError,KeyError,TypeError) as exc:return source,{'status':'unavailable','message':str(exc),'fetched':time.time()}
 with ThreadPoolExecutor(max_workers=2) as pool:return dict(pool.map(run,['leetcode','github']))

