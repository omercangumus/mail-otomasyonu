#!/bin/bash
# Email Otomasyonu - Mac Kurulum

clear
echo "===================================================="
echo " EMAIL OTOMASYONU - OTOMATIK KURULUM"
echo "===================================================="
echo ""
read -p "Baslamak icin Enter'a bas..." 

cd "$(dirname "${BASH_SOURCE[0]}")"

echo ""
echo "[1/4] Python kontrolu..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 bulunamadi!"
    echo "Python yukleyin: https://python.org"
    exit 1
fi
python3 --version
sleep 1

echo ""
echo "[2/4] Bagimliliklar yukleniyor..."
python3 -m pip install --quiet --upgrade pip --user
python3 -m pip install --quiet customtkinter pillow pyinstaller certifi --user

echo ""
echo "[3/4] Uygulama derleniyor (2-3 dakika)..."
echo ""

# Temizlik
rm -rf build dist __pycache__ *.spec 2>/dev/null

# PyInstaller PATH
export PATH="$PATH:$HOME/Library/Python/3.9/bin:$HOME/Library/Python/3.10/bin:$HOME/Library/Python/3.11/bin:$HOME/Library/Python/3.12/bin"

# MAC İÇİN ÖZEL BUILD - TKINTER FIX
python3 -m PyInstaller \
    --name=EmailOtomasyonu \
    --windowed \
    --onedir \
    --hidden-import=tkinter \
    --hidden-import=customtkinter \
    --hidden-import=PIL \
    --hidden-import=PIL._tkinter_finder \
    --collect-all=customtkinter \
    --collect-all=tkinter \
    --noconfirm \
    --clean \
    bulk_email_app.py

if [ ! -d "dist/EmailOtomasyonu.app" ]; then
    echo "❌ Build basarisiz!"
    echo ""
    echo "Hata ayiklama icin dist klasorunu kontrol edin"
    ls -la dist/ 2>/dev/null
    exit 1
fi

echo "✅ Build tamamlandi"

echo ""
echo "[4/4] Masaustune kopyalaniyor..."

DESKTOP="$HOME/Desktop"
TARGET_PATH="$DESKTOP/EmailOtomasyonu.app"

if [ -d "$DESKTOP" ]; then
    # Eski dosyayı sil
    rm -rf "$TARGET_PATH" 2>/dev/null
    
    # Yeni dosyayı kopyala
    cp -R "dist/EmailOtomasyonu.app" "$DESKTOP/"
    
    if [ -d "$TARGET_PATH" ]; then
        # Gatekeeper hatası önleme
        echo "Mac güvenlik ayarı düzeltiliyor..."
        xattr -cr "$TARGET_PATH" 2>/dev/null
        
        # Calıstırma izni ver
        chmod +x "$TARGET_PATH/Contents/MacOS/EmailOtomasyonu" 2>/dev/null
        
        echo "✅ BASARILI!"
        echo ""
        echo "Masaustunde: EmailOtomasyonu.app"
        echo ""
    else
        echo "⚠️  Masaustune kopyalanamadi"
        echo "dist klasorunde: EmailOtomasyonu.app"
        echo ""
    fi
else
    echo "⚠️  Masaustu bulunamadi"
    echo "dist klasorunde: EmailOtomasyonu.app"
fi

echo "===================================================="
echo "          KURULUM TAMAMLANDI!"
echo "===================================================="
echo ""
echo "Not: İlk açılışta Mac 'Uygulama acilamadi' diyebilir."
echo "Cozum: Sag tikla -> Ac"
echo ""
sleep 5
exit 0
