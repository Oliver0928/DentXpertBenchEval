param(
    [switch]$DryRun,
    [int]$Limit = 0,
    [int]$Workers = 32,
    [int]$Retries = 0,
    [double]$RetrySleep = 0,
    [int]$Timeout = 0,
    [int]$MaxTokens = 0,
    [switch]$Debug,
    [switch]$ContinueOnError
)

$ErrorActionPreference = "Stop"
$EvalRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigRoot = Join-Path $EvalRoot "configs"
$ResultsRoot = Join-Path $EvalRoot "results"

$configNames = @(
    "model-qwen-local.json",
    "model-deepseek-flashjson",
    "model-gpt-6-luna.json"
)
if ($Workers -lt 1) {
    throw "Workers must be at least 1."
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python was not found."
}

New-Item -ItemType Directory -Force -Path $ResultsRoot | Out-Null

Push-Location $EvalRoot
try {
    foreach ($configName in $configNames) {
        $configPath = Join-Path $ConfigRoot $configName
        if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
            throw "Missing model config: $configPath"
        }

        $apiName = [IO.Path]::GetFileNameWithoutExtension($configName)
        Write-Host "=== API: $apiName ===" -ForegroundColor Cyan
        $arguments = @(
            "run.py", "--task", "all",
            "--model-config", $configPath,
            "--workers", $Workers,
            "--include-model-in-output"
        )
        if ($DryRun) { $arguments += "--dry-run" }
        if ($Limit -gt 0) { $arguments += @("--limit", $Limit) }
        if ($Retries -gt 0) { $arguments += @("--retries", $Retries) }
        if ($RetrySleep -gt 0) { $arguments += @("--retry-sleep", $RetrySleep) }
        if ($Timeout -gt 0) { $arguments += @("--timeout", $Timeout) }
        if ($MaxTokens -gt 0) { $arguments += @("--max-tokens", $MaxTokens) }
        if ($Debug) { $arguments += "--debug" }

        & $python.Source @arguments
        if ($LASTEXITCODE -ne 0) {
            $message = "[$apiName] failed with exit code $LASTEXITCODE."
            if (-not $ContinueOnError) {
                throw $message
            }
            Write-Warning $message
        }
    }
}
finally {
    Pop-Location
}

Write-Host "Completed all configured APIs and tasks. Results are in: $ResultsRoot" -ForegroundColor Green
