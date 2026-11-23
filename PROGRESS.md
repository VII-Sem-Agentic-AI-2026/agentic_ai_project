# Project progress

Project folder: `C:\Users\DELL\Documents\Codex\2026-11-16\see\outputs\placement-portal`

Files are saved locally. No GitHub repository has been connected or pushed.

## Completed

- [x] Read teacher requirements and workflow diagrams.
- [x] Document all 14 labs and agreed assessment/interview features.
- [x] Create project folders, README, ignore rules and environment example.
- [x] Implement initial approval/publication/rollback domain rules.
- [x] Run seven domain tests successfully.

## Next implementation milestone

- [ ] Database persistence and migrations.
- [ ] USN/password authentication and faculty permissions.
- [ ] Student and faculty interface foundations.
- [ ] Consent and profile intake.

## Remaining milestones

- [ ] Resume parsing and profile correction.
- [ ] Coding-platform connector and role benchmark library.
- [ ] Gemini integration and specialist agents.
- [ ] Coordinator graph, memory, checkpoints and parallel swarm.
- [ ] Evidence validation and targeted repair.
- [ ] Preparation roadmap and progress tracking.
- [ ] Aptitude and technical assessments.
- [ ] Isolated coding assessment execution.
- [ ] AI project and HR interviews.
- [ ] Microphone, transcription and private video recordings.
- [ ] Faculty review, corrections and versioned publication through the API.
- [ ] Full browser and integration testing.
- [ ] Deployment documentation and GitHub readiness verification.

This checklist records verified progress, not background activity. The frontend and complete application are not running yet.

## Latest development update

- [x] Local SQLite persistence and account provisioning.
- [x] Password hashing, expiring cookie sessions and logout.
- [x] Student profile and consent form with persistent saves.
- [x] Faculty submissions page with backend role checks.
- [x] Responsive login and workspace interface.
- [x] Nine automated tests passing; JavaScript syntax check passing.
- [x] Local preview server launched at http://localhost:8000.
- [ ] Browser visual verification and account walkthrough.

The earlier next-milestone list is partially implemented by this local slice. Database migrations and production authentication hardening remain pending. No AI analysis, resume upload or assessment execution is implemented yet.
`nTheme updated: navy login panel, slate text, light grey workspace and blue controls.

Account setup milestone: first-officer setup, officer-only student creation, duplicate-ID rejection, role escalation prevention, and ten passing tests. Refresh the local preview to begin setup.

Student self-registration implemented: students choose their USN/password; public registration always creates a student, regardless of submitted role. Officer setup is separate and one-time. Eleven automated tests pass.

## Resume and preparation report sprint

- [x] Consented PDF/DOCX/TXT resume upload, size validation and text extraction.
- [x] Resume text preview and re-upload workflow.
- [x] Seven sample role benchmarks and evidence-linked keyword comparison.
- [x] Gap-linked weekly preparation tasks.
- [x] Persistent reports and officer review queue.
- [x] Approve/release and request-corrections actions.
- [x] Student draft hiding, ownership checks and consent-withdrawal access checks.
- [x] Pending report invalidation after profile/resume updates.
- [ ] Browser visual verification: blocked by browser permission gate.

See docs/SPRINT_TEST_GUIDE.md. This sprint implements a deterministic preparation workflow; it does not complete the proposed AI-agent architecture.

## Structured resume and coding profiles sprint

- [x] Sectioned personal, academic, project, experience and skill views.
- [x] Optional GitHub account/URL with separate consent.
- [x] Concurrent public GitHub and LeetCode adapters.
- [x] Coding difficulty counts, available activity, GitHub language/repository summaries.
- [x] Private-calendar fallback and honest provider failure states.
- [x] Source-labelled project briefs in combined reports.
- [x] Consent-aware source display and snapshot invalidation.
- [x] Live public-account smoke checks for both providers.

See docs/SPRINT_3_TEST_GUIDE.md. Semantic Gemini analysis and assessments remain pending.

## Resume boundaries and practice assessment sprint

- [x] Fixed PROJECTS & EXPERIENCE boundary on the saved resume.
- [x] Retained full project descriptions, separate from technical skills.
- [x] Aptitude and software-fundamentals question banks.
- [x] Timed persistent attempts, saved selections and resume-after-refresh.
- [x] Server-side marking, explanations and topic feedback.
- [x] Student attempt history and officer review of practice.
- [x] Latest practice evidence and weak-topic tasks in newly generated reports.
- [ ] Formal assessments, isolated coding execution and AI interviews remain pending.

Test instructions: docs/SPRINT_4_TEST_GUIDE.md. Browser visual verification remains unconfirmed.

Sprint verification: 31 automated tests passed; frontend JavaScript syntax check passed; local preview restarted.

## JD comparison and export sprint

- [x] Optional JD field under Target Role.
- [x] JD text and explainable coverage after Profile Summary.
- [x] Missing-skill suggestions, matched excerpts and project-level JD comparison.
- [x] JD gaps included in newly generated preparation roadmaps.
- [x] Approved-report plain-text download.

Test guide: docs/SPRINT_5_TEST_GUIDE.md. Matching is deterministic document evidence coverage, not Gemini or a hiring probability.

Verification: all 37 prior tests passed; the new JD API integration test also passed (38 distinct tests total). JavaScript syntax check passed.

## Mock interview sprint

- [x] Private persistent five-turn interview sessions and history.
- [x] Role/project-aware opening questions and project follow-up.
- [x] Clearly labelled guided practice without a key.
- [x] Backend Gemini structured-feedback adapter and local .env loading.
- [x] Separate transcript and AI-provider consent.
- [x] Optional browser microphone transcription and spoken questions, with typed fallback.
- [ ] Live Gemini verification awaits configured credentials.
- [ ] Browser microphone verification and private video recording remain pending.

See docs/SPRINT_6_TEST_GUIDE.md.

Interview verification: 42-test full suite passed, followed by 7 interview/provider tests including 3 new validation cases (45 distinct tests). Frontend syntax check passed. Live Gemini and microphone still need verification.

## Camera-on interview update

- [x] Side-by-side live camera and question panel.
- [x] Camera + microphone required to start recording and advance questions.
- [x] Private ordered media uploads, finalisation and authenticated playback.
- [x] Optional transcript recognition; recorded speech works without transcription in guided mode.
- [x] Tab/camera/microphone events available for human review.
- [ ] Actual browser media capture/playback verification pending.

See docs/VIDEO_INTERVIEW_TEST_GUIDE.md. This is basic recorded proctoring, not automated cheating detection.

Camera entry fix: Video interview is now the primary action; text-only practice is in a separate collapsed section. Static assets are versioned and served without caching. Syntax and served-file checks passed; actual camera capture still needs browser verification.

Voice-first layout update: current question inside the live camera panel, Start answering and Next question controls, no transcript form in the active screen. Added window-focus review event alongside tab/device events. Browser media verification remains pending.

## Interview layout and ten-question sprint

- [x] Clear camera view left, compact top-right question card.
- [x] Ten prompts based on saved role, resume projects and JD/skills.
- [x] Dynamic question counters preserve older session compatibility.
- [x] Visible live-device status and camera playback fallback.
- [x] Direct Gemini audio answer transcription/evaluation, with separate consent and size limits.
- [x] Voice-only guided sessions require neither typing nor browser recognition.
- [ ] Live browser camera/audio and Gemini verification still pending.

Updated test guide: docs/VIDEO_INTERVIEW_TEST_GUIDE.md.

Validation: all 51 automated tests passed; JavaScript syntax check passed; restarted local server and verified updated HTML/JS served over HTTP. Actual browser camera/microphone capture and live Gemini calls remain unverified.

## Sprint 8: recording recovery and preparation tracking

- [x] Fixed comma-containing WebM codec metadata corrupting recording uploads.
- [x] Raw-byte base64 encoding and bounded upload chunks.
- [x] Failed uploads retain bytes and sequence for retry; final-save failures keep the session available for recovery.
- [x] Answer retries reconcile with server state when a response was lost.
- [x] Approved roadmap tracker with saved status, evidence notes and completion counts.
- [x] Placement officer read-only progress view, student scope checks and audit records.
- [x] 55 Python tests and four JavaScript upload regression tests passed; JavaScript syntax check passed.
- [ ] Live camera/audio playback and Gemini remain user-browser verification steps.

Test flow: docs/SPRINT_8_TEST_GUIDE.md. Core agent orchestration, MCP, swarm and isolated coding execution requirements remain outstanding; this sprint does not complete the full capstone.

## Sprint 9: mandatory Gemini interviews and officer evaluation

- [x] Removed new guided/text-only starts and mode selectors; missing provider configuration blocks start.
- [x] Versioned technical/project/behavioural rubrics with resume project/skill and JD context.
- [x] Four validated Gemini scores, strengths, missing concepts and illustrative answers.
- [x] Transcript confirmation; correction reevaluation preserves the original text.
- [x] Cached draft retries avoid repeating the same audio evaluation.
- [x] Aggregated scores, partial/unscorable labels and preparation suggestions.
- [x] Placement officer results list, detailed answers and audited review notes/history.
- [x] Updated README and environment example to match the implemented application.
- [ ] Gemini credentials are absent; live AI accuracy and browser media verification remain pending.

Test flow: docs/SPRINT_9_TEST_GUIDE.md. Agent orchestration/MCP/swarm/coding execution remain outstanding.

Sprint 9 verification: 63 backend tests and four recording-upload tests passed; frontend syntax passed. Provider tests use mocks. Gemini configuration was checked without exposing credentials and is absent.

## Officer-managed Gemini connection

- Added officer-only masked key entry and Save & test connection; no model selector.
- Windows DPAPI encrypts saved settings; same-account restarts reload them.
- Successful setup enables student interviews immediately. Failed replacement preserves the previous key.
- Student read/write access is denied; status responses and audit records never contain the key.
- Automatic model is gemini-3.8-flash, checked against official documentation.
- Real-key and live audio verification remain pending until the officer enters a key.

Test flow: docs/OFFICER_GEMINI_SETUP.md.

Verification: all 70 backend tests passed, including seven new provider-setting/encryption checks. Frontend syntax and served asset checks passed. Live provider acceptance awaits the officer's key.

Connection repair: accept dotted auth-key format; distinguish provider availability failures from invalid credentials. Try gemini-3.5-flash once if the primary model is unavailable; save only a successfully verified model/key pair. Ten provider-setting tests pass. Live checks authenticated model listing successfully, but generation timed out on the primary and the fallback returned HTTP 503 high demand. No successful live interview evaluation has been claimed or credential saved by these diagnostics.

## Specialist orchestration foundation sprint

- Explicit coordinator, resume/JD, coding, assessment, preparation and acceptance stages.
- Parallel resume/JD and coding execution, bounded to two concurrent report runs.
- Stored successful-run trace with dependencies, durations, run ID and workflow version.
- Validation checks complete gap coverage, task grounding and current-resume evidence before review.
- Cached sources respect current consent/account; publication rechecks resume digest and profile.
- Preparation tasks merge overlapping gaps and assessment evidence.
- Officer/student report detail displays trace and acceptance checks.
- Durable failed-run checkpoints, MCP, memory, repair and swarm remain pending.

Test flow: docs/SPRINT_11_TEST_GUIDE.md.

Verification: 77 backend tests passed, including actual parallel-stage execution, stale-consent exclusion and validation rejection. Frontend syntax passed. Local server restarted with the updated workflow.

## Sprints 12 and 13: runtime recovery and coding

- Persistent run and stage checkpoints, evidence fingerprints, bounded retry budgets and atomic draft publication.
- One targeted repair invalidates the faulty stage and its descendants; completed unrelated stages remain reusable.
- Authenticated typed tool gateway with local MCP-style JSON-RPC discovery and calls.
- Same-student approved memory retrieval; role/consent boundaries enforced by the gateway.
- Officer batch analysis of up to eight students with two report workers, independent outcomes and progress polling.
- Disposable sequential/parallel benchmark with output-equivalence checks.
- Python coding workspace: saved code, 30-minute attempts, sample runs, hidden-test submission and officer results.
- Docker runner: no network/host mounts, read-only root, non-root user, CPU/memory/process/output/time limits.
- Coding weaknesses feed newly generated preparation reports.

Manual test guide: docs/SPRINTS_12_13_TEST_GUIDE.md. Full external MCP interoperability and autonomous LLM planning are not claimed by this deterministic runtime.

Verification: 86-test backend suite passed; five coding tests then passed including one additional hidden-output privacy regression (87 distinct backend tests covered). Four recording-upload JavaScript tests and frontend syntax checks passed. Live Docker tests verified a correct solution against five cases, syntax errors, time/output limits, blocked network and read-only root writes. An HTTP coding submission in a temporary database produced the expected 2/5 score and added Arrays to the next preparation report. No real student records were used for these checks.

Four-student benchmark: sequential 1.357 s, two-worker parallel 1.784 s, equivalent coverage/gaps/roadmaps and all validations passing. This fixture has no remote latency; no parallel speedup is claimed.

## Final implementation sprints: planning, governance and delivery

- Saved clarify/plan/revise preparation plans, weekly time allocation, optional validated Gemini advice and plan-bound report intake.
- Seven officer-reviewable benchmark packs with source, version and expiry; expired reviewed evidence cannot be newly approved or restored.
- Immutable officer report revisions, explicit current publication, audited rollback and current roadmap ordering.
- Consent history, report/run metrics and audit viewer; tracker reads respect revoked resume consent.
- Recording playback auditing and explicit owner/officer deletion after completed interviews.
- Windows startup/verification scripts, local diagnostics, source release scan, Windows/Linux GitHub Actions configuration and consolidated manual test guide.

Verification: full backend suite passed 93 tests. The final full suite includes publication ordering and revoked-consent tracker regression coverage. Provider responses in automated tests are mocked; real Gemini connection and browser camera/audio remain manual acceptance work. This is a local demo release, not a publicly hardened deployment.

Start with docs/FINAL_TEST_GUIDE.md. Historical sprint guides remain for implementation history.

## Gemini generation extension

New interviews generate ten questions through Gemini. Three bounded adaptive follow-up slots preserve technical/HR coverage. Consented AI preparation plans generate activities from resume, JD, coding evidence and assessment weaknesses; subsequent report activities use Gemini while preserving validated gap coverage and officer approval. UI explains external processing consent. Provider failures do not silently become template outputs.

Verification: 98-test full suite passed, then 24 targeted governance/interview tests passed including one additional generation-failure regression (99 distinct tests). JavaScript syntax passed. Live Gemini generation and camera/browser acceptance still require configured credentials.

## Personalised practice assessments

New aptitude/technical attempts are generated by Gemini from each student's consented resume excerpts, role and JD. Ten-question schema validation, private saved answer keys, immutable attempt questions, generation outside database write transactions, evidence-change checks, consent enforcement and failure without template fallback are implemented. Existing attempts remain resumable. Results clearly identify AI answer-key limitations.

Verification: 103 backend tests passed, JavaScript syntax passed, source scan passed, restarted portal returned HTTP 200 with updated assets. Provider tests are mocked; live Gemini personalisation and content correctness still need acceptance testing.
