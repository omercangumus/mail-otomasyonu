#!/usr/bin/env bash
# Tek dosya çalıştırılabilir üretir (macOS .app / Linux binary).
# ÖNEMLİ: Windows .exe için bu script DEĞİL, build.bat'i WINDOWS'ta çalıştır.
# PyInstaller çapraz derleme yapmaz: her .exe/.app kendi OS'unda üretilir.
set -e
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || { echo "Önce ./install.sh"; exit 1; }
pip install pyinstaller -q

ICON_ARG=""
[ -f icon.icns ] && ICON_ARG="--icon icon.icns"   # macOS
[ -f icon.png ] && [ "$(uname)" = "Linux" ] && ICON_ARG="--icon icon.png"

pyinstaller --noconfirm --clean --windowed --onefile \
  --name EmailAI $ICON_ARG \
  --collect-all customtkinter \
  app.py

echo ""
echo "✅ Çıktı: dist/EmailAI"
[ "$(uname)" = "Darwin" ] && echo "macOS app: dist/EmailAI.app  (ilk açılışta: sağ tık > Aç)"
