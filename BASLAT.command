#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/activate" ]; then
    echo "[1/3] Sanal ortam olusturuluyor..."
    python3 -m venv .venv || { echo "HATA: python3 bulunamadi."; exit 1; }
    echo "[2/3] Bagimliliklar yukleniyor..."
    source .venv/bin/activate
    pip install -r requirements.txt || { echo "HATA: Bagimlilik kurulumu basarisiz."; exit 1; }
else
    source .venv/bin/activate
fi

echo "[3/3] Uygulama baslatiliyor..."
python3 app.py
