# Complete project test flow

This guide replaces the historical sprint guides. Use two browser profiles (or a normal and private window) to keep student and placement officer sessions separate.

## Start and configure

1. Install Python 3.11+, then run `python -m pip install -r backend/requirements.txt` from the project root. Run `python backend/server.py` and open http://localhost:8000. Windows users can alternatively run `scripts/start.ps1 -PythonPath <path-to-python>`.
2. For coding assessments, keep Docker Desktop running with Linux containers. Run `docker pull python:3.12-alpine` once. Other workspaces do not require Docker.
3. On a fresh installation, use Initial placement officer setup. Choose your own officer ID and a password of at least 12 characters. Existing installations retain accounts; no fixed password is shipped. The internal faculty role means placement officer.
4. Officer: open Interview scores, paste a fresh Gemini API key and use Save & test connection. Wait for a successful connection result before testing interviews. There is no model selector. Invalid credentials, unavailable models or quota failures must show errors rather than a successful connection. Never commit or share your key.
5. Officer: open Versions & audit. Review the sample benchmark skills for your target role, add a real placement source/review justification and save. Sample benchmarks are labelled illustrative until reviewed.

## Student journey

1. Register a student account with USN and password, then log in.
2. My profile: enter academic details, target role and JD text. Select the relevant consent choices and save. Academic information is self-reported.
3. Resume workspace: upload PDF, DOCX or TXT. Verify personal details, academic details, projects and technical skills. Check JD match, missing skills and project relevance. Correct extracted information where supported; extraction is not guaranteed for every layout or scanned PDF.
4. Coding & GitHub: enter a public LeetCode username and optionally GitHub, with the corresponding consent. Import the profiles and check provenance and project summaries. Private repositories are not imported. External service failures must be reported clearly.
5. Preparation planner: first try a vague goal such as “Help”. Expect clarification questions. Revise to a specific goal such as “Prepare for backend developer interviews using Python, SQL and my project”, set weekly hours and save. Expect a ready plan and a new version. Optional Gemini advice sends the stated goal, role, focus and time budget to Google after consent.
6. Resume workspace: generate the preparation report. The officer’s Agent diagnostics workspace shows completed stages. The report remains pending until officer approval. A plan still requiring clarification blocks report generation.
7. Officer window: review the submission and report evidence, then approve or request changes. Student: refresh Reports & preparation and Preparation tracker. Approved tasks should appear; update a task with a meaningful evidence note.
8. Practice assessments: complete aptitude and technical questions. Check saved results, topic weaknesses and attempt history.
9. Coding assessments: start a Python problem, read the JSON input/output contract, save code, run samples and submit. Final submission closes the attempt and runs hidden tests. Check score and officer visibility. A failed Docker service must not create a made-up score.
10. Generate a new preparation report after assessments to incorporate the new evidence, then have the officer review it.

## Camera and voice interview

1. Use a current Chrome or Edge browser on localhost. Open Interview studio, consent and begin. Allow camera and microphone access. Check that your camera preview is visible with the current question beside it.
2. Answer the displayed resume/JD/project or technical/HR question using Start answering. Stop/review the spoken answer, inspect the transcript and confirm before proceeding. Complete the ten-question sequence.
3. Correct an inaccurate transcript and confirm; the corrected text must be evaluated again. Do not treat AI feedback as a verified answer key.
4. Switch tabs once and return. Check the recorded review event. Such events are not automatic findings of cheating; this project does not claim to detect every form of malpractice.
5. If Gemini fails, retain/retry the answer and check the error. Scores must not be fabricated. Skipped or unscorable answers must be labelled accordingly, and partial results must remain labelled partial.
6. Finish and check per-answer rubric feedback and overall results. Officer: verify the same session in Interview scores, inspect transcript corrections and events, and save review notes.
7. Play the uploaded recording. If upload fails, retry before leaving/refreshing the page. Retry data is held in browser memory and cannot survive page closure.
8. For a disposable finished session, choose Delete recording and confirm. Playback should become unavailable while interview scores remain. Active-session recording deletion is blocked.

## Governance and agent demonstrations

- Officer Versions & audit: revise an approved report's activities and provide a reason. This creates a separate pending version. Approve it, then restore the previous approved version with a reason. Check the Current publication label and preparation tracker ordering. Original evidence and scores must remain unchanged.
- Approved-memory retrieval runs behind the preparation workflow and remains scoped to the student. Pending reports are not approved memory. Students do not need an agent diagnostics screen.
- Officer batch: select up to eight consented students and start analysis. Each student gets an independent result; reports still require review. Two report workers are allowed at a time.
- Recovery: a failed/interrupted run can resume within its three-attempt budget when its evidence is unchanged. Changed evidence requires a new run. Unit tests exercise injected failures and targeted repair without damaging real student data.
- Revoke resume consent and check that reports, memory and tracker data are unavailable through their protected views. Re-consent before continuing.
- Inspect Versions & audit for review, revision, rollback and recording access/deletion events. Consent changes are also stored as versioned history.

## Automated verification and delivery

Run `scripts/verify.ps1 -PythonPath <path-to-python>` on Windows, or run the individual commands in README. Run `python scripts/doctor.py` for local dependency, Docker and Gemini configuration status without displaying secrets.

The release verification covered 93 backend tests, four recording-upload JavaScript tests, JavaScript syntax, live Docker execution/limits and an HTTP coding-to-roadmap flow using disposable data. Provider unit tests use mock responses. Live browser camera/audio and real Gemini scoring remain manual acceptance checks.

The architecture implements a governed specialist graph, durable checkpoints, bounded repair, lexical approved-memory retrieval, local MCP-style tools, and batch fan-out. Optional Gemini planning advice cannot override the fixed tool, consent or review policy. This is not a general external MCP host or an unrestricted autonomous agent.

This is a localhost demonstration project. Public hosting, institution identity verification, encrypted media at rest, automated retention policies and production operations are separate deployment work. Recordings currently remain until explicitly deleted. No GitHub repository has been published automatically. The source ZIP excludes accounts, recordings, keys and runtime data; use it for a clean GitHub upload.

## Gemini generation update

Connect Gemini through the officer portal. In Preparation planner, select the explicit Gemini evidence-processing consent and save a new plan. Check the generated weekly activities. Generate a new report, approve it as officer, and inspect the AI activities in the tracker. Complete assessments and generate another report to include updated weaknesses. Saving a new plan without AI consent restores basic rule planning.

Start a NEW interview to test Gemini-generated questions; existing sessions retain their questions. Questions 3, 6 and 8 can adapt to the preceding scored answer. Ten questions remain, including HR and reflection. A failed generation must display an error without creating a new interview. Live Gemini testing is still needed; automated tests use mocked provider responses.

## Personalised Gemini practice assessments

New aptitude and technical attempts now use Gemini rather than the shared question bank. Students must save a target role and JD, upload a resume with consent, and explicitly consent to sending that context to Google. Technical questions target their skills/projects and role requirements; aptitude keeps quantitative, logical and verbal reasoning with role-relevant scenarios. Each new attempt has ten multiple-choice questions and a 20-minute timer starting after generation.

Gemini supplies questions, answer keys and explanations. The backend validates structure and marks against the saved key; this does not prove the AI answer is factually correct. Answers/explanations remain hidden until submission. Completed results remain visible to the student and officer and feed subsequent preparation reports. Existing attempts retain their original questions. Provider failure saves no new attempt, and changed evidence during generation requires a retry.

Test: connect Gemini as officer; student completes profile/JD/resume; open Practice assessments, select processing consent and start aptitude or technical practice. Submit and review explanations. Start a fresh attempt under another student/role to inspect personalisation. Live Gemini content quality still requires manual acceptance; automated tests mock provider responses.
