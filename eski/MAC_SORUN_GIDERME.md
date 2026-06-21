# 📧 Email Otomasyonu - Mac Sorun Giderme

## ❌ "Uygulama açılamadı" hatası

### Çözüm 1: Sağ tıkla + Aç
1. EmailOtomasyonu.app'e **SAĞ TIKLA**
2. **"Aç"** seçeneğini tıkla
3. "Yine de aç" butonuna tıkla

### Çözüm 2: Terminal komutu
```bash
xattr -cr ~/Desktop/EmailOtomasyonu.app
chmod +x ~/Desktop/EmailOtomasyonu.app/Contents/MacOS/EmailOtomasyonu
open ~/Desktop/EmailOtomasyonu.app
```

### Çözüm 3: Sistem Tercihleri
1. Sistem Tercihleri → Güvenlik ve Gizlilik
2. "Yine de Aç" butonuna tıkla

---

## 💡 Eğer Hiçbiri İşe Yaramazsa

Terminal'den direkt çalıştır:
```bash
cd ~/Desktop
python3 -m pip install customtkinter pillow
python3 bulk_email_app.py
```

Bu Python script'ini direkt çalıştırır (build olmadan).
