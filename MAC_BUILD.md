# Mac İçin Kurulum Rehberi

## 🚀 Hızlı Kurulum (Önerilen)

1. `KUR.command` dosyasına çift tıklayın.
2. Açılan terminal penceresinde kurulumun tamamlanmasını bekleyin.
3. Masaüstüne `EmailOtomasyonu` uygulaması gelecektir.

> **Not:** Eğer "Geliştiricisi doğrulanamadı" hatası alırsanız:
> Uygulamaya **Sağ Tık -> Aç** diyerek açın.

---

## 🛠 Manuel Kurulum (Alternatif)

Eğer otomatik kurulum çalışmazsa:

1. Terminali açın
2. Proje klasörüne gidin:
   ```bash
   cd /path/to/folder
   ```
3. Gerekli paketleri yükleyin:
   ```bash
   pip3 install customtkinter pillow pyinstaller certifi
   ```
4. Uygulamayı çalıştırın:
   ```bash
   python3 bulk_email_app.py
   ```

## ⚠️ Sık Karşılaşılan Sorunlar

**"Uygulama hasarlı" veya "Açılamıyor" hatası:**
Terminalde şu komutu çalıştırın:
```bash
xattr -cr ~/Desktop/EmailOtomasyonu.app
```

**Python bulunamadı hatası:**
Mac'inizde Python 3 yüklü olduğundan emin olun. Terminale `python3 --version` yazarak kontrol edebilirsiniz.
