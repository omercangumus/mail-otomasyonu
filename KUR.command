#!/bin/bash
# ====================================================
# EMAIL OTOMASYONU - OTOMATİK KURULUM (Mac)
# ====================================================
# Kullanım: Bu dosyaya çift tıkla!
# ====================================================

# Terminal başlığını ayarla
echo -ne "\033]0;Email Otomasyonu - Kurulum\007"

clear
echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║                                                   ║"
echo "║     📧 EMAIL OTOMASYONU - OTOMATİK KURULUM       ║"
echo "║                                                   ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "Bu script otomatik olarak:"
echo "  ✅ Python kontrolü yapacak"
echo "  ✅ Bağımlılıkları yükleyecek"
echo "  ✅ Uygulamayı derleyecek"
echo "  ✅ Masaüstüne kopyalayacak"
echo ""
read -p "Başlamak için Enter'a bas..." 

# Renk kodları
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Script'in bulunduğu klasöre git
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "📂 Çalışma dizini: $SCRIPT_DIR"
echo ""

echo -e "${BLUE}[1/5] Python kontrolü...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 bulunamadı!${NC}"
    echo ""
    echo "Python yüklemek için:"
    echo "  1. https://python.org adresine git"
    echo "  2. 'Download Python' butonuna tıkla"
    echo "  3. İndirdiğin dosyayı çalıştır"
    echo ""
    read -p "Devam etmek için bir tuşa bas..."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION bulundu${NC}"
sleep 1

echo ""
echo -e "${BLUE}[2/5] Bağımlılıklar yükleniyor...${NC}"
echo "Bu işlem biraz zaman alabilir, lütfen bekleyin..."

python3 -m pip install --upgrade pip --quiet --user
python3 -m pip install -r requirements.txt --quiet --user

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Bağımlılıklar yüklenemedi!${NC}"
    read -p "Devam etmek için bir tuşa bas..."
    exit 1
fi

echo -e "${GREEN}✅ Bağımlılıklar yüklendi${NC}"
sleep 1

echo ""
echo -e "${BLUE}[3/5] PyInstaller yükleniyor...${NC}"
python3 -m pip install pyinstaller --quiet --user

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ PyInstaller yüklenemedi!${NC}"
    read -p "Devam etmek için bir tuşa bas..."
    exit 1
fi

echo -e "${GREEN}✅ PyInstaller yüklendi${NC}"
sleep 1

echo ""
echo -e "${BLUE}[4/5] Uygulama derleniyor...${NC}"
echo "Bu işlem 2-3 dakika sürebilir, lütfen bekleyin..."
echo ""

# Eski build dosyalarını temizle
rm -rf build dist __pycache__ *.spec 2>/dev/null

# PyInstaller PATH'e ekle
export PATH="$PATH:$HOME/Library/Python/3.9/bin:$HOME/Library/Python/3.10/bin:$HOME/Library/Python/3.11/bin:$HOME/Library/Python/3.12/bin"

# .app oluştur
python3 -m PyInstaller --name="Email Otomasyonu" \
    --onefile \
    --windowed \
    --icon=icon.ico \
    --clean \
    --noconfirm \
    bulk_email_app.py

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ PyInstaller çalıştırılamadı!${NC}"
    echo ""
    echo "Manuel olarak deneyin:"
    echo "  python3 -m PyInstaller --name=\"Email Otomasyonu\" --onefile --windowed bulk_email_app.py"
    echo ""
    read -p "Devam etmek için bir tuşa bas..."
    exit 1
fi

# .app dosyasını kontrol et
if [ ! -d "dist/Email Otomasyonu.app" ]; then
    echo ""
    echo -e "${RED}❌ .app dosyası oluşturulamadı!${NC}"
    echo ""
    echo "Lütfen 'dist' klasörünü kontrol edin."
    ls -la dist/ 2>/dev/null || echo "dist klasörü bulunamadı"
    echo ""
    read -p "Devam etmek için bir tuşa bas..."
    exit 1
fi

echo -e "${GREEN}✅ Uygulama derlendi${NC}"
sleep 1

echo ""
echo -e "${BLUE}[5/5] Masaüstüne kopyalanıyor...${NC}"

DESKTOP="$HOME/Desktop"

if [ -d "dist/Email Otomasyonu.app" ]; then
    echo "📦 dist/Email Otomasyonu.app bulundu"
    
    if [ -d "$DESKTOP" ]; then
        echo "📁 Masaüstü: $DESKTOP"
        
        # Eski dosyayı sil
        if [ -d "$DESKTOP/Email Otomasyonu.app" ]; then
            echo "🗑️  Eski dosya siliniyor..."
            rm -rf "$DESKTOP/Email Otomasyonu.app"
        fi
        
        # Yeni dosyayı kopyala
        echo "📋 Kopyalanıyor..."
        cp -R "dist/Email Otomasyonu.app" "$DESKTOP/"
        
        # Kontrol et
        if [ -d "$DESKTOP/Email Otomasyonu.app" ]; then
            echo -e "${GREEN}✅ Masaüstüne kopyalandı!${NC}"
            echo ""
            echo "📍 Dosya yolu: $DESKTOP/Email Otomasyonu.app"
        else
            echo -e "${YELLOW}⚠️  Kopyalanamadı${NC}"
            echo "📂 Dosyayı 'dist' klasöründe bulabilirsiniz"
            echo "   Yol: $SCRIPT_DIR/dist/Email Otomasyonu.app"
        fi
    else
        echo -e "${YELLOW}⚠️  Masaüstü bulunamadı${NC}"
        echo "📂 Dosyayı 'dist' klasöründe bulabilirsiniz"
    fi
else
    echo -e "${RED}❌ dist/Email Otomasyonu.app bulunamadı!${NC}"
fi

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║                                                   ║"
echo "║          🎉 KURULUM TAMAMLANDI! 🎉               ║"
echo "║                                                   ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Uygulamanız kullanıma hazır!${NC}"
echo ""

if [ -d "$DESKTOP/Email Otomasyonu.app" ]; then
    echo "Masaüstünde 'Email Otomasyonu.app' dosyasını bulacaksınız."
else
    echo "Uygulama: $SCRIPT_DIR/dist/Email Otomasyonu.app"
fi

echo "Çift tıklayın ve kullanmaya başlayın!"
echo ""

# İlk açılışta Gatekeeper uyarısı için bilgilendirme
echo -e "${YELLOW}💡 İlk açılışta 'Güvenilmeyen Geliştirici' uyarısı alabilirsiniz.${NC}"
echo ""
echo "Çözüm 1 - Sistem Tercihleri:"
echo "  Sistem Tercihleri → Güvenlik ve Gizlilik → 'Yine de Aç'"
echo ""
echo "Çözüm 2 - Terminal komutu:"
if [ -d "$DESKTOP/Email Otomasyonu.app" ]; then
    echo "  xattr -cr ~/Desktop/Email\\ Otomasyonu.app"
else
    echo "  xattr -cr '$SCRIPT_DIR/dist/Email Otomasyonu.app'"
fi
echo ""
echo -e "${GREEN}5 saniye sonra kapanıyor...${NC}"
sleep 5

exit 0
