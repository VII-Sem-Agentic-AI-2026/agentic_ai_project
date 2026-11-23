# Sprint 4 — Resume boundaries and practice assessments

## Resume fix

Combined headings such as PROJECTS & EXPERIENCE, numbered headings and spaced-out PROJECTS are recognised. PDF bullet characters are normalised. Project descriptions and wrapped continuation lines are retained under Projects, with full descriptions expandable below each brief. Skills are taken from their own section. Existing uploaded resumes use the new parser immediately; old generated reports remain historical snapshots.

The reported saved resume was checked locally: three project groups, fifteen project-content lines and five skill lines, with no project-content lines in skills. Those private details were not copied into repository fixtures.

## Practice features

- Aptitude: a 12-question original bank covering numerical, logical and verbal fundamentals.
- Technical: a 16-question original bank covering software fundamentals. Core-engineering and higher-studies specialist tests are not implemented.
- Each attempt samples 10 questions, with a 20-minute server-enforced deadline.
- Answers save on selection. Refreshing or leaving the page does not reset time.
- Starting the same category resumes its active attempt.
- Answer keys and explanations are withheld by the API until submission or expiry.
- One mark per correct answer; no negative marking. Unanswered questions receive zero.
- Repeated submissions return the already stored result. Expired attempts grade saved answers; new late answers are ignored.
- Feedback includes answers, explanations and topic-based preparation suggestions.
- Student history is scoped to the current account. Officers can inspect all practice attempts in this single-college prototype, but cannot answer or submit on a student's behalf.
- New preparation reports include each category's latest submitted practice and add tasks for topics answered incorrectly. Readiness coverage remains a separate resume-based metric.

## Test flow

1. Refresh the portal. Open Resume workspace and verify Projects and Technical skills. Expand Full project description to inspect all descriptions. No re-upload is necessary.
2. Open Practice assessments and start aptitude. Answer two or three questions and wait for All answers saved.
3. Refresh, return to Practice assessments and resume. Saved choices should remain and the timer should have continued.
4. Submit. Inspect the score, correct answers, explanations and preparation suggestions. Leaving questions blank is allowed and earns zero for those questions.
5. Return to history and review the submitted attempt. Start technical practice and repeat.
6. Open Resume workspace and generate a new preparation report. The latest submitted attempts and their weak-topic tasks should appear in the officer's report review.
7. Officer: open Practice assessments to inspect student history, then Reports & preparation to approve the updated plan.
8. Student: open Reports & preparation to inspect the newly approved preparation plan.

## Remaining scope

These are learning/practice quizzes, not a secure formal examination. The bank is small and questions can repeat. Gemini, isolated coding execution, conversational interviews, microphone/video, verified company matching and production hardening remain unfinished. Browser visual inspection remains unverified because the earlier local-browser access request was denied. API tests cover persistence, marking, expiry, ownership and immutable submission.
