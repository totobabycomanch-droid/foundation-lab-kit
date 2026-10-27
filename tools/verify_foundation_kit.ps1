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
        $package = Get-Content -LiteralPath $packagePath -Raw -Encoding UTF8 | ConvertFrom-Json
        $lockText = Get-Content -LiteralPath $lockPath -Raw -Encoding UTF8
        $lockName = [regex]::Match($lockText, '(?m)^\s*"name"\s*:\s*"([^"]+)"').Groups[1].Value
        Write-Check ($package.name -eq $lockName) "$Label package and lock identify the same project"
    }
}

Write-Host "Foundation Lab Kit: $kitRoot"

$requiredPaths = @(
    "chapter-reference/ch10/schema.sql",
    "chapter-reference/ch10/server.py",
    "chapter-reference/ch10/seed.sql",
    "chapter-reference/ch11/approve_order.sql",
    "chapter-reference/ch11/main.py",
    "chapter-reference/ch11/ApproveOrder.vue",
    "chapter-reference/ch11/App.vue",
    "chapter-reference/ch11/README.md",
    "practice-workspace/ch11/observation_record.md",
    "practice-workspace/AGENTS.md",
    "practice-workspace/README.md",
    "practice-workspace/ch03/AGENTS.md",
    "practice-workspace/ch03/README.md",
    "practice-workspace/ch03/start_lab.ps1",
    "practice-workspace/ch03/verify_observation.py",
    "practice-workspace/ch03/observation-baseline.json",
    "practice-workspace/ch03/requirements.txt",
    "practice-workspace/ch03/package.json",
    "practice-workspace/ch03/package-lock.json",
    "practice-workspace/ch03/backend/__init__.py",
    "practice-workspace/ch03/backend/app.py",
    "practice-workspace/ch03/backend/models.py",
    "practice-workspace/ch03/backend/store.py",
    "practice-workspace/ch03/backend/order_write.py",
    "practice-workspace/ch03/backend/order_replay.py",
    "practice-workspace/ch03/backend/company_read.py",
    "practice-workspace/ch03/backend/lab_auth.py",
    "practice-workspace/ch03/frontend/index.html",
    "practice-workspace/ch03/frontend/app.js",
    "practice-workspace/ch03/frontend/order-form.js",
    "practice-workspace/ch03/frontend/order-transport.js",
    "practice-workspace/ch03/frontend/company-probe.js",
    "practice-workspace/ch03/frontend/style.css",
    "practice-workspace/ch03/_starter/backend/order_write.py",
    "practice-workspace/ch03/_starter/backend/order_replay.py",
    "practice-workspace/ch03/_starter/backend/company_read.py",
    "practice-workspace/ch03/_starter/frontend/order-form.js",
    "practice-workspace/ch04/AGENTS.md",
    "practice-workspace/ch04/.gitignore",
    "practice-workspace/ch04/README.md",
    "practice-workspace/ch04/start_lab.ps1",
    "practice-workspace/ch04/requirements.txt",
    "practice-workspace/ch04/package.json",
    "practice-workspace/ch04/package-lock.json",
    "practice-workspace/ch04/verify_observation.py",
    "practice-workspace/ch04/backend/__init__.py",
    "practice-workspace/ch04/backend/app.py",
    "practice-workspace/ch04/backend/lab_auth.py",
    "practice-workspace/ch04/backend/store.py",
    "practice-workspace/ch04/frontend/index.html",
    "practice-workspace/ch04/frontend/app.js",
    "practice-workspace/ch04/frontend/transport.js",
    "practice-workspace/ch04/frontend/style.css",
    "practice-workspace/ch04/_starter/backend/approval_rules.py",
    "practice-workspace/ch04/_starter/frontend/approval-action.js",
    "practice-workspace/ch04/lessons/01_requirement.md",
    "practice-workspace/ch04/lessons/02_role.md",
    "practice-workspace/ch04/lessons/03_state.md",
    "practice-workspace/ch04/lessons/04_company.md",
    "practice-workspace/ch04/backend/defect_rules.py",
    "practice-workspace/ch04/backend/defect_approval.py",
    "practice-workspace/ch04/_starter/backend/defect_scope.py",
    "practice-workspace/ch04/observation-baseline.json",
    "practice-workspace/ch04/backend/approval_rules.py",
    "practice-workspace/ch04/frontend/approval-action.js",
    "practice-workspace/ch04/backend/defect_scope.py",
    "practice-workspace/ch05/AGENTS.md",
    "practice-workspace/ch05/README.md",
    "practice-workspace/ch05/sql/README.md",
    "practice-workspace/ch05/reference/README.md",
    "practice-workspace/ch05/reference/01_current_and_history.sql",
    "practice-workspace/ch05/reference/02_relationship_and_delete.sql",
    "practice-workspace/ch06/.env.tools.example",
    "practice-workspace/ch07/AGENTS.md",
    "practice-workspace/ch07/README.md",
    "practice-workspace/ch07/understanding/AGENTS.md",
    "practice-workspace/ch07/understanding/README.md",
    "practice-workspace/ch07/understanding/reference/transaction_example.py",
    "practice-workspace/ch07/understanding/reference/sale_example.py",
    "practice-workspace/ch07/understanding/reference/test_examples.py",
    "tools/verify_ch07_core.ps1",
    "practice-workspace/ch08/ai_build_rules.md",
    "practice-workspace/ch08/ai_review_rules.md",
    "practice-workspace/ch08/chapter8_order_spec.md",
    "practice-workspace/ch08/understanding/AGENTS.md",
    "practice-workspace/ch08/understanding/README.md",
    "practice-workspace/ch08/understanding/checks/test_order_rules.py",
    "practice-workspace/ch08/understanding/reference/order_example.py",
    "practice-workspace/ch08/understanding/reference/test_order_example.py",
    "tools/verify_ch08_core.ps1",
    "practice-workspace/ch09/README.md",
    "practice-workspace/ch09/erp-mini/domain/__init__.py",
    "practice-workspace/ch09/checks/test_order_rules.py",
    "practice-workspace/ch09/reference/order.py",
    "practice-workspace/ch09/reference/test_order.py",
    "practice-workspace/ch09/reference/README.md",
    "tools/verify_ch09_core.ps1",
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
Test-PackageLock (Join-Path $practiceRoot "ch03") "Chapter 3 Vue lab"
Test-PackageLock (Join-Path $practiceRoot "ch04") "Chapter 4 Vue lab"
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
