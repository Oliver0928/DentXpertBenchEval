@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-All-A1-A4.ps1" %*
if errorlevel 1 (
    echo.
    echo 批量评测执行失败，请查看上面的错误信息。
    pause
    exit /b 1
)

echo.
echo 批量评测执行完成。
pause
