[CmdletBinding()]
param(
    [ValidateRange(1024,65535)][int]$Port = 8308,
    [string]$PythonExecutable = 'python'
)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    & $PythonExecutable -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)"
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 or newer is required.' }
    & $PythonExecutable -B (Join-Path $PSScriptRoot 'web_server.py') --port $Port
    if ($LASTEXITCODE -ne 0) { throw 'Server stopped with an error. Check the port and Python files.' }
} finally { Pop-Location }
