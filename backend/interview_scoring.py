"""Versioned rubric context and deterministic aggregation of Gemini's scores."""
DIMENSIONS=('relevance','clarity','depth','correctness')
CONCEPTS={
 'SQL':'INNER JOIN returns matches; LEFT JOIN preserves left rows and yields NULL for missing right matches; explain a concrete example.',
 'Python':'Mutability, object identity/aliasing, an example such as shared lists or default arguments, and a test demonstrating the bug.',
 'React':'State updates and rendering, component dependencies, measuring renders and justified optimisation.',
 'JavaScript':'Promises, await, asynchronous execution, try/catch and handling API error responses.',
 'Docker':'Image versus container, Dockerfile, configuration/secrets outside the image and health checking.',
 'Machine Learning':'Independent train/test split, avoiding leakage, selecting metrics appropriate to the task.',
 'Testing':'Unit versus integration versus end-to-end boundaries and concrete tests for the chosen feature.',
 'Data Structures':'A suitable structure, lookup complexity, memory cost and relevant trade-offs.',
 'REST APIs':'Resource design, HTTP methods, input validation, status codes and failure handling.',
 'RAG':'Retrieval and generation distinction; retrieval relevance metrics and separate grounded-answer evaluation.',
 'LLMs':'Evidence checking, expressing uncertainty and avoiding unsupported claims.',
 'Git':'Understand conflicting changes, resolve deliberately, run tests and preserve intended behaviour.'}

def resume_evidence(text):
 from resume_structure import structure
 parsed=structure(text)
 lines=['Skills: '+', '.join(parsed['skills'])]
 for project in parsed['projects'][:8]:
  lines.append(project['title']+': '+' '.join(project.get('details',[])))
 return '\n'.join(lines)[:12000]

def context_for(state,index):
 kind='technical' if 4<=index<=7 else 'project' if 1<=index<=3 else 'behavioural'
 criteria={
  'technical':'Check conceptual correctness, reasoning, concrete examples, edge cases and testing. Identify factual errors explicitly.',
  'project':'Check problem, architecture, personal contribution, trade-offs, testing and results. Resume claims are unverified; do not assume they are true.',
  'behavioural':'Check relevant concrete examples, actions, reasoning and reflection. Correctness means internal consistency and answering the question, not a preferred personality.'}
 source=state.get('questionSources',[{}]*10)[index]
 return {'rubricVersion':2,'category':kind,'criteria':criteria[kind],
  'expectedConcepts':CONCEPTS.get(source.get('topic'),'Use the actual question and rubric; accept sound alternative approaches. Flag uncertainty rather than inventing a definitive answer.'),
  'scale':'0: absent/incorrect; 1: major gaps; 2: partly correct; 3: mostly sound with minor gaps; 4: clear, accurate and well supported.',
  'resumeExcerpt':state.get('evidence',{}).get('resume',''),
  'jobDescription':state.get('evidence',{}).get('jd',''),
  'source':source}

def summary(state):
 turns=state.get('turns',[]);scored=[]
 for turn in turns:
  f=turn['feedback']
  if f.get('scorable',True) and all(type(f.get(k)) is int and 0<=f[k]<=4 for k in DIMENSIONS):scored.append(f)
 averages={k:round(sum(f[k] for f in scored)/len(scored),2) for k in DIMENSIONS} if scored else {}
 return {'percentage':round(sum(sum(f[k] for k in DIMENSIONS) for f in scored)/(16*len(scored))*100,1) if scored else None,
  'dimensions':averages,'scored':len(scored),'answered':len(turns),'total':len(state['questions']),
  'complete':state['status']=='completed' and len(scored)==len(state['questions']),
  'label':'Gemini practice score; arithmetic mean of four 0-4 rubric scores. Unscorable answers excluded. Partial results are not a final interview score.',
  'nextSteps':list(dict.fromkeys(t['feedback']['improvement'] for t in turns))[:10]}
