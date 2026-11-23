# Interview sprint

The Interview studio supports five saved rounds: introduction, project explanation, follow-up, teamwork and reflection. Opening questions use the saved target role and first detected resume project (only with resume consent). Completed turns are private to the student and placement officer in this single-college prototype.

## Test without Gemini

1. Refresh the portal and open Interview studio.
2. Select Guided practice and consent to saving the transcript.
3. Start, answer by typing and submit. Guided feedback is a simple checklist, not AI evaluation or a competence score.
4. After the project answer, inspect the follow-up. Complete all five turns.
5. Reopen the completed transcript from history. Officer accounts can inspect the history too.
6. Optional: tick the speech-recognition consent and try Start microphone, speak, Stop microphone, review the text, then submit. Unsupported browsers and denied permission must leave typed answers available.

## Configure Gemini privately

Create `.env` in the project root (already ignored by Git):

```dotenv
GEMINI_API_KEY=your_private_key
GEMINI_MODEL=your_available_gemini_model_id
```

Restart the server. No key is sent to the browser. Select Gemini mode and separately consent to sending interview questions/answers and the target role to Google. Structured feedback includes relevance, clarity and depth (0–4), an improvement suggestion and a project follow-up. Feedback is AI-generated practice guidance and may be wrong. Configuration is not proof the key works; live verification requires a valid key/model and successful interview response.

## Limits

- Guided mode runs now. Gemini is implemented but live calls have not been verified with user credentials.
- Microphone uses browser SpeechRecognition where available; the browser may send audio to its recognition provider. Only reviewed, submitted text is saved by this application.
- No audio or video recording/storage is implemented. Camera proctoring is not implemented.
- Unsubmitted text is not saved on refresh. Completed turns are checkpointed in SQLite.
- Provider errors preserve the current turn and allow retry; there is no silent substitution with guided feedback.
- Local development serialises interview mutations to avoid duplicate turns; this is not a production multi-worker concurrency design.
- Browser visual and microphone verification remain unavailable due to the earlier browser permission denial.

Provider reference: https://ai.google.dev/api/generate-content

