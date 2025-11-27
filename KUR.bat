@echo off
setlocal EnableDelayedExpansion
title Email Otomasyonu - Akilli Kurulum
color 0A

:: Debug bilgisi
echo [BASLATIYOR] Kurulum scripti calisiyor...
echo Calisma dizini: %CD%

:: Yönetici izni kontrolü
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :ADMIN_OK
) else (
    echo.
    echo [BILGI] Yonetici izni gerekiyor...
    echo Lutfen acilan pencerede "Evet" deyin.
    echo.
    
    :: /k parametresi ile CMD penceresini açık tutuyoruz
    powershell -Command "Start-Process cmd -ArgumentList '/k, \"\"%~f0\"\"' -Verb RunAs"
    
    if %errorLevel% neq 0 (
        echo [HATA] Yonetici izni alinirken hata olustu!
        pause
    )
    exit /b
)

:ADMIN_OK
:: Çalışma dizinini scriptin olduğu yere sabitle
cd /d "%~dp0"
echo [BILGI] Yonetici modu aktif.
echo [BILGI] Calisma dizini: %CD%
echo.

echo ====================================================
echo.
echo      EMAIL OTOMASYONU - AKILLI KURULUM
echo.
echo ====================================================
echo.

:: 1. Python Kontrolü
echo [1/3] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [UYARI] Python bulunamadi!
    echo [ISLEM] Python 3.11 otomatik olarak indiriliyor...
    
    :: İndirme
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
    
    if not exist "%TEMP%\python_installer.exe" (
        color 0C
        echo [HATA] Python indirilemedi!
        echo Lutfen internet baglantinizi kontrol edin.
        pause
        exit /b 1
    )
    
    echo [ISLEM] Python kuruluyor (Bu islem biraz surebilir)...
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    :: PATH güncelleme
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

:: 2. Animasyonlu Kurulum
echo.
echo [2/3] Kurulum sihirbazi baslatiliyor...
timeout /t 2 >nul

if not exist "install_animation.py" (
    color 0C
    echo [HATA] install_animation.py dosyasi bulunamadi!
    echo Lutfen dosyalari eksiksiz indirdiginizden emin olun.
    pause
    exit /b 1
)

python install_animation.py
if %errorLevel% neq 0 (
    color 0C
    echo.
    echo [HATA] Kurulum sihirbazi hata verdi.
    echo Hata kodu: %errorLevel%
    echo.
    echo Manuel kurulum denemek icin:
    echo pip install customtkinter pillow certifi pyinstaller
    pause
    exit /b 1
)

:: 3. Derleme
echo.
echo [3/3] Uygulama derleniyor...
echo.

if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
del /q *.spec 2>nul

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
echo Pencereyi kapatabilirsiniz.
pause
