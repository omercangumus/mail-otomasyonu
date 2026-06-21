"""SMTP gönderim servisi. LLM olmadan da tek başına çalışır."""
import os
import ssl
import socket
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Tuple

try:
    import certifi
    _CA = certifi.where()
except Exception:
    _CA = None

log = logging.getLogger("email")


def _ctx():
    return ssl.create_default_context(cafile=_CA) if _CA else ssl.create_default_context()


def test_connection(server: str, port: int, email: str, password: str) -> Tuple[bool, str]:
    try:
        with smtplib.SMTP(server, int(port), timeout=12) as smtp:
            smtp.starttls(context=_ctx())
            smtp.login(email, password)
        return True, "Bağlantı başarılı."
    except smtplib.SMTPAuthenticationError:
        return False, ("Kimlik doğrulama hatası.\n• E-posta/şifre yanlış olabilir.\n"
                       "• Gmail için normal şifre DEĞİL, 'Uygulama Şifresi' gerekir.")
    except (smtplib.SMTPConnectError, socket.gaierror, OSError):
        return False, "Sunucuya bağlanılamadı. İnternet ve SMTP adresini kontrol et."
    except Exception as e:
        return False, f"Beklenmeyen hata: {e}"


def send_email(server: str, port: int, email: str, password: str,
               sender_name: str, to_addr: str, subject: str, body: str,
               html: bool = False, attachment_path: Optional[str] = None,
               unsubscribe_note: bool = True) -> Tuple[bool, str]:
    try:
        msg = MIMEMultipart()
        msg["From"] = f"{sender_name} <{email}>" if sender_name else email
        msg["To"] = to_addr
        msg["Subject"] = subject

        if html:
            full = body
            if unsubscribe_note and "unsubscribe" not in body.lower():
                full += ('<hr><p style="font-size:11px;color:#888">'
                         'Bu mailleri almak istemiyorsanız lütfen yanıtlayıp bildirin.</p>')
            msg.attach(MIMEText(full, "html", "utf-8"))
        else:
            full = body
            if unsubscribe_note:
                full += "\n\n—\nBu mailleri almak istemiyorsanız lütfen yanıtlayıp bildirin."
            msg.attach(MIMEText(full, "plain", "utf-8"))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",
                            f'attachment; filename="{os.path.basename(attachment_path)}"')
            msg.attach(part)

        with smtplib.SMTP(server, int(port), timeout=30) as smtp:
            smtp.starttls(context=_ctx())
            smtp.login(email, password)
            smtp.send_message(msg)
        return True, "OK"
    except Exception as e:
        log.error("gönderim hatası %s: %s", to_addr, e)
        return False, str(e)
