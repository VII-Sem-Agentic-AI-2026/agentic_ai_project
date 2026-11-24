"""Rebuild original Worklet 9 notebook sources; execution is a separate step."""
import json,textwrap
from pathlib import Path
HERE=Path(__file__).resolve().parent
TEAM='Vijay Kumar — 01FE23BCI083; Rishi Kulkarni — 01FE23BCI088; Prajwal Hugar — 01FE23BCI075; Rohit Yendegeri — 01FE23BCI001.'
LABS=[
('Planner_Loop','Clarify, plan and revise','Turn a vague placement goal into a versioned, editable preparation plan.','Student goal, target role, consent and weekly hours.','At least two clarification questions; two revisions; invalid time budget rejected.','backend/coordinator_service.py',r'''
profile=clone(STUDENTS['DEMO001'])
vague=build(profile,'Help',8,'')
assert len(vague['questions'])>=2
show(vague['questions'])
v1=build(profile,'Prepare for backend developer interviews',8,'SQL')
v2=build(profile,v1['goal'],12,'SQL joins and API testing')
v3=build(profile,v2['goal'],6,'SQL joins and project explanation')
assert all(v['status']=='ready' for v in (v1,v2,v3))
assert v1['hours']==8 and v3['hours']==6
assert v1['steps']==v2['steps']==v3['steps']
conflict=build(profile,v3['goal'],60,'Everything immediately')
assert conflict['status']=='needs_clarification'
show({'revision_history':[{'version':i+1,'hours':v['hours'],'focus':v['focus']} for i,v in enumerate((v1,v2,v3))],'conflict':conflict['questions']})
''','test_final_governance.FinalGovernanceTests.test_clarify_revise_and_apply_plan','A chatbot could answer once. This coordinator returns missing-information questions and stores revised intent. The teaching versions are explicit snapshots; the portal persists versions in SQLite.'),
('Typed_Tools','Tool-using agent','Compute evidence coverage and assessment percentages through typed functions, not prompt arithmetic.','Structured skills and a saved assessment key.','Reject invalid tool arguments; recompute scores; draft a reminder without sending it.','backend/tool_gateway.py; backend/practice_service.py',r'''
from practice_service import grade,validate_answers
required=['Python','SQL','Git','Testing']
score=coverage(['Python','SQL','Python'],required)
assert score==50
expect(ValueError,lambda:coverage('Python',required))
bank=[{'id':'q1','topic':'SQL','prompt':'Which clause filters grouped rows?','options':['WHERE','HAVING','ORDER BY','LIMIT'],'answer':1,'explanation':'HAVING filters groups after aggregation.'}]
answers=validate_answers({'q1':1},bank)
assert grade(bank,answers)['percentage']==100
expect(ValueError,lambda:validate_answers({'q1':True},bank))
draft={'to':'DEMO001','body':'Please practise Git and Testing.','status':'draft','sent':False}
show({'coverage':score,'assessment':grade(bank,answers)['percentage'],'reminder':draft})
assert draft['sent'] is False
''','test_practice.SectionBoundaryTests.test_bank_grading','Coverage is keyword evidence coverage, not hiring probability. The reminder is a draft artifact only; this notebook has no messaging tool.'),
('Reusable_Skills','Reusable typed skills','Compose analysis and report-formatting skills across independent student cases.','Two synthetic resumes and different target roles.','The same two callable skills work for both students; schema violations fail.','backend/analysis_service.py; backend/agent_pipeline.py',r'''
analyse_skill=Skill('analyse_resume',{'text':str,'role':str},lambda text,role:analyse(text,role,digest(text)))
format_skill=Skill('format_summary',{'result':dict},lambda result:{'role':result['target'],'coverage':result['coverage'],'gaps':result['gaps']})
outputs=[]
for student in STUDENTS.values():
 outputs.append(format_skill(result=analyse_skill(text=student['text'],role=student['target'])))
assert outputs[0]['role']!=outputs[1]['role']
assert outputs[0]['gaps']!=outputs[1]['gaps']
expect(ValueError,lambda:analyse_skill(text=123,role='Backend Developer'))
show(outputs)
''','test_agent_pipeline.PipelineTests.test_validator_rejects_missing_task_and_wrong_evidence','The wrapper is an educational typed-skill contract. The calculations are the real portal analyse function; no separate model is invented for each student.'),
('Memory_and_Retrieval','Run state versus approved memory','Retrieve similar approved preparation history without leaking another student\'s information.','Synthetic approved/pending report archive and a SQL query.','Correct owner/status/tag filtering, nonzero similarity and immutable historical input.','backend/tool_gateway.py; backend/runtime_service.py',r'''
archive=[{'student':'DEMO001','status':'approved','tags':['backend'],'text':'SQL joins and query testing','id':1},
 {'student':'DEMO001','status':'approved','tags':['backend'],'text':'Git branching workflow','id':2},
 {'student':'DEMO001','status':'pending','tags':['backend'],'text':'SQL SQL SQL','id':3},
 {'student':'DEMO002','status':'approved','tags':['backend'],'text':'SQL joins private other student','id':4}]
before=clone(archive)
matches=retrieve(archive,'DEMO001','SQL joins',tag='backend')
assert matches[0]['id']==1 and matches[0]['similarity']>0
assert {r['id'] for r in matches}=={1,2}
run_state={'draft':clone(matches[0])};run_state['draft']['text']='Changed current draft'
assert archive==before
show({'vector_method':'TF-IDF cosine (not neural embeddings)','retrieved':matches,'archive_unchanged':archive==before})
''','test_runtime.RuntimeTests.test_mcp_schema_memory_scope_and_consent','The notebook demonstrates lexical vector similarity. The website uses lexical Jaccard retrieval; it does not claim a neural embedding index. Current run checkpoints and approved history have distinct lifetimes.'),
('MCP_Connector','Governed MCP-style connector','Swap the evidence source while leaving the consuming agent unchanged.','Identical synthetic profile stored in JSON, SQLite and an API-shaped local adapter.','Source substitution yields identical output; invalid schema, wrong owner and revoked consent fail.','backend/tool_gateway.py',r'''
import tempfile
with tempfile.TemporaryDirectory() as directory:
 path=Path(directory)/'profiles.json';path.write_text(json.dumps({'DEMO001':{'skills':['Python','SQL']}}))
 database=sqlite3.connect(':memory:');database.execute('CREATE TABLE profiles(id TEXT,data TEXT)')
 database.execute('INSERT INTO profiles VALUES(?,?)',('DEMO001',json.dumps({'skills':['Python','SQL']})))
 readers=[lambda student:json.loads(path.read_text())[student],lambda student:json.loads(database.execute('SELECT data FROM profiles WHERE id=?',(student,)).fetchone()[0]),lambda student:{'skills':['Python','SQL']}]
 agent=lambda gateway:coverage(gateway.call('DEMO001','DEMO001')['skills'],['Python','SQL','Git','Testing'])
 gateways=[Connector(reader) for reader in readers]
 assert [agent(g) for g in gateways]==[50,50,50]
 expect(PermissionError,lambda:gateways[0].call('DEMO002','DEMO001'))
 expect(PermissionError,lambda:gateways[0].call('DEMO001','DEMO001',False))
 expect(ValueError,lambda:Connector(lambda _:{}).call('DEMO001','DEMO001'))
 show({'same_agent_results':[agent(g) for g in gateways],'audit':gateways[0].audit})
 database.close()
''','test_runtime.RuntimeTests.test_mcp_schema_memory_scope_and_consent','The API adapter here is simulated and clearly labelled. The regression exercises the real authenticated /api/mcp JSON-RPC endpoint. External MCP client interoperability is not asserted.'),
('Governed_Runtime','Checkpoint, resume and budgets','Recover after an injected failure without repeating successful stages.','A temporary checkpoint file, six-action budget and officer gate.','A new runtime resumes saved work; action budgets, dependencies and approval are enforced.','backend/runtime_service.py',r'''
import tempfile
with tempfile.TemporaryDirectory() as directory:
 path=Path(directory)/'checkpoint.json';runtime=Runtime(path)
 runtime.perform('intake',[],lambda:{'student':'DEMO001'})
 def crash():raise ValueError('Injected connector outage')
 expect(ValueError,lambda:runtime.perform('analysis',['intake'],crash))
 restored=Runtime(path)
 def forbidden():raise AssertionError('Completed intake reran')
 restored.perform('intake',[],forbidden)
 restored.perform('analysis',['intake'],lambda:{'coverage':50})
 expect(PermissionError,lambda:restored.perform('publish',['analysis'],lambda:{'approved':True},human_gate=True))
 restored.perform('publish',['analysis'],lambda:{'approved':True},officer=True,human_gate=True)
 expect(ValueError,lambda:restored.perform('bad',['missing'],lambda:{}))
 limited=Runtime(Path(directory)/'limited.json',budget=0)
 expect(ValueError,lambda:limited.perform('intake',[],lambda:{}))
 show(restored.state)
''','test_runtime.RuntimeTests.test_checkpoint_resume_and_idempotent_publication','The teaching runtime logs inputs/dependencies and results to a temporary file. The portal regression verifies real persisted stage reuse and no duplicate draft publication. This is not a proprietary OpenClaw integration.'),
('Node_Graph','Explicit specialist graph','Inspect and execute the portal\'s dependency graph, including the human review boundary.','Synthetic resume, JD and role.','Six automated stages complete; their dependencies exist; officer review remains pending.','backend/agent_pipeline.py',r'''
r=report();trace=r['trace'];names={node['stage'] for node in trace}
assert len(trace)==7
assert all(set(node.get('dependsOn',[]))<=names for node in trace)
assert trace[-1]['stage']=='Placement officer approval' and trace[-1]['status']=='pending'
print('flowchart TD')
ids={node['stage']:'N'+str(i) for i,node in enumerate(trace)}
for node in trace:
 print(f'  {ids[node["stage"]]}["{node["stage"]}"]')
 for parent in node.get('dependsOn',[]):print(f'  {ids[parent]} --> {ids[node["stage"]]}')
show({'execution':r['execution'],'validation':r['validation']})
assert all(r['validation'].values())
''','test_agent_pipeline.PipelineTests.test_parallel_stages_and_validated_trace','Parallel branches are real Python worker calls. The production runtime owns targeted repair outside the graph function; the diagram shows successful dependencies, not an invented external graph framework.'),
('Parallel_Swarm','Parallel swarm, partial results and reconciliation','Compare serial/parallel student processing, bounded retries and identity-aware merge.','Two synthetic students plus an intentionally unavailable student.','Equal serial/parallel quality, bounded retries, explicit missing coverage and no duplicate student totals.','backend/runtime_service.py; backend/benchmark_swarm.py',r'''
started=time.perf_counter();serial=[report(s) for s in STUDENTS];serial_time=time.perf_counter()-started
started=time.perf_counter();parallel=swarm(list(STUDENTS),report);parallel_time=time.perf_counter()-started
assert [r['coverage'] for r in serial]==[r['report']['coverage'] for r in parallel['results']]
calls={}
def flaky(student):
 calls[student]=calls.get(student,0)+1
 if student=='MISSING' or (student=='DEMO002' and calls[student]==1):raise ValueError('Injected unavailable evidence')
 return report(student)
partial=swarm(['DEMO001','DEMO002','MISSING'],flaky)
assert partial['missing']==['MISSING'] and calls['DEMO002']==2 and calls['MISSING']==2
assert partial['coverage']==2/3
merged,conflicts=merge_versions([{'student':'DEMO001','version':1},{'student':'DEMO001','version':2},{'student':'DEMO002','version':1}])
assert len(merged)==2 and conflicts==['DEMO001'] and merged[0]['version']==2
show({'sequential_seconds':serial_time,'parallel_seconds':parallel_time,'partial_coverage':partial['coverage'],'missing':partial['missing'],'merged':merged,'conflicts':conflicts})
''','test_runtime.RuntimeTests.test_swarm_matches_single_run_quality_and_bounds_workers','Timing is measured, not assumed faster. Identity reconciliation and per-worker retry are notebook extensions; the portal batch has independent student outcomes, two workers and runtime retry support.'),
('Evidence_Grounding','Grounding and evidence','Reject fluent claims that have no located, consented evidence.','Synthetic resume/GitHub evidence records and valid/invalid candidate claims.','Every accepted claim has an owner, source, locator and matching value; missing/drifted evidence fails.','backend/agent_pipeline.py; backend/jd_matching.py',r'''
sources={'resume:demo':{'student':'DEMO001','consent':True,'values':{'skills':['Python','SQL']}},'github:demo':{'student':'DEMO001','consent':True,'values':{'public_repositories':3}}}
claim={'source':'resume:demo','locator':'skills','value':['Python','SQL']}
accepted=ground(claim,sources,'DEMO001')
bad=[{'source':'unverified','locator':'hiring_probability','value':99},dict(claim,value=['Python','SQL','Docker']),dict(claim,locator='salary')]
for candidate in bad:expect(ValueError,lambda c=candidate:ground(c,sources,'DEMO001'))
expect(ValueError,lambda:ground(claim,sources,'DEMO002'))
sources['resume:demo']['consent']=False
expect(ValueError,lambda:ground(claim,sources,'DEMO001'))
show({'accepted_before_revocation':accepted,'rejected_candidates':bad})
''','test_agent_pipeline.PipelineTests.test_validator_rejects_missing_task_and_wrong_evidence','A resume citation proves that the text exists, not that the student mastered a skill. Do not convert profile activity into a guaranteed job, salary or readiness probability.'),
('Ops_Resilience','Diagnose and repair only the failing part','Repair a corrupted evidence row and escalate an irreparable claim.','A valid report, a missing citation and an invented skill.','Exactly the faulty evidence row changes; unrelated rows remain identical; unknown claims exhaust the budget.','backend/runtime_service.py',r'''
baseline=report();broken=clone(baseline)
assert len(broken['evidence'])>=2
broken['evidence'][0]['source']='missing'
fixed,diagnosis=repair(broken,baseline,budget=1)
assert fixed==baseline and len(diagnosis)==1
assert fixed['evidence'][1:]==broken['evidence'][1:]
impossible=clone(baseline);impossible['evidence'].append({'skill':'Unverified Quantum Mastery','source':'invented','excerpt':'Unsupported'})
expect(ValueError,lambda:repair(impossible,baseline,budget=1))
show({'diagnosis':diagnosis,'unrelated_rows_unchanged':True})
''','test_runtime.RuntimeTests.test_targeted_repair_invalidates_only_dependent_stages','The row repair is a teaching model. The website repairs a failed stage and invalidates its dependents, retaining unrelated checkpoints. Neither path fabricates missing source evidence.'),
('SDLC_Factory','Plan as specification and acceptance gate','Derive section/gap acceptance checks from a specification and block incomplete drafts.','Role, required sections and skill gaps from a generated report.','A broken artifact is blocked; fixing it passes; adding a spec clause automatically adds a failing check.','backend/agent_pipeline.py',r'''
artifact=report();spec={'target':artifact['target'],'sections':['structured','evidence','roadmap','jdMatch'],'gaps':artifact['gaps']}
bad=clone(artifact);bad.pop('evidence');bad['roadmap']=[]
expect(ValueError,lambda:gate(bad,spec))
green=gate(artifact,spec)
changed=clone(spec);changed['sections'].append('officerCoverNote')
new_checks=acceptance(artifact,changed)
assert len(new_checks)==len(green['checks'])+1 and not new_checks['section:officerCoverNote']
expect(ValueError,lambda:gate(artifact,changed))
artifact['officerCoverNote']='Review source assumptions before approval.'
assert all(gate(artifact,changed)['checks'].values())
show({'initial_checks':green['checks'],'changed_spec_checks':acceptance(artifact,changed)})
''','test_governance.GovernanceTests.test_validation_failure_blocks_approval','The notebook derives tests from a spec. The portal currently has a fixed acceptance validator; this exercise does not claim that arbitrary spec-derived tests are deployed in the website.'),
('Safety_and_Governance','Approval, privacy, versioning and rollback','Publish only after officer review and restore an earlier version without deleting history.','Two preparation report versions and student/officer actors.','Student approval and cross-student reads fail; rollback restores v1 and preserves v2.','backend/governance_service.py; backend/analysis_service.py',r'''
artifact=report();spec={'target':artifact['target'],'sections':['roadmap','evidence'],'gaps':artifact['gaps']}
governance=Governance()
expect(PermissionError,lambda:governance.publish('DEMO001',artifact,spec))
assert governance.publish('officer',artifact,spec)==1
revision=clone(artifact);revision['roadmap'][0]['task']='Complete a tested project exercise and attach evidence.'
assert governance.publish('officer',revision,spec)==2
expect(PermissionError,lambda:governance.view('DEMO002','DEMO001'))
expect(PermissionError,lambda:governance.rollback('DEMO001',1))
governance.rollback('officer',1)
assert governance.view('DEMO001','DEMO001')==artifact and len(governance.versions)==2
show({'current':governance.current,'retained_versions':len(governance.versions),'audit':governance.audit})
''','test_final_governance.FinalGovernanceTests.test_revision_approval_and_rollback_are_persistent','The real API regression additionally checks persistent report pointers and preparation tracker order. Academic details are self-reported; interview events are review signals, not automatic misconduct findings.'),
('Domain_Specialists','Domain-specific role packs','Apply software, analytics, core-engineering and higher-studies benchmarks with checkable outputs.','Seven portal role packs and sample skill evidence.','Every pack partitions required skills into found/gaps and produces only gap-linked tasks.','backend/analysis_service.py; backend/benchmark_service.py',r'''
outputs=[]
for role,skills in BENCHMARKS.items():
 r=specialist(role,'Skills\n'+', '.join(skills[:2]))
 assert set(r['found']).isdisjoint(r['gaps'])
 assert {t['skill'] for t in r['roadmap']}==set(r['gaps'])
 outputs.append({'role':role,'required':skills,'found':r['found'],'gaps':r['gaps']})
assert len(outputs)==7
expect(ValueError,lambda:specialist('Invented role','Python'))
show(outputs)
''','test_final_governance.FinalGovernanceTests.test_reviewed_benchmark_used_and_expiry_blocks_approval','Sample packs are illustrative until officer-reviewed. These are structured role specialists, not seven separate LLMs. Expired reviewed benchmarks are checked by the production approval API.'),
('Capstone','Integrated Worklet 9 capstone','Connect student evidence, plan, graph, validation, officer review and learning feedback.','A synthetic backend student, a clarified goal and the existing portal components.','One complete request becomes an approved report; scope and human approval are retained.','backend/server.py; backend/agent_pipeline.py; docs/FINAL_TEST_GUIDE.md',r'''
student='DEMO001';profile=clone(STUDENTS[student])
plan=build(profile,'Prepare for backend developer interviews',8,'SQL and project explanation')
assert plan['status']=='ready'
artifact=report(student)
assert all(artifact['validation'].values())
spec={'target':profile['target'],'sections':['roadmap','evidence','jdMatch','practice'],'gaps':artifact['gaps']}
store=Governance();store.publish('officer',artifact,spec)
published=store.view(student,student)
show({'student':student,'plan':plan['weeklySchedule'],'coverage':published['coverage'],'gaps':published['gaps'],'roadmap':published['roadmap'],'current_version':store.current,'stages':published['trace']})
assert len(published['trace'])==7
''','test_api.ApiTests.test_resume_to_approved_report','This is an offline synthetic capstone plus real HTTP integration tests. Camera/audio, live Gemini quality, real public profile imports and the teacher presentation still require the manual guide. No real student records or paid API calls are used.')]

def cell(kind,source):
 source=textwrap.dedent(source).strip()+'\n'
 data={'cell_type':kind,'metadata':{},'source':source.splitlines(keepends=True)}
 if kind=='code':data.update(execution_count=None,outputs=[])
 return data

def main():
 for number,(slug,title,goal,inputs,acceptance,implementation,demo,test,reflection) in enumerate(LABS,1):
  setup="""from pathlib import Path
import sys
folder=Path.cwd()
if not (folder/'lab_support.py').exists():folder=folder/'Assignments'
assert (folder/'lab_support.py').exists(), 'Run from the repository root or Assignments directory'
sys.path.insert(0,str(folder.resolve()))
from lab_support import *
print('Worklet 9: offline synthetic demonstration; no Gemini API calls')
"""
  cells=[cell('markdown',f'# Worklet 9 — Placement Readiness & Career Intelligence Portal\n## Lab {number:02d}: {title}\n\n**Team:** {TEAM}\n\n**Problem statement:** Help students understand resume/JD gaps and prepare with auditable, placement-officer-reviewed guidance.\n\n| Item | This lab |\n| --- | --- |\n| Goal | {goal} |\n| Inputs | {inputs} |\n| Deliverable | Executable demonstration, assertions and recorded output |\n| Acceptance | {acceptance} |\n\nRun top to bottom from this repository. The notebook imports `lab_support.py` and existing backend modules; it is independent of other notebooks, but is not a standalone Colab upload. All examples use synthetic data.'),cell('markdown','### 1. Environment and scope\n\nOnly local code and disposable fixtures are used. Dependencies: Python 3.11+ and the repository backend requirements. No secrets, real student records, or reference-notebook outputs are copied.'),cell('code',setup),cell('markdown','### 2. Worklet-specific implementation and experiment\n\nThe following code executes the stated scenario and deliberately exercises rejection paths where relevant.'),cell('code',demo),cell('markdown',f'### 3. Acceptance checks against the actual portal\n\nThe demonstration asserts its own contract above. This additional test calls the project implementation using disposable fixtures. Implementation references: `{implementation}`.'),cell('code',f"regression_result=regressions('{test}')\nshow(regression_result)"),cell('markdown',f'### 4. Results, reflection and limits\n\n{reflection}\n\nThe output above is generated by execution, not an expected-output transcription. If any assertion or regression fails, this notebook is not accepted.\n\n### 5. Deliverables and next step\n\n- This executed notebook and its assertion output.\n- Shared original teaching helpers in `lab_support.py`.\n- Relevant production code and regression mapping above.\n- Full sequence and provenance in `Assignments/README.md`.\n\n'+('Continue to Lab '+str(number+1)+' to build on this contract.' if number<14 else 'Use the complete test guide for a live student/officer demonstration; do not label synthetic tests as real-user validation.'))]
  notebook={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'},'worklet':9,'execution_policy':'offline synthetic fixtures'},'cells':cells}
  for i,c in enumerate(cells):c['id']=f'lab{number:02d}-cell{i:02d}'
  path=HERE/f'LAB_{number:02d}_Worklet9_{slug}.ipynb'
  path.write_text(json.dumps(notebook,indent=1,ensure_ascii=False)+'\n',encoding='utf-8')
 print('Generated',len(LABS),'original Worklet 9 notebooks.')

if __name__=='__main__':main()
