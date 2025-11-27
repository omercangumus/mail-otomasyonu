# 🍎 MAC İÇİN BUILD TALİMATLARI

## AWS veya Mac'te Çalıştır

### Adım 1: Bağımlılıkları Yükle
```bash
pip3 install -r requirements.txt
pip3 install pyinstaller
```

### Adım 2: .app Oluştur
```bash
pyinstaller --name="Email Otomasyonu" \
    --onefile \
    --windowed \
    --icon=icon.ico \
    --clean \
    bulk_email_app.py
```

### Adım 3: Oluşan Dosya
```
dist/Email Otomasyonu.app
```

Çift tıkla → Açılır!

---

## Veya build_mac.sh Kullan

```bash
chmod +x build_mac.sh
./build_mac.sh
```

Otomatik build yapar ve masaüstüne kopyalar.

---

## Not
Bu işlem sadece **Mac** sistemlerde çalışır.
