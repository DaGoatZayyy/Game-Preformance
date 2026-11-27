@echo off
setlocal
cd /d "%~dp0"
echo Installing build dependencies...
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto failed

if not exist "tools" mkdir tools
set PM_ARGS=
if exist "tools\PresentMon.exe" (
    set PM_ARGS=--add-binary "tools\PresentMon.exe;tools"
    echo Bundling PresentMon FPS capture.
) else (
    echo PresentMon.exe not found in tools. FPS capture can be configured later in Settings.
)

echo Building standalone Performance Air...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "Performance Air" --collect-all pynvml %PM_ARGS% main.py
if errorlevel 1 goto failed

echo.
echo Build complete: dist\Performance Air.exe
echo This is a single-file Windows application. No Command Prompt is needed to run it.
pause
exit /b 0
:failed
echo.
echo Build failed. Check the error output above.
pause
exit /b 1
