[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$kitRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$practiceRoot = Join-Path $kitRoot "practice-workspace"
$script:failed = $false

function Write-Check([bool]$Condition, [string]$Message) {
    if ($Condition) {
        Write-Host "PASS    $Message" -ForegroundColor Green
    }
    else {
        Write-Host "FAIL    $Message" -ForegroundColor Red
        $script:failed = $true
    }
}

function Test-Command([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        Write-Host "NOT RUN $Name is not available" -ForegroundColor Yellow
    }
    else {
        Write-Host "PASS    $Name is available"
    }
}

function Test-PackageLock([string]$FrontendRoot, [string]$Label) {
    $packagePath = Join-Path $FrontendRoot "package.json"
    $lockPath = Join-Path $FrontendRoot "package-lock.json"
    if ((Test-Path -LiteralPath $packagePath) -and (Test-Path -LiteralPath $lockPath)) {
        $package = Get-Content -LiteralPath $packagePath -Raw | ConvertFrom-Json
        $lockText = Get-Content -LiteralPath $lockPath -Raw
        $lockName = [regex]::Match($lockText, '(?m)^\s*"name"\s*:\s*"([^"]+)"').Groups[1].Value
        Write-Check ($package.name -eq $lockName) "$Label package and lock identify the same project"
    }
}

Write-Host "Foundation Lab Kit: $kitRoot"

$requiredPaths = @(
    "practice-workspace/AGENTS.md",
    "practice-workspace/README.md",
    "practice-workspace/ch04/AGENTS.md",
    "practice-workspace/ch05/sql/README.md",
    "practice-workspace/ch06/.env.tools.example",
    "practice-workspace/ch07/requirements.txt",
    "practice-workspace/ch08/project/database.py",
    "practice-workspace/ch08/project/models.py",
    "practice-workspace/ch09/erp-mini/domain/__init__.py",
    "practice-workspace/ch10/erp-mini/db.py",
    "practice-workspace/ch10/erp-mini/schema.sql",
    "practice-workspace/ch11/workspace/erp-project/requirements.txt",
    "practice-workspace/ch11/workspace/frontend-project/package.json",
    "practice-workspace/ch11/workspace/frontend-project/package-lock.json",
    "reference-app/AGENTS.md",
    "reference-app/README.md",
    "reference-app/review-workspace/ch03/AGENTS.md",
    "reference-app/review-workspace/ch03/README.md",
    "reference-app/review-workspace/ch03/expected-verdict.md",
    "reference-app/review-workspace/ch03/ai-verdict-template.md",
    "reference-app/review-workspace/ch03/comparison-template.md",
    "reference-app/backend/requirements.txt",
    "reference-app/backend/app/models/company.py",
    "reference-app/backend/app/routers/company.py",
    "reference-app/backend/app/routers/purchase.py",
    "reference-app/backend/tests/conftest.py",
    "reference-app/backend/tests/test_day05_company_master.py",
    "reference-app/backend/tests/test_day18_http_contract.py",
    "reference-app/database/day01_bootstrap.sql",
    "reference-app/database/fn_process_purchase_receipt.sql",
    "reference-app/frontend/package.json",
    "reference-app/frontend/package-lock.json",
    "reference-app/frontend/src/views/admin/CompanyMasterView.vue",
    "reference-app/frontend/src/views/store/PurchaseOrderListView.vue",
    "reference-app/frontend/e2e/day05-partner-master.spec.js",
    "reference-app/checkpoints/run_day05_mock_e2e.ps1"
)

foreach ($relativePath in $requiredPaths) {
    Write-Check (Test-Path -LiteralPath (Join-Path $kitRoot $relativePath)) $relativePath
}

$forbiddenNames = @(".env", "node_modules", "dist", "venv", ".venv", "__pycache__")
$forbiddenItems = @(Get-ChildItem -LiteralPath $kitRoot -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $forbiddenNames -contains $_.Name -or (!$_.PSIsContainer -and $_.Extension -in @(".db", ".sqlite", ".sqlite3")) })
Write-Check ($forbiddenItems.Count -eq 0) "generated files and real .env files are absent"
if ($forbiddenItems.Count -gt 0) {
    $forbiddenItems | ForEach-Object { Write-Host "        $($_.FullName)" }
}

Test-PackageLock (Join-Path $practiceRoot "ch11/workspace/frontend-project") "Chapter 11 frontend"
Test-PackageLock (Join-Path $kitRoot "reference-app/frontend") "Reference app frontend"

Test-Command "powershell"
Test-Command "python"
Test-Command "node"
Test-Command "npm"
Test-Command "docker"

if ($script:failed) {
    Write-Host "Foundation Lab Kit verification failed." -ForegroundColor Red
    exit 1
}

Write-Host "Foundation Lab Kit verification passed." -ForegroundColor Green
