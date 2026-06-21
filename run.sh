#!/usr/bin/env bash
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || { echo "Önce ./install.sh çalıştır."; exit 1; }
python3 app.py
