"""SMTP gönderim servisi. LLM olmadan da tek başına çalışır.
- Türkçe gönderen adı için formataddr (doğru kodlama).
- 465 portunda SSL, 587'de STARTTLS otomatik.
"""
import os
import re
import ssl
import socket
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import formataddr
from email import encoders
from typing import Optional, Tuple

try:
    import certifi
    _CA = certifi.where()
except Exception:
    _CA = None

log = logging.getLogger("email")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valid_email(addr: str) -> bool:
    return bool(EMAIL_RE.match((addr or "").strip()))


def _ctx():
    return ssl.create_default_context(cafile=_CA) if _CA else ssl.create_default_context()


def _connect(server, port):
    """465 -> SSL, diğer -> STARTTLS."""
    port = int(port)
    if port == 465:
        smtp = smtplib.SMTP_SSL(server, port, timeout=30, context=_ctx())
    else:
        smtp = smtplib.SMTP(server, port, timeout=30)
        smtp.starttls(context=_ctx())
    return smtp


def test_connection(server, port, email, password) -> Tuple[bool, str]:
    try:
        with _connect(server, port) as smtp:
            smtp.login(email, password)
        return True, "Bağlantı başarılı ✓"
    except smtplib.SMTPAuthenticationError:
        return False, ("Kimlik doğrulama hatası.\n• Gmail için normal şifre DEĞİL, "
                       "'Uygulama Şifresi' gerekir.\n• 2 Adımlı Doğrulama açık olmalı.")
    except (smtplib.SMTPConnectError, socket.gaierror, OSError):
        return False, "Sunucuya bağlanılamadı. İnternet ve SMTP sunucu/port'u kontrol et."
    except Exception as e:
        return False, f"Beklenmeyen hata: {e}"


def send_email(server, port, email, password, sender_name, to_addr, subject, body,
               html: bool = False, attachment_path: Optional[str] = None,
               unsubscribe_note: bool = True) -> Tuple[bool, str]:
    to_addr = (to_addr or "").strip()
    if not valid_email(to_addr):
        return False, "Geçersiz e-posta adresi."
    try:
        msg = MIMEMultipart()
        msg["From"] = formataddr((sender_name or "", email))
        msg["To"] = to_addr
        msg["Subject"] = subject or ""

        if html:
            full = body + (
                '<hr><p style="font-size:11px;color:#888">Bu mailleri almak '
                'istemiyorsanız lütfen yanıtlayıp bildirin.</p>'
                if unsubscribe_note and "unsubscribe" not in body.lower() else "")
            msg.attach(MIMEText(full, "html", "utf-8"))
        else:
            full = body + ("\n\n—\nBu mailleri almak istemiyorsanız lütfen yanıtlayıp bildirin."
                           if unsubscribe_note else "")
            msg.attach(MIMEText(full, "plain", "utf-8"))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                            f'attachment; filename="{os.path.basename(attachment_path)}"')
            msg.attach(part)

        with _connect(server, port) as smtp:
            smtp.login(email, password)
            smtp.send_message(msg)
        return True, "OK"
    except Exception as e:
        log.error("gönderim hatası %s: %s", to_addr, e)
        return False, str(e)
