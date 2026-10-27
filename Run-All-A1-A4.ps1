param(
    [switch]$DryRun,
    [int]$Limit = 0,
    [string]$ModelConfig = "",
    [int]$MaxTokens = 0,
    [int]$Timeout = 0,
    [int]$Workers = 32,
    [switch]$Debug
)

$ErrorActionPreference = "Stop"
$EvalRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path (Join-Path $EvalRoot "run.py"))) {
    throw "Cannot find run.py in: $EvalRoot"
}

$python = $null
$pythonCandidates = @(Get-Command python -All -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -Unique)
foreach ($candidate in $pythonCandidates) {
    $probeOutput = $null
    try {
        $probeOutput = & $candidate -c "import PIL" 2>&1
        $probeExitCode = $LASTEXITCODE
    } catch {
        $probeExitCode = 1
    }
    if ($probeExitCode -eq 0) {
        $python = $candidate
        break
    }
}
if (-not $python) {
    throw "No Python interpreter with Pillow was found. Run: python -m pip install Pillow"
}

$arguments = @("run.py", "--task", "all")
if ($DryRun) { $arguments += "--dry-run" }
if ($Limit -gt 0) { $arguments += @("--limit", $Limit) }
if ($ModelConfig) { $arguments += @("--model-config", $ModelConfig) }
if ($MaxTokens -gt 0) { $arguments += @("--max-tokens", $MaxTokens) }
if ($Timeout -gt 0) { $arguments += @("--timeout", $Timeout) }
if ($Workers -gt 0) { $arguments += @("--workers", $Workers) }
if ($Debug) { $arguments += "--debug" }

if ($ModelConfig -and -not $DryRun) {
    $configPath = $ModelConfig
    if (-not [System.IO.Path]::IsPathRooted($configPath)) {
        $configPath = Join-Path $EvalRoot $configPath
    }
    if (Test-Path $configPath) {
        $config = Get-Content -Raw $configPath | ConvertFrom-Json
        $uri = [Uri]$config.base_url
        if ($uri.Host -in @("127.0.0.1", "localhost")) {
            $client = New-Object System.Net.Sockets.TcpClient
            try {
                $connectTask = $client.ConnectAsync($uri.Host, $uri.Port)
                if (-not $connectTask.Wait(2000) -or -not $client.Connected) {
                    throw "SSH tunnel is not listening at $($uri.Host):$($uri.Port). Start Eval-Qwen-Start-Tunnel.cmd first and keep it open."
                }
            } catch {
                throw "Cannot connect to $($uri.Host):$($uri.Port). Start Eval-Qwen-Start-Tunnel.cmd first and keep the SSH window open."
            } finally {
                $client.Dispose()
            }
        }
    }
}

Write-Host "Running all tasks from A1.1 through A4.3 in order." -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "Dry-run mode: no model calls and no result files." -ForegroundColor Yellow
} else {
    Write-Host "Evaluation mode: model calls will be made and results saved under results." -ForegroundColor Yellow
}

Push-Location $EvalRoot
try {
    & $python @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Batch evaluation failed with exit code: $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

Write-Host "All A1-A4 tasks completed." -ForegroundColor Green
