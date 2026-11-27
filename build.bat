@echo off
setlocal EnableExtensions
title Performance Air - Build

cd /d "%~dp0"
if errorlevel 1 (
    echo [ERROR] Could not open the project folder.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo        PERFORMANCE AIR - EXE BUILDER
echo ==========================================
echo.

REM Find Python. The Windows Python launcher is preferred.
where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON=py -3"
) else (
    where python >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON=python"
    ) else (
        echo [ERROR] Python 3 was not found.
        echo Install Python 3 and enable "Add Python to PATH".
        pause
        exit /b 1
    )
)

if not exist "main.py" (
    echo [ERROR] main.py was not found. Run this file from the project folder.
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt was not found.
    pause
    exit /b 1
)

echo [1/4] Updating pip...
%PYTHON% -m pip install --upgrade pip
if errorlevel 1 goto failed

echo.
echo [2/4] Installing application and build dependencies...
%PYTHON% -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto failed

echo.
echo [3/4] Checking Python files...
%PYTHON% -m py_compile main.py fps_capture.py
if errorlevel 1 goto failed

echo.
echo [4/4] Compiling the standalone Windows application...
if not exist "tools" mkdir "tools"

if exist "tools\PresentMon.exe" (
    echo Including tools\PresentMon.exe for game FPS capture.
    %PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed --name "Performance Air" --hidden-import pynvml --add-binary "tools\PresentMon.exe;tools" main.py
) else (
    echo PresentMon not found in tools. Building without bundled FPS capture.
    %PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed --name "Performance Air" --hidden-import pynvml main.py
)
if errorlevel 1 goto failed

if not exist "dist\Performance Air.exe" (
    echo [ERROR] PyInstaller finished but the EXE was not found.
    goto failed
)

echo.
echo ==========================================
echo BUILD SUCCESSFUL
echo ==========================================
echo.
echo Your application is here:
echo %CD%\dist\Performance Air.exe
echo.
echo You can copy that EXE anywhere and run it.
echo It will not open a Command Prompt window.
echo.
pause
exit /b 0

:failed
echo.
echo ==========================================
echo BUILD FAILED
echo ==========================================
echo Check the error messages above.
echo.
pause
exit /b 1
