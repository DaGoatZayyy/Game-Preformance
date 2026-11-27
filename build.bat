@echo off
setlocal
cd /d "%~dp0"
echo Installing build dependencies...
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto failed

if not exist "tools" mkdir tools
if not exist "tools\PresentMon.exe" (
    echo Downloading the official PresentMon command-line capture tool...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$release = Invoke-RestMethod https://api.github.com/repos/GameTechDev/PresentMon/releases/latest; $asset = $release.assets | Where-Object { $_.name -match '^PresentMon-.*-x64\.exe

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
 } | Select-Object -First 1; if (-not $asset) { throw 'No x64 PresentMon executable found in latest release' }; Invoke-WebRequest -Uri $asset.browser_download_url -OutFile 'tools/PresentMon.exe'"
    if errorlevel 1 echo Download failed. FPS can still be configured later in Settings.
)

set PM_ARGS=
if exist "tools\PresentMon.exe" (
    set PM_ARGS=--add-binary "tools\PresentMon.exe;tools"
    echo Bundling PresentMon FPS capture.
) else (
    echo Building without bundled FPS capture.
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
