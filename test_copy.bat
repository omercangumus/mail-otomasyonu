@echo off
echo Testing copy...

REM Test dosyası oluştur
cd /d "%~dp0"
echo test > "test_file.txt"

echo.
echo Test 1: Boşluksuz dosya kopyalama
copy /Y "test_file.txt" "%USERPROFILE%\Desktop\test_file.txt"
if exist "%USERPROFILE%\Desktop\test_file.txt" (
    echo ✅ Basarili!
    del "%USERPROFILE%\Desktop\test_file.txt"
) else (
    echo ❌ Basarisiz
)

echo.
echo Test 2: Boşluklu dosya kopyalama
echo test2 > "Test File.txt"
copy /Y "Test File.txt" "%USERPROFILE%\Desktop\Test File.txt"
if exist "%USERPROFILE%\Desktop\Test File.txt" (
    echo ✅ Basarili!
    del "%USERPROFILE%\Desktop\Test File.txt"
) else (
    echo ❌ Basarisiz
)

REM Temizlik
del "test_file.txt"
del "Test File.txt"

echo.
echo Masaüstü yolu: %USERPROFILE%\Desktop
dir "%USERPROFILE%\Desktop" | find "Email"

pause
