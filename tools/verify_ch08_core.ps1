[CmdletBinding()]
param()

# Chapter 8 Core completion check (read-only).
# Runs request/decision, persistence, and API tests; confirms the route; then
# reads product and order master/detail/audit values from the local chapter8.db.
# It does not create application files, send HTTP requests, or read .env.

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
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Source))
    $launcher = "import base64;exec(base64.b64decode('$encoded'))"
    return Invoke-Python @("-c", $launcher)
}

# 1. Environment and required files
$envReady = Test-Path -LiteralPath $venvPython
Write-Check $envReady "ch08/.venv Python exists" "Create the Chapter 8 Python 3.12 virtual environment first."
if (-not $envReady) { Write-Host "ch08 core verification failed." -ForegroundColor Red; exit 1 }

$localEnv = Join-Path $projectRoot ".env"
$localEnvAbsent = -not (Test-Path -LiteralPath $localEnv)
Write-Check $localEnvAbsent "project/.env is absent for the local SQLite Core" "Do not open or print .env. Move it outside the kit before continuing."
if (-not $localEnvAbsent) { Write-Host "ch08 core verification failed." -ForegroundColor Red; exit 1 }

$requiredFiles = @(
    "services/franchise_order.py",
    "repositories/franchise_order.py",
    "routers/franchise_order.py",
    "main.py",
    "tests/test_change.py",
    "tests/test_persist.py",
    "tests/test_api.py"
)
foreach ($relativePath in $requiredFiles) {
    Write-Check (Test-Path -LiteralPath (Join-Path $projectRoot $relativePath)) "project/$relativePath exists"
}
if ($script:failed) {
    Write-Host "ch08 core verification failed. Finish the missing steps first." -ForegroundColor Red
    exit 1
}

$implementationFiles = @(
    "models.py",
    "services/franchise_order.py",
    "repositories/franchise_order.py",
    "routers/franchise_order.py"
)
$implementationText = ($implementationFiles | ForEach-Object {
    Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $projectRoot $_)
}) -join "`n"
$forbiddenMutationPattern = '(?i)\b(deposit|stock_qty|current_balance|credit_limit)\b'
Write-Check (-not [regex]::IsMatch($implementationText, $forbiddenMutationPattern)) "order registration has no stock or balance mutation contract" "Remove the old deposit/stock contract from the Chapter 8 implementation."

Push-Location $projectRoot
try {
    # 2. Core tests
    foreach ($testFile in @("tests/test_change.py", "tests/test_persist.py", "tests/test_api.py")) {
        $result = Invoke-Python @("-m", "pytest", "-q", "-p", "no:cacheprovider", $testFile)
        $last = ($result.Output | Where-Object { $_.Trim() } | Select-Object -Last 1)
        Write-Check ($result.ExitCode -eq 0) "$testFile result: $last" "Run it directly in project/: python -m pytest -q $testFile"
    }

    # Fixed checks keep completion meaningful if readers organize tests differently.
    $orderContract = @'
from dataclasses import FrozenInstanceError

from services.franchise_order import (
    CHANGE_ERROR_HTTP_STATUS,
    FranchiseOrderChangeError,
    ProductSnapshot,
    decide_franchise_order,
    parse_franchise_order_event,
)


def expect_error(action, expected_code, expected_http):
    try:
        action()
    except FranchiseOrderChangeError as exc:
        assert exc.code == expected_code
        assert CHANGE_ERROR_HTTP_STATUS.get(exc.code) == expected_http
    else:
        raise AssertionError(f"expected {expected_code}")


payload = {
    "master": {
        "dept_code": " 10 ",
        "emp_code": " E001 ",
        "delivery_code": 101,
        "is_vat": "2",
        "corp_id": "tampered-corp",
        "partner_id": "tampered-partner",
        "order_status": "60",
        "total_amount": 1,
    },
    "details": [
        {"prod_code": " A001 ", "qty": 5, "unit_price": 1, "total_amount": 5}
    ],
}
valid = parse_franchise_order_event(payload)
assert (valid.dept_code, valid.emp_code, valid.delivery_code, valid.is_vat) == (
    "10", "E001", 101, "2"
)
assert (valid.details[0].prod_code, valid.details[0].qty) == ("A001", 5)
assert not hasattr(valid, "corp_id")
assert not hasattr(valid.details[0], "unit_price")
try:
    valid.details[0].qty = 99
except FrozenInstanceError:
    pass
else:
    raise AssertionError("request object is mutable")

zero_qty = {
    "master": {"dept_code": "10", "emp_code": "E001", "delivery_code": 101, "is_vat": "2"},
    "details": [{"prod_code": "A001", "qty": 0}],
}
expect_error(lambda: parse_franchise_order_event(zero_qty), "invalid_detail", 400)

duplicate = {
    "master": {"dept_code": "10", "emp_code": "E001", "delivery_code": 101, "is_vat": "2"},
    "details": [{"prod_code": "A001", "qty": 5}, {"prod_code": "A001", "qty": 1}],
}
expect_error(lambda: parse_franchise_order_event(duplicate), "duplicate_product", 400)

product = ProductSnapshot(prod_code="A001", unit_price=1000, is_active=True)
plan = decide_franchise_order(valid, products={"A001": product})
assert (plan.corp_id, plan.partner_id, plan.order_status) == ("branch01", "admin", "10")
assert (plan.details[0].net_price, plan.details[0].vat, plan.total_amount) == (5000, 500, 5500)

expect_error(
    lambda: decide_franchise_order(valid, products={}),
    "product_not_found",
    400,
)
expect_error(
    lambda: decide_franchise_order(
        valid,
        products={"A001": ProductSnapshot("A001", 0, True)},
    ),
    "invalid_unit_price",
    409,
)
expect_error(
    lambda: decide_franchise_order(valid, products={"A001": ProductSnapshot("A001", 1000, False)}),
    "product_not_found",
    400,
)
rounding = decide_franchise_order(valid, products={"A001": ProductSnapshot("A001", 201, True)})
assert (rounding.details[0].net_price, rounding.details[0].vat, rounding.total_amount) == (1005, 101, 1106)
print("request and decision contract passed")
'@
    $result = Invoke-PythonSource $orderContract
    $last = ($result.Output | Where-Object { $_.Trim() } | Select-Object -Last 1)
    Write-Check ($result.ExitCode -eq 0) "request and decision contract: $last" "Check the actual request subset, server-owned fields, server price, VAT, and HTTP mapping."

    # 3. Route registration
    $registration = "from main import app; assert 'post' in app.openapi()['paths']['/franchise/order']"
    $result = Invoke-Python @("-c", $registration)
    Write-Check ($result.ExitCode -eq 0) "POST /franchise/order is registered in the app" "Check main.py includes the order router. Output: $($result.Output | Select-Object -Last 1)"

    # 4. Read-only database check after exactly one normal order
    $dbReady = Test-Path -LiteralPath (Join-Path $projectRoot "chapter8.db")
    Write-Check $dbReady "chapter8.db exists" "Run practice_db.py prepare, then send the normal order once."
    if ($dbReady) {
        $databaseContract = @'
from sqlalchemy import func, select

from database import SessionLocal
from models import AuditLog, Product, PurchaseOrder, PurchaseOrderDetail

with SessionLocal() as db:
    product = db.get(Product, "A001")
    order_count = db.scalar(select(func.count()).select_from(PurchaseOrder))
    detail_count = db.scalar(select(func.count()).select_from(PurchaseOrderDetail))
    audit_count = db.scalar(select(func.count()).select_from(AuditLog))
    order = db.scalar(select(PurchaseOrder))
    detail = db.scalar(select(PurchaseOrderDetail))
    audit = db.scalar(select(AuditLog))

    assert product is not None
    assert (product.unit_price, product.is_active) == (1000, True)
    assert (order_count, detail_count, audit_count) == (1, 1, 1)
    assert (order.total_amount, detail.total_amount, audit.total_amount) == (5500, 5500, 5500)
    assert (order.order_status, audit.detail_count) == ("10", 1)

print("product=1000/active orders=1 details=1 audits=1 total=5500")
'@
        $result = Invoke-PythonSource $databaseContract
        $last = ($result.Output | Where-Object { $_.Trim() } | Select-Object -Last 1)
        Write-Check ($result.ExitCode -eq 0) "DB contract after one order: $last" "Run practice_db.py show. The expected clean result is product 1000/active and master/detail/audit 1/1/1 with total 5500."
    }
}
finally { Pop-Location }

if ($script:failed) {
    Write-Host "ch08 core verification failed." -ForegroundColor Red
    exit 1
}
Write-Host "ch08 core verification passed." -ForegroundColor Green
