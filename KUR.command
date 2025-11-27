#!/bin/bash
# Email Otomasyonu - Mac Kurulum

set -e  # Exit on error

clear
echo "===================================================="
echo " EMAIL OTOMASYONU - KURULUM"
echo "===================================================="
echo ""
read -p "Başlamak için Enter'a basın..." 

# Script dizinine git
cd "$(dirname "$0")"
echo "Çalışma dizini: $(pwd)"
echo ""

# Python kontrolü
echo "[1/4] Python kontrolu..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 bulunamadı!"
    echo ""
    echo "Çözüm:"
    echo "1. https://python.org adresinden Python 3 indirin"
    echo "2. Kurulumu tamamlayıp bu scripti tekrar çalıştırın"
    echo ""
    read -p "Enter'a basarak çıkın..."
    exit 1
fi

PY_VER=$(python3 --version)
echo "[OK] $PY_VER bulundu."
sleep 1

# Bağımlılıklar
echo ""
echo "[2/4] Bağımlılıklar yükleniyor..."

if [ -f "install_animation.py" ]; then
    python3 install_animation.py || {
        echo "⚠️  Animasyon hata verdi, manuel devam..."
        python3 -m pip install --quiet --upgrade pip --user
        python3 -m pip install --quiet customtkinter pillow pyinstaller certifi --user
    }
else
    echo "[MANUEL] pip install..."
    python3 -m pip install --quiet --upgrade pip --user
    python3 -m pip install --quiet customtkinter pillow pyinstaller certifi --user
fi

# Derleme
echo ""
echo "[3/4] Uygulama derleniyor (2-3 dakika)..."
echo ""

# Temizlik
rm -rf build dist __pycache__ *.spec 2>/dev/null

# PyInstaller PATH
export PATH="$PATH:$HOME/Library/Python/3.9/bin:$HOME/Library/Python/3.10/bin:$HOME/Library/Python/3.11/bin:$HOME/Library/Python/3.12/bin:$HOME/Library/Python/3.13/bin"

# Derle
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
    echo "❌ Derleme başarısız!"
    echo ""
    echo "dist klasörünü kontrol edin:"
    ls -la dist/ 2>/dev/null || echo "dist klasörü yok!"
    echo ""
    read -p "Enter'a basarak çıkın..."
    exit 1
fi

echo "[OK] Derleme tamamlandı!"

# Masaüstüne kopyala
echo ""
echo "[4/4] Masaüstüne kopyalanıyor..."

DESKTOP="$HOME/Desktop"
TARGET="$DESKTOP/EmailOtomasyonu.app"

if [ -d "$DESKTOP" ]; then
    # Eski dosyayı sil
    rm -rf "$TARGET" 2>/dev/null
    
    # Yeni dosyayı kopyala
    cp -R "dist/EmailOtomasyonu.app" "$DESKTOP/"
    
    if [ -d "$TARGET" ]; then
        # Gatekeeper sorununu çöz
        echo "Mac güvenlik ayarları düzeltiliyor..."
        xattr -cr "$TARGET" 2>/dev/null || true
        chmod +x "$TARGET/Contents/MacOS/EmailOtomasyonu" 2>/dev/null || true
        
        echo "[OK] Masaüstüne kopyalandı!"
    else
        echo "⚠️  Kopyalama başarısız!"
        echo "dist klasöründe: EmailOtomasyonu.app"
    fi
else
    echo "⚠️  Masaüstü bulunamadı!"
    echo "dist klasöründe: EmailOtomasyonu.app"
fi

echo ""
echo "===================================================="
echo "          KURULUM TAMAMLANDI!"
echo "===================================================="
echo ""
echo "NOT: İlk açılışta 'Uygulama açılamadı' diyebilir."
echo "Çözüm: Sağ tık -> Aç"
echo ""
sleep 5
