"""CV / profil metni çıkarımı.
Öncelik: PyMuPDF (fitz) — tasarımlı CV'lerde boşlukları korur.
Yedek: pypdf. TXT/MD doğrudan okunur.
Çıktı, yapışık kelimeleri bir nebze açan hafif bir temizlemeden geçer.
"""
import os
import re
import logging

log = logging.getLogger("profile")


def _clean(text: str) -> str:
    if not text:
        return ""
    # fazla boş satırları sadeleştir
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # camelCase ve harf↔rakam sınırlarına boşluk (PDF yapışmalarını açar)
    text = re.sub(r"(?<=[a-zçğıöşü])(?=[A-ZÇĞİÖŞÜ])", " ", text)
    text = re.sub(r"(?<=[A-Za-zÇĞİÖŞÜçğıöşü])(?=\d)", " ", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-zÇĞİÖŞÜ])", " ", text)
    return text.strip()


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
        # 1) PyMuPDF (en iyi)
        try:
            import fitz
            doc = fitz.open(path)
            parts = [page.get_text("text") for page in doc]
            doc.close()
            txt = "\n".join(parts).strip()
            if txt:
                return _clean(txt)
        except ImportError:
            pass
        except Exception as e:
            log.error("pymupdf hatası: %s", e)
        # 2) pypdf yedek
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            txt = "\n".join((p.extract_text() or "") for p in reader.pages).strip()
            return _clean(txt) if txt else ""
        except ImportError:
            return "__NO_PDF_LIB__"
        except Exception as e:
            log.error("pypdf hatası: %s", e)
            return ""
    return ""
