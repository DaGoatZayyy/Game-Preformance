@echo off
setlocal
cd /d "%~dp0"
if exist "dist\Performance Air.exe" (
    start "" "dist\Performance Air.exe"
) else (
    where pythonw >nul 2>nul
    if errorlevel 1 (
        echo Python is not installed. Build the standalone EXE with build.bat first.
        pause
    ) else (
        start "" pythonw main.py
    )
)
exit /b 0
