# 📧 EmailAI — Akıllı E-posta Asistanı / Smart Email Assistant

[Türkçe](#türkçe) | [English](#english)

---

# Türkçe

Şirket/kişi adı ver → yapay zeka onu **araştırır**, kişiye özel mail **yazar**, (varsa) **mail adresini bulur** ve **gönderir**. Toplu mail de atabilirsin. **Yapay zeka olmadan da** mail gönderme kısmı çalışır.

> Tasarım ilkesi: AI **uydurmaz**. Mail içeriğini gerçek web araştırmasına dayandırır (Gemini grounding). Mail adresini doğrulayamadığında "tahmin (doğrulanmadı)" diye açıkça işaretler — `verified`/`guessed`/`unknown`. Her mail göndermeden önce **sen onaylarsın**.

---

## ✨ Ne yapar?

- **AI Mail sekmesi:** Hedef listesi (Ad Soyad + şirket/site, LinkedIn URL ya da direkt mail) + bir "brief" (mailin amacı) ver. AI her hedefi araştırıp ayrı ayrı kişiselleştirilmiş, ATS uyumlu taslak üretir. Düzenle, onayla, gönder.
  - Kullanım örnekleri: hocana tez savunması daveti, birden çok kişiye iş/işbirliği maili, etkinlik daveti, soğuk outreach…
  - **Ek Desteği:** Oluşturulan taslak maillere göndermeden önce dosya (PDF, Word, görsel vb.) ekleyebilirsiniz.
- **Profilim sekmesi:** CV (PDF/TXT/DOCX) yükle ya da kendini anlat → AI mailleri **senin ağzından** yazsın.
  - **Word (.docx) Okuyucu:** CV'lerinizi `.docx` formatında da doğrudan yükleyebilirsiniz.
- **Toplu Gönderim sekmesi:** Aynı maili çok kişiye. `{ad}` ile basit kişiselleştirme. LLM gerekmez.
- **Gerçek Zamanlı Otomatik Kayıt (Auto-Save):** Yazdığınız veya değiştirdiğiniz tüm alanlar (brief, alıcılar, profiller, SMTP ayarları, API anahtarları vb.) arka planda anlık olarak kaydedilir.
- **Dinamik Dil Desteği:** Sol panelden Türkçe ve English arasında tek tıkla geçiş yapabilirsiniz, tüm arayüz anında güncellenir.
- **Çoklu sağlayıcı (BYOK):** Kendi **Gemini**, **OpenRouter** veya **OpenAI-uyumlu** API anahtarını getirirsin.
- **Güvenli:** Şifre ve API anahtarları `keyring` ile işletim sisteminin kasasında saklanır, `settings.json`'a **yazılmaz**.

---

## 🚀 Başlatma (tek tıkla)

Gereken: **Python 3.9+** ([python.org](https://www.python.org/downloads/)).
Windows/Mac'te `tkinter` Python ile birlikte gelir. Linux'ta ayrıca gerekir (aşağıda).

### Windows
`BASLAT.bat`'e çift tıkla — ilk açılışta venv oluşturur ve bağımlılıkları kurar (2-3 dk), sonraki açılışlarda direkt başlar.

### macOS
`BASLAT.command`'a çift tıkla (ilk seferinde Terminal açılabilir — normal).

### Linux (terminalde)
```bash
chmod +x BASLAT.command   # bir kez
./BASLAT.command
```
**Linux'ta tkinter:** `sudo apt install python3-tk` (Debian/Ubuntu) · `sudo dnf install python3-tkinter` (Fedora) · `sudo pacman -S tk` (Arch).

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
- Ayarlar: Sağlayıcı `gemini`, Model `gemini-2.5-flash` (veya `gemini-3.5-flash`), anahtarı yapıştır, **grounding açık**.
- Grounding (web araması) güncel modellerde aylık geniş ücretsiz kotayla gelir; aşınca sorgu başına ücretlenir.

### 3) OpenRouter (çok model, tek anahtar — önerilen alternatif)
- [openrouter.ai/keys](https://openrouter.ai/keys) → anahtar al. Ayarlar'da sağlayıcı **OpenRouter** seç.
- Model: açılır listeden seç (Claude, GPT, Gemini, DeepSeek, Llama…) **ya da** openrouter.ai/models'tan kopyaladığın herhangi bir slug'ı elle yaz.
- **İnternet araması** kutusu açıkken model slug'ına otomatik `:online` eklenir → model web'de araştırır.

### 4) OpenAI / Özel endpoint
- Sağlayıcı `OpenAI / Özel`, Model (örn. `gpt-4o-mini`), gerekiyorsa **Base URL** (uyumlu endpoint), anahtar.

### 5) Hunter.io (gerçek mail bulmak için — opsiyonel)
- Anahtar yoksa app, ad+domain'den **kalıp tahmini** yapar ve "doğrulanmadı" işaretler.
- Gerçek/doğrulanmış mail için [hunter.io](https://hunter.io) → API anahtarı.

---

## 🧭 Kullanım akışı (AI Mail)
1. **Profilim**'i doldur (CV yükle / kendini anlat). Otomatik kaydedilir.
2. **Ayarlar**'da SMTP + LLM anahtarını gir → test et. Otomatik kaydedilir.
3. **AI Mail**:
   - *Brief*: "Hocama YL tez savunmama davet maili" gibi.
   - *Hedefler*: her satıra bir kişi → `Ahmet Yılmaz, beko.com`
   - Ton + dil + uzunluk + (istersen ek dosya ve HTML) seç → **Araştır & Taslak Üret**.
4. Her kart için mail/konu/gövdeyi düzenle, mail rozetine bak (`✓`/`≈`/`✗`), **onayla**.
5. **Onaylananları Gönder**.

---

## 🔒 Güvenlik & yasal
- Şifre/anahtarlar keyring'de; repoya/JSON'a sızmaz. `settings.json` ve `.venv` `.gitignore`'da.
- **Sorumlu kullanım:** Toplu/soğuk e-posta yasaya tabidir. Türkiye'de ticari ileti için **İYS (İleti Yönetim Sistemi) kaydı ve alıcı izni** gerekir; AB için GDPR. App, her mailde "almak istemiyorsanız bildirin" notu ekler ve gönderim öncesi insan onayı ister — ama **izinli listeye** göndermek senin sorumluluğunda.

---

## 📦 Paylaşım için .exe / .app üretme

| Platform | Komut | Çıktı |
|----------|-------|-------|
| Windows | `build.bat` | `dist\EmailAI.exe` |
| macOS | `./build.sh` | `dist/EmailAI.app` |
| Linux | `./build.sh` | `dist/EmailAI` |

---

## 🛠 Sorun giderme
| Sorun | Çözüm |
|------|-------|
| `No module named tkinter` | Linux: `python3-tk` kur. Win/Mac: Python'u yeniden kur. |
| Gmail "Authentication" hatası | Uygulama Şifresi kullan (normal şifre değil), 2FA açık olmalı. |
| AI "uydurma mail" verdi | Hunter anahtarı ekle; yoksa `≈ tahmin` rozetli mailleri elle doğrula. |
| Grounding pahalı/limit | Daha ucuz Flash model kullan; grounding'i kapatabilirsin. |
| PDF okunmuyor | `pypdf` ve `pymupdf` yüklü olmalı, veya CV'yi metin olarak yapıştır. |
| SmartScreen/Gatekeeper | Win: "Yine de çalıştır". Mac: `xattr -cr dist/EmailAI.app`. |

---

## 🗂 Dosya yapısı
```
app.py                        # arayüz (sol menü: Oluştur · Toplu · Profil · Ayarlar)
core/
  settings.py                 # ayarlar + keyring
  email_service.py            # SMTP gönderim (SSL/STARTTLS otomatik, Türkçe ad desteği)
  llm.py                      # Gemini · OpenRouter · OpenAI-uyumlu
  finder.py                   # Hunter + kalıp tahmini (sosyal medya hariç)
  profile.py                  # CV/PDF/DOCX metin çıkarımı
  i18n.py                     # Çok dilli arayüz çevirileri (TR / EN)
BASLAT.bat / BASLAT.command   # tek tıkla başlatıcı (Win / Mac-Linux)
build.bat / build.sh          # PyInstaller ile .exe/.app üretme
requirements.txt
```

---
---

# English

Provide a company/person name → AI **researches** them, writes a **personalized email**, **finds the email address** (if available), and **sends** it. You can also send bulk emails. The sending part works **even without AI**.

> Design principle: AI **does not hallucinate**. It bases email content on real web research (Gemini grounding). When it cannot verify an email address, it clearly flags it as "guessed (unverified)" — `verified`/`guessed`/`unknown`. You **approve** every email before it is sent.

---

## ✨ What it does

- **AI Mail Tab:** Provide a target list (Name + Company/site, LinkedIn URL, or direct email) + a "brief" (purpose of the email). AI researches each target and drafts a custom, personalized, and ATS-friendly email. Edit, approve, and send.
  - Use cases: inviting a professor to your thesis defense, job or partnership applications to multiple contacts, event invitations, cold outreach…
  - **Attachments Support:** You can add attachments (PDF, Word, images, etc.) to the generated drafts before sending.
- **My Profile Tab:** Upload your CV (PDF/TXT/DOCX) or describe yourself → AI writes emails **in your voice**.
  - **Word (.docx) Reader:** You can directly upload `.docx` format CVs.
- **Bulk Send Tab:** Same email to many people. Simple personalization with `{name}`. No LLM required.
- **Real-Time Auto-Save:** All input fields, targets, profiles, SMTP settings, and API keys are saved automatically in the background as you type or change them.
- **Dynamic UI Language:** Switch between Turkish and English with a single click in the left sidebar; the entire UI refreshes instantly.
- **Multi-provider (BYOK):** Bring your own **Gemini**, **OpenRouter**, or **OpenAI-compatible** API key.
- **Secure:** SMTP passwords and API keys are securely stored in the OS credential manager via `keyring`, and never written to `settings.json`.

---

## 🚀 Getting Started (One-click)

Requires: **Python 3.9+** ([python.org](https://www.python.org/downloads/)).
Tkinter comes pre-installed with Python on Windows/Mac. Linux requires a manual install (see below).

### Windows
Double-click `BASLAT.bat` — it creates a virtual environment (venv) and installs dependencies on the first run (takes 2-3 mins), then launches the app directly on subsequent runs.

### macOS
Double-click `BASLAT.command` (Terminal may open on the first run — this is normal).

### Linux (via Terminal)
```bash
chmod +x BASLAT.command   # once
./BASLAT.command
```
**Tkinter on Linux:** `sudo apt install python3-tk` (Debian/Ubuntu) · `sudo dnf install python3-tkinter` (Fedora) · `sudo pacman -S tk` (Arch).

---

## 🔑 Where do I get the keys?

### 1) Gmail "App Password" (for sending emails)
Your normal Gmail password **will not work**. Steps:
1. Google Account → Security → Turn on **2-Step Verification**.
2. [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) → Generate a 16-character App Password.
3. Settings tab: Enter your email + this app password. **Test SMTP Connection**.
- Outlook/Other: Enter SMTP server/port accordingly (Gmail: `smtp.gmail.com` / `587`).

### 2) Gemini API Key (for AI — recommended)
- [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → Get a free key.
- Settings: Provider `gemini`, Model `gemini-2.5-flash` (or `gemini-3.5-flash`), paste the key, and keep **grounding enabled**.
- Grounding (web search) comes with a generous monthly free quota on modern models.

### 3) OpenRouter (many models, single key — recommended alternative)
- [openrouter.ai/keys](https://openrouter.ai/keys) → Get a key. Select **OpenRouter** as provider in Settings.
- Model: Select from dropdown (Claude, GPT, Gemini, DeepSeek, Llama…) **or** type any model slug manually from openrouter.ai/models.
- When the **Web Search** checkbox is checked, `:online` is appended to the model slug → model researches the web.

### 4) OpenAI / Custom Endpoint
- Provider `OpenAI / Custom`, Model (e.g., `gpt-4o-mini`), **Base URL** (compatible endpoint) if needed, and API key.

### 5) Hunter.io (for email discovery — optional)
- If empty, the app will make a **pattern guess** based on name and domain, and flag it as unverified.
- For verified emails, go to [hunter.io](https://hunter.io) → get API key (free tier includes ~25 searches/month).

---

## 🧭 Workflow (AI Mail)
1. Fill out **My Profile** (upload CV / write bio). Saved automatically.
2. Enter SMTP + LLM keys in **Settings** → test them. Saved automatically.
3. **AI Mail**:
   - *Brief*: e.g. "Invite my professor to my MSc thesis defense"
   - *Targets*: one per line → `John Smith, acme.com`
   - Select Tone + language + length + (optionally attachments & HTML) → **Research & Generate Draft**.
4. Review/edit the subject, email body, check the email confidence badge (`✓`/`≈`/`✗`), and **approve**.
5. **Send Approved**.

---

## 🔒 Security & Legal Compliance
- Passwords and keys are stored in keyring, never leaked to git/JSON. `settings.json` and `.venv` are ignored.
- **Responsible outreach:** Cold emails are subject to regulations (GDPR in EU, CAN-SPAM in US, IYS in Turkey). The app adds an opt-out footer and requires manual human review before sending — but sending to **opted-in lists** is your responsibility.

---

## 📦 Packaging .exe / .app (PyInstaller)

| Platform | Command | Output |
|----------|---------|--------|
| Windows | `build.bat` | `dist\EmailAI.exe` |
| macOS | `./build.sh` | `dist/EmailAI.app` |
| Linux | `./build.sh` | `dist/EmailAI` |

---

## 🛠 Troubleshooting
| Issue | Solution |
|------|----------|
| `No module named tkinter` | Linux: install `python3-tk`. Win/Mac: reinstall Python. |
| Gmail "Authentication" Error | Use Google App Password (not normal password) with 2FA turned on. |
| AI provided "fake email" | Add Hunter.io API key, or manually verify `≈ guessed` emails. |
| Grounding expensive/limits | Use a cheaper model (Flash) or turn off grounding (lowers research quality). |
| PDF not reading | Make sure `pypdf` and `pymupdf` are installed, or paste CV as text. |
| SmartScreen/Gatekeeper | Win: Click "Run anyway". Mac: Run `xattr -cr dist/EmailAI.app`. |

---

## 🗂 File Structure
```
app.py                        # GUI (sidebar: Compose · Bulk · Profile · Settings)
core/
  settings.py                 # Settings manager + keyring
  email_service.py            # SMTP sending (SSL/STARTTLS auto, Unicode support)
  llm.py                      # Gemini · OpenRouter · OpenAI-compatible client
  finder.py                   # Hunter.io + email pattern guesser (skips social media)
  profile.py                  # CV reader (PDF/TXT/DOCX)
  i18n.py                     # Multi-language translations (TR / EN)
BASLAT.bat / BASLAT.command   # One-click launchers (Win / Mac-Linux)
build.bat / build.sh          # Packaging executable files via PyInstaller
requirements.txt
```

---

Good sending! 🚀
