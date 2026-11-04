[CmdletBinding()]
param(
    [string]$PythonExecutable = '',
    [ValidateSet('all', 'db', 'http', 'build')]
    [string]$Only = 'all'
)

$ErrorActionPreference = 'Stop'
$backend = (Resolve-Path (Join-Path $PSScriptRoot '../practice-workspace/ch11/workspace/erp-project')).Path
if (!$PythonExecutable) {
    $localPython = Join-Path $backend 'venv/Scripts/python.exe'
    if (Test-Path -LiteralPath $localPython -PathType Leaf) { $PythonExecutable = $localPython }
    else { $PythonExecutable = 'python' }
}
$arguments = @((Join-Path $backend 'verify_core.py'))
if ($Only -ne 'all') { $arguments += @('--only', $Only) }
& $PythonExecutable @arguments
exit $LASTEXITCODE
