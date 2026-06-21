@echo off
REM EmailAI kurulum - Windows
cd /d "%~dp0"

echo ==^> Python kontrol ediliyor...
where python >nul 2>nul
if errorlevel 1 (
  echo HATA: Python bulunamadi. https://www.python.org/downloads/ adresinden kur.
  echo Kurarken "Add Python to PATH" kutucugunu isaretle.
  pause
  exit /b 1
)

echo ==^> Sanal ortam olusturuluyor...
python -m venv .venv
call .venv\Scripts\activate.bat

echo ==^> Bagimliliklar yukleniyor...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

echo.
echo Kurulum tamam!
echo Calistirmak icin: run.bat  (veya cift tikla)
pause
