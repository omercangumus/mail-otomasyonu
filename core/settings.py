"""Ayar yönetimi. Hassas bilgiler (şifre / API anahtarları) keyring'de,
geri kalan ayarlar settings.json içinde tutulur."""
import os
import json
import logging
from typing import Any, Dict

log = logging.getLogger("settings")

APP_NAME = "EmailAI"
SERVICE = "email-ai-app"  # keyring service adı

if os.name == "nt":
    DATA_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), APP_NAME)
elif os.name == "posix" and os.path.exists(os.path.expanduser("~/Library")):
    DATA_DIR = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
else:  # Linux
    DATA_DIR = os.path.join(os.path.expanduser("~"), ".config", APP_NAME)

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# Hassas alanlar -> keyring'e yazılır, json'a ASLA yazılmaz
SECRET_KEYS = {"smtp_password", "llm_api_key", "hunter_api_key"}

DEFAULTS: Dict[str, Any] = {
    # SMTP
    "sender_name": "",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email": "",
    # LLM
    "llm_provider": "gemini",          # "gemini" | "openai"
    "llm_model": "gemini-2.5-flash",
    "llm_base_url": "",                 # openai-uyumlu için
    "use_grounding": True,             # Gemini google_search
    # Finder
    "use_hunter": False,
    # Profil
    "profile_text": "",                # CV / hakkımda metni
    "signature": "",
    # Genel
    "default_tone": "samimi",          # resmi | samimi | satış | akademik
    "default_lang": "tr",
    "ui_lang": "tr",                   # arayüz dili (tr / en)
    "send_as_html": False,
    "send_delay_sec": 2.0,             # spam'a takılmamak için
    "ai_requests": 0,                  # toplam AI istek sayacı
    # son toplu mail içeriği (kolaylık)
    "bulk_subject": "",
    "bulk_message": "",
    "bulk_recipients": [],
    "attachment_path": "",
}


class Settings:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._kr = self._try_keyring()
        self.data = self._load()

    def _try_keyring(self):
        try:
            import keyring
            # erişilebilir bir backend var mı kontrol
            keyring.get_keyring()
            return keyring
        except Exception as e:
            log.warning("keyring kullanılamıyor (%s). Sırlar bellekte tutulacak.", e)
            return None

    def _load(self) -> Dict[str, Any]:
        data = DEFAULTS.copy()
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                for k, v in saved.items():
                    if k not in SECRET_KEYS:
                        data[k] = v
            except Exception as e:
                log.error("settings.json okunamadı: %s", e)
        # sırları belleğe çek
        self._secret_cache = {}
        for k in SECRET_KEYS:
            self._secret_cache[k] = self._kr_get(k)
        return data

    # ---- sır okuma/yazma ----
    def _kr_get(self, key: str) -> str:
        if self._kr:
            try:
                return self._kr.get_password(SERVICE, key) or ""
            except Exception:
                return ""
        return getattr(self, "_secret_cache", {}).get(key, "")

    def _kr_set(self, key: str, value: str):
        if self._kr:
            try:
                if value:
                    self._kr.set_password(SERVICE, key, value)
                else:
                    try:
                        self._kr.delete_password(SERVICE, key)
                    except Exception:
                        pass
                return
            except Exception as e:
                log.error("keyring yazma hatası: %s", e)
        self._secret_cache[key] = value

    # ---- genel API ----
    def get(self, key: str, default: Any = None) -> Any:
        if key in SECRET_KEYS:
            return self._secret_cache.get(key, "") or default or ""
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        if key in SECRET_KEYS:
            self._secret_cache[key] = value or ""
            self._kr_set(key, value or "")
        else:
            self.data[key] = value

    def save(self) -> bool:
        try:
            safe = {k: v for k, v in self.data.items() if k not in SECRET_KEYS}
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(safe, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            log.error("settings kaydedilemedi: %s", e)
            return False

    @property
    def has_llm(self) -> bool:
        return bool(self.get("llm_api_key"))
