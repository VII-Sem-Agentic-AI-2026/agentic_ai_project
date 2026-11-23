param([string]$PythonPath = 'python')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $projectRoot 'backend')
try {
    & $PythonPath -m unittest discover -s tests
    if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed' }
} finally { Pop-Location }
Push-Location $projectRoot
try {
    node --check frontend/app.js
    if ($LASTEXITCODE -ne 0) { throw 'Frontend syntax failed' }
    node --check frontend/workspaces.js
    if ($LASTEXITCODE -ne 0) { throw 'Workspace syntax failed' }
    node --test frontend/tests/media-upload.test.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Recording upload tests failed' }
    & $PythonPath scripts/check_release.py
    if ($LASTEXITCODE -ne 0) { throw 'Source release check failed' }
} finally { Pop-Location }
