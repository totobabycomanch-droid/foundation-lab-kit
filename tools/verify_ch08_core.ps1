[CmdletBinding()]
param()

# Chapter 8 Core completion check (read-only).
# Runs the two Core test files, confirms the order route is registered,
# and reads the local chapter8.db values with the kit's practice_db.py.
# It does not create application files, send HTTP requests, or read .env.
# Core requires project/.env to be absent, so the script stops before importing
# the application when that file exists.

$ErrorActionPreference = "Stop"
$kitRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$chapterRoot = Join-Path $kitRoot "practice-workspace/ch08"
$projectRoot = Join-Path $chapterRoot "project"
$venvPython = Join-Path $chapterRoot ".venv/Scripts/python.exe"
$script:failed = $false

function Write-Check([bool]$Condition, [string]$Message, [string]$Hint = "") {
    if ($Condition) { Write-Host "PASS    $Message" -ForegroundColor Green }
    else {
        Write-Host "FAIL    $Message" -ForegroundColor Red
        if ($Hint) { Write-Host "        $Hint" -ForegroundColor Yellow }
        $script:failed = $true
    }
}

function Invoke-Python([string[]]$PythonArgs) {
    # Native stderr must not stop the script; judge by exit code instead.
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $env:PYTHONIOENCODING = "utf-8"
    try {
        $output = & $venvPython @PythonArgs 2>&1 | ForEach-Object { "$_" }
        return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = @($output) }
    }
    finally { $ErrorActionPreference = $previous }
}

function Invoke-PythonSource([string]$Source) {
    # Windows PowerShell 5.1 can split a multi-line `python -c` argument.
    # Base64 keeps the source in one ASCII-only argument without writing a temp file.
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Source))
    $launcher = "import base64;exec(base64.b64decode('$encoded'))"
    return Invoke-Python @("-c", $launcher)
}

# 1. Environment and files
$envReady = Test-Path -LiteralPath $venvPython
Write-Check $envReady "ch08/.venv Python exists" "Create the virtual environment first (manuscript: Chapter 8 Python environment)."
if (-not $envReady) { Write-Host "ch08 core verification failed." -ForegroundColor Red; exit 1 }

$localEnv = Join-Path $projectRoot ".env"
$localEnvAbsent = -not (Test-Path -LiteralPath $localEnv)
Write-Check $localEnvAbsent "project/.env is absent for the local SQLite Core" "Do not open or print .env. Stop the server and move the file outside the kit as described in the manuscript."
if (-not $localEnvAbsent) { Write-Host "ch08 core verification failed." -ForegroundColor Red; exit 1 }

$requiredFiles = @(
    "services/franchise_order.py",
    "repositories/franchise_order.py",
    "routers/franchise_order.py",
    "main.py",
    "tests/test_change.py",
    "tests/test_persist.py"
)
foreach ($relativePath in $requiredFiles) {
    Write-Check (Test-Path -LiteralPath (Join-Path $projectRoot $relativePath)) "project/$relativePath exists"
}
if ($script:failed) {
    Write-Host "ch08 core verification failed. Finish the missing steps first." -ForegroundColor Red
    exit 1
}

Push-Location $projectRoot
try {
    # 2. Core tests
    foreach ($testFile in @("tests/test_change.py", "tests/test_persist.py")) {
        $result = Invoke-Python @("-m", "pytest", "-q", "-p", "no:cacheprovider", $testFile)
        $last = ($result.Output | Where-Object { $_.Trim() } | Select-Object -Last 1)
        Write-Check ($result.ExitCode -eq 0) "$testFile result: $last" "Run it directly in project/ and read the full output: python -m pytest -q $testFile"
    }

    # Fixed business checks keep Core verification meaningful even when readers
    # organize their pytest cases differently.
    $orderContract = @'
from dataclasses import FrozenInstanceError

from services.franchise_order import (
    CHANGE_ERROR_HTTP_STATUS,
    FranchiseOrderChangeError,
    decide_franchise_order,
    parse_franchise_order_event,
)


def expect_error(payload, expected_http):
    try:
        parse_franchise_order_event(payload)
    except FranchiseOrderChangeError as exc:
        assert CHANGE_ERROR_HTTP_STATUS.get(exc.code) == expected_http
    else:
        raise AssertionError(f"request was accepted: {payload!r}")


valid = parse_franchise_order_event(
    {"franchise_id": 1, "prod_code": " A001 ", "qty": 5}
)
assert (valid.franchise_id, valid.prod_code, valid.qty) == (1, "A001", 5)
try:
    valid.qty = 99
except FrozenInstanceError:
    pass
else:
    raise AssertionError("request object is mutable")

for invalid in (
    {"franchise_id": 1, "prod_code": "A001", "qty": 0},
    {"franchise_id": 1, "prod_code": "A001", "qty": -1},
    {"franchise_id": 1, "prod_code": "A001", "qty": "5"},
    {"franchise_id": 1, "prod_code": "A001", "qty": True},
    {"franchise_id": 1, "prod_code": "A001"},
    {"franchise_id": 1, "prod_code": "  ", "qty": 5},
    {"franchise_id": 1, "prod_code": 1001, "qty": 5},
    {"franchise_id": 1, "qty": 5},
    {"franchise_id": 0, "prod_code": "A001", "qty": 5},
    {"franchise_id": "1", "prod_code": "A001", "qty": 5},
    {"franchise_id": True, "prod_code": "A001", "qty": 5},
    {"prod_code": "A001", "qty": 5},
):
    expect_error(invalid, 400)

plan = decide_franchise_order(
    valid, stock_qty=100, unit_price=1000, deposit=50000
)
assert (plan.qty, plan.total_price, plan.order_status) == (5, 5000, 10)
for stock_qty, deposit in ((5, 50000), (100, 5000), (5, 5000)):
    boundary = decide_franchise_order(
        valid, stock_qty=stock_qty, unit_price=1000, deposit=deposit
    )
    assert boundary.total_price == 5000

try:
    decide_franchise_order(valid, stock_qty=4, unit_price=1000, deposit=4999)
except FranchiseOrderChangeError as stock_error:
    assert CHANGE_ERROR_HTTP_STATUS.get(stock_error.code) == 409
    stock_error_code = stock_error.code
else:
    raise AssertionError("stock shortage was accepted")

try:
    decide_franchise_order(valid, stock_qty=100, unit_price=1000, deposit=4999)
except FranchiseOrderChangeError as deposit_error:
    assert CHANGE_ERROR_HTTP_STATUS.get(deposit_error.code) == 409
    assert deposit_error.code != stock_error_code
else:
    raise AssertionError("deposit shortage was accepted")

print("request and decision contract passed")
'@
    $result = Invoke-PythonSource $orderContract
    $last = ($result.Output | Where-Object { $_.Trim() } | Select-Object -Last 1)
    Write-Check ($result.ExitCode -eq 0) "request and decision contract: $last" "Check request validation, boundary values, shortage decisions, and HTTP status mapping."

    # 3. Route registration
    $registration = "from main import app; assert 'post' in app.openapi()['paths']['/franchise/order']"
    $result = Invoke-Python @("-c", $registration)
    Write-Check ($result.ExitCode -eq 0) "POST /franchise/order is registered in the app" "Check main.py includes the order router. Output: $($result.Output | Select-Object -Last 1)"

    # 4. Database values after exactly one order from the initial values
    $dbReady = Test-Path -LiteralPath (Join-Path $projectRoot "chapter8.db")
    Write-Check $dbReady "chapter8.db exists" "Run: python practice_db.py prepare, then send the order once (manuscript 8.5)."
    if ($dbReady) {
        $result = Invoke-Python @("practice_db.py", "show")
        $text = ($result.Output -join " ")
        if ($result.ExitCode -eq 0 -and $text -match "=(\d+)\s.*?=(\d+)\s.*?=(\d+)") {
            $stock = [int]$Matches[1]; $deposit = [int]$Matches[2]; $orders = [int]$Matches[3]
            Write-Check ($stock -eq 95 -and $deposit -eq 45000 -and $orders -eq 1) "DB values after one order: stock=$stock deposit=$deposit orders=$orders (expected 95 / 45000 / 1)" "Expected values assume the initial 100 / 50000 / 0 and exactly one order of quantity 5. If the start differs, see the manuscript section on re-preparing the local DB only."
        }
        else {
            Write-Check $false "practice_db.py show output could not be read" "Run it directly: python practice_db.py show"
        }
    }
}
finally { Pop-Location }

if ($script:failed) {
    Write-Host "ch08 core verification failed." -ForegroundColor Red
    exit 1
}
Write-Host "ch08 core verification passed." -ForegroundColor Green
