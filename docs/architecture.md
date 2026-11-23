# Architecture and implementation order

## Proposed components

React/TypeScript frontend; Python/FastAPI API and workers; PostgreSQL persistence; private file storage; server-side Gemini adapter. Dependency versions will be selected and locked when services are installed.

All agents access sources through a typed authenticated connector. The coordinator owns a locked plan, budgets, checkpoints and audit references. Specialist outputs include typed payloads, evidence references, warnings and provenance. Resume extraction precedes concurrent skill-gap and coding analytics; matching joins both results. Validation failures route to bounded targeted repair. Approved immutable report versions are the student-facing publication boundary.

Gemini handles extraction, question generation and rubric explanations. Deterministic tools calculate objective scores and eligibility. Model output is untrusted input and must pass schemas and evidence validation. Documents and resumes are data, not executable instructions.

HTTP identity must come from authenticated server sessions. Domain actor objects must never be constructed from client-supplied roles. Every student resource query is scoped by owner and authorised faculty assignment. The initial in-memory domain model is a unit-test foundation; transactional persistence and assignment-based access remain necessary.

## Delivery sequence

1. Repository, requirements and governance domain tests.
2. Database migrations, account provisioning, password/session controls and consent.
3. Student/faculty UI shell and upload/profile workflow.
4. Connector adapters, benchmarks and specialist agents.
5. Runtime graph, checkpoint recovery, evidence and bounded swarm.
6. Practice and formal aptitude, technical and isolated coding assessments.
7. Gemini project/HR interview, microphone, transcription and private video.
8. Faculty corrections, approval, publication, roadmap exports and rollback.
9. Failure injection, browser workflows, integration checks, deployment and GitHub handoff.

## External configuration required for final verification

Gemini credentials; permitted coding-platform connectivity; approved benchmark/job data; real student case with consent; deployment database and private storage; isolated coding execution service. A college academic-account integration additionally requires a documented college API. Manual/imported records remain supported.
