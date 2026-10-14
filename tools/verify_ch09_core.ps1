[CmdletBinding()]
param([string]$PythonExecutable = "python")

$ErrorActionPreference = "Stop"
$kitRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$chapterRoot = Join-Path $kitRoot "practice-workspace/ch09"
foreach ($name in @("domain/order.py", "main.py", "tests/test_erp_flow.py")) {
    if (-not (Test-Path -LiteralPath (Join-Path $chapterRoot "erp-mini/$name") -PathType Leaf)) {
        Write-Host "NOT RUN $name is missing. Generate the three practice files first."
        exit 1
    }
}
& $PythonExecutable -B (Join-Path $chapterRoot "checks/test_order_rules.py")
if ($LASTEXITCODE -ne 0) { Write-Host "FAIL    Fixed Order checks"; exit 1 }
Write-Host "PASS    Fixed Order checks (33 tests, including 30 state/action combinations)."
Write-Host "INFO    Review main.py and generated tests separately using the manuscript."
Write-Host "NOT RUN DB, HTTP, concurrent requests and idempotency are outside this example."
