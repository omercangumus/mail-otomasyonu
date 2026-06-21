@echo off
REM EmailAI.exe uretir - WINDOWS uzerinde calistir.
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" ( echo Once install.bat & pause & exit /b 1 )
call .venv\Scripts\activate.bat
pip install pyinstaller -q

set ICON=
if exist icon.ico set ICON=--icon icon.ico

pyinstaller --noconfirm --clean --windowed --onefile ^
  --name EmailAI %ICON% ^
  --collect-all customtkinter ^
  app.py

echo.
echo Cikti: dist\EmailAI.exe
echo (SmartScreen uyarisi cikarsa: "Daha fazla bilgi" ^> "Yine de calistir")
pause
