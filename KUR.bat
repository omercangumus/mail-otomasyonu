@echo off
title Email Otomasyonu - Otomatik Kurulum
color 0B

cls
echo.
echo ====================================================
echo.
echo      ^📧 EMAIL OTOMASYONU - OTOMATIK KURULUM
echo.
echo ====================================================
echo.
echo Bu script otomatik olarak:
echo   ✅ Python kontrolu yapacak
echo   ✅ Bagimliliklari yukleyecek
echo   ✅ Uygulamayi derleyecek
echo   ✅ Masaustune kopyalayacak
echo.
pause

REM Script'in bulunduğu klasöre git
cd /d "%~dp0"

echo.
echo [1/5] Python kontrolu...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo ❌ Python bulunamadi!
    echo.
    echo Python yuklemek icin:
    echo   1. https://python.org adresine git
    echo   2. 'Download Python' butonuna tikla
    echo   3. Indirdigin dosyayi calistir
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ %PYTHON_VERSION% bulundu
timeout /t 1 >nul

echo.
echo [2/5] Bagimliliklar yukleniyor...
echo Bu islem biraz zaman alabilir, lutfen bekleyin...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if errorlevel 1 (
    color 0C
    echo ❌ Bagimliliklar yuklenemedi!
    pause
    exit /b 1
)

echo ✅ Bagimliliklar yuklendi
timeout /t 1 >nul

echo.
echo [3/5] PyInstaller yukleniyor...
pip install pyinstaller --quiet

if errorlevel 1 (
    color 0C
    echo ❌ PyInstaller yuklenemedi!
    pause
    exit /b 1
)

echo ✅ PyInstaller yuklendi
timeout /t 1 >nul

echo.
echo [4/5] Uygulama derleniyor...
echo Bu islem 2-3 dakika surebilir, lutfen bekleyin...
echo.

REM Eski build dosyalarını temizle
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
del /q *.spec 2>nul

REM .exe oluştur
pyinstaller --name="Email Otomasyonu" --onefile --windowed --icon=icon.ico --clean --noconfirm bulk_email_app.py

if errorlevel 1 (
    color 0C
    echo.
    echo ❌ Uygulama derlenemedi!
    pause
    exit /b 1
)

if not exist "dist\Email Otomasyonu.exe" (
    color 0C
    echo.
    echo ❌ .exe dosyasi olusturulamadi!
    pause
    exit /b 1
)

echo ✅ Uygulama derlendi
timeout /t 1 >nul

echo.
echo [5/5] Masaustune kopyalaniyor...

if exist "dist\Email Otomasyonu.exe" (
    copy /Y "dist\Email Otomasyonu.exe" "%USERPROFILE%\Desktop\Email Otomasyonu.exe" >nul 2>&1
    
    if exist "%USERPROFILE%\Desktop\Email Otomasyonu.exe" (
        echo ✅ Masaustune kopyalandi!
        echo.
        echo Dosya: %USERPROFILE%\Desktop\Email Otomasyonu.exe
    ) else (
        echo ⚠️  Masaustune kopyalanamadi
        echo Dosyayi 'dist' klasorunde bulabilirsiniz
    )
) else (
    echo ❌ dist\Email Otomasyonu.exe bulunamadi!
)

color 0A
echo.
echo ====================================================
echo.
echo           🎉 KURULUM TAMAMLANDI! 🎉
echo.
echo ====================================================
echo.
echo Uygulamaniz kullanima hazir!
echo.
echo Masaustunde 'Email Otomasyonu.exe' dosyasini bulacaksiniz.
echo Cift tiklayin ve kullanmaya baslayin!
echo.
echo 💡 Windows SmartScreen uyarisi alabilirsiniz.
echo    Cozum: 'Daha fazla bilgi' -^> 'Yine de calistir'
echo.
echo Kurulum scripti kapatiliyor...
timeout /t 5 >nul
exit /b 0
