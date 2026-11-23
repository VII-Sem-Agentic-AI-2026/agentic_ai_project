# Sprint test guide

## Student

1. Register with a unique USN and sign in.
2. Select Backend Developer (or another target), enable resume consent and save.
3. Open Resume workspace. Upload a text-based PDF, DOCX or TXT under 2 MB.
4. Inspect extracted text. No claim of verified competency is made.
5. Generate preparation report. Open Reports & preparation: only status should be visible until approved.

## Placement officer

1. Sign in with the separately provisioned officer account.
2. Open Reports & preparation; inspect evidence, sample requirements and roadmap.
3. Request corrections with a note, or approve the report.
4. A report cannot be approved twice. Changes to a student's saved profile or resume supersede pending reports; the student must generate a new one.

## Student after review

1. Sign in again and open Reports & preparation.
2. Approved reports show coverage, resume excerpts and weekly preparation tasks.
3. Correction notes are visible without releasing draft analysis.
4. Withdrawing resume consent hides report access for student and officer. Stored records remain retained locally; this is not a deletion action.

## Current limits

The analysis uses deterministic keyword matching against seven sample role benchmarks. It is not Gemini analysis, readiness scoring, coding-platform verification, company matching or an assessment. PDF OCR, manual extracted-text editing, report export, published-version rollback UI, job-description management, persistent agent runtime and mock interviews are still pending. Initial PDF support uses pypdf. The development HTTP server is loopback-only. Browser visual verification was blocked by the app permission gate; automated API and extraction tests cover this sprint.
