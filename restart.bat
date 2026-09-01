@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title Hanasu AI - Quick Restart

echo ====================================================================
echo   HANASU AI - QUICK RESTART
echo ====================================================================
echo.
echo [1/2] Dang dong cac dich vu dang chay...
call "%~dp0stop.bat"

echo.
echo [2/2] Dang khoi dong lai toan bo he thong...
call "%~dp0start.bat" start
