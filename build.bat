@echo off
setlocal
cd /d "%~dp0"
echo Installing build dependencies...
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto failed
echo Building Performance Air...
py -m PyInstaller --noconfirm --clean --windowed --name "Performance Air" --collect-all pynvml main.py
if errorlevel 1 goto failed
echo.
echo Build complete: dist\Performance Air\Performance Air.exe
echo You can distribute the complete dist\Performance Air folder.
pause
exit /b 0
:failed
echo.
echo Build failed. Check the error output above.
pause
exit /b 1
