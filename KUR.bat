@echo off
setlocal EnableDelayedExpansion
:: UTF-8 karakter destegi
chcp 65001 >nul 2>&1
title Email Otomasyonu - Kurulum
color 0A

:: Script dizinini al
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Yönetici kontrolü
net session >nul 2>&1
if %errorLevel% == 0 goto :ADMIN_OK

:: Yönetici değilse, yetki iste
echo.
echo [BILGI] Yonetici izni gerekiyor...
echo Lutfen acilan pencerede "Evet" deyin.
echo.
powershell -Command "Start-Process cmd -ArgumentList '/k cd /d \"%SCRIPT_DIR%\" && \"%~f0\"' -Verb RunAs"
exit /b

:ADMIN_OK
:: Çalışma dizinini sabitle
cd /d "%SCRIPT_DIR%"
cls

echo ====================================================
echo.
echo      EMAIL OTOMASYONU - KURULUM
echo.
echo ====================================================
echo.
echo Calisma dizini: %CD%
echo.

:: Python kontrolü
echo [1/3] Python kontrol ediliyor...

:: where komutu ile Python'u bul
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [UYARI] Python bulunamadi!
    goto :INSTALL_PYTHON
)

:: Python çalışıyor mu test et
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [UYARI] Python yuklu ama calismıyor!
    goto :INSTALL_PYTHON
)

:: Python bulundu
for /f "delims=" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo [OK] %PY_VER% bulundu.
goto :START_INSTALL

:INSTALL_PYTHON
echo.
echo [INDIRILIYOR] Python 3.11...
powershell -NoProfile -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile '%TEMP%\python_installer.exe'}"

if not exist "%TEMP%\python_installer.exe" (
    echo [HATA] Indirme basarisiz! Internet baglantinizi kontrol edin.
    pause
    exit /b 1
)

echo [KURULUYOR] Python (bu birkaç dakika surebilir)...
"%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: PATH güncelleme
set "PATH=%PATH%;C:\Program Files\Python311\Scripts\;C:\Program Files\Python311\"

:: Kontrol
timeout /t 3 >nul
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [HATA] Kurulum basarisiz! Manuel yukleyin: https://python.org
    pause
    exit /b 1
)

echo [OK] Python kuruldu!

:START_INSTALL
echo.
echo [2/3] Bagimliliklar yukleniyor...

:: Önce install_animation.py var mı kontrol et
if exist "install_animation.py" (
    python install_animation.py
    if errorlevel 1 (
        echo [UYARI] Animasyon hata verdi, normal devam...
        goto :MANUAL_INSTALL
    )
) else (
    :MANUAL_INSTALL
    echo [MANUEL] pip install...
    python -m pip install --quiet --upgrade pip
    python -m pip install --quiet customtkinter pillow certifi pyinstaller
)

:: Derleme
echo.
echo [3/3] Uygulama derleniyor...
echo Bu islem 2-3 dakika surebilir...
echo.

:: Temizlik
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
del /q *.spec 2>nul

:: PyInstaller ile derle
python -m PyInstaller ^
    --name=EmailOtomasyonu ^
    --onefile ^
    --windowed ^
    --icon=icon.ico ^
    --hidden-import=customtkinter ^
    --collect-all=customtkinter ^
    --noconfirm ^
    bulk_email_app.py

:: EXE kontrolü
if not exist "dist\EmailOtomasyonu.exe" (
    echo [HATA] Derleme basarisiz!
    pause
    exit /b 1
)

:: Masaüstüne kopyala
set "DESKTOP=%USERPROFILE%\Desktop"
copy /Y "dist\EmailOtomasyonu.exe" "%DESKTOP%\EmailOtomasyonu.exe" >nul 2>&1

cls
echo.
echo ====================================================
echo           KURULUM TAMAMLANDI!
echo ====================================================
echo.

if exist "%DESKTOP%\EmailOtomasyonu.exe" (
    echo [OK] Uygulama masaustune kopyalandi:
    echo      %DESKTOP%\EmailOtomasyonu.exe
) else (
    echo [BILGI] Uygulama 'dist' klasorunde hazir.
)

echo.
echo Pencereyi kapatabilirsiniz.
pause
