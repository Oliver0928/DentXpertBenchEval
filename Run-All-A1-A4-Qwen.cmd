@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-All-A1-A4.ps1" -ModelConfig "%~dp0configs\model-qwen-local.json" %*
if errorlevel 1 (
    echo.
    echo Evaluation failed. Check that the SSH tunnel is still running.
    pause
    exit /b 1
)
echo.
echo Qwen evaluation completed.
pause
