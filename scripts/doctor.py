"""Print deployment readiness without revealing credentials or student data."""
import sys,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import server,coding_runner
print('Python:',sys.version.split()[0])
print('PDF extraction dependency:',bool(importlib.util.find_spec('pypdf')))
print('Gemini configured:',server.gemini_provider.configured())
print('Coding runner:',coding_runner.status()['message'])
print('Deployment: localhost development/demo server; public hosting needs production hardening.')
