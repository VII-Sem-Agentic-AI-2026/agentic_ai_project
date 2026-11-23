# Recording recovery and preparation progress

## Camera interview regression

1. End the old interview if it is open. Refresh the page so the new upload code loads. An already-open page still runs the old code.
2. Open Interview studio and start a **new camera interview**. Allow camera and microphone access.
3. In guided mode, click Start answering, speak for at least five seconds, and click Next question. The counter should advance and the camera should remain visible.
4. Repeat through ten questions, finish, then open the saved interview and play its recording.
5. Tab away and return during a test interview. Check that a review event appears with the saved recording; this is not a cheating verdict.
6. Optional recovery check: temporarily disconnect the network while recording, then restore it. Retry saving the answer or recording. Keep the page open during recovery: queued recording bytes are held in memory, not durable offline storage.
7. Gemini mode additionally requires backend configuration and explicit audio consent. Check transcription and feedback separately with a real key. Guided mode saves speech without judging its content.

Cause fixed: `FileReader` data URLs can contain `video/webm;codecs=vp8,opus`. Splitting at commas corrupted the base64 payload. The new uploader converts raw bytes directly, splits large blobs into bounded chunks, preserves their sequence on retries and retains failed uploads.

## Preparation tracker

1. Save a profile and resume, then generate a preparation report containing roadmap tasks.
2. As the placement officer, approve the report under Reports & preparation.
3. As the student, open **Preparation tracker**. Only approved reports appear.
4. Set a task to In progress, add a learning note and save. Reload and verify it persists.
5. Set it to Completed with a concrete evidence note of at least ten characters. Verify the completed-task counter changes.
6. Sign in as the placement officer and open Preparation tracker. Verify the student's status and notes are visible but not editable.
7. A different student must not see or edit those tasks. Pending reports must not appear. Each report retains its own task history; a newly generated report does not silently inherit completion.

Completion is self-reported. It does not change the approved report or certify skill mastery. Status changes are recorded in the audit table.

## Automated checks

From `backend`: `python -m unittest discover -s tests`

From the project root: `node --test frontend/tests/media-upload.test.cjs` and `node --check frontend/app.js`

Verification: 55 Python tests and four Node uploader tests passed. Live browser camera playback and live Gemini transcription have not been verified by the coding agent.
