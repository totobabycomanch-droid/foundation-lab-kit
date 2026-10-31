[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port = 8310)
$ErrorActionPreference = 'Stop'
$project = Join-Path $PSScriptRoot 'erp-mini'
$python = Join-Path $project '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Create erp-mini/.venv and install requirements.txt first.' }
Push-Location $project
try { & $python -m uvicorn lab_app:app --host 127.0.0.1 --port $Port --reload }
finally { Pop-Location }
