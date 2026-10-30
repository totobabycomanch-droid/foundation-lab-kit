[CmdletBinding()]
param([string]$PythonExecutable = "python")

# 업무 검사와 제공 로컬 HTTP 연결 검사. 실제 ERP DB에는 연결하지 않는다.
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
    & $PythonExecutable -B -c "import sys, unittest; count = unittest.defaultTestLoader.loadTestsFromName('test_order_example').countTestCases(); print('Generated test cases:', count); sys.exit(0 if count else 1)"
    if ($LASTEXITCODE -ne 0) { Write-Host 'FAIL    No generated tests could be loaded'; exit 1 }
    & $PythonExecutable -m unittest -v test_order_example.py
    $testExit = $LASTEXITCODE
    if ($testExit -ne 0) { Write-Host "FAIL    Small example tests"; exit 1 }
    Write-Host "PASS    Generated example tests."
    & $PythonExecutable -B (Join-Path $exampleRoot "checks/test_order_rules.py")
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL    Fixed order rules"; exit 1 }
    Write-Host "PASS    Fixed order rules. Review actual example calls and generated test evidence separately."
    & $PythonExecutable -B (Join-Path $exampleRoot 'verify_web.py')
    if ($LASTEXITCODE -ne 0) { Write-Host 'FAIL    Provided local connection checks'; exit 1 }
    Write-Host 'PASS    Provided local connection checks (temporary stubs, not ERP API).'
    Write-Host 'SCOPE   Actual ERP API, DB persistence, rollback and concurrency are outside this chapter.'
}
finally {
    Pop-Location
    $env:PYTHONDONTWRITEBYTECODE = $previousBytecodeSetting
}
