# Officer API-key setup test

1. Refresh and sign in as the placement officer.
2. Open Interview scores (the officer Interview studio).
3. Paste your Gemini API key in the masked input. There is no model selector.
4. Click Save & test connection. This makes a small Gemini request and may consume quota.
5. Wait for Connected. On failure, follow the access, quota or network message. A failed replacement preserves the previous key.
6. Sign out and sign in as a student. Start interview should be enabled immediately.
7. Complete a spoken answer and verify transcription and scoring with the actual key.
8. Sign back in as the officer to review scores.
9. Restart the server and verify the connection remains configured. Storage is encrypted for the same Windows user; moving computers/accounts requires reentry.

Automated tests use synthetic secrets and mocked Google responses. Windows encryption round trips are tested locally. Actual provider acceptance and live audio evaluation remain pending until a real key is entered.
