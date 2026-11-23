# Sprint 9: Gemini interview evaluation and officer results

Set GEMINI_API_KEY and GEMINI_MODEL in the project-root .env, restart the backend and refresh the portal. Use a model supporting audio and structured JSON. These settings were absent during development verification; no live Gemini evaluation was performed.

## Student test

1. Save your resume, target role and JD with appropriate consent.
2. Open Interview studio -> Start interview. No mode selector or text-only start form should appear.
3. Accept recording and Gemini processing consent -> Begin interview -> allow camera/microphone.
4. Read the question beside the camera -> Start answering -> speak -> Review spoken answer.
5. Check the transcription and correct misheard words -> Confirm & next question. Corrections are reevaluated and visible to the officer; unchanged text reuses the evaluation.
6. Complete ten questions. Check the overall percentage, four dimension averages, per-question strengths/gaps, illustrative answers and preparation suggestions.
7. Early-ended interviews must show partial results. Unscorable answers must not become zero scores or a full final result.
8. Provider failures must keep the current question available for retry while the page stays open.

## Placement officer test

1. Sign in as the placement officer and open Interview studio.
2. Verify student identity, answered count and Gemini score in the history list.
3. Open a session to view answers, scores, transcription corrections and private recording.
4. Choose Reviewed or Needs follow-up and save a feedback/correction note. Reload and check persistence.
5. Verify the student can read the review but cannot submit officer reviews. Other students must not access this interview.

## Evaluation limits

Gemini assigns correctness, relevance, clarity and depth, each 0-4. The server calculates the mean percentage over scorable answers. Technical answers use expected-concept rubrics; project answers use architecture, contribution, testing and results. Resume claims remain unverified. Behavioural evaluation uses examples, reasoning and reflection, not personality or accent.

Test known correct, partly correct, incorrect and inaudible recordings with a real model and human reviewer before relying on results. Mock provider tests verify data flow, validation and arithmetic, not model accuracy.

Old guided sessions remain readable without invented retroactive scores. Review history and original Gemini scores are retained. Full agent orchestration and isolated coding assessments are not part of this sprint.
