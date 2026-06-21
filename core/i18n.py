"""Çok dilli arayüz desteği (TR / EN).
set_ui_lang() ile dil ayarlanır; t(key) ile çeviri alınır.
Uygulama başlangıcında Settings'den okunan 'ui_lang' değeri kullanılır.
"""

_lang = "tr"

# ── Temel string'ler ──────────────────────────────────────────────
_S = {
    # Sidebar
    "app_subtitle":     {"tr": "akıllı mail asistanı",        "en": "smart email assistant"},
    "nav_compose":      {"tr": "Oluştur",                     "en": "Compose"},
    "nav_bulk":         {"tr": "Toplu Gönder",                "en": "Bulk Send"},
    "nav_profile":      {"tr": "Profil",                      "en": "Profile"},
    "nav_settings":     {"tr": "Ayarlar",                     "en": "Settings"},
    "status_mail":      {"tr": "● Mail: ",                    "en": "● Mail: "},
    "status_ai":        {"tr": "● Yapay zeka: ",              "en": "● AI: "},
    "status_ready":     {"tr": "hazır",                       "en": "ready"},
    "status_missing":   {"tr": "eksik",                       "en": "missing"},

    # Compose
    "compose_title":    {"tr": "✨ AI ile Mail Oluştur",      "en": "✨ Compose with AI"},
    "compose_sub":      {"tr": "Kime + ne yazılacağını söyle, gerisini AI halletsin.",
                         "en": "Tell who and what to write, AI handles the rest."},
    "card_purpose":     {"tr": "1 · Amaç & detay",           "en": "1 · Purpose & detail"},
    "purpose_label":    {"tr": "Mail ne hakkında?",           "en": "What is the email about?"},
    "detail_label":     {"tr": "Detay (serbest yaz: bağlam, ne istediğin, özel notlar)",
                         "en": "Detail (free text: context, what you want, notes)"},
    "card_target":      {"tr": "2 · Kime?  (her satıra biri: Ad Soyad, şirket/site ya da LinkedIn linki)",
                         "en": "2 · To whom?  (one per line: Name, company/site or LinkedIn link)"},
    "target_ph":        {"tr": "Ahmet Yılmaz, beko.com\nhttps://www.linkedin.com/in/ornek\nali@firma.com",
                         "en": "John Smith, acme.com\nhttps://www.linkedin.com/in/example\njohn@company.com"},
    "card_tone":        {"tr": "3 · Üslup & zamanlama",      "en": "3 · Tone & scheduling"},
    "length_label":     {"tr": "Uzunluk:",                    "en": "Length:"},
    "time_label":       {"tr": "Saat:",                       "en": "Time:"},
    "time_empty":       {"tr": "(boş=hemen)",                 "en": "(empty=now)"},
    "btn_generate":     {"tr": "✨  Araştır & Taslak Üret",  "en": "✨  Research & Generate Draft"},
    "drafts_label":     {"tr": "Taslaklar",                   "en": "Drafts"},
    "btn_send_sel":     {"tr": "🚀  Onaylananları Gönder",   "en": "🚀  Send Approved"},
    "generating":       {"tr": "Üretiliyor…",                 "en": "Generating…"},
    "researching":      {"tr": "🔎 Araştırılıyor…  {i}/{n}", "en": "🔎 Researching…  {i}/{n}"},
    "gen_done":         {"tr": "✓ Hazır. Düzenle, onayla, gönder.",
                         "en": "✓ Ready. Edit, approve, send."},
    "no_ai_title":      {"tr": "Yapay zeka yok",             "en": "No AI"},
    "no_ai_msg":        {"tr": "AI üretimi için Ayarlar'da bir API anahtarı gir.\n"
                               "(Anahtarsız 'Toplu Gönder'i kullanabilirsin.)",
                         "en": "Enter an API key in Settings for AI generation.\n"
                               "(Without a key, you can use 'Bulk Send'.)"},
    "no_target_title":  {"tr": "Hedef yok",                  "en": "No target"},
    "no_target_msg":    {"tr": "En az bir kişi gir.",        "en": "Enter at least one person."},
    "badge_verified":   {"tr": "✓ doğrulandı",               "en": "✓ verified"},
    "badge_guessed":    {"tr": "≈ tahmin (kontrol et)",      "en": "≈ guessed (check)"},
    "badge_unknown":    {"tr": "✗ mail yok",                 "en": "✗ no email"},
    "source_prefix":    {"tr": "Kaynak: ",                   "en": "Source: "},
    "send_title":       {"tr": "Gönder",                     "en": "Send"},
    "no_valid_draft":   {"tr": "Onaylı + geçerli mailli taslak yok.",
                         "en": "No approved draft with valid email."},
    "confirm_title":    {"tr": "Onay",                       "en": "Confirm"},
    "scheduled_note":   {"tr": "\n(Zamanlı: uygulama açık kalmalı.)",
                         "en": "\n(Scheduled: app must stay open.)"},
    "continue_q":       {"tr": "\nDevam?",                   "en": "\nContinue?"},
    "when_now":         {"tr": "hemen",                      "en": "now"},
    "queued":           {"tr": "Sırada…",                    "en": "Queued…"},
    "sending":          {"tr": "Gönderiliyor…",              "en": "Sending…"},
    "done_title":       {"tr": "Bitti",                      "en": "Done"},
    "html_label":       {"tr": "HTML",                       "en": "HTML"},

    # Bulk
    "bulk_title":       {"tr": "📨 Toplu Gönderim",         "en": "📨 Bulk Send"},
    "bulk_sub":         {"tr": "Aynı maili çok kişiye. Yapay zeka gerekmez.",
                         "en": "Same email to many people. No AI needed."},
    "card_content":     {"tr": "Mail içeriği",               "en": "Email content"},
    "subject_ph":       {"tr": "Konu",                       "en": "Subject"},
    "bulk_msg_label":   {"tr": "Mesaj  ({ad} ile kişiselleştir)",
                         "en": "Message  (personalize with {name})"},
    "html_send":        {"tr": "HTML olarak gönder",         "en": "Send as HTML"},
    "card_recipients":  {"tr": "Alıcılar  (her satır:  mail   ya da   mail, Ad)",
                         "en": "Recipients  (each line:  email   or   email, Name)"},
    "btn_import":       {"tr": "📥 Dosyadan Yükle",         "en": "📥 Load from File"},
    "att_none":         {"tr": "Ek: yok",                    "en": "Attachment: none"},
    "att_prefix":       {"tr": "Ek: ",                       "en": "Att: "},
    "btn_pick_att":     {"tr": "Ek Seç",                     "en": "Pick File"},
    "btn_remove":       {"tr": "Kaldır",                     "en": "Remove"},
    "schedule_label":   {"tr": "⏰ Gönderim saati (HH:MM, boş=hemen):",
                         "en": "⏰ Send time (HH:MM, empty=now):"},
    "schedule_note":    {"tr": "zamanlıysa uygulama açık kalmalı",
                         "en": "app must stay open if scheduled"},
    "btn_bulk_send":    {"tr": "🚀  Toplu Gönder",          "en": "🚀  Bulk Send"},
    "no_recip_title":   {"tr": "Alıcı yok",                 "en": "No recipients"},
    "no_recip_msg":     {"tr": "Alıcı listesi boş.",        "en": "Recipient list is empty."},
    "filetype_text":    {"tr": "Metin/CSV",                  "en": "Text/CSV"},
    "filetype_all":     {"tr": "Tümü",                       "en": "All"},
    "error_title":      {"tr": "Hata",                       "en": "Error"},

    # Profile
    "profile_title":    {"tr": "👤 Profilim",                "en": "👤 My Profile"},
    "profile_sub":      {"tr": "AI mailleri SENİN ağzından yazsın diye. CV yükle ya da yaz.",
                         "en": "So AI writes emails in YOUR voice. Upload CV or type."},
    "card_about":       {"tr": "Hakkımda / CV",              "en": "About Me / CV"},
    "btn_upload_cv":    {"tr": "📄 CV Yükle (PDF/TXT)",     "en": "📄 Upload CV (PDF/TXT)"},
    "btn_clear":        {"tr": "Temizle",                    "en": "Clear"},
    "card_signature":   {"tr": "İmza",                       "en": "Signature"},
    "btn_save_profile": {"tr": "💾  Profili Kaydet",        "en": "💾  Save Profile"},
    "pdf_title":        {"tr": "PDF",                        "en": "PDF"},
    "pdf_msg":          {"tr": "PDF okuyucu bulunamadı. TXT yükle ya da metni yapıştır.",
                         "en": "No PDF reader found. Upload TXT or paste text."},
    "cv_title":         {"tr": "CV",                         "en": "CV"},
    "cv_msg":           {"tr": "Metin çıkarılamadı. TXT dene veya elle yapıştır.",
                         "en": "Could not extract text. Try TXT or paste manually."},
    "ok_title":         {"tr": "Tamam",                      "en": "OK"},
    "profile_saved":    {"tr": "Profil kaydedildi.",         "en": "Profile saved."},

    # Settings
    "settings_title":   {"tr": "⚙️ Ayarlar",               "en": "⚙️ Settings"},
    "settings_sub":     {"tr": "Bir kere doldur, keyring'de güvenle saklanır.",
                         "en": "Fill once, securely stored in keyring."},
    "card_lang":        {"tr": "🌐 Arayüz Dili",           "en": "🌐 Interface Language"},
    "lang_label":       {"tr": "Dil",                        "en": "Language"},
    "lang_restart":     {"tr": "Dil değişikliği uygulamayı yeniden başlattığınızda aktif olur.",
                         "en": "Language change takes effect when you restart the app."},
    "card_mail":        {"tr": "📧 Mail Hesabı",            "en": "📧 Mail Account"},
    "service_label":    {"tr": "Servis",                     "en": "Service"},
    "email_label":      {"tr": "E-posta",                    "en": "Email"},
    "email_ph":         {"tr": "seninmailin@gmail.com",      "en": "youremail@gmail.com"},
    "pass_label":       {"tr": "Şifre (Gmail: Uygulama Şifresi)",
                         "en": "Password (Gmail: App Password)"},
    "smtp_server_lbl":  {"tr": "SMTP Sunucu",                "en": "SMTP Server"},
    "smtp_port_lbl":    {"tr": "Port",                       "en": "Port"},
    "btn_test_smtp":    {"tr": "🔌 Bağlantıyı Test Et",    "en": "🔌 Test Connection"},
    "card_ai":          {"tr": "🤖 Yapay Zeka",             "en": "🤖 AI"},
    "provider_label":   {"tr": "Sağlayıcı",                 "en": "Provider"},
    "model_label":      {"tr": "Model (listeden seç ya da elle yaz)",
                         "en": "Model (pick from list or type manually)"},
    "btn_fetch_models": {"tr": "🔄 OpenRouter'dan tüm modelleri çek",
                         "en": "🔄 Fetch all models from OpenRouter"},
    "apikey_label":     {"tr": "API Anahtarı",               "en": "API Key"},
    "apikey_ph":        {"tr": "kendi anahtarın",            "en": "your key"},
    "baseurl_label":    {"tr": "Base URL (sadece OpenAI/Özel)",
                         "en": "Base URL (OpenAI/Custom only)"},
    "online_label":     {"tr": "İnternet araması (Gemini grounding / OpenRouter :online)",
                         "en": "Web search (Gemini grounding / OpenRouter :online)"},
    "key_hint":         {"tr": "Anahtar: Gemini → aistudio.google.com/apikey · OpenRouter → openrouter.ai/keys",
                         "en": "Keys: Gemini → aistudio.google.com/apikey · OpenRouter → openrouter.ai/keys"},
    "btn_test_llm":     {"tr": "🤖 LLM Test Et",           "en": "🤖 Test LLM"},
    "card_finder":      {"tr": "🔎 E-posta Bulucu (opsiyonel)",
                         "en": "🔎 Email Finder (optional)"},
    "hunter_label":     {"tr": "Hunter.io API anahtarı — boşsa kalıp tahmini (doğrulanmaz)",
                         "en": "Hunter.io API key — if empty, pattern guess (unverified)"},
    "card_usage":       {"tr": "📊 Kullanım",               "en": "📊 Usage"},
    "ai_count":         {"tr": "Toplam AI isteği: {count}",  "en": "Total AI requests: {count}"},
    "ai_count_hint":    {"tr": "Her 'Araştır & Taslak Üret' = hedef kişi sayısı kadar AI isteği.",
                         "en": "Each 'Research & Generate' = one AI request per target."},
    "btn_save_settings":{"tr": "💾  Tüm Ayarları Kaydet",  "en": "💾  Save All Settings"},
    "connecting":       {"tr": "bağlanıyor…",                "en": "connecting…"},
    "testing":          {"tr": "test ediliyor…",             "en": "testing…"},
    "working":          {"tr": "çalışıyor ✓",               "en": "working ✓"},
    "failed":           {"tr": "başarısız",                  "en": "failed"},
    "enter_key_first":  {"tr": "önce anahtar gir",          "en": "enter key first"},
    "fetching_models":  {"tr": "modeller çekiliyor…",        "en": "fetching models…"},
    "models_loaded":    {"tr": "{count} model yüklendi ✓",   "en": "{count} models loaded ✓"},
    "fetch_failed":     {"tr": "çekilemedi (internet?)",     "en": "failed to fetch (internet?)"},
    "settings_saved":   {"tr": "Ayarlar kaydedildi.",        "en": "Settings saved."},
    "port_error":       {"tr": "Port sayı olmalı.",          "en": "Port must be a number."},
    "no_mail_title":    {"tr": "Mail ayarı yok",             "en": "No mail setup"},
    "no_mail_msg":      {"tr": "Önce Ayarlar'da mail hesabını gir.",
                         "en": "First enter your mail account in Settings."},
    "critical_error":   {"tr": "Kritik Hata",                "en": "Critical Error"},
    "smtp_custom":      {"tr": "Özel",                       "en": "Custom"},
    "provider_openai":  {"tr": "OpenAI / Özel",              "en": "OpenAI / Custom"},
}


def set_ui_lang(lang: str):
    """Arayüz dilini ayarla (tr veya en)."""
    global _lang
    _lang = lang if lang in ("tr", "en") else "tr"


def get_ui_lang() -> str:
    return _lang


def t(key: str, **kwargs) -> str:
    """Çeviri döndür.  t("ai_count", count=5) → formatlı string."""
    entry = _S.get(key)
    if not entry:
        return key
    s = entry.get(_lang, entry.get("tr", key))
    if kwargs:
        try:
            return s.format(**kwargs)
        except (KeyError, IndexError):
            return s
    return s


# ── PURPOSES (amaç şablonları) ───────────────────────────────────
_PURPOSES = {
    "tr": {
        "Serbest (aşağıya kendim yazacağım)": "",
        "İş / staj başvurusu": "Bu kişiye/şirkete iş veya staj başvurusu maili. Profilimdeki deneyim ve becerilerden somut örneklerle neden uygun olduğumu anlat.",
        "İşbirliği / ortaklık teklifi": "Bu kişiye/şirkete işbirliği veya ortaklık teklifi maili.",
        "Etkinlik / toplantı daveti": "Bu kişiyi bir etkinliğe veya toplantıya davet maili.",
        "Soğuk satış / tanıtım": "Bu kişiye ürün/hizmet tanıtımı ve kısa, fayda odaklı bir soğuk satış maili.",
        "Takip / nazik hatırlatma": "Önceki bir konunun nazik takibi / hatırlatması maili.",
        "Teşekkür": "Bu kişiye içten bir teşekkür maili.",
        "Tez / akademik davet": "Hocama/akademisyene yüksek lisans tez savunmama davet maili.",
    },
    "en": {
        "Custom (I'll write below)": "",
        "Job / internship application": "Write a job or internship application email to this person/company. Use concrete examples from my profile to explain why I'm a good fit.",
        "Partnership / collaboration": "Write a partnership or collaboration proposal email to this person/company.",
        "Event / meeting invitation": "Write an event or meeting invitation email to this person.",
        "Cold outreach / promotion": "Write a short, benefit-focused cold outreach email promoting a product/service.",
        "Follow-up / reminder": "Write a polite follow-up / reminder email about a previous topic.",
        "Thank you": "Write a sincere thank you email to this person.",
        "Thesis / academic invitation": "Write an email inviting my professor/academic to my master's thesis defense.",
    },
}


def get_purposes() -> dict:
    """Mevcut dilde amaç şablonları {label: template}."""
    return _PURPOSES.get(_lang, _PURPOSES["tr"])


# ── TONE display labels ──────────────────────────────────────────
_TONE_LABELS = {
    "tr": {"resmi": "Resmi", "samimi": "Samimi", "satış": "Satış", "akademik": "Akademik"},
    "en": {"resmi": "Formal", "samimi": "Friendly", "satış": "Sales", "akademik": "Academic"},
}


def get_tone_labels() -> dict:
    """{internal_key: display_label} — mevcut dilde."""
    return _TONE_LABELS.get(_lang, _TONE_LABELS["tr"])


def tone_key_from_label(label: str) -> str:
    """Display label → internal key."""
    for k, v in get_tone_labels().items():
        if v == label:
            return k
    return "samimi"


# ── LENGTH options ────────────────────────────────────────────────
_LENGTHS = {
    "tr": {
        "Kısa (2-3 paragraf)": "short",
        "Orta (4-5 paragraf)": "medium",
        "Uzun (6-8 paragraf)": "long",
    },
    "en": {
        "Short (2-3 paragraphs)": "short",
        "Medium (4-5 paragraphs)": "medium",
        "Long (6-8 paragraphs)": "long",
    },
}


def get_length_labels() -> list:
    """Mevcut dilde uzunluk seçeneklerinin display label listesi."""
    return list(_LENGTHS.get(_lang, _LENGTHS["tr"]).keys())


def length_value_from_label(label: str) -> str:
    """Display label → internal value (short / medium / long)."""
    return _LENGTHS.get(_lang, _LENGTHS["tr"]).get(label, "medium")


# ── SMTP presets ──────────────────────────────────────────────────
def get_smtp_presets() -> dict:
    """SMTP preset'leri (Custom etiketi çevrilmiş)."""
    return {
        "Gmail": ("smtp.gmail.com", 587),
        "Outlook": ("smtp.office365.com", 587),
        "Yandex": ("smtp.yandex.com", 465),
        t("smtp_custom"): ("", 0),
    }


# ── Provider labels ──────────────────────────────────────────────
def get_provider_labels() -> dict:
    """{display_label: internal_key}"""
    return {
        "Google Gemini": "gemini",
        "OpenRouter": "openrouter",
        t("provider_openai"): "openai",
    }


def get_label_by_provider() -> dict:
    """{internal_key: display_label}"""
    return {v: k for k, v in get_provider_labels().items()}


# ── Language display names ────────────────────────────────────────
UI_LANG_LABELS = {"Türkçe": "tr", "English": "en"}
UI_LANG_BY_CODE = {v: k for k, v in UI_LANG_LABELS.items()}
