[CmdletBinding()]
param([string]$PythonExecutable = "python")

$ErrorActionPreference = "Stop"
$kitRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$exampleRoot = Join-Path $kitRoot "practice-workspace/ch07/understanding"
foreach ($name in @("transaction_example.py", "sale_example.py", "test_examples.py")) {
    if (-not (Test-Path -LiteralPath (Join-Path $exampleRoot $name) -PathType Leaf)) {
        Write-Host "NOT RUN $name is missing. Generate the examples in $exampleRoot first."
        exit 1
    }
}
$runner = @"
import sys, unittest
suite = unittest.defaultTestLoader.loadTestsFromName('test_examples')
if suite.countTestCases() == 0:
    print('FAIL: no tests collected')
    sys.exit(1)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
"@
Push-Location $exampleRoot
try {
    & $PythonExecutable -B -c $runner
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL    SQLite example tests"; exit 1 }
    Write-Host "PASS    SQLite tests. Confirm the required DB-state assertions in the evidence."
    Write-Host "NOT RUN PostgreSQL, HTTP, concurrent requests and forced shutdown."
}
finally { Pop-Location }
