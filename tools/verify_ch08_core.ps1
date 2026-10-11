[CmdletBinding()]
param([string]$PythonExecutable = "python")

# Read-only completion check for the small example. No DB or HTTP operations.
$ErrorActionPreference = "Stop"
$chapterRoot = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path "practice-workspace/ch08"
$exampleRoot = Join-Path $chapterRoot "understanding"
foreach ($name in @("order_example.py", "test_order_example.py")) {
    if (-not (Test-Path -LiteralPath (Join-Path $exampleRoot $name) -PathType Leaf)) {
        Write-Host "NOT RUN $name is missing. Generate the small example in $exampleRoot first."
        exit 1
    }
}
$previousBytecodeSetting = $env:PYTHONDONTWRITEBYTECODE
$env:PYTHONDONTWRITEBYTECODE = "1"
Push-Location $exampleRoot
try {
    & $PythonExecutable -m unittest -v test_order_example.py
    $testExit = $LASTEXITCODE
    if ($testExit -ne 0) { Write-Host "FAIL    Small example tests"; exit 1 }
    Write-Host "PASS    Small example tests. Confirm the three required cases in the test evidence."
    Write-Host "NOT RUN DB persistence, rollback, HTTP and concurrency are outside this chapter."
}
finally {
    Pop-Location
    $env:PYTHONDONTWRITEBYTECODE = $previousBytecodeSetting
}
