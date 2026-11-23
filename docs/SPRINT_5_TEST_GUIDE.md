# Sprint 5 — Job description matching and report export

## Included

- Optional job description text field directly below Target Role, capped at 15,000 characters.
- JD comparison immediately after Profile Summary in Resume workspace.
- Original pasted JD displayed verbatim as escaped text.
- Equal-weight percentage: recognised required/unspecified JD skills with resume evidence divided by all recognised required/unspecified skills.
- Preferred requirements displayed separately from the main percentage.
- Matching resume excerpts and corresponding JD excerpts.
- Brief missing-skill learning suggestions and per-project coverage.
- Unrecognised requirements, experience and qualification clauses retained for human review. No numeric score is invented when no requirements are recognised.
- Newly generated reports snapshot the JD comparison and add missing JD skills to preparation tasks.
- Approved reports can be downloaded as plain-text files. Pending student reports remain inaccessible. Export uses the already authorised, consent-filtered report returned by the API.

## Test flow

1. In Profile & preferences paste this below Target Role: `Required: Python, SQL and Docker. React preferred.` Save.
2. Open Resume workspace. After Profile Summary, inspect the JD text, coverage, evidence and brief learning suggestions.
3. If the resume mentions Python and SQL but not Docker, expected recognised required-skill coverage is 2/3 = 67%. React is preferred and does not alter this percentage.
4. Inspect each project. Only skills mentioned in that project's title/description count for its project coverage; skills listed elsewhere do not count for the project.
5. Change or clear the JD and save. The workspace comparison should immediately reflect the saved JD.
6. Generate a new preparation report with the desired JD. The officer should see the JD snapshot and additional missing-skill tasks.
7. Approve, sign in as the student and download the approved report from Reports & preparation.

## Interpretation and limits

The student-visible JD comparison is explicitly an unreviewed personal document comparison requested by the student, not a published placement readiness score. Official preparation report publication still requires officer approval. Existing approved reports retain their historical JD.

Matching is vocabulary/keyword-based, not Gemini semantic analysis. Equivalent wording, negation and mixed preferred/required clauses can be ambiguous. Percentages do not measure hiring probability, years of experience, eligibility, code quality or verified skill mastery. Raw resume text and pasted JDs are treated as data, escaped before display.

Coding execution, Gemini interviews, microphone/video and production hardening remain unfinished. Browser visual verification remains blocked by the previous permission denial.

