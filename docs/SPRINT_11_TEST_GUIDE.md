# Specialist report workflow

1. Refresh the portal and sign in as a student.
2. Save your profile, target role, JD and source consent. Upload a resume.
3. Optionally sync coding profiles and complete a practice assessment.
4. Generate a new preparation report in Resume workspace.
5. Sign in as placement officer. Open Reports & preparation and inspect the new report.
6. Check the Specialist execution trace: intake, parallel resume/JD and coding stages, assessment evidence, planning, acceptance validation, then pending officer approval.
7. Check that missing role/JD skills have preparation tasks. Overlapping assessment weaknesses should add evidence to the same task rather than duplicate it.
8. Approve the report. As student, view the approved report and its trace, then update tasks in Preparation tracker.
9. Withdraw GitHub consent or change the coding account, generate another report and verify the old cached source is excluded.

Each successful report retains its run ID, stage dependencies, timing and validation results in the stored report snapshot. Exceptions stop publication; failed runs are not yet stored as durable checkpoints. Maximum concurrency is two reports with two parallel specialist workers per report. Existing connector timeouts apply.

This is a deterministic specialist graph. MCP transport, autonomous LLM planning, durable resume/retry checkpoints, scoped memory and multi-student swarm execution are later work. The trace does not claim those capabilities are implemented.
