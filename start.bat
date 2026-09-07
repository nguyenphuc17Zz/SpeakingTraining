@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion
title JapS - Japanese Speaking AI Training OS

set ROOT_DIR=%~dp0
set API_DIR=%ROOT_DIR%apps\api
set WEB_DIR=%ROOT_DIR%apps\web

REM ============================================================
REM CLI: start.bat [start|stop|restart|status|menu]
REM Default (no arg / double-click) => auto start: kill old -> start all -> open browser
REM ============================================================
if /i "%~1"=="stop" goto :STOP_SERVICES
if /i "%~1"=="restart" goto :RESTART_SERVICES
if /i "%~1"=="status" goto :STATUS_VIEW
if /i "%~1"=="menu" goto :MENU
if /i "%~1"=="start" goto :AUTO_START
if not "%~1"=="" goto :AUTO_START
goto :AUTO_START

REM ============================================================
REM AUTO START (default)
REM ============================================================
:AUTO_START
cls
echo ====================================================================
echo   JAPS - JAPANESE SPEAKING AI TRAINING OS (localhost only)
echo ====================================================================
echo.

REM 0. Kill old processes first (always)
echo [0/4] Dang dung cac tien trinh cu tren 8000/3000 (neu co)...
call :KILL_PORT 8000 "FastAPI Backend"
call :KILL_PORT 3000 "Next.js Web"
ping 127.0.0.1 -n 2 >nul

REM 1. Ensure .env
echo [1/4] Kiem tra .env...
if not exist "%ROOT_DIR%.env" (
    if exist "%ROOT_DIR%.env.example" (
        echo   - .env chua co, dang sao chep tu .env.example...
        copy /Y "%ROOT_DIR%.env.example" "%ROOT_DIR%.env" >nul
        if errorlevel 1 echo   ^! Canh bao: Khong sao chep duoc .env.example
    ) else (
        echo   ^! Khong tim thay .env.example, bo qua.
    )
) else (
    echo   - Da co .env
)
REM Ensure frontend env points to localhost (fix CORS host mismatch)
if not exist "%WEB_DIR%\.env.local" (
    echo   - Tao apps\web\.env.local -^> http://localhost:8000/api/v1
    >"%WEB_DIR%\.env.local" echo NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
) else (
    findstr /C:"localhost:8000" "%WEB_DIR%\.env.local" >nul 2>&1
    if errorlevel 1 (
        echo   - Cap nhat apps\web\.env.local ve localhost:8000...
        >"%WEB_DIR%\.env.local" echo NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    ) else (
        echo   - apps\web\.env.local OK
    )
)

REM 2. Python venv
echo [2/4] Kiem tra moi truong Python Backend...
set PYTHON_EXE=%API_DIR%\.venv\Scripts\python.exe
if exist "%PYTHON_EXE%" (
    echo   - Da co .venv Backend ^(khoi dong nhanh, bo qua cai lai pip^).
    if /i "%~1"=="install" (
        echo   - Dang cap nhat thu vien backend theo yeu cau...
        "%PYTHON_EXE%" -m pip install -e "%API_DIR%"
    )
) else (
    echo   - Chua co .venv, dang tao moi...
    where python >nul 2>&1
    if errorlevel 1 (
        echo   ^! Loi: Khong tim thay 'python' trong PATH. Cai Python 3.10+ truoc.
        pause
        exit /b 1
    )
    python -m venv "%API_DIR%\.venv"
    if errorlevel 1 (
        echo   ^! Loi tao venv that bai.
        pause
        exit /b 1
    )
    echo   - Cai dependencies backend...
    "%PYTHON_EXE%" -m pip install --upgrade pip >nul
    "%PYTHON_EXE%" -m pip install -e "%API_DIR%" >nul 2>&1
    echo   - Da cai xong backend deps
)

REM 3. Node modules
echo [3/4] Kiem tra thu vien Frontend...
if not exist "%WEB_DIR%\node_modules" (
    echo   - Chua co node_modules, dang chay npm install ^(co the mat vai phut^)...
    pushd "%WEB_DIR%"
    where npm >nul 2>&1
    if errorlevel 1 (
        echo   ^! Loi: Khong tim thay 'npm'. Cai Node.js truoc.
        pause
        exit /b 1
    )
    call npm install
    if errorlevel 1 (
        echo   ^! npm install loi, thu lai sau.
        pause
        exit /b 1
    )
    popd
) else (
    echo   - Da co node_modules
    if /i "%~1"=="install" (
        echo   - Dang cap nhat thu vien frontend theo yeu cau...
        pushd "%WEB_DIR%" && call npm install && popd
    )
)

REM 4. Launch services
echo [4/4] Khoi dong dich vu...
echo   - Backend FastAPI: http://localhost:8000 ^(docs: /docs^)
start "JapS - FastAPI Backend (8000)" /D "%API_DIR%" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
ping 127.0.0.1 -n 2 >nul

echo   - Frontend Next.js: http://localhost:3000
start "JapS - Next.js Web (3000)" /D "%WEB_DIR%" cmd /k "npm run dev"
ping 127.0.0.1 -n 2 >nul

echo.
echo   Dang mo trinh duyet...
start "" http://localhost:3000

echo.
echo ====================================================================
echo  [THANH CONG] He thong dang chay:
echo    * Web App  : http://localhost:3000
echo    * API Docs : http://localhost:8000/docs
echo    * Health   : http://localhost:8000/api/v1/health
echo  Hai cua so cmd moi da mo - dung dong chung khi dang dung.
echo  Chay stop.bat de dung toan bo.
echo ====================================================================
echo.
echo  Nhan phim bat ky de dong cua so nay (dich vu van chay o 2 cua so khac)...
pause >nul
exit /b 0

REM ============================================================
REM KILL helper: kill all PIDs listening on given port
REM ============================================================
:KILL_PORT
set PORT=%~1
set LABEL=%~2
set KILL_FOUND=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT%\>"') do (
    if not "%%a"=="0" (
        echo   - Dung %LABEL% ^(PID %%a tren port %PORT%^)...
        taskkill /F /T /PID %%a >nul 2>&1
        set KILL_FOUND=1
    )
)
if "!KILL_FOUND!"=="0" echo   - Khong co tien trinh nao tren port %PORT%
exit /b 0

REM ============================================================
REM STOP
REM ============================================================
:STOP_SERVICES
echo.
echo ====================================================================
echo   DANG DUNG HANASU AI...
echo ====================================================================
call :KILL_PORT 8000 "FastAPI Backend"
call :KILL_PORT 3000 "Next.js Web"
echo.
echo [XONG] Da dung cac tien trinh tren 8000/3000.
if "%~1"=="non_interactive" exit /b 0
ping 127.0.0.1 -n 3 >nul
exit /b 0

:RESTART_SERVICES
call :STOP_SERVICES non_interactive
ping 127.0.0.1 -n 3 >nul
goto :AUTO_START

:STATUS_VIEW
echo.
echo [TRANG THAI]
call :STATUS_PORT 8000 "Backend FastAPI"
call :STATUS_PORT 3000 "Frontend Next.js"
pause
exit /b 0

:STATUS_PORT
set PORT=%~1
set LABEL=%~2
set STATUS_FOUND=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT%\>"') do (
    if not "%%a"=="0" (
        echo   * %LABEL% [%PORT%]: DANG CHAY - PID %%a
        set STATUS_FOUND=1
    )
)
if "!STATUS_FOUND!"=="0" echo   * %LABEL% [%PORT%]: DANG DUNG
exit /b 0

REM ============================================================
REM MENU (only when explicitly called: start.bat menu)
REM ============================================================
:MENU
cls
echo ====================================================================
echo              HANASU AI OS -- CONTROL CENTER
echo ====================================================================
echo.
call :STATUS_PORT 8000 "Backend FastAPI (8000)"
call :STATUS_PORT 3000 "Frontend Next.js (3000)"
echo.
echo   [1] Auto Start (kill cu + chay nhanh)
echo   [2] Dung toan bo
echo   [3] Khoi dong lai
echo   [4] Xoa .next va khoi dong lai
echo   [5] Mo browser http://localhost:3000
echo   [6] Cap nhat / Cai lai dependencies (pip + npm)
echo   [0] Thoat
echo ====================================================================
set /p CHOICE="Chon [0-6]: "
if "%CHOICE%"=="1" goto :AUTO_START
if "%CHOICE%"=="2" goto :STOP_SERVICES
if "%CHOICE%"=="3" goto :RESTART_SERVICES
if "%CHOICE%"=="4" goto :CLEAN_RESTART
if "%CHOICE%"=="5" start "" http://localhost:3000 & goto :MENU
if "%CHOICE%"=="6" call :AUTO_START install
if "%CHOICE%"=="0" exit /b 0
goto :MENU

:CLEAN_RESTART
call :STOP_SERVICES non_interactive
if exist "%WEB_DIR%\.next" rmdir /s /q "%WEB_DIR%\.next" >nul 2>&1
goto :AUTO_START
