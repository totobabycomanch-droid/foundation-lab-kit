param([int]$Port = 5195)

$day05Utf8Encoding = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $day05Utf8Encoding
[Console]::OutputEncoding = $day05Utf8Encoding
$OutputEncoding = $day05Utf8Encoding
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$frontendRoot = Join-Path $repoRoot 'frontend'
$viteEntry = Join-Path $frontendRoot 'node_modules/vite/bin/vite.js'
$playwrightEntry = Join-Path $frontendRoot 'node_modules/@playwright/test/cli.js'
$server = $null

if (-not (Test-Path -LiteralPath $viteEntry -PathType Leaf) -or
    -not (Test-Path -LiteralPath $playwrightEntry -PathType Leaf)) {
    throw 'frontend/node_modules is missing. Install npm dependencies and retry.'
}

try {
    $server = Start-Process -FilePath 'node.exe' -ArgumentList @($viteEntry, '--host', '127.0.0.1', '--port', $Port, '--strictPort') -WorkingDirectory $frontendRoot -WindowStyle Hidden -PassThru
    $ready = $false
    for ($attempt = 1; $attempt -le 40; $attempt++) {
        if ($server.HasExited) { throw "The Day 5 Vite server exited (exit=$($server.ExitCode))." }
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port" -UseBasicParsing -TimeoutSec 1
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        }
        catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $ready) { throw "The Day 5 Vite server was not ready (port=$Port)." }

    Push-Location $frontendRoot
    try {
        $env:DAY13_E2E_PORT = $Port.ToString()
        $env:DAY13_E2E_REUSE = '1'
        & node $playwrightEntry test e2e/day05-partner-master.spec.js
        if ($LASTEXITCODE -ne 0) { throw "Day 5 mock E2E failed (exit=$LASTEXITCODE)." }
    }
    finally {
        Remove-Item Env:DAY13_E2E_PORT -ErrorAction SilentlyContinue
        Remove-Item Env:DAY13_E2E_REUSE -ErrorAction SilentlyContinue
        Pop-Location
    }
}
finally {
    if ($null -ne $server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force
        [void]$server.WaitForExit(5000)
    }
}

Write-Host 'PASS D05-MOCK-E2E: partner master UI scenarios completed'
