"""Ten bounded interview prompts grounded in saved resume and JD evidence."""
from resume_structure import structure
from jd_matching import compare
TECH={
 'Python':'Explain mutable versus immutable objects in Python. Describe a bug this distinction can cause and how you would test it.',
 'Docker':'How would you containerise your application, manage configuration and check that the container is healthy?',
 'React':'Explain how state updates trigger rendering in React. How would you diagnose an unnecessary re-render?',
 'JavaScript':'Explain promises and async/await. How would you handle a failed API request without freezing the interface?',
 'Machine Learning':'How would you split training and test data to prevent leakage, and choose a suitable evaluation metric?',
 'RAG':'Explain the retrieval and generation stages in a RAG pipeline. How would you test retrieval quality separately from answer quality?',
 'LLMs':'How would you handle an LLM response that is plausible but unsupported by the supplied evidence?',
 'SQL':'Explain INNER JOIN versus LEFT JOIN with an example from an application you could build.',
 'Testing':'Describe unit, integration and end-to-end tests for one feature in your project.',
 'Data Structures':'Choose a data structure for fast lookup in your project. Explain its time and memory trade-offs.',
 'REST APIs':'Design a REST endpoint for your project, including validation, status codes and error handling.',
 'Git':'How would you resolve a merge conflict and verify that neither contributor lost their changes?',
 'PyTorch':'Explain a training loop in PyTorch and how you would detect overfitting.',
 'OCR':'How would you evaluate OCR quality and handle noisy or missing text in a document pipeline?',
 'LangGraph':'How would you represent state, conditional routing and bounded retries in an agent graph?'}

def build_questions(resume,jd,role):
 parsed=structure(resume);projects=parsed['projects'];project=projects[0]['title'] if projects else 'a project you have worked on'
 comparison=compare(resume,jd)
 skills=[r['skill'] for r in comparison.get('requirements',[]) if r['priority']!='preferred']
 jd_skills=set(skills)
 if not skills:
  skills=[r['skill'] for r in compare(resume,'\n'.join(parsed['skills'])).get('requirements',[])]
 if not skills:skills=['Problem Solving','Testing','Data Structures','Communication']
 selected=list(dict.fromkeys(skills))[:4]
 while len(selected)<4:selected.append(next(s for s in ['Testing','Problem Solving','Data Structures','Communication'] if s not in selected))
 q=[f'Introduce yourself and explain how your experience connects to {role}.',f'Your resume lists {project}. Explain the problem, architecture, your personal contribution and the result.',f'In {project}, explain one difficult design trade-off and how you tested the outcome.',f'Compare {projects[1]["title"]} with {project}. What did you learn and which responsibilities were yours?' if len(projects)>1 else f'If {project} had ten times more users or data, what would you measure and improve first?']
 evidence=[{'source':'Target role','topic':role},{'source':'Resume project' if projects else 'General project discussion','topic':project},{'source':'Project follow-up','topic':project},{'source':'Resume projects' if len(projects)>1 else 'Technical scenario','topic':project}]
 for skill in selected:
  q.append(TECH.get(skill,f'Explain a core concept in {skill}, give a concrete example and describe how you would test your solution.'))
  evidence.append({'source':'Job description' if skill in jd_skills else 'Resume skills / practice fallback','topic':skill})
 q.extend(['Describe a disagreement or failure in a team project. What did you do, and what would you do differently?',f'For {role}, which requirement would you prioritise learning next, and how would you demonstrate progress?'])
 evidence.extend([{'source':'Behavioural practice','topic':'Teamwork'},{'source':'Target role and learning plan','topic':role}])
 return q,evidence
