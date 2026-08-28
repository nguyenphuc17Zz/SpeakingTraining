@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title Hanasu AI - Stop

echo Dang dung Hanasu AI (8000/3000)...
for %%P in (8000 3000) do (
    set FOUND=0
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%%P\>"') do (
        if not "%%a"=="0" (
            echo  - Kill PID %%a tren port %%P
            taskkill /F /T /PID %%a >nul 2>&1
            set FOUND=1
        )
    )
    if "!FOUND!"=="0" echo  - Khong co tien trinh tren port %%P
)
echo [XONG] Da dung.
ping 127.0.0.1 -n 3 >nul
exit /b 0
