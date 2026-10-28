[CmdletBinding()]
param([ValidateRange(1024, 65535)][int]$Port = 8305)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    python -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)"
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 or newer is required.' }
    $labPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $labPython)) {
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Virtual environment setup failed.' }
    }
    & $labPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    Write-Host "Open http://127.0.0.1:$Port ; stop with Ctrl+C."
    & $labPython -m uvicorn backend.app:app --host 127.0.0.1 --port $Port --reload --reload-dir backend
    if ($LASTEXITCODE -ne 0) { throw 'Server stopped with an error.' }
}
finally { Pop-Location }
