[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("ch04", "ch05", "ch07", "ch08", "ch09", "ch10", "ch11")]
    [string]$Chapter
)

$ErrorActionPreference = "Stop"
$kitRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$practiceRoot = Join-Path $kitRoot "practice-workspace"
$chapterRoot = Join-Path $practiceRoot $Chapter
$script:failed = $false

function Write-Check([bool]$Condition, [string]$Message) {
    if ($Condition) { Write-Host "PASS    $Message" -ForegroundColor Green }
    else {
        Write-Host "FAIL    $Message" -ForegroundColor Red
        $script:failed = $true
    }
}

$required = @{
    ch04 = @("AGENTS.md", "README.md", "inputs/requirements_brief.md", "inputs/unsafe_tenant_query.py", "inputs/debug_case.md")
    ch05 = @("AGENTS.md", "sql/README.md", "sql/00_initialize_lab.sql", "sql/99_reset_lab.sql")
    ch07 = @("AGENTS.md", "README.md", "requirements.txt")
    ch08 = @("AGENTS.md", "README.md", "project/AGENTS.md", "project/database.py", "project/models.py", "project/practice_db.py", "project/_starter/database.py", "project/_starter/models.py")
    ch09 = @("erp-mini/domain/__init__.py", "erp-mini/routers/__init__.py", "erp-mini/services/__init__.py", "erp-mini/tests/__init__.py")
    ch10 = @("erp-mini/db.py", "erp-mini/schema.sql", "erp-mini/server.py", "erp-mini/sql/00_initialize_lab.sql", "erp-mini/sql/99_reset_lab.sql")
    ch11 = @("workspace/erp-project/requirements.txt", "workspace/frontend-project/package.json", "workspace/_starter/App.vue", "workspace/sql/00_initialize_lab.sql", "workspace/sql/99_reset_lab.sql")
}

Write-Check (Test-Path -LiteralPath $chapterRoot -PathType Container) "$Chapter root exists"
foreach ($relativePath in $required[$Chapter]) {
    Write-Check (Test-Path -LiteralPath (Join-Path $chapterRoot $relativePath)) "$Chapter/$relativePath"
}

if ($Chapter -eq "ch08") {
    $chapterRulesPath = Join-Path $chapterRoot "AGENTS.md"
    $projectRulesPath = Join-Path $chapterRoot "project/AGENTS.md"
    $rulesVersion = "common-rules-version: chapter8-v3"
    $requiredMarkers = @("approval-required", "secrets-protected", "evidence-scoped")

    if ((Test-Path -LiteralPath $chapterRulesPath) -and (Test-Path -LiteralPath $projectRulesPath)) {
        $chapterRules = Get-Content -Raw -Encoding UTF8 -LiteralPath $chapterRulesPath
        $projectRules = Get-Content -Raw -Encoding UTF8 -LiteralPath $projectRulesPath
        Write-Check ($chapterRules.Contains($rulesVersion)) "ch08 common rules version"
        Write-Check ($projectRules.Contains($rulesVersion)) "ch08/project common rules version"
        foreach ($marker in $requiredMarkers) {
            Write-Check ($chapterRules.Contains($marker)) "ch08 rule marker: $marker"
            Write-Check ($projectRules.Contains($marker)) "ch08/project rule marker: $marker"
        }
        Write-Check ($chapterRules.Contains("Mock") -and $projectRules.Contains("Mock")) "ch08 Mock evidence boundary"
        Write-Check ($chapterRules.Contains("테스트 없음") -and $projectRules.Contains("테스트 없음")) "ch08 test-missing verdict"
    }
}

if ($Chapter -in @("ch05", "ch10", "ch11")) {
    Write-Host "NOT RUN database execution requires a dedicated disposable lab database" -ForegroundColor Yellow
}

if ($Chapter -in @("ch07", "ch08", "ch09", "ch10", "ch11")) {
    Write-Host "INFO    Preview reset targets with: .\tools\reset_practice_chapter.ps1 -Chapter $Chapter"
}

if ($script:failed) { exit 1 }
Write-Host "$Chapter static verification passed." -ForegroundColor Green
