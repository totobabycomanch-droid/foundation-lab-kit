[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("check", "demo", "shell", "test", "verify", "fault", "reset")]
    [string]$Action,
    [switch]$Apply,
    [string]$PythonExecutable = "python"
)

$ErrorActionPreference = "Stop"
$kitRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../.."))
$toolsRoot = Join-Path $kitRoot "tools"
$erpRoot = Join-Path $PSScriptRoot "erp-mini"
if ($Apply -and $Action -ne "reset") {
    Write-Host "FAIL    -Apply is only supported for reset."
    exit 1
}

$required = switch ($Action) {
    "demo" { "erp-mini/main.py" }
    "shell" { "erp-mini/domain/order.py" }
    "test" { "erp-mini/domain/order.py"; "erp-mini/tests/test_erp_flow.py" }
    "fault" { "fault-lab/order.py" }
}
foreach ($relativePath in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $relativePath) -PathType Leaf)) {
        Write-Host "NOT RUN $relativePath is missing. Prepare the requested example first."
        exit 1
    }
}

$pushed = $false
$exitCode = 0
$global:LASTEXITCODE = 0
try {
    if ($Action -in @("demo", "shell", "test")) {
        Push-Location -LiteralPath $erpRoot
        $pushed = $true
    }
    switch ($Action) {
        "check" { & (Join-Path $toolsRoot "verify_practice_chapter.ps1") -Chapter ch09 }
        "demo" { & $PythonExecutable -B main.py }
        "shell" { & $PythonExecutable -B -i }
        "test" { & $PythonExecutable -B -m unittest discover -s tests -p "test_erp_flow.py" -v }
        "verify" { & (Join-Path $toolsRoot "verify_ch09_core.ps1") -PythonExecutable $PythonExecutable }
        "fault" {
            & $PythonExecutable -B (Join-Path $PSScriptRoot "checks/test_order_rules.py") `
                --order-file (Join-Path $PSScriptRoot "fault-lab/order.py")
        }
        "reset" { & (Join-Path $toolsRoot "reset_practice_chapter.ps1") -Chapter ch09 -Apply:$Apply }
    }
    $exitCode = $LASTEXITCODE
} catch {
    Write-Host "FAIL    $($_.Exception.Message)"
    $exitCode = 1
} finally {
    if ($pushed) { Pop-Location }
}
exit $exitCode
