#!/usr/bin/env bash
# EmailAI kurulum — macOS & Linux
set -e
cd "$(dirname "$0")"

echo "==> Python kontrol ediliyor..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "HATA: python3 bulunamadı. https://www.python.org/downloads/ adresinden kur."
  exit 1
fi
PYV=$(python3 -c 'import sys;print(".".join(map(str,sys.version_info[:2])))')
echo "    Python $PYV"

# Linux'ta tkinter kontrolü
if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
  echo "==> tkinter eksik."
  if [ "$(uname)" = "Linux" ]; then
    echo "    Debian/Ubuntu:  sudo apt install -y python3-tk"
    echo "    Fedora:         sudo dnf install -y python3-tkinter"
    echo "    Arch:           sudo pacman -S tk"
    echo "Kurup tekrar çalıştır."
    exit 1
  fi
fi

echo "==> Sanal ortam (venv) oluşturuluyor..."
python3 -m venv .venv
source .venv/bin/activate

echo "==> Bağımlılıklar yükleniyor..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "✅ Kurulum tamam!"
echo "Çalıştırmak için:"
echo "    source .venv/bin/activate && python3 app.py"
echo "(veya:  ./run.sh )"
