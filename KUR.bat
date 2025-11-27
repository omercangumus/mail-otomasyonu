@echo off
setlocal EnableDelayedExpansion
title Email Otomasyonu - Akilli Kurulum
color 0A

:: Yönetici izni kontrolü
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :ADMIN_OK
) else (
    echo.
    echo [BILGI] Python otomatik kurulumu icin Yonetici izni gerekiyor...
    echo Lutfen acilan pencerede "Evet" deyin.
    echo.
    powershell -Command "Start-Process '%~0' -Verb RunAs"
    exit /b
)

:ADMIN_OK
cd /d "%~dp0"
cls

echo.
echo ====================================================
echo.
echo      EMAIL OTOMASYONU - AKILLI KURULUM
echo.
echo ====================================================
echo.

:: 1. Python Kontrolü ve Otomatik Kurulum
echo [1/3] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [UYARI] Python bulunamadi!
    echo [ISLEM] Python 3.11 otomatik olarak indiriliyor ve kuruluyor...
    echo         Bu islem internet hizina bagli olarak 1-2 dakika surebilir.
    echo.
    
    :: Python İndirme
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
    
    if not exist "%TEMP%\python_installer.exe" (
        color 0C
        echo [HATA] Python indirilemedi! Internet baglantinizi kontrol edin.
        pause
        exit /b 1
    )
    
    echo [ISLEM] Python kuruluyor (Sessiz Mod)...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    :: PATH güncelleme (Geçici olarak bu oturum için)
    set "PATH=%PATH%;C:\Program Files\Python311\Scripts\;C:\Program Files\Python311\"
    
    :: Tekrar kontrol
    python --version >nul 2>&1
    if !errorLevel! neq 0 (
        color 0C
        echo [HATA] Otomatik kurulum basarisiz oldu.
        echo Lutfen manuel yukleyin: https://python.org
        pause
        exit /b 1
    )
    
    echo [BASARILI] Python kuruldu!
) else (
    echo [BILGI] Python zaten yuklu.
)

:: 2. Animasyonlu Kurulum (Bağımlılıklar)
echo.
echo [2/3] Kurulum sihirbazi baslatiliyor...
timeout /t 1 >nul
python install_animation.py

if %errorLevel% neq 0 (
    color 0C
    echo.
    echo [HATA] Kurulum sihirbazi bir sorunla karsilasti.
    pause
    exit /b 1
)

:: 3. Derleme (Build)
echo.
echo [3/3] Uygulama derleniyor (EXE olusturuluyor)...
echo.

:: Temizlik
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
del /q *.spec 2>nul

:: Build
python -m PyInstaller --name=EmailOtomasyonu --onefile --windowed --icon=icon.ico --hidden-import=customtkinter --collect-all=customtkinter --noconfirm bulk_email_app.py

if not exist "dist\EmailOtomasyonu.exe" (
    color 0C
    echo.
    echo [HATA] Derleme basarisiz oldu!
    pause
    exit /b 1
)

:: Masaüstüne Kopyalama
set "TARGET_PATH=%USERPROFILE%\Desktop\EmailOtomasyonu.exe"
copy /Y "dist\EmailOtomasyonu.exe" "%TARGET_PATH%" >nul 2>&1

cls
echo.
echo ====================================================
echo           KURULUM BASARIYLA TAMAMLANDI!
echo ====================================================
echo.
if exist "%TARGET_PATH%" (
    echo [OK] Uygulama masaustune kopyalandi:
    echo      %TARGET_PATH%
) else (
    echo [BILGI] Uygulama 'dist' klasorunde hazir.
)
echo.
echo Cikmak icin bir tusa basin...
pause >nul
