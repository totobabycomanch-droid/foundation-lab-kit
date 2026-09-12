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
    ch08 = @("project/database.py", "project/models.py", "project/_starter/database.py", "project/_starter/models.py")
    ch09 = @("erp-mini/domain/__init__.py", "erp-mini/routers/__init__.py", "erp-mini/services/__init__.py", "erp-mini/tests/__init__.py")
    ch10 = @("erp-mini/db.py", "erp-mini/schema.sql", "erp-mini/server.py", "erp-mini/sql/00_initialize_lab.sql", "erp-mini/sql/99_reset_lab.sql")
    ch11 = @("workspace/erp-project/requirements.txt", "workspace/frontend-project/package.json", "workspace/_starter/App.vue", "workspace/sql/00_initialize_lab.sql", "workspace/sql/99_reset_lab.sql")
}

Write-Check (Test-Path -LiteralPath $chapterRoot -PathType Container) "$Chapter root exists"
foreach ($relativePath in $required[$Chapter]) {
    Write-Check (Test-Path -LiteralPath (Join-Path $chapterRoot $relativePath)) "$Chapter/$relativePath"
}

if ($Chapter -in @("ch05", "ch10", "ch11")) {
    Write-Host "NOT RUN database execution requires a dedicated disposable lab database" -ForegroundColor Yellow
}

if ($Chapter -in @("ch07", "ch08", "ch09", "ch10", "ch11")) {
    Write-Host "INFO    Preview reset targets with: .\tools\reset_practice_chapter.ps1 -Chapter $Chapter"
}

if ($script:failed) { exit 1 }
Write-Host "$Chapter static verification passed." -ForegroundColor Green
