[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("ch07", "ch08", "ch09", "ch10", "ch11")]
    [string]$Chapter,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$kitRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$chapterRoot = (Resolve-Path (Join-Path $kitRoot "practice-workspace/$Chapter")).Path

$removeTargets = @{
    ch07 = @("understanding/transaction_example.py", "understanding/sale_example.py", "understanding/test_examples.py")
    ch08 = @("understanding/order_example.py", "understanding/test_order_example.py")
    ch09 = @(
        "erp-mini/main.py", "erp-mini/domain/order.py", "erp-mini/domain/payment.py",
        "erp-mini/domain/inventory.py", "erp-mini/routers/orders.py",
        "erp-mini/services/order_service.py", "erp-mini/tests/test_erp_flow.py"
    )
    ch10 = @()
    ch11 = @(
        "workspace/erp-project/api/main.py",
        "workspace/frontend-project/src/components/ApproveOrder.vue"
    )
}

$ch07Web = Test-Path -LiteralPath (Join-Path $kitRoot 'practice-workspace/ch07/understanding/observation-baseline.json')

$restoreTargets = @{
    ch07 = @()
    ch08 = @()
    ch09 = @()
    ch10 = @(
        @("erp-mini/_starter/db.py", "erp-mini/db.py"),
        @("erp-mini/_starter/schema.sql", "erp-mini/schema.sql"),
        @("erp-mini/_starter/server.py", "erp-mini/server.py")
    )
    ch11 = ,@("workspace/_starter/App.vue", "workspace/frontend-project/src/App.vue")
}

if ($Chapter -eq 'ch07' -and $ch07Web) {
    $removeTargets['ch07'] = @()
    $restoreTargets['ch07'] = @(
        @('understanding/_starter/transaction_example.py','understanding/transaction_example.py'),
        @('understanding/_starter/sale_example.py','understanding/sale_example.py'),
        @('understanding/_starter/test_examples.py','understanding/test_examples.py')
    )
}

function Resolve-SafePath([string]$RelativePath) {
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $chapterRoot $RelativePath))
    $prefix = $chapterRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes chapter root: $RelativePath"
    }
    return $candidate
}

Write-Host "Chapter root: $chapterRoot"
Write-Host "Remove targets:"
foreach ($relativePath in $removeTargets[$Chapter]) {
    $target = Resolve-SafePath $relativePath
    $state = if (Test-Path -LiteralPath $target) { "exists" } else { "absent" }
    Write-Host "  [$state] $target"
}

Write-Host "Restore targets:"
foreach ($pair in $restoreTargets[$Chapter]) {
    $source = Resolve-SafePath $pair[0]
    $destination = Resolve-SafePath $pair[1]
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Starter file is missing: $source"
    }
    Write-Host "  $source -> $destination"
}

if (-not $Apply) {
    Write-Host "NOT RUN Preview only. Re-run with -Apply after checking every target." -ForegroundColor Yellow
    exit 0
}

foreach ($relativePath in $removeTargets[$Chapter]) {
    $target = Resolve-SafePath $relativePath
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Force
        Write-Host "REMOVED $target"
    }
}

foreach ($pair in $restoreTargets[$Chapter]) {
    $source = Resolve-SafePath $pair[0]
    $destination = Resolve-SafePath $pair[1]
    Copy-Item -LiteralPath $source -Destination $destination -Force
    Write-Host "RESTORED $destination"
}
Write-Host "$Chapter practice files were reset." -ForegroundColor Green
