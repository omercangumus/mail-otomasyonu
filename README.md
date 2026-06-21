# 📧 EmailAI — Akıllı E-posta Asistanı

Şirket/kişi adı ver → yapay zeka onu **araştırır**, kişiye özel mail **yazar**,
(varsa) **mail adresini bulur** ve **gönderir**. Toplu mail de atabilirsin.
**Yapay zeka olmadan da** mail gönderme kısmı çalışır.

> Tasarım ilkesi: AI **uydurmaz**. Mail içeriğini gerçek web araştırmasına dayandırır
> (Gemini grounding). Mail adresini doğrulayamadığında "tahmin (doğrulanmadı)" diye
> açıkça işaretler — `verified`/`guessed`/`unknown`. Her mail göndermeden önce **sen onaylarsın**.

---

## ✨ Ne yapar?

- **AI Mail sekmesi:** Hedef listesi (Ad Soyad + şirket/site, LinkedIn URL ya da direkt mail) + bir "brief" (mailin amacı) ver. AI her hedefi araştırıp ayrı ayrı kişiselleştirilmiş taslak üretir. Düzenle, onayla, gönder.
  - Kullanım örnekleri: hocana tez savunması daveti, birden çok kişiye iş/işbirliği maili, etkinlik daveti, soğuk outreach…
- **Profilim sekmesi:** CV (PDF/TXT) yükle ya da kendini anlat → AI mailleri **senin ağzından** yazar.
- **Toplu Gönderim sekmesi:** Aynı maili çok kişiye. `{ad}` ile basit kişiselleştirme. LLM gerekmez.
- **Çoklu sağlayıcı (BYOK):** Kendi **Gemini** veya **OpenAI-uyumlu** API anahtarını getirirsin.
- **Güvenli:** Şifre ve API anahtarları `keyring` ile işletim sisteminin kasasında saklanır, `settings.json`'a **yazılmaz**.

---

## 🚀 Kurulum

Gereken: **Python 3.9+** ([python.org](https://www.python.org/downloads/)).
Windows/Mac'te `tkinter` Python ile birlikte gelir. Linux'ta ayrıca gerekir (aşağıda).

### Windows
1. `install.bat`'e çift tıkla (ilk seferde 2-3 dk).
2. Bitince `run.bat`'e çift tıkla.

### macOS / Linux
```bash
chmod +x install.sh run.sh
./install.sh
./run.sh
```
**Linux'ta tkinter:** `sudo apt install python3-tk` (Debian/Ubuntu) ·
`sudo dnf install python3-tkinter` (Fedora) · `sudo pacman -S tk` (Arch).

---

## 🔑 Anahtarları nereden alırım?

### 1) Gmail "Uygulama Şifresi" (mail göndermek için)
Normal Gmail şifren **çalışmaz**. Adımlar:
1. Google Hesabı → Güvenlik → **2 Adımlı Doğrulama**'yı aç.
2. [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) → 16 haneli şifre üret.
3. Ayarlar sekmesine: e-posta + bu uygulama şifresi. **SMTP Test Et**.
- Outlook/diğer: SMTP sunucu/portu ona göre gir (Gmail: `smtp.gmail.com` / `587`).

### 2) Gemini API anahtarı (AI için — önerilen)
- [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → ücretsiz anahtar.
- Ayarlar: Sağlayıcı `gemini`, Model `gemini-2.5-flash` (veya yeni `gemini-3.5-flash`), anahtarı yapıştır, **grounding açık**.
- Grounding (web araması) güncel modellerde aylık geniş ücretsiz kotayla gelir; aşınca sorgu başına ücretlenir.

### 3) OpenAI-uyumlu (alternatif)
- Sağlayıcı `openai`, Model (örn. `gpt-4o-mini`), gerekiyorsa **Base URL** (kendi/uyumlu endpoint), anahtar.
- Not: bu modda Google grounding yoktur; araştırma modelin kendi bilgisiyle sınırlı kalır.

### 4) Hunter.io (gerçek mail bulmak için — opsiyonel)
- Anahtar yoksa app, ad+domain'den **kalıp tahmini** yapar ve "doğrulanmadı" işaretler.
- Gerçek/doğrulanmış mail için [hunter.io](https://hunter.io) → API anahtarı (ücretsiz tier ayda ~25 arama). Ayarlar'a yapıştır.

---

## 🧭 Kullanım akışı (AI Mail)
1. **Profilim**'i doldur (CV yükle / kendini anlat) → Kaydet.
2. **Ayarlar**'da SMTP + LLM anahtarını gir → ikisini de test et → Kaydet.
3. **AI Mail**:
   - *Brief*: "Hocama YL tez savunmama davet maili" gibi.
   - *Hedefler*: her satıra bir kişi → `Ahmet Yılmaz, beko.com`
   - Ton + dil + (istersen HTML) seç → **Araştır & Taslak Üret**.
4. Her kart için mail/konu/gövdeyi düzenle, mail rozetine bak (`✓`/`≈`/`✗`), **onayla**.
5. **Onaylananları Gönder**.

---

## 🔒 Güvenlik & yasal
- Şifre/anahtarlar keyring'de; repoya/JSON'a sızmaz. `settings.json` ve `.venv` `.gitignore`'da.
- **Sorumlu kullanım:** Toplu/soğuk e-posta yasaya tabidir. Türkiye'de ticari ileti için **İYS (İleti Yönetim Sistemi) kaydı ve alıcı izni** gerekir; AB için GDPR. App, her mailde "almak istemiyorsanız bildirin" notu ekler ve gönderim öncesi insan onayı ister — ama **izinli listeye** göndermek senin sorumluluğunda.
- Gönderim arası gecikme (varsayılan 2 sn) ve günlük Gmail limiti (~500) sender itibarını korur. Çok yüksek hacim için profesyonel SMTP (SendGrid vb.) düşün.

---

## 📦 Çalıştırılabilir (.exe / .app) üretme
PyInstaller **çapraz derlemez**: her dosyayı kendi işletim sisteminde üret.
- **Windows:** `build.bat` → `dist\EmailAI.exe`
- **macOS:** `./build.sh` → `dist/EmailAI.app` (ilk açılış: sağ tık → Aç)
- **Linux:** `./build.sh` → `dist/EmailAI`
İkon istersen: `icon.ico` (Win), `icon.icns` (Mac), `icon.png` (Linux) koy.

---

## 🛠 Sorun giderme
| Sorun | Çözüm |
|------|-------|
| `No module named tkinter` | Linux: `python3-tk` kur. Win/Mac: Python'u python.org'dan yeniden kur. |
| Gmail "Authentication" hatası | Uygulama Şifresi kullan (normal şifre değil), 2FA açık olmalı. |
| AI "uydurma mail" verdi | Hunter anahtarı ekle; yoksa `≈ tahmin` rozetli mailleri elle doğrula. |
| Grounding pahalı/limit | Daha ucuz Flash model kullan; grounding'i kapatabilirsin (araştırma zayıflar). |
| PDF okunmuyor | `pip install pypdf` ya da CV'yi TXT/metin olarak yapıştır. |
| SmartScreen/Gatekeeper | Win: "Yine de çalıştır". Mac: `xattr -cr dist/EmailAI.app`. |

---

## 🗂 Dosya yapısı
```
app.py                 # arayüz (sekmeler)
core/
  settings.py          # ayarlar + keyring
  email_service.py     # SMTP gönderim (plain/HTML, ek)
  llm.py               # Gemini(grounding) + OpenAI-uyumlu
  finder.py            # Hunter + kalıp tahmini
  profile.py           # CV/PDF metin çıkarımı
install.* / run.* / build.*   # kurulum, çalıştırma, paketleme
requirements.txt
```

İyi gönderimler 🚀
