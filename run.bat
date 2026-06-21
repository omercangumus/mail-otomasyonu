@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
  echo Once install.bat calistir.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python app.py
