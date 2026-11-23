# Structured resume and connected profile sprint

## What changed

- Resume display is organised into personal details, academics, projects, experience, skills, certifications and achievements. Existing uploaded resumes are organised on read; uploading again is optional.
- Resume descriptions are preserved as brief project summaries. Missing or ambiguous headings are labelled rather than invented. This is heading-based extraction, not Gemini understanding.
- GitHub is optional, accepts a username or profile URL, and requires separate consent. Only public non-fork repository metadata is used. Languages, descriptions, recency and archive status are displayed. Private code, authorship and code quality are not inspected.
- LeetCode returns public accepted-problem counts and activity where available. Private calendars fall back to public counts. Missing activity is shown as unavailable, never zero.
- Public profile calls execute concurrently with fixed destination hosts, response size limits and timeouts.
- Reports include source timestamps, coding summaries and brief projects after the resume analysis. Resume evidence coverage is kept separate from coding counts.
- Officer review still gates report publication. Changing consent removes source access; editing the saved profile clears old sync snapshots.

## Test flow

1. Refresh localhost:8000 and sign in as a student.
2. Profile & preferences: enter LeetCode username/URL. Optionally enter GitHub username/URL. Tick the matching consent checkboxes and save.
3. Resume workspace: upload a PDF/DOCX/TXT (or inspect the existing resume). Confirm personal details, academic details, projects and extra skills appear as sections. Standard resume headings improve recognition.
4. Coding & GitHub: click Sync public profiles. Inspect each source status, solved counts, available activity, languages and repository summaries. Leaving GitHub blank must not block anything.
5. Resume workspace: generate a preparation report. Recent sync data is reused for up to one hour; otherwise consented sources are fetched automatically.
6. Sign in as placement officer. Reports & preparation: inspect the report, including Coding & GitHub analysis and Projects in brief. Approve or request corrections.
7. Sign back in as student. Approved reports now show the combined results and roadmap.
8. Optional failure checks: use a nonexistent account, clear GitHub, or withdraw consent after clearing its username. Errors should be explicit, and unrelated sources should still work.

## Verification and limits

Automated tests cover extraction, URL validation, consent, source errors, private-calendar fallback and the approval workflow. Live smoke tests succeeded against GitHub's public octocat profile and LeetCode's public leetcode profile; these examples are not persisted as student evidence. Browser visual verification remains unavailable following the earlier browser permission denial.

Still pending: Gemini integration, richer semantic extraction, verified company benchmarks, executable agent runtime, coding assessments, interviews, audio/video and production hardening. Source metadata does not verify student ownership or independent competency.

## Provider references

- GitHub repository endpoint: https://docs.github.com/en/rest/repos/repos
- GitHub rate limits: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- LeetCode endpoint reference: https://github.com/LeetCode-OpenSource/vscode-leetcode/blob/master/src/shared.ts
