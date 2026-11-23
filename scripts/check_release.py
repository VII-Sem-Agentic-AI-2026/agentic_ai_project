"""Scan source-only release candidates without printing potential secret contents."""
from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'.git','.venv','node_modules','runtime','__pycache__','.pytest_cache','dist','coverage'}
PATTERNS=[re.compile(r'AQ\.[A-Za-z0-9_-]{35,}'),re.compile(r'AIza[A-Za-z0-9_-]{30,}'),re.compile(r'sk-[A-Za-z0-9_-]{30,}')]
def files():
 for path in ROOT.rglob('*'):
  relative=path.relative_to(ROOT)
  if path.is_file() and not any(part in EXCLUDED for part in relative.parts) and not path.name.startswith('.env') and path.suffix not in ('.pyc','.sqlite3','.db','.log','.zip','.dpapi'):
   yield path
 example=ROOT/'.env.example'
 if example.exists():yield example
def main():
 issues=[];count=0
 for path in files():
  count+=1
  try:text=path.read_text(encoding='utf-8-sig')
  except UnicodeError:continue
  for number,line in enumerate(text.splitlines(),1):
   if any(pattern.search(line) for pattern in PATTERNS):issues.append(f'{path.relative_to(ROOT)}:{number}: possible credential')
 if issues:
  print('\n'.join(issues));return 1
 print(f'Checked {count} source files; no recognised live-key patterns found. Runtime data and local secrets are excluded.');return 0
if __name__=='__main__':sys.exit(main())
