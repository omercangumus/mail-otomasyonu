"""CV / profil metni çıkarımı. PDF için pypdf (opsiyonel), yoksa txt/yapıştır."""
import os
import logging

log = logging.getLogger("profile")


def extract_text(path: str) -> str:
    if not path or not os.path.exists(path):
        return ""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md"):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            log.error("txt okunamadı: %s", e)
            return ""
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        except ImportError:
            return "__NO_PYPDF__"
        except Exception as e:
            log.error("pdf okunamadı: %s", e)
            return ""
    return ""
