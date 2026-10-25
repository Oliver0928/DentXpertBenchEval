@echo off
setlocal
echo Starting SSH tunnel: 127.0.0.1:18000 -> server 127.0.0.1:8000
echo Keep this window open while the evaluation is running.
echo.
ssh -N -L 18000:127.0.0.1:8000 -p 21657 root@124.222.246.189
pause
