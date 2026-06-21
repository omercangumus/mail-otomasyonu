@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [1/3] Sanal ortam olusturuluyor...
    python -m venv .venv
    if errorlevel 1 (
        echo HATA: Python bulunamadi. python.org/downloads adresinden yukleyin.
        pause
        exit /b 1
    )
    echo [2/3] Bagimliliklar yukleniyor...
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 (
        echo HATA: Bagimlilik kurulumu basarisiz.
        pause
        exit /b 1
    )
) else (
    call .venv\Scripts\activate.bat
)

echo [3/3] Uygulama baslatiliyor...
python app.py
if errorlevel 1 (
    echo.
    echo HATA: Uygulama beklenmedik sekilde kapandi.
    pause
)
