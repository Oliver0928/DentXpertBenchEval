param(
    [int]$Workers = 16,
    [int]$Retries = 10,
    [double]$RetrySleep = 2.0
)

$ErrorActionPreference = "Stop"
$EvalRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    throw "Python was not found."
}

Push-Location $EvalRoot
try {
    & $Python.Source run.py `
        --task all `
        --model-config configs/model-gpt-6-luna.json `
        --workers $Workers `
        --retries $Retries `
        --retry-sleep $RetrySleep

    if ($LASTEXITCODE -ne 0) {
        throw "Evaluation process exited with code: $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

Write-Host "All tasks completed."
