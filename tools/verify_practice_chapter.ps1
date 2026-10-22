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
    ch05 = @("AGENTS.md", "README.md", "sql/README.md", "reference/README.md", "reference/01_current_and_history.sql", "reference/02_relationship_and_delete.sql")
    ch07 = @("AGENTS.md", "README.md", "understanding/AGENTS.md", "understanding/README.md", "understanding/reference/transaction_example.py", "understanding/reference/sale_example.py", "understanding/reference/test_examples.py")
    ch08 = @("AGENTS.md", "README.md", "ai_build_rules.md", "ai_review_rules.md", "chapter8_order_spec.md", "understanding/AGENTS.md", "understanding/README.md", "understanding/checks/test_order_rules.py", "understanding/reference/order_example.py", "understanding/reference/test_order_example.py", "../../tools/verify_ch08_core.ps1")
    ch09 = @("AGENTS.md", "README.md", "run.ps1", "erp-mini/AGENTS.md", "erp-mini/domain/__init__.py", "erp-mini/routers/__init__.py", "erp-mini/services/__init__.py", "erp-mini/tests/__init__.py", "checks/test_order_rules.py", "reference/order.py", "reference/test_order.py", "reference/README.md", "../../tools/verify_ch09_core.ps1")
    ch10 = @("erp-mini/db.py", "erp-mini/schema.sql", "erp-mini/server.py", "erp-mini/sql/00_initialize_lab.sql", "erp-mini/sql/99_reset_lab.sql")
    ch11 = @("workspace/erp-project/requirements.txt", "workspace/frontend-project/package.json", "workspace/_starter/App.vue", "workspace/sql/00_initialize_lab.sql", "workspace/sql/99_reset_lab.sql")
}

Write-Check (Test-Path -LiteralPath $chapterRoot -PathType Container) "$Chapter root exists"
foreach ($relativePath in $required[$Chapter]) {
    Write-Check (Test-Path -LiteralPath (Join-Path $chapterRoot $relativePath)) "$Chapter/$relativePath"
}

if ($Chapter -eq "ch05") {
    $rulesPath = Join-Path $chapterRoot "AGENTS.md"
    if (Test-Path -LiteralPath $rulesPath) {
        $rules = Get-Content -Raw -Encoding UTF8 -LiteralPath $rulesPath
        Write-Check ($rules.Contains("common-rules-version: chapter5-v4")) "ch05 staged execution rules version"
    }
    $sqlPath = Join-Path $chapterRoot "reference/02_relationship_and_delete.sql"
    if (Test-Path -LiteralPath $sqlPath) {
        $sql = Get-Content -Raw -Encoding UTF8 -LiteralPath $sqlPath
        $previousEnd = 0
        foreach ($stage in 1..3) {
            $startPattern = '(?m)^-- \[구간 ' + $stage + ' 시작\].*$'
            $endPattern = '(?m)^-- \[구간 ' + $stage + ' 끝\].*$'
            $starts = [regex]::Matches($sql, $startPattern)
            $ends = [regex]::Matches($sql, $endPattern)
            $valid = $starts.Count -eq 1 -and $ends.Count -eq 1
            if ($valid) {
                $valid = $starts[0].Index -ge $previousEnd -and $ends[0].Index -gt $starts[0].Index
            }
            Write-Check $valid "ch05 stage $stage has one ordered, non-overlapping boundary pair"
            if (-not $valid) { continue }
            $body = $sql.Substring($starts[0].Index, $ends[0].Index - $starts[0].Index)
            $previousEnd = $ends[0].Index + $ends[0].Length
            $begins = [regex]::Matches($body, '(?m)^BEGIN;\s*$')
            $commits = [regex]::Matches($body, '(?m)^COMMIT;\s*$')
            $transaction = $begins.Count -eq 1 -and $commits.Count -eq 1
            if ($transaction) { $transaction = $begins[0].Index -lt $commits[0].Index }
            Write-Check $transaction "ch05 stage $stage has one explicit transaction"
            $checks = [regex]::Matches($body, '(?m)^\s*RAISE EXCEPTION\b')
            $checksBeforeCommit = $transaction -and $checks.Count -gt 0
            if ($checksBeforeCommit) {
                $checksBeforeCommit = @($checks | Where-Object { $_.Index -gt $commits[0].Index }).Count -eq 0
            }
            Write-Check $checksBeforeCommit "ch05 stage $stage contains failing checks before COMMIT"
            if ($stage -gt 1) {
                Write-Check (-not [regex]::IsMatch($body, '(?im)^\s*(DROP|TRUNCATE|CREATE)\b')) "ch05 stage $stage does not reset tables"
                $guard = $body.IndexOf("to_regclass(")
                $mutation = [regex]::Match($body, '(?m)^\s*(DELETE FROM|UPDATE)\b')
                Write-Check ($guard -ge 0 -and $mutation.Success -and $guard -lt $mutation.Index) "ch05 stage $stage checks required tables before mutation"
            }
        }
        Write-Check (-not [regex]::IsMatch($sql, '(?im)^\s*(DROP TABLE(?: IF EXISTS)?|TRUNCATE(?: TABLE)?|DELETE FROM|UPDATE)\s+ch05_lab\.lab_stock(?:_history)?\b')) "ch05 relationship reference does not mutate exercise 1"
    }
    Write-Host "INFO    Stage boundaries and SQL structure checked; data behavior is NOT RUN."
}

if ($Chapter -eq "ch08") {
    foreach ($relativePath in @("AGENTS.md", "understanding/AGENTS.md")) {
        $path = Join-Path $chapterRoot $relativePath
        if (Test-Path -LiteralPath $path) {
            $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $path
            Write-Check ($text.Contains("common-rules-version: chapter8-v6")) "$relativePath rules version"
            foreach ($marker in @("approval-required", "secrets-protected", "evidence-scoped")) {
                Write-Check ($text.Contains($marker)) "$relativePath marker: $marker"
            }
            Write-Check ($text.Contains("chapter8_order_spec.md")) "$relativePath references the small example specification"
        }
    }
    $specPath = Join-Path $chapterRoot "chapter8_order_spec.md"
    if (Test-Path -LiteralPath $specPath) {
        $text = Get-Content -Raw -Encoding UTF8 -LiteralPath $specPath
        foreach ($section in @("## 입력 검증", "## 서버 기준 계산", "## 세 대표 사례와 완료 기준", "## 본문 읽기와 Day 16 연결")) {
            Write-Check ($text.Contains($section)) "ch08 specification section: $section"
        }
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
