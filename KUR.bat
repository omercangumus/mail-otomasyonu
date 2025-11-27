@echo off
title Email Otomasyonu - Kurulum
color 0B

cls
echo.
echo ====================================================
echo.
echo      EMAIL OTOMASYONU - OTOMATIK KURULUM
echo.
echo ====================================================
echo.
pause

cd /d "%~dp0"

echo.
echo [1/4] Python kontrolu...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo ❌ Python bulunamadi!
    echo Python yukleyin: https://python.org
    pause
    exit /b 1
)
python --version
timeout /t 1 >nul

echo.
echo [2/4] Bagimliliklar yukleniyor...
python -m pip install --quiet --upgrade pip
pip install --quiet customtkinter pillow pyinstaller certifi

echo.
echo [3/4] Uygulama derleniyor (2-3 dakika)...
echo.

REM Temizlik
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
del /q *.spec 2>nul

REM Build - BOŞLUKSUZ DOSYA ADI
REM Build - BOŞLUKSUZ DOSYA ADI
python -m PyInstaller --name=EmailOtomasyonu --onefile --windowed --icon=icon.ico --hidden-import=customtkinter --collect-all=customtkinter --noconfirm bulk_email_app.py

if not exist "dist\EmailOtomasyonu.exe" (
    color 0C
    echo ❌ Build basarisiz!
    pause
    exit /b 1
)

echo ✅ Build tamamlandi

echo.
echo [4/4] Masaustune kopyalaniyor...

set TARGET_PATH=%USERPROFILE%\Desktop\EmailOtomasyonu.exe

copy /Y "dist\EmailOtomasyonu.exe" "%TARGET_PATH%" >nul 2>&1

if exist "%TARGET_PATH%" (
    color 0A
    echo ✅ BASARILI!
    echo.
    echo Masaustunde: EmailOtomasyonu.exe
    echo.
) else (
    color 0E
    echo ⚠️  Masaustune kopyalanamadi
    echo dist klasorunde: EmailOtomasyonu.exe
    echo.
)

echo ====================================================
echo           KURULUM TAMAMLANDI!
echo ====================================================
echo.
timeout /t 5
exit /b 0
