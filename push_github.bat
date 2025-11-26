@echo off
echo Pushing to GitHub...
echo.

cd /d "%~dp0"

git remote add origin https://github.com/omercangumus/mail-otomasyonu.git 2>nul
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo ❌ Push basarisiz!
    echo.
    echo Manuel push icin:
    echo   git push -u origin main
    echo.
    pause
) else (
    echo.
    echo ✅ GitHub'a yuklendi!
    echo.
    echo Kontrol et: https://github.com/omercangumus/mail-otomasyonu
    echo.
    timeout /t 3
)
