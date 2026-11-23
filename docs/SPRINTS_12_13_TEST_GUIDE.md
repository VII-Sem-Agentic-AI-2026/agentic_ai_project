# Sprints 12 and 13: runtime and coding assessments

## Runtime, tools and report memory

1. Refresh the portal. As a student, save a profile, resume and JD, then generate a preparation report.
2. Open **Agent runs & memory**. Check the run status and saved specialist stages.
3. As placement officer, approve the generated report. As student, search approved report memory by role or skill. Pending reports and other students' history must not appear.
4. As officer, open **Agent runs & memory**, select up to eight consented student profiles, and start batch analysis. Two report workers run at a time. Each student retains an independent result/error and review gate.
5. Refresh status or wait for automatic refresh. Inspect resulting drafts under Reports & preparation.
6. A failed/interrupted run can be resumed up to three run attempts. Completed stages are reused only if the evidence fingerprint is unchanged. Changed input requires a new run. The same request ID never publishes a second report.

The runtime checkpoints stage outputs in SQLite. There is one automatic targeted validation repair per execution, plus one retry for transient stage exceptions. Source reads use an authenticated typed tool gateway. Same-student approved memory uses lexical Jaccard matching, not embeddings.

The local `/api/mcp` endpoint implements JSON-RPC `initialize`, `ping`, `tools/list`, `tools/call` and initialized notifications for the tool gateway. It uses the portal's session cookie and same-origin protections. This is an MCP-style tool interface, not a claim of full Streamable HTTP/OAuth interoperability with arbitrary external clients. Its schema and tool-call envelopes follow the [MCP tools specification](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-06-18/server/tools.mdx).

Run `python benchmark_swarm.py` from backend for a comparison using a disposable database. The benchmark checks equal coverage, gaps, roadmaps and validation; it reports measured timings and does not assume parallel execution is faster for small inputs.

## Coding assessment

1. Ensure Docker Desktop is running with Linux containers. Install the runner image once with `docker pull python:3.12-alpine`.
2. As student, open **Coding assessments**, select one of the three Python exercises and start. The attempt lasts 30 minutes.
3. Write Python that reads JSON from standard input and prints one JSON value. Click Save code before leaving. Reopening the attempt restores saved code and its original deadline.
4. Run sample to test the visible case. Sample success is not a final score.
5. Submit final answer. The backend executes sample and hidden cases in separate containers and saves the result. Repeating the same final submission returns the existing result.
6. As placement officer, open Coding assessments to view the student's code and results. Officers cannot change the student's submission.
7. Generate a new preparation report after submission. Coding topics with failed tests should appear in the assessment evidence and preparation tasks.

Three initial exercises cover arrays, strings and hash maps. Python is the only supported language in this sprint. Tests are deterministic and evaluated by execution, not Gemini. Hidden inputs and expected outputs are never included in student API responses.

Containers have no network, no host mounts, a read-only root, an unprivileged user, dropped capabilities, 64 MB memory, half a CPU, a 32-process limit, capped output and a 12-second wall-time limit per case. Docker resource controls are documented [here](https://docs.docker.com/engine/containers/resource_constraints). These controls support local development; production hostile multi-tenant execution requires separate worker infrastructure and operational hardening.

Docker unavailability never creates a fabricated zero score. Code remains saved and the user receives a retryable infrastructure error. Existing Gemini availability issues are separate from coding execution.

Verified locally: the full 86-test suite, five updated coding tests (one new privacy case), four JavaScript upload tests, live Docker limit tests, and an HTTP submission-to-preparation-report integration. The benchmark produced equivalent outputs for four students: 1.357 seconds sequential versus 1.784 seconds with two workers on the local fixture. Browser layout and interactive microphone use still need user testing.

## Remaining project work

These sprints implement a deterministic governed runtime and a local isolated Python assessment flow. Full external MCP client compatibility, autonomous LLM coordinator planning/clarification, full teacher-lab acceptance demonstrations, production deployment, retention/deletion controls and final documentation still need completion. Live Gemini interview evaluation also remains a separate verification requirement.
