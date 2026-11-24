# Contributing

## Development setup

Use Python 3.11 or later (Python 3.12 is tested in CI) and Node.js for the frontend upload tests.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate

python -m pip install -r backend/requirements.txt
```

Run the backend from the repository root with:

```bash
python -m backend.app
```

Docker Desktop with Linux containers is required to test isolated coding execution.

## Before submitting

Run the same checks used by CI:

Run Python tests from `backend/`:

```bash
cd backend
python -m unittest discover -s tests
```

Then run the remaining checks from the repository root:

```bash
cd ..
node --check frontend/app.js
node --check frontend/workspaces.js
node --test frontend/tests/media-upload.test.cjs
python scripts/check_release.py
```

## Pull requests

- Keep changes focused and explain the behavior or bug being addressed.
- Add or update tests for functional changes.
- Do not commit credentials, private keys, recordings, databases or generated runtime data.
- Follow the existing Python standard-library style and vanilla HTML/CSS/JavaScript frontend approach.
- Update relevant documentation, including `README.md` and `docs/CHANGELOG.md`, when behavior changes.
