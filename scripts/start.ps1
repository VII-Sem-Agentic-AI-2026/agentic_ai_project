param([string]$PythonPath = 'python', [ValidateRange(1024,65535)][int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
& $PythonPath (Join-Path $projectRoot 'backend\server.py') --port $Port
exit $LASTEXITCODE
