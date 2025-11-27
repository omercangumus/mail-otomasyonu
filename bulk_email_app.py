#!/usr/bin/env python3
import tkinter
import sys
import os
import json
import smtplib
import threading
import time
import ssl
import re
import logging
import socket
import gc
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from tkinter import messagebox, filedialog
from typing import Dict, List, Optional, Any
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import weakref

# --- LOGGING SETUP ---
logging.basicConfig(
    filename='app_debug.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- IMPORTS WITH FALLBACK ---
try:
    import customtkinter as ctk
    import certifi
    from PIL import Image, ImageTk
except ImportError as e:
    logging.critical(f"Missing dependencies: {e}")
    import tkinter.messagebox as msg
    root = tkinter.Tk()
    root.withdraw()
    msg.showerror("Kritik Hata", f"Gerekli kütüphaneler eksik:\n{str(e)}\n\nLütfen 'KUR.bat' dosyasını çalıştırın.")
    sys.exit(1)

# --- CONSTANTS ---
APP_NAME = "EmailOtomasyonu"
VERSION = "2.1.0"
DEFAULT_SMTP_SERVER = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587
DEFAULT_INTERVAL = 30

# --- PATHS ---
if os.name == 'nt':
    DATA_DIR = os.path.join(os.getenv('APPDATA'), APP_NAME)
else:
    DATA_DIR = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', APP_NAME)

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
LOG_FILE = os.path.join(DATA_DIR, "activity.log")

# --- DEFAULT CONFIG ---
DEFAULT_SETTINGS = {
    "smtp_server": DEFAULT_SMTP_SERVER,
    "smtp_port": DEFAULT_SMTP_PORT,
    "sender_name": "", # User must fill this
    "email": "",
    "password": "",
    "subject": "",
    "message": "",
    "interval_days": DEFAULT_INTERVAL,
    "recipients": [],
    "last_sent_date": None,
    "attachment_path": "",
    "single_email": "",
    "single_subject": "",
    "single_message": "",
    "single_interval_days": 7,
    "single_last_sent_date": None,
    "single_attachment_path": ""
}

# --- DECORATORS FOR SAFETY ---
def safe_execute(func):
    """Decorator to catch and log exceptions in functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {e}", exc_info=True)
            return None
    return wrapper

def rate_limit(min_interval=1.0):
    """Decorator to rate limit function calls."""
    def decorator(func):
        last_called = [0.0]
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if now - last_called[0] < min_interval:
                time.sleep(min_interval - (now - last_called[0]))
            last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator

class SettingsManager:
    """Manages application settings with robust error handling."""
    
    def __init__(self):
        self._ensure_data_dir()
        self.settings = self._load_settings()
        self._lock = threading.Lock()  # Thread safety

    @safe_execute
    def _ensure_data_dir(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)

    @safe_execute
    def _load_settings(self) -> Dict[str, Any]:
        if not os.path.exists(SETTINGS_FILE):
            return DEFAULT_SETTINGS.copy()
        
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Validate data size (prevent memory overload)
                if sys.getsizeof(data) > 10 * 1024 * 1024:  # 10MB limit
                    logging.warning("Settings file too large, using defaults")
                    return DEFAULT_SETTINGS.copy()
                
                # Merge with defaults
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in data:
                        data[key] = value
                return data
        except json.JSONDecodeError:
            logging.error("Settings file corrupted. Backup created.")
            try:
                os.rename(SETTINGS_FILE, SETTINGS_FILE + ".bak")
            except: pass
            return DEFAULT_SETTINGS.copy()
        except Exception as e:
            logging.error(f"Error loading settings: {e}")
            return DEFAULT_SETTINGS.copy()

    @safe_execute
    def save(self) -> bool:
        with self._lock:
            try:
                with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=4, ensure_ascii=False)
                return True
            except Exception as e:
                logging.error(f"Error saving settings: {e}")
                return False

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        with self._lock:
            self.settings[key] = value

class EmailService:
    """Handles SMTP connections and email sending with detailed error reporting."""
    
    def __init__(self):
        self._connection_pool = weakref.WeakValueDictionary()
        self._send_lock = threading.Lock()
    
    @staticmethod
    @safe_execute
    def test_connection(server, port, email, password) -> tuple[bool, str]:
        try:
            # Input validation
            if not all([server, port, email, password]):
                return False, "Tüm alanları doldurun"
            
            context = ssl.create_default_context(cafile=certifi.where())
            with smtplib.SMTP(server, port, timeout=10) as smtp:
                smtp.starttls(context=context)
                smtp.login(email, password)
            return True, "Bağlantı Başarılı"
        except smtplib.SMTPAuthenticationError:
            return False, "❌ Kimlik doğrulama hatası!\n\n• E-posta veya şifre yanlış olabilir\n• Gmail kullanıyorsanız 'Uygulama Şifresi' gereklidir\n• Ayarlarınızı kaydettiniz mi kontrol edin"
        except smtplib.SMTPConnectError:
            return False, "❌ Sunucuya bağlanılamadı!\n\n• İnternet bağlantınızı kontrol edin\n• SMTP sunucu adresini doğrulayın\n• Ayarlarınızı kaydettiniz mi kontrol edin"
        except socket.gaierror:
            return False, "❌ Sunucu adresi bulunamadı!\n\n• SMTP sunucu adresini kontrol edin\n• İnternet bağlantınızı doğrulayın\n• Ayarlarınızı kaydettiniz mi kontrol edin"
        except socket.timeout:
            return False, "❌ Bağlantı zaman aşımına uğradı!\n\nSunucu yanıt vermiyor."
        except Exception as e:
            return False, f"❌ Beklenmeyen hata: {str(e)}\n\nAyarlarınızı kaydetmeyi deneyin."

    @rate_limit(min_interval=0.5)  # Rate limiting: min 0.5s between emails
    @safe_execute
    def send_email(self, config: Dict, recipient: str, is_single: bool = False) -> tuple[bool, str]:
        with self._send_lock:  # Thread safety
            try:
                # Input validation
                if not recipient or '@' not in recipient:
                    return False, "Geçersiz e-posta adresi"
                
                msg = MIMEMultipart()
                sender_name = config.get("sender_name", "")
                from_addr = f"{sender_name} <{config['email']}>" if sender_name else config['email']
                
                msg['From'] = from_addr
                msg['To'] = recipient
                msg['Subject'] = config['single_subject'] if is_single else config['subject']
                
                body = config['single_message'] if is_single else config['message']
                msg.attach(MIMEText(body, 'plain'))
                
                att_path = config.get('single_attachment_path' if is_single else 'attachment_path')
                if att_path and os.path.exists(att_path):
                    try:
                        # File size check (prevent huge attachments)
                        file_size = os.path.getsize(att_path)
                        if file_size > 25 * 1024 * 1024:  # 25MB limit
                            return False, "Ek dosya çok büyük (max 25MB)"
                        
                        with open(att_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(att_path)}')
                            msg.attach(part)
                    except Exception as e:
                        return False, f"Ek dosya hatası: {e}"

                context = ssl.create_default_context(cafile=certifi.where())
                with smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=30) as smtp:
                    smtp.starttls(context=context)
                    smtp.login(config['email'], config['password'])
                    smtp.send_message(msg)
                
                return True, "OK"
            except Exception as e:
                return False, str(e)

class SplashScreen(ctk.CTk):
    """Premium loading screen."""
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        
        # Center window
        w, h = 400, 250
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        
        self.configure(fg_color="#1a1a1a")
        
        # Logo/Icon
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except: pass

        # UI Elements
        self.label = ctk.CTkLabel(self, text=APP_NAME, font=("Roboto", 24, "bold"), text_color="white")
        self.label.pack(pady=(60, 10))
        
        self.status = ctk.CTkLabel(self, text="Başlatılıyor...", font=("Roboto", 12), text_color="#888888")
        self.status.pack(pady=5)
        
        self.progress = ctk.CTkProgressBar(self, width=200, height=4, progress_color="#1E88E5")
        self.progress.pack(pady=20)
        self.progress.set(0)
        
        self.after(100, self.animate)

    def animate(self):
        steps = [
            (0.2, "Ayarlar yükleniyor..."),
            (0.4, "Veritabanı kontrol ediliyor..."),
            (0.6, "Arayüz hazırlanıyor..."),
            (0.8, "Güvenlik modülleri başlatılıyor..."),
            (1.0, "Hazır!")
        ]
        
        for i, (prog, text) in enumerate(steps):
            self.after(i * 400, lambda p=prog, t=text: self.update_status(p, t))
        
        self.after(2500, self.destroy)

    def update_status(self, progress, text):
        self.progress.set(progress)
        self.status.configure(text=text)

class BulkEmailAutomationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.email_service = EmailService()
        self.unsaved_changes = False
        
        self._setup_window()
        self._init_ui()
        self._load_initial_state()
        
        # Window close handler
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_window(self):
        self.title(f"📧 {APP_NAME} v{VERSION}")
        self.geometry("1150x800")  # Slightly larger for better spacing
        self.minsize(900, 600)  # Minimum size
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Modern colors
        self._colors = {
            'primary': '#1E88E5',
            'primary_dark': '#1565C0',
            'success': '#2ECC71',
            'warning': '#FFA726',
            'danger': '#E74C3C',
            'bg_dark': '#1a1a1a',
            'bg_card': '#2B2B2B',
            'text_muted': '#888888'
        }
        
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except: pass

    def _init_ui(self):
        # Main Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self._build_sidebar()

        # Main Content Area
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self._build_tabs()

    def _build_sidebar(self):
        # Title
        ctk.CTkLabel(self.sidebar, text=APP_NAME, font=ctk.CTkFont(size=20, weight="bold")).pack(pady=30)

        # Status Card
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="#2B2B2B")
        self.status_frame.pack(padx=20, pady=10, fill="x")
        
        self.status_icon = ctk.CTkLabel(self.status_frame, text="⏳", font=ctk.CTkFont(size=40))
        self.status_icon.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Durum Bekleniyor", font=ctk.CTkFont(weight="bold"))
        self.status_label.pack(pady=5)

        # Quick Stats
        self.stats_label = ctk.CTkLabel(self.sidebar, text="", justify="left", text_color="#aaaaaa")
        self.stats_label.pack(padx=20, pady=20, anchor="w")

        # Action Button
        self.send_btn = ctk.CTkButton(
            self.sidebar, 
            text="🚀 Kontrol Et ve Gönder",
            command=self._on_send_click,
            height=40,
            fg_color="#1E88E5", 
            hover_color="#1565C0"
        )
        self.send_btn.pack(padx=20, pady=10, side="bottom")

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self.main_area)
        self.tabview.pack(fill="both", expand=True)

        self.tab_settings = self.tabview.add("Ayarlar")
        self.tab_recipients = self.tabview.add("Alıcılar")
        self.tab_single = self.tabview.add("Tekli Gönderim")
        self.tab_log = self.tabview.add("Günlük")

        self._build_settings_tab()
        self._build_recipients_tab()
        self._build_single_tab()
        self._build_log_tab()

    def _build_settings_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_settings, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Helper to create labeled entries
        def create_entry(parent, label, key, show=None):
            ctk.CTkLabel(parent, text=label, font=("Roboto", 12, "bold")).pack(anchor="w", pady=(10, 0))
            entry = ctk.CTkEntry(parent, show=show)
            entry.pack(fill="x", pady=(5, 0))
            val = self.settings_manager.get(key)
            if val: entry.insert(0, str(val))
            return entry

        # SMTP Settings
        ctk.CTkLabel(scroll, text="SMTP Ayarları", font=("Roboto", 16, "bold")).pack(anchor="w", pady=10)
        self.ent_sender = create_entry(scroll, "Gönderen Adı (Örn: Ad Soyad)", "sender_name")
        self.ent_server = create_entry(scroll, "SMTP Sunucusu", "smtp_server")
        self.ent_port = create_entry(scroll, "SMTP Portu", "smtp_port")
        self.ent_email = create_entry(scroll, "E-posta Adresi", "email")
        self.ent_pass = create_entry(scroll, "Uygulama Şifresi", "password", show="●")

        ctk.CTkButton(scroll, text="Bağlantıyı Test Et", command=self._test_smtp, fg_color="#27AE60").pack(pady=15, fill="x")

        # Content Settings
        ctk.CTkLabel(scroll, text="İçerik Ayarları", font=("Roboto", 16, "bold")).pack(anchor="w", pady=20)
        self.ent_subject = create_entry(scroll, "Konu Başlığı", "subject")
        
        ctk.CTkLabel(scroll, text="Mesaj İçeriği", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(10, 0))
        self.txt_message = ctk.CTkTextbox(scroll, height=150)
        self.txt_message.pack(fill="x", pady=(5, 0))
        self.txt_message.insert("1.0", self.settings_manager.get("message", ""))

        # Attachment
        self.lbl_attachment = ctk.CTkLabel(scroll, text="Ek Dosya: Yok", text_color="gray")
        self.lbl_attachment.pack(anchor="w", pady=10)
        
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x")
        ctk.CTkButton(btn_frame, text="Dosya Seç", command=lambda: self._select_file(False)).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Kaldır", command=lambda: self._remove_file(False), fg_color="#C0392B").pack(side="left", expand=True, padx=5)

        # Interval
        self.ent_interval = create_entry(scroll, "Gönderim Sıklığı (Gün)", "interval_days")

        # Save Button
        ctk.CTkButton(scroll, text="Ayarları Kaydet", command=self._save_settings, height=40).pack(pady=30, fill="x")

    def _build_recipients_tab(self):
        frame = ctk.CTkFrame(self.tab_recipients, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Her satıra bir e-posta adresi girin:").pack(anchor="w")
        self.txt_recipients = ctk.CTkTextbox(frame)
        self.txt_recipients.pack(fill="both", expand=True, pady=10)
        self.txt_recipients.insert("1.0", "\n".join(self.settings_manager.get("recipients", [])))
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        ctk.CTkButton(btn_frame, text="Dosyadan Yükle", command=self._import_recipients).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Kaydet", command=self._save_recipients).pack(side="left", expand=True, padx=5)

    def _build_single_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_single, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        ctk.CTkLabel(scroll, text="Tekil Otomasyon", font=("Roboto", 16, "bold")).pack(anchor="w", pady=10)
        
        # Helper to create labeled entries (reused)
        def create_entry(parent, label, key):
            ctk.CTkLabel(parent, text=label, font=("Roboto", 12, "bold")).pack(anchor="w", pady=(10, 0))
            entry = ctk.CTkEntry(parent)
            entry.pack(fill="x", pady=(5, 0))
            val = self.settings_manager.get(key)
            if val: entry.insert(0, str(val))
            return entry

        self.ent_single_email = create_entry(scroll, "Alıcı E-posta", "single_email")
        self.ent_single_subject = create_entry(scroll, "Konu", "single_subject")
        
        ctk.CTkLabel(scroll, text="Mesaj", font=("Roboto", 12, "bold")).pack(anchor="w", pady=(10, 0))
        self.txt_single_message = ctk.CTkTextbox(scroll, height=150)
        self.txt_single_message.pack(fill="x", pady=(5, 0))
        self.txt_single_message.insert("1.0", self.settings_manager.get("single_message", ""))

        # Single Attachment
        self.lbl_single_attachment = ctk.CTkLabel(scroll, text="Ek Dosya: Yok", text_color="gray")
        self.lbl_single_attachment.pack(anchor="w", pady=10)
        
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x")
        ctk.CTkButton(btn_frame, text="Dosya Seç", command=lambda: self._select_file(True)).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Kaldır", command=lambda: self._remove_file(True), fg_color="#C0392B").pack(side="left", expand=True, padx=5)

        self.ent_single_interval = create_entry(scroll, "Sıklık (Gün)", "single_interval_days")
        
        ctk.CTkButton(scroll, text="Ayarları Kaydet", command=self._save_single_settings).pack(pady=20, fill="x")
        ctk.CTkButton(scroll, text="Şimdi Gönder", command=self._send_single_now, fg_color="#8E44AD").pack(pady=5, fill="x")

    def _build_log_tab(self):
        self.txt_log = ctk.CTkTextbox(self.tab_log, font=("Consolas", 12))
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=10)

    # --- LOGIC ---

    def _log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert("end", f"[{timestamp}] {msg}\n")
        self.txt_log.see("end")
        logging.info(msg)

    def _load_initial_state(self):
        self._update_attachment_labels()
        self._refresh_status()
        self._log("Uygulama başlatıldı.")

    def _update_attachment_labels(self):
        # Main
        path = self.settings_manager.get("attachment_path")
        if path and os.path.exists(path):
            self.lbl_attachment.configure(text=f"📎 {os.path.basename(path)}", text_color="#2ECC71")
        else:
            self.lbl_attachment.configure(text="Ek Dosya: Yok", text_color="gray")
            
        # Single
        path = self.settings_manager.get("single_attachment_path")
        if path and os.path.exists(path):
            self.lbl_single_attachment.configure(text=f"📎 {os.path.basename(path)}", text_color="#2ECC71")
        else:
            self.lbl_single_attachment.configure(text="Ek Dosya: Yok", text_color="gray")

    def _refresh_status(self):
        # Main Status
        last_sent = self.settings_manager.get("last_sent_date")
        interval = self.settings_manager.get("interval_days", 30)
        recipients = self.settings_manager.get("recipients", [])
        
        status_text = ""
        icon = "❓"
        color = "gray"
        
        if not last_sent:
        if filename:
            key = "single_attachment_path" if is_single else "attachment_path"
            self.settings_manager.set(key, filename)
            self.settings_manager.save()
            self._update_attachment_labels()

    def _remove_file(self, is_single):
        key = "single_attachment_path" if is_single else "attachment_path"
        self.settings_manager.set(key, "")
        self.settings_manager.save()
        self._update_attachment_labels()

    def _save_single_settings(self):
        try:
            self.settings_manager.set("single_email", self.ent_single_email.get())
            self.settings_manager.set("single_subject", self.ent_single_subject.get())
            self.settings_manager.set("single_message", self.txt_single_message.get("1.0", "end-1c"))
            self.settings_manager.set("single_interval_days", int(self.ent_single_interval.get()))
            self.settings_manager.save()
            messagebox.showinfo("Başarılı", "Tekli ayarlar kaydedildi.")
        except ValueError:
            messagebox.showerror("Hata", "Gün alanı sayı olmalıdır.")

    def _test_smtp(self):
        threading.Thread(target=self._test_smtp_thread, daemon=True).start()

    def _test_smtp_thread(self):
        try:
            server = self.ent_server.get()
            port = int(self.ent_port.get())
            email = self.ent_email.get()
            password = self.ent_pass.get()
            
            success, msg = self.email_service.test_connection(server, port, email, password)
            if success:
                self.after(0, lambda: messagebox.showinfo("Başarılı", msg))
            else:
                self.after(0, lambda: messagebox.showerror("Başarısız", msg))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Hata", str(e)))

    def _on_send_click(self):
        # Check if due
        last_sent = self.settings_manager.get("last_sent_date")
        interval = self.settings_manager.get("interval_days", 30)
        is_due = False
        
        if not last_sent:
            is_due = True
        else:
            try:
                days = (datetime.now() - datetime.fromisoformat(last_sent)).days
                if days >= interval:
                    is_due = True
            except: is_due = True
            
        if is_due:
            if messagebox.askyesno("Onay", "Zamanı gelmiş! Şimdi göndermek ister misiniz?"):
                self._start_sending()
        else:
            if messagebox.askyesno("Zamanı Gelmedi", "Henüz zamanı gelmedi. Yine de zorla göndermek ister misiniz?"):
                self._start_sending()

    def _start_sending(self):
        recipients = self.settings_manager.get("recipients", [])
        if not recipients:
            messagebox.showerror("Hata", "Alıcı listesi boş!")
            return
            
        self.send_btn.configure(state="disabled", text="Gönderiliyor...")
        threading.Thread(target=self._sending_process, daemon=True).start()

    def _sending_process(self):
        config = self.settings_manager.settings
        recipients = config.get("recipients", [])
        success_count = 0
        fail_count = 0
        
        self._log("Toplu gönderim başlatıldı...")
        
        for recipient in recipients:
            success, msg = self.email_service.send_email(config, recipient)
            if success:
                success_count += 1
                self.after(0, self._log, f"✅ {recipient}")
            else:
                fail_count += 1
                self.after(0, self._log, f"❌ {recipient}: {msg}")
            
            # Small delay to prevent spam flagging
            time.sleep(1)
            
        self.settings_manager.set("last_sent_date", datetime.now().isoformat())
        self.settings_manager.save()
        
        self.after(0, self._sending_finished, success_count, fail_count)

    def _sending_finished(self, s, f):
        self.send_btn.configure(state="normal", text="🚀 Kontrol Et ve Gönder")
        self._refresh_status()
        messagebox.showinfo("Tamamlandı", f"İşlem bitti.\nBaşarılı: {s}\nBaşarısız: {f}")

    def _send_single_now(self):
        if messagebox.askyesno("Onay", "Tekli e-posta gönderilsin mi?"):
            threading.Thread(target=self._single_sending_process, daemon=True).start()

    def _single_sending_process(self):
        config = self.settings_manager.settings
        recipient = config.get("single_email")
        if not recipient:
            self.after(0, lambda: messagebox.showerror("Hata", "Alıcı e-posta girilmemiş."))
            return

        self._log(f"Tekli gönderim: {recipient}")
        success, msg = self.email_service.send_email(config, recipient, is_single=True)
        
        if success:
            self.settings_manager.set("single_last_sent_date", datetime.now().isoformat())
            self.settings_manager.save()
            self.after(0, lambda: messagebox.showinfo("Başarılı", "E-posta gönderildi."))
            self.after(0, self._log, f"✅ Tekli gönderildi: {recipient}")
        else:
            self.after(0, lambda: messagebox.showerror("Hata", msg))
            self.after(0, self._log, f"❌ Tekli hata: {msg}")

    def _on_closing(self):
        """Handle window close event with save confirmation."""
        if self.unsaved_changes:
            response = messagebox.askyesnocancel(
                "Kaydetmeden Çık",
                "Kaydedilmemiş değişiklikler var!\n\nKaydetmek ister misiniz?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes, save
                self._save_all_settings()
        
        self.destroy()
    
    def _save_all_settings(self):
        """Save all settings before closing."""
        try:
            # Update main settings from UI
            self.settings_manager.set("sender_name", self.ent_sender.get())
            self.settings_manager.set("smtp_server", self.ent_server.get())
            self.settings_manager.set("smtp_port", int(self.ent_port.get() or 587))
            self.settings_manager.set("email", self.ent_email.get())
            self.settings_manager.set("password", self.ent_pass.get())
            self.settings_manager.set("subject", self.ent_subject.get())
            self.settings_manager.set("message", self.txt_message.get("1.0", "end-1c"))
            self.settings_manager.set("interval_days", int(self.ent_interval.get() or 30))
            
            # Save recipients
            text = self.txt_recipients.get("1.0", "end-1c")
            recipients = [line.strip() for line in text.split("\n") if line.strip() and "@" in line]
            self.settings_manager.set("recipients", recipients)
            
            # Save single email settings
            self.settings_manager.set("single_email", self.ent_single_email.get())
            self.settings_manager.set("single_subject", self.ent_single_subject.get())
            self.settings_manager.set("single_message", self.txt_single_message.get("1.0", "end-1c"))
            self.settings_manager.set("single_interval_days", int(self.ent_single_interval.get() or 7))
            
            self.settings_manager.save()
            self.unsaved_changes = False
            messagebox.showinfo("Başarılı", "Tüm ayarlar kaydedildi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme hatası: {e}")
    
    def _mark_unsaved(self):
        """Mark that there are unsaved changes."""
        self.unsaved_changes = True

if __name__ == "__main__":
    # Global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        messagebox.showerror(
            "Kritik Hata",
            f"Bir hata oluştu:\n{exc_type.__name__}: {exc_value}\n\nUygulama kapatılacak."
        )
    
    sys.excepthook = handle_exception
    
    # Splash Screen
    try:
        splash = SplashScreen()
        splash.mainloop()
    except Exception as e:
        logging.error(f"Splash error: {e}")
        print(f"Splash error: {e}")

    # Main App
    try:
        app = BulkEmailAutomationApp()
        app.mainloop()
    except Exception as e:
        logging.critical(f"Application crashed: {e}")
        messagebox.showerror("Kritik Hata", f"Uygulama çöktü: {e}")
