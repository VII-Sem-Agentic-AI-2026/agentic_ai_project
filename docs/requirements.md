# Requirements and verification map

Sources: teacher-provided Chapter 9 (14 pages) and Placement Readiness and Career Intelligence Portal DOCX; additional assessment and interview requirements agreed in the project conversation. Source documents are not redistributed in this repository.

The table records the original acceptance targets. See the release status below for actual implementation and verification. Passing a domain unit test does not establish that a deployed application is secure.

| Requirement | Implementation target | Acceptance evidence |
| --- | --- | --- |
| USN/password student login; separate faculty login | Server sessions, student registration and one-time officer setup, role and student scope | Authentication and cross-student access tests |
| Separate source consent | Versioned consent records and connector enforcement | Revoked/missing consent blocks reads |
| Resume PDF/DOCX intake | Validated upload, extraction, structured profile and correction | Real fixture extraction and unsupported-file handling |
| Coding profile | Backend LeetCode adapter, provenance and import fallback | Live connector verification; timeout and missing-profile tests |
| Academic information | Consented entry/import and verification status | Input and eligibility tests |
| Five to eight role benchmarks | Faculty-reviewed library with sources and dates | Benchmark schema and expiry checks |
| Lab 1: clarify, plan, revise | Coordinator planning loop | Vague request produces at least two clarification questions |
| Lab 2: typed tools | Data readers and score calculators | Calculations reproducible without LLM arithmetic |
| Lab 3: reusable skills | Typed planning and report assembly | Two different cases work without code changes |
| Lab 4: memory and retrieval | Separate run checkpoints, approved history and scoped similarity retrieval | Tag/similarity retrieval and privacy tests |
| Lab 5: MCP-style connector | Authenticated typed source gateway | No agent bypasses connector; source adapter replacement test |
| Lab 6: governed runtime | Budgets, checkpoints, resume and audit | Interrupted run resumes without duplicate publication |
| Lab 7: executable graph | Intake → parallel analysis → matching → interview/roadmap → validation → review | End-to-end draft with explicit transitions |
| Lab 8: swarm | Bounded student fan-out and plan-aligned merge | Sequential/parallel quality, coverage and timing comparison |
| Lab 9: grounding | Evidence IDs attached to output claims | Missing or out-of-scope evidence rejected |
| Lab 10: targeted repair | Failure diagnosis and bounded stage regeneration | Injected faults repaired or escalated |
| Lab 11: acceptance gate | Validation suite before review | Failed validation cannot advance |
| Lab 12: governance | Approval, edits, versions, metrics, rollback | API tests cover immutable revisions, approval, rollback and persistent publication pointers |
| Lab 13: specialists | Software, analytics, core and higher-studies role packs | Domain-specific schemas and benchmark tests |
| Lab 14: capstone | Deployed system and real-case demonstration | Consent → approved report, with audit trail |
| Initial and updated preparation plans | Gap-linked activities and progress | Assessment evidence changes relevant tasks |
| Aptitude and technical tests | Question bank, attempts, timers, deterministic marking | Correct scoring and answer-key confidentiality |
| Coding assessment | Isolated execution provider and hidden tests | Execution limits and actual test results |
| Project/HR interview | Gemini questions, follow-ups and rubric feedback | Session continuity, grounded questions and AI labels |
| Microphone | Consent, capture, transcription and typed fallback | Permission denial and transcription error flows |
| Private interview video | Private storage, scoped playback, retention and access audit | Unauthorised playback rejected; deletion verified |
| Faculty dashboard | Queue, evidence, correction, approval and version history | Student cannot invoke faculty actions |
| GitHub delivery | Ignore rules, examples, locks, CI, setup and demo guide | Clean-clone build, tests and secret review |

## Interpretation decisions

- Follow the explicit hybrid execution section where simplified sequential tables differ: skill-gap analysis and coding analytics run concurrently after profile validation.
- Group letters differ between the illustration and roster; stable agent names define responsibilities.
- The coordinator name describes its role; no proprietary AURA integration is supplied or assumed.
- Dashboard reference values are illustrative, not real student evidence or verified job openings.
- Automated video events are review signals, not proof of misconduct. No facial emotion or personality scoring.
- Faculty approval gates personalised published reports. Generic practice can be available before approval.

## Local demonstration release status

Implemented: authentication and source consent; structured resume extraction; public coding/GitHub connectors; JD matching; seven role packs; preparation reports and progress; aptitude/technical tests; Docker Python assessments; Gemini interview evaluation and private recording; officer review; and the local agent workflow below.

| Labs | Concrete implementation | Verification and limits |
| --- | --- | --- |
| 1–3 | Versioned clarification/planning, typed tools, reusable role/report functions | Vague goal gives at least two questions; revised plan enters the report. Gemini advice is optional; tool/review order is enforced. |
| 4–6 | Durable run/stage checkpoints, same-student approved lexical memory, authenticated MCP-style JSON-RPC gateway | Scope, consent, stale evidence, idempotency and interrupted-run tests. Local MCP-style interface; no claim of general external client interoperability. |
| 7–8 | Parallel analysis graph and two-worker student batches | Equal quality/coverage in disposable sequential/batch benchmark; no speedup claim for the small fixture. |
| 9–11 | Evidence validation, bounded targeted repair, acceptance gate | Injected failure tests and rejected invalid drafts; completed unrelated checkpoints preserved. |
| 12 | Officer revisions, approvals, publication rollback, metrics and audits | Persistent API tests; original evidence unchanged. Current publication is reflected in report/tracker views. |
| 13 | Seven role benchmark packs with officer review, provenance and expiry | Reviewed benchmark used in scoring; expired reviewed benchmark blocks approval/restore. Sample packs are illustrative. |
| 14 | Runnable localhost capstone and complete demo guide | Automated API checks and live Docker execution completed. Real browser/Gemini and teacher presentation acceptance still required. |

Additional delivery evidence: 93 backend tests, four JavaScript upload tests and frontend syntax checks; source-only packaging; CI configuration (remote execution pending). Explicit private-recording deletion is implemented and tested. Automatic retention, media encryption at rest, institutional identity verification and public production deployment remain outside this demo release. Scanned-image OCR and arbitrary resume layouts are not guaranteed. Follow docs/FINAL_TEST_GUIDE.md before presenting the project.
