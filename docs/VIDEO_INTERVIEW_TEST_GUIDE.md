# Ten-question camera interview

## Current screen

A large, unobstructed camera preview appears on the left. A compact question card sits at the upper right. It shows the current question, its resume/JD topic, Start answering, Next question and Hear question. Device status labels indicate whether camera and microphone tracks are live. On very narrow phone screens the question card stacks below the preview.

## Question plan

New sessions contain ten questions: introduction; first resume project; project follow-up; second project or scaling scenario; four technical topics selected from the JD (or resume skills/fallback topics); teamwork; and a role-specific learning reflection. Prompts are template-based with explicit source labels. With Gemini enabled, the project follow-up adapts to the previous answer. Existing sessions retain their original question count.

## Test flow

1. Save your latest resume, resume consent, target role and JD.
2. Open Interview studio and start a NEW camera interview.
3. Consent to recording and allow camera/microphone access. Confirm your face is visible and both status labels say on.
4. Read the question at the upper right. Click Start answering, speak, then Next question. The recording continues between questions.
5. In guided mode, audio is saved for human review without AI scoring. No browser speech recognition or typing is required.
6. In configured Gemini mode, separately consent to sending spoken answers to Google. Each answer is encoded as audio, transcribed and evaluated by Gemini. Browser speech recognition is no longer required. Keep answers within about two minutes; the per-answer limit is 2 MB.
7. Finish question 10 and wait for the recording-saved message. Reopen the session to review the transcript and recording. The officer can view it too.
8. A temporary tab switch or focus change creates a review event, not a cheating verdict. Camera/microphone interruptions prevent advancing until restored or the interview is ended.

## Verification limits

API tests cover ten-question completion, source selection, audio request construction, response validation, transcript privacy and provider failure. Media tests cover ordered uploads and authenticated retrieval. Actual camera capture, audio quality, playback and live Gemini audio remain unverified in this environment because browser access was previously denied and live credentials have not been verified.

This is a loopback development application with basic recording/event monitoring, not tamper-proof proctoring. Recordings live in ignored runtime/recordings. Production encryption, retention, identity verification and scalable worker coordination remain pending.

Gemini audio reference: https://ai.google.dev/gemini-api/docs/audio
