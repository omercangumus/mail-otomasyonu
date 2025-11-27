#!/usr/bin/env python3
import tkinter
"""
Toplu E-posta Otomasyonu
Modern ve kullanıcı dostu arayüzle tarih bazlı otomatik toplu e-posta gönderimi.
"""

try:
    import customtkinter as ctk
    import certifi
    from PIL import Image
except ImportError as e:
    import tkinter.messagebox as msg
    import sys
    root = tkinter.Tk()
    root.withdraw()
    msg.showerror("Eksik Kütüphane", f"Gerekli kütüphaneler bulunamadı:\n{str(e)}\n\nLütfen 'KUR.bat' veya 'KUR.command' dosyasını çalıştırın.")
    sys.exit(1)

import json
import os
import smtplib
import threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from tkinter import messagebox, filedialog
import re
import ssl
import certifi

# Sabitler
APP_NAME = "EmailOtomasyonu"
if os.name == 'nt':  # Windows
    DATA_DIR = os.path.join(os.getenv('APPDATA'), APP_NAME)
else:  # Mac/Linux
    DATA_DIR = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', APP_NAME)

if not os.path.exists(DATA_DIR):
    try:
        os.makedirs(DATA_DIR)
    except:
        DATA_DIR = os.path.join(os.path.expanduser('~'), f'.{APP_NAME}')
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_name": "Ömer Can Gümüş",
    "email": "",
    "password": "",
    "subject": "",
    "message": "",
    "interval_days": 30,
    "recipients": [],
    "last_sent_date": None,
    "attachment_path": "",
    # Tekli gönderim ayarları
    "single_email": "",
    "single_subject": "",
    "single_message": "",
    "single_interval_days": 7,
    "single_last_sent_date": None,
    "single_attachment_path": ""
}


class ModernEmailApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Pencere ayarları
        self.title("📧 Toplu E-posta Otomasyonu")
        self.geometry("1100x750")
        
        # İkon ayarı (Windows için)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except:
                pass # Mac/Linux'ta hata verebilir, yoksay
        
        # Modern tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Ayarları yükle
        self.settings = self.load_settings()
        
        # Ana layout
        self.create_modern_ui()
        
        # Başlangıçta durumu kontrol et
        self.after(100, self.check_and_update_status)
    
    def load_settings(self):
        """Ayarları JSON'dan yükle veya varsayılanları oluştur"""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    for key in DEFAULT_SETTINGS:
                        if key not in settings:
                            settings[key] = DEFAULT_SETTINGS[key]
                    return settings
            except Exception as e:
                messagebox.showerror("Hata", f"Ayarlar yüklenemedi: {str(e)}")
                return DEFAULT_SETTINGS.copy()
        return DEFAULT_SETTINGS.copy()
    
    def save_settings(self):
        """Ayarları JSON'a kaydet"""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("Hata", f"Ayarlar kaydedilemedi: {str(e)}")
            return False
    
    def create_modern_ui(self):
        """Modern, temiz arayüz oluştur"""
        # Ana container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Sol panel - Kontrol paneli
        left_panel = ctk.CTkFrame(main_container, width=400, corner_radius=15)
        left_panel.pack(side="left", fill="both", padx=(0, 10), pady=0)
        left_panel.pack_propagate(False)
        
        # Sağ panel - Sekme içeriği
        right_panel = ctk.CTkFrame(main_container, corner_radius=15)
        right_panel.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=0)
        
        # Sol panel içeriği
        self.build_control_panel(left_panel)
        
        # Sağ panel - Tab view
        self.build_content_tabs(right_panel)
    
    def build_control_panel(self, parent):
        """Sol kontrol panelini oluştur"""
        # Başlık
        title_label = ctk.CTkLabel(
            parent,
            text="📊 DURUM",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Durum kartı
        self.status_card = ctk.CTkFrame(parent, corner_radius=12, fg_color=("#2B2B2B", "#1E1E1E"))
        self.status_card.pack(padx=20, pady=10, fill="x")
        
        # Durum ikonu ve metni
        self.status_icon = ctk.CTkLabel(
            self.status_card,
            text="⏳",
            font=ctk.CTkFont(size=48)
        )
        self.status_icon.pack(pady=(20, 5))
        
        self.status_text = ctk.CTkLabel(
            self.status_card,
            text="Yükleniyor...",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.status_text.pack(pady=5)
        
        self.status_detail = ctk.CTkLabel(
            self.status_card,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=("#999999", "#666666")
        )
        self.status_detail.pack(pady=(0, 15))
        
        # Bilgi kartı
        info_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color=("#2B2B2B", "#1E1E1E"))
        info_frame.pack(padx=20, pady=10, fill="x")
        
        self.next_send_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=14),
            wraplength=340
        )
        self.next_send_label.pack(pady=15, padx=15)
        
        # Ayırıcı
        separator = ctk.CTkFrame(parent, height=2, fg_color=("#333333", "#2A2A2A"))
        separator.pack(fill="x", padx=30, pady=15)
        
        # Hızlı istatistikler
        stats_label = ctk.CTkLabel(
            parent,
            text="📈 İSTATİSTİKLER",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        stats_label.pack(pady=(10, 10))
        
        self.stats_frame = ctk.CTkFrame(parent, corner_radius=12, fg_color=("#2B2B2B", "#1E1E1E"))
        self.stats_frame.pack(padx=20, pady=5, fill="x")
        
        self.recipient_stat = ctk.CTkLabel(
            self.stats_frame,
            text=f"👥 Alıcı Sayısı: {len(self.settings['recipients'])}",
            font=ctk.CTkFont(size=13)
        )
        self.recipient_stat.pack(pady=(12, 5), padx=15, anchor="w")
        
        self.interval_stat = ctk.CTkLabel(
            self.stats_frame,
            text=f"⏰ Gönderim Aralığı: {self.settings['interval_days']} gün",
            font=ctk.CTkFont(size=13)
        )
        self.interval_stat.pack(pady=5, padx=15, anchor="w")
        
        last_sent = self.settings.get('last_sent_date')
        if last_sent:
            try:
                date_str = datetime.fromisoformat(last_sent).strftime('%d.%m.%Y')
                last_text = f"📅 Son Gönderim: {date_str}"
            except:
                last_text = "📅 Son Gönderim: -"
        else:
            last_text = "📅 Son Gönderim: Hiç gönderilmedi"
        
        self.last_sent_stat = ctk.CTkLabel(
            self.stats_frame,
            text=last_text,
            font=ctk.CTkFont(size=13)
        )
        self.last_sent_stat.pack(pady=(5, 5), padx=15, anchor="w")
        
        # Ek dosya durumu
        attachment = self.settings.get('attachment_path', '')
        if attachment and os.path.exists(attachment):
            att_text = f"📎 Ek: {os.path.basename(attachment)}"
        else:
            att_text = "📎 Ek: Yok"
        
        self.attachment_stat = ctk.CTkLabel(
            self.stats_frame,
            text=att_text,
            font=ctk.CTkFont(size=13)
        )
        self.attachment_stat.pack(pady=(5, 12), padx=15, anchor="w")
        
        # Aksiyon butonları
        action_label = ctk.CTkLabel(
            parent,
            text="⚡ HIZLI İŞLEMLER",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        action_label.pack(pady=(20, 10))
        
        # Ana gönder butonu - Direkt gönder
        self.send_button = ctk.CTkButton(
            parent,
            text="✉️ Hemen Gönder",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=("#1E88E5", "#1565C0"),
            hover_color=("#1976D2", "#0D47A1"),
            command=self.send_now
        )
        self.send_button.pack(padx=20, pady=5, fill="x")
        
        # Test gönder butonu - Tarihi sıfırla
        test_button = ctk.CTkButton(
            parent,
            text="🔄 Tarihi Sıfırla ve Gönder",
            font=ctk.CTkFont(size=13),
            height=45,
            corner_radius=10,
            fg_color=("#FF6B35", "#CC5629"),
            hover_color=("#E85528", "#B34520"),
            command=self.force_send
        )
        test_button.pack(padx=20, pady=5, fill="x")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(parent, corner_radius=10, height=8)
        self.progress_bar.pack(padx=20, pady=(15, 10), fill="x")
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            parent,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#999999", "#666666")
        )
        self.progress_label.pack()
    
    def build_content_tabs(self, parent):
        """Sağ panel - içerik sekmeleri"""
        # Tab view
        self.tabview = ctk.CTkTabview(parent, corner_radius=12)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Sekmeleri oluştur
        tab1 = self.tabview.add("⚙️ Ayarlar")
        tab2 = self.tabview.add("👥 Alıcılar")
        tab3 = self.tabview.add("✉️ Tekli Mail")
        tab4 = self.tabview.add("📋 Günlük")
        
        # Sekmeler
        self.build_settings_tab(tab1)
        self.build_recipients_tab(tab2)
        self.build_single_email_tab(tab3)
        self.build_log_tab(tab4)
    
    def build_settings_tab(self, parent):
        """Ayarlar sekmesi"""
        # Scrollable frame
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # SMTP Bölümü
        smtp_header = ctk.CTkLabel(
            scroll,
            text="📮 SMTP Ayarları",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        smtp_header.pack(anchor="w", pady=(10, 15))
        
        # Sender Name
        ctk.CTkLabel(scroll, text="Gönderen İsmi", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.sender_name_entry = ctk.CTkEntry(scroll, height=38, corner_radius=8)
        self.sender_name_entry.pack(fill="x", pady=(0, 10))
        self.sender_name_entry.insert(0, self.settings.get("sender_name", "Ömer Can Gümüş"))
        
        # SMTP Server
        ctk.CTkLabel(scroll, text="Sunucu Adresi", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.smtp_server_entry = ctk.CTkEntry(scroll, height=38, corner_radius=8)
        self.smtp_server_entry.pack(fill="x", pady=(0, 10))
        self.smtp_server_entry.insert(0, self.settings["smtp_server"])
        
        # Port ve Email yan yana
        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))
        
        port_frame = ctk.CTkFrame(row1, fg_color="transparent")
        port_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(port_frame, text="Port", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.smtp_port_entry = ctk.CTkEntry(port_frame, height=38, corner_radius=8)
        self.smtp_port_entry.pack(fill="x")
        self.smtp_port_entry.insert(0, str(self.settings["smtp_port"]))
        
        email_frame = ctk.CTkFrame(row1, fg_color="transparent")
        email_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(email_frame, text="E-posta Adresiniz", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.email_entry = ctk.CTkEntry(email_frame, height=38, corner_radius=8)
        self.email_entry.pack(fill="x")
        self.email_entry.insert(0, self.settings["email"])
        
        # Şifre
        ctk.CTkLabel(scroll, text="Uygulama Şifresi", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.password_entry = ctk.CTkEntry(scroll, height=38, corner_radius=8, show="●")
        self.password_entry.pack(fill="x", pady=(0, 15))
        self.password_entry.insert(0, self.settings["password"])
        
        # Test butonu
        test_btn = ctk.CTkButton(
            scroll,
            text="🔌 Bağlantıyı Test Et",
            height=38,
            corner_radius=8,
            fg_color=("#2ECC71", "#27AE60"),
            hover_color=("#27AE60", "#1E8449"),
            command=self.test_smtp_connection
        )
        test_btn.pack(fill="x", pady=(0, 20))
        
        # Ayırıcı
        ctk.CTkFrame(scroll, height=2, fg_color=("#333333", "#2A2A2A")).pack(fill="x", pady=15)
        
        # E-posta İçeriği
        content_header = ctk.CTkLabel(
            scroll,
            text="✉️ E-posta İçeriği",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        content_header.pack(anchor="w", pady=(5, 15))
        
        # Konu
        ctk.CTkLabel(scroll, text="Konu", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.subject_entry = ctk.CTkEntry(scroll, height=38, corner_radius=8)
        self.subject_entry.pack(fill="x", pady=(0, 10))
        self.subject_entry.insert(0, self.settings["subject"])
        
        # Mesaj
        ctk.CTkLabel(scroll, text="Mesaj İçeriği", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.message_text = ctk.CTkTextbox(scroll, height=180, corner_radius=8)
        self.message_text.pack(fill="x", pady=(0, 15))
        self.message_text.insert("1.0", self.settings["message"])
        
        # Ayırıcı
        ctk.CTkFrame(scroll, height=2, fg_color=("#333333", "#2A2A2A")).pack(fill="x", pady=15)
        
        # Ek Dosya
        attachment_header = ctk.CTkLabel(
            scroll,
            text="📎 Ek Dosya",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        attachment_header.pack(anchor="w", pady=(5, 15))
        
        # Dosya bilgisi
        self.attachment_label = ctk.CTkLabel(
            scroll,
            text="Seçili dosya yok",
            font=ctk.CTkFont(size=12),
            text_color=("#999999", "#666666")
        )
        self.attachment_label.pack(anchor="w", pady=(0, 10))
        
        # Dosya işlemleri
        att_buttons = ctk.CTkFrame(scroll, fg_color="transparent")
        att_buttons.pack(fill="x", pady=(0, 15))
        
        select_file_btn = ctk.CTkButton(
            att_buttons,
            text="📁 Dosya Seç",
            height=38,
            corner_radius=8,
            fg_color=("#9B59B6", "#8E44AD"),
            hover_color=("#8E44AD", "#7D3C98"),
            command=self.select_attachment
        )
        select_file_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        remove_file_btn = ctk.CTkButton(
            att_buttons,
            text="❌ Eki Kaldır",
            height=38,
            corner_radius=8,
            fg_color=("#E74C3C", "#C0392B"),
            hover_color=("#C0392B", "#A93226"),
            command=self.remove_attachment
        )
        remove_file_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))
        
        # Mevcut dosyayı göster
        self.update_attachment_display()
        
        # Ayırıcı
        ctk.CTkFrame(scroll, height=2, fg_color=("#333333", "#2A2A2A")).pack(fill="x", pady=15)
        
        # Zamanlama
        timing_header = ctk.CTkLabel(
            scroll,
            text="⏰ Zamanlama",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        timing_header.pack(anchor="w", pady=(5, 15))
        
        ctk.CTkLabel(scroll, text="Gönderim Aralığı (gün)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.interval_entry = ctk.CTkEntry(scroll, height=38, corner_radius=8)
        self.interval_entry.pack(fill="x", pady=(0, 20))
        self.interval_entry.insert(0, str(self.settings["interval_days"]))
        
        # Kaydet butonu
        save_btn = ctk.CTkButton(
            scroll,
            text="💾 Tüm Ayarları Kaydet",
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#1E88E5", "#1565C0"),
            hover_color=("#1976D2", "#0D47A1"),
            command=self.save_config
        )
        save_btn.pack(fill="x", pady=(10, 20))
    
    def build_recipients_tab(self, parent):
        """Alıcılar sekmesi"""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Üst bilgi
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(10, 15))
        
        ctk.CTkLabel(
            header_frame,
            text="👥 E-posta Alıcıları",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")
        
        self.recipient_count = ctk.CTkLabel(
            header_frame,
            text=f"{len(self.settings['recipients'])} alıcı",
            font=ctk.CTkFont(size=14),
            text_color=("#1E88E5", "#1565C0")
        )
        self.recipient_count.pack(side="left", padx=15)
        
        # Açıklama
        ctk.CTkLabel(
            container,
            text="Her satıra bir e-posta adresi girin:",
            font=ctk.CTkFont(size=12),
            text_color=("#999999", "#666666")
        ).pack(anchor="w", pady=(0, 8))
        
        # Metin alanı
        self.recipients_text = ctk.CTkTextbox(container, corner_radius=8)
        self.recipients_text.pack(fill="both", expand=True, pady=(0, 15))
        self.recipients_text.insert("1.0", "\n".join(self.settings["recipients"]))
        
        # Alt butonlar
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x")
        
        import_btn = ctk.CTkButton(
            button_frame,
            text="📂 Dosyadan Yükle",
            height=40,
            corner_radius=8,
            fg_color=("#9B59B6", "#8E44AD"),
            hover_color=("#8E44AD", "#7D3C98"),
            command=self.import_recipients
        )
        import_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Alıcıları Kaydet",
            height=40,
            corner_radius=8,
            fg_color=("#1E88E5", "#1565C0"),
            hover_color=("#1976D2", "#0D47A1"),
            command=self.save_recipients
        )
        save_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))
    
    def build_single_email_tab(self, parent):
        """Tekli e-posta sekmesi"""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        header = ctk.CTkLabel(
            scroll,
            text="✉️ Tekil E-posta Gönderimi",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.pack(anchor="w", pady=(10, 5))
        
        desc = ctk.CTkLabel(
            scroll,
            text="Tek bir kişiye sürekli tekrarlayan e-posta gönderin",
            font=ctk.CTkFont(size=12),
            text_color=("#999999", "#666666")
        )
        desc.pack(anchor="w", pady=(0, 20))
        
        # Alıcı e-posta
        ctk.CTkLabel(scroll, text="Alıcı E-posta", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.single_email_entry = ctk.CTkEntry(scroll, height=38, corner_radius=8, placeholder_text="ornek@email.com")
        self.single_email_entry.pack(fill="x", pady=(0, 15))
        self.single_email_entry.insert(0, self.settings.get("single_email", ""))
        
        # Konu
        ctk.CTkLabel(scroll, text="Konu", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.single_subject_entry = ctk.CTkEntry(scroll, height=38, corner_radius=8)
        self.single_subject_entry.pack(fill="x", pady=(0, 15))
        self.single_subject_entry.insert(0, self.settings.get("single_subject", ""))
        
        # Mesaj
        ctk.CTkLabel(scroll, text="Mesaj İçeriği", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.single_message_text = ctk.CTkTextbox(scroll, height=200, corner_radius=8)
        self.single_message_text.pack(fill="x", pady=(0, 15))
        self.single_message_text.insert("1.0", self.settings.get("single_message", ""))
        
        # Aralık
        ctk.CTkLabel(scroll, text="Gönderim Aralığı (gün)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 2))
        self.single_interval_entry = ctk.CTkEntry(scroll, height=38, corner_radius=8)
        self.single_interval_entry.pack(fill="x", pady=(0, 20))
        self.single_interval_entry.insert(0, str(self.settings.get("single_interval_days", 7)))
        
        # Ek Dosya Bölümü
        ctk.CTkLabel(scroll, text="📎 Ek Dosya", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 10))
        
        self.single_attachment_label = ctk.CTkLabel(
            scroll,
            text="Seçili dosya yok",
            font=ctk.CTkFont(size=12),
            text_color=("#999999", "#666666")
        )
        self.single_attachment_label.pack(anchor="w", pady=(0, 10))
        
        single_att_buttons = ctk.CTkFrame(scroll, fg_color="transparent")
        single_att_buttons.pack(fill="x", pady=(0, 20))
        
        select_single_file_btn = ctk.CTkButton(
            single_att_buttons,
            text="📁 Dosya Seç",
            height=38,
            corner_radius=8,
            fg_color=("#9B59B6", "#8E44AD"),
            hover_color=("#8E44AD", "#7D3C98"),
            command=self.select_single_attachment
        )
        select_single_file_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        remove_single_file_btn = ctk.CTkButton(
            single_att_buttons,
            text="❌ Eki Kaldır",
            height=38,
            corner_radius=8,
            fg_color=("#E74C3C", "#C0392B"),
            hover_color=("#C0392B", "#A93226"),
            command=self.remove_single_attachment
        )
        remove_single_file_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))
        
        # Mevcut dosyayı göster
        self.update_single_attachment_display()
        
        # Durum
        self.single_status_frame = ctk.CTkFrame(scroll, corner_radius=12, fg_color=("#2B2B2B", "#1E1E1E"))
        self.single_status_frame.pack(fill="x", pady=(0, 20))
        
        self.single_status_label = ctk.CTkLabel(
            self.single_status_frame,
            text="Durum yükleniyor...",
            font=ctk.CTkFont(size=14)
        )
        self.single_status_label.pack(pady=15, padx=15)
        
        # Butonlar
        button_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 20))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Ayarları Kaydet",
            height=45,
            corner_radius=8,
            fg_color=("#1E88E5", "#1565C0"),
            hover_color=("#1976D2", "#0D47A1"),
            command=self.save_single_email_config
        )
        save_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        send_now_btn = ctk.CTkButton(
            button_frame,
            text="📧 Hemen Gönder",
            height=45,
            corner_radius=8,
            fg_color=("#9B59B6", "#8E44AD"),
            hover_color=("#8E44AD", "#7D3C98"),
            command=self.send_single_email_now
        )
        send_now_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))
        
        # İlk durumu kontrol et
        self.check_single_email_status()
    
    def build_log_tab(self, parent):
        """Günlük sekmesi"""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        header = ctk.CTkLabel(
            container,
            text="📋 İşlem Günlüğü",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(anchor="w", pady=(10, 15))
        
        # Günlük alanı
        self.log_text = ctk.CTkTextbox(container, corner_radius=8, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.pack(fill="both", expand=True)
        
        # Başlangıç mesajı
        self.log("Uygulama başlatıldı.")
        self.log(f"Ayarlar yüklendi: {len(self.settings['recipients'])} alıcı.")
        self.log(f"Veri Klasörü: {DATA_DIR}")
    
    def log(self, message):
        """Günlüğe mesaj ekle"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
    
    def check_and_update_status(self):
        """Durumu kontrol et ve güncelle"""
        last_sent = self.settings.get("last_sent_date")
        interval = self.settings.get("interval_days", 30)
        
        if last_sent is None:
            self.status_icon.configure(text="⚠️")
            self.status_text.configure(text="Hiç Gönderilmedi", text_color="#FFA726")
            self.status_detail.configure(text="İlk gönderim için hazır")
            self.next_send_label.configure(text="Henüz hiç e-posta gönderilmedi.\nHazır olduğunuzda gönderin!")
            self.log("Durum: Hiç gönderilmedi.")
            return False
        
        try:
            last_sent_date = datetime.fromisoformat(last_sent)
            current_date = datetime.now()
            days_passed = (current_date - last_sent_date).days
            days_remaining = interval - days_passed
            next_send_date = last_sent_date + timedelta(days=interval)
            
            if days_passed >= interval:
                self.status_icon.configure(text="🔔")
                self.status_text.configure(text="GÖNDERİLMELİ!", text_color="#FF6B35")
                self.status_detail.configure(text=f"{days_passed - interval} gün gecikmiş")
                self.next_send_label.configure(
                    text=f"E-postalar {days_passed - interval} gün gecikmiş!\n\nSon gönderim: {last_sent_date.strftime('%d.%m.%Y')}"
                )
                self.log(f"⚠️ Durum: GÖNDERİLMELİ! {days_passed} gün geçti.")
                return True
            else:
                self.status_icon.configure(text="✅")
                self.status_text.configure(text="Her Şey Yolunda", text_color="#2ECC71")
                self.status_detail.configure(text=f"{days_remaining} gün kaldı")
                self.next_send_label.configure(
                    text=f"Sonraki gönderim:\n{next_send_date.strftime('%d %B %Y')}"
                )
                self.log(f"✅ Durum: Tamam. {days_remaining} gün kaldı.")
                return False
        except Exception as e:
            self.log(f"Hata: {str(e)}")
            return False
    
    def save_config(self):
        """Ayarları kaydet"""
        try:
            self.settings["sender_name"] = self.sender_name_entry.get()
            self.settings["smtp_server"] = self.smtp_server_entry.get()
            self.settings["smtp_port"] = int(self.smtp_port_entry.get())
            self.settings["email"] = self.email_entry.get()
            self.settings["password"] = self.password_entry.get()
            self.settings["subject"] = self.subject_entry.get()
            self.settings["message"] = self.message_text.get("1.0", "end-1c")
            self.settings["interval_days"] = int(self.interval_entry.get())
            
            if self.save_settings():
                messagebox.showinfo("Başarılı", "Ayarlar kaydedildi!")
                self.log("✅ Ayarlar kaydedildi.")
                self.update_stats()
                self.check_and_update_status()
        except ValueError:
            messagebox.showerror("Hata", "Port ve aralık için geçerli sayılar girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Ayarlar kaydedilemedi: {str(e)}")
    
    def save_recipients(self):
        """Alıcıları kaydet"""
        try:
            text = self.recipients_text.get("1.0", "end-1c")
            recipients = [line.strip() for line in text.split("\n") if line.strip()]
            
            # E-posta doğrulama
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            valid_emails = [e for e in recipients if email_pattern.match(e)]
            invalid_emails = [e for e in recipients if not email_pattern.match(e)]
            
            if invalid_emails:
                messagebox.showwarning(
                    "Uyarı",
                    f"{len(invalid_emails)} geçersiz e-posta bulundu ve kaydedilmedi."
                )
            
            self.settings["recipients"] = valid_emails
            
            if self.save_settings():
                self.recipient_count.configure(text=f"{len(valid_emails)} alıcı")
                messagebox.showinfo("Başarılı", f"{len(valid_emails)} alıcı kaydedildi!")
                self.log(f"✅ {len(valid_emails)} alıcı kaydedildi.")
                self.update_stats()
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme hatası: {str(e)}")
    
    def import_recipients(self):
        """Dosyadan alıcıları yükle"""
        filename = filedialog.askopenfilename(
            title="Alıcı dosyası seçin",
            filetypes=[("Metin dosyaları", "*.txt"), ("Tüm dosyalar", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.recipients_text.delete("1.0", "end")
                    self.recipients_text.insert("1.0", content)
                    self.log(f"📂 {os.path.basename(filename)} yüklendi.")
                    messagebox.showinfo("Başarılı", "Dosya yüklendi! Kaydetmeyi unutmayın.")
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya yüklenemedi: {str(e)}")
    
    def test_smtp_connection(self):
        """SMTP bağlantısını test et"""
        try:
            server = self.smtp_server_entry.get()
            port = int(self.smtp_port_entry.get())
            email = self.email_entry.get()
            password = self.password_entry.get()
            
            if not all([server, port, email, password]):
                messagebox.showerror("Hata", "Tüm SMTP alanlarını doldurun.")
                return
            
            self.log(f"🔌 {server}:{port} test ediliyor...")
            
            context = ssl.create_default_context(cafile=certifi.where())
            smtp = smtplib.SMTP(server, port)
            smtp.starttls(context=context)
            smtp.login(email, password)
            smtp.quit()
            
            messagebox.showinfo("Başarılı", "✅ SMTP bağlantısı başarılı!")
            self.log("✅ SMTP testi başarılı.")
        except Exception as e:
            messagebox.showerror("Başarısız", f"❌ Bağlantı hatası:\n{str(e)}")
            self.log(f"❌ SMTP testi başarısız: {str(e)}")
    
    def select_attachment(self):
        """Ek dosya seç"""
        filename = filedialog.askopenfilename(
            title="Eklenecek dosyayı seçin",
            filetypes=[
                ("PDF Dosyaları", "*.pdf"),
                ("Word Dosyaları", "*.docx *.doc"),
                ("Resim Dosyaları", "*.jpg *.jpeg *.png"),
                ("Tüm Dosyalar", "*.*")
            ]
        )
        
        if filename:
            self.settings["attachment_path"] = filename
            self.save_settings()
            self.update_attachment_display()
            self.update_stats()
            self.log(f"📎 Ek dosya seçildi: {os.path.basename(filename)}")
            messagebox.showinfo("Başarılı", f"Ek dosya seçildi:\n{os.path.basename(filename)}")
    
    def remove_attachment(self):
        """Ek dosyayı kaldır"""
        self.settings["attachment_path"] = ""
        self.save_settings()
        self.update_attachment_display()
        self.update_stats()
        self.log("❌ Ek dosya kaldırıldı")
        messagebox.showinfo("Tamamlandı", "Ek dosya kaldırıldı")
    
    def update_attachment_display(self):
        """Ek dosya görüntüsünü güncelle"""
        attachment = self.settings.get("attachment_path", "")
        if attachment and os.path.exists(attachment):
            filename = os.path.basename(attachment)
            filesize = os.path.getsize(attachment) / 1024  # KB
            if filesize > 1024:
                size_str = f"{filesize/1024:.1f} MB"
            else:
                size_str = f"{filesize:.1f} KB"
            self.attachment_label.configure(
                text=f"✅ {filename} ({size_str})",
                text_color=("#2ECC71", "#27AE60")
            )
        else:
            self.attachment_label.configure(
                text="Seçili dosya yok",
                text_color=("#999999", "#666666")
            )
    
    def check_and_process(self):
        """Kontrol et ve gerekirse gönder"""
        is_due = self.check_and_update_status()
        
        if is_due:
            response = messagebox.askyesno(
                "Gönder",
                "E-postalar gönderilmeli!\nŞimdi göndermek ister misiniz?"
            )
            if response:
                self.send_emails()
        else:
            messagebox.showinfo(
                "Henüz Değil",
                "E-postalar henüz gönderilmeli değil.\nSonraki gönderim tarihi için duruma bakın."
            )
    
    def send_now(self):
        """İstediğin zaman direkt gönder"""
        response = messagebox.askyesno(
            "E-posta Gönder",
            "Tüm alıcılara e-posta göndermek istiyor musunuz?\n\nGönderim sonrası süre sıfırlanacak."
        )
        
        if response:
            self.log("✉️ Direkt gönderim başlatıldı...")
            self.send_emails()
    
    def force_send(self):
        """Test gönderimi (tarihi sıfırla)"""
        response = messagebox.askyesno(
            "Tarihi Sıfırla",
            "Bu işlem son gönderim tarihini sıfırlayıp\ne-postaları hemen gönderecek.\n\nDevam edilsin mi?"
        )
        
        if response:
            self.settings["last_sent_date"] = None
            self.save_settings()
            self.log("🔄 Test modu: Tarih sıfırlandı.")
            self.send_emails()
    
    def send_emails(self):
        """E-postaları gönder"""
        if not self.settings["recipients"]:
            messagebox.showerror("Hata", "Alıcı yok!")
            return
        
        if not all([
            self.settings["smtp_server"],
            self.settings["smtp_port"],
            self.settings["email"],
            self.settings["password"],
            self.settings["subject"],
            self.settings["message"]
        ]):
            messagebox.showerror("Hata", "Ayarları tamamlayın!")
            return
        
        self.send_button.configure(state="disabled", text="⏳ Gönderiliyor...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Hazırlanıyor...")
        self.log(f"🚀 {len(self.settings['recipients'])} alıcıya gönderim başlıyor...")
        
        thread = threading.Thread(target=self._send_emails_thread)
        thread.daemon = True
        thread.start()
    
    def _send_emails_thread(self):
        """Gönderim thread'i"""
        recipients = self.settings["recipients"]
        total = len(recipients)
        success = 0
        failed = 0
        
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            smtp = smtplib.SMTP(self.settings["smtp_server"], self.settings["smtp_port"])
            smtp.starttls(context=context)
            smtp.login(self.settings["email"], self.settings["password"])
            
            for i, recipient in enumerate(recipients):
                try:
                    msg = MIMEMultipart()
                    # Gönderen ismini ekle
                    sender_name = self.settings.get("sender_name", "")
                    if sender_name:
                        msg['From'] = f"{sender_name} <{self.settings['email']}>"
                    else:
                        msg['From'] = self.settings["email"]
                    msg['To'] = recipient
                    msg['Subject'] = self.settings["subject"]
                    msg.attach(MIMEText(self.settings["message"], 'plain'))
                    
                    # Ek dosya varsa ekle
                    attachment_path = self.settings.get("attachment_path", "")
                    if attachment_path and os.path.exists(attachment_path):
                        with open(attachment_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(attachment_path)}'
                            )
                            msg.attach(part)
                    
                    smtp.send_message(msg)
                    success += 1
                    self.after(0, self.log, f"✅ {recipient}")
                except Exception as e:
                    failed += 1
                    self.after(0, self.log, f"❌ {recipient}: {str(e)}")
                
                progress = (i + 1) / total
                self.after(0, self.progress_bar.set, progress)
                self.after(0, self.progress_label.configure, {"text": f"{i+1}/{total}"})
            
            smtp.quit()
            
            self.settings["last_sent_date"] = datetime.now().isoformat()
            self.save_settings()
            
            self.after(0, self._sending_complete, success, failed)
            
        except Exception as e:
            self.after(0, self.log, f"❌ SMTP Hatası: {str(e)}")
            self.after(0, messagebox.showerror, "Hata", f"Gönderim hatası:\n{str(e)}")
            self.after(0, self.send_button.configure, {"state": "normal", "text": "🚀 Kontrol Et ve Gönder"})
            self.after(0, self.progress_label.configure, {"text": ""})
    
    def _sending_complete(self, success, failed):
        """Gönderim tamamlandı"""
        self.log(f"✅ Tamamlandı: {success} başarılı, {failed} başarısız")
        messagebox.showinfo(
            "Tamamlandı",
            f"E-posta gönderimi tamamlandı!\n\n✅ Başarılı: {success}\n❌ Başarısız: {failed}"
        )
        self.send_button.configure(state="normal", text="🚀 Kontrol Et ve Gönder")
        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self.check_and_update_status()
        self.update_stats()
    
    def update_stats(self):
        """İstatistikleri güncelle"""
        self.recipient_stat.configure(text=f"👥 Alıcı Sayısı: {len(self.settings['recipients'])}")
        self.interval_stat.configure(text=f"⏰ Gönderim Aralığı: {self.settings['interval_days']} gün")
        
        last_sent = self.settings.get('last_sent_date')
        if last_sent:
            try:
                date_str = datetime.fromisoformat(last_sent).strftime('%d.%m.%Y')
                self.last_sent_stat.configure(text=f"📅 Son Gönderim: {date_str}")
            except:
                self.last_sent_stat.configure(text="📅 Son Gönderim: -")
        else:
            self.last_sent_stat.configure(text="📅 Son Gönderim: Hiç gönderilmedi")
        
        # Ek dosya durumu
        attachment = self.settings.get('attachment_path', '')
        if attachment and os.path.exists(attachment):
            att_text = f"📎 Ek: {os.path.basename(attachment)}"
        else:
            att_text = "📎 Ek: Yok"
        self.attachment_stat.configure(text=att_text)
    
    def check_single_email_status(self):
        """Tekli e-posta durumunu kontrol et"""
        last_sent = self.settings.get("single_last_sent_date")
        interval = self.settings.get("single_interval_days", 7)
        
        if not self.settings.get("single_email"):
            self.single_status_label.configure(
                text="⚠️ Henüz e-posta adresi girilmedi",
                text_color="#FFA726"
            )
            return
        
        if last_sent is None:
            self.single_status_label.configure(
                text=f"✉️ {self.settings['single_email']} adresine henüz gönderilmedi",
                text_color="#2ECC71"
            )
            return
        
        try:
            last_sent_date = datetime.fromisoformat(last_sent)
            current_date = datetime.now()
            days_passed = (current_date - last_sent_date).days
            days_remaining = interval - days_passed
            next_send_date = last_sent_date + timedelta(days=interval)
            
            if days_passed >= interval:
                self.single_status_label.configure(
                    text=f"🔔 {self.settings['single_email']} adresine {days_passed - interval} gün gecikmeyle gönderilmeli!",
                    text_color="#FF6B35"
                )
            else:
                self.single_status_label.configure(
                    text=f"✅ Sonraki gönderim: {next_send_date.strftime('%d.%m.%Y')} ({days_remaining} gün kaldı)",
                    text_color="#2ECC71"
                )
        except Exception as e:
            self.single_status_label.configure(
                text=f"Hata: {str(e)}",
                text_color="#E74C3C"
            )
    
    def select_single_attachment(self):
        """Tekli mail için ek dosya seç"""
        filename = filedialog.askopenfilename(
            title="Tekli mail için ek dosya seçin",
            filetypes=[
                ("PDF Dosyaları", "*.pdf"),
                ("Word Dosyaları", "*.docx *.doc"),
                ("Resim Dosyaları", "*.jpg *.jpeg *.png"),
                ("Tüm Dosyalar", "*.*")
            ]
        )
        
        if filename:
            self.settings["single_attachment_path"] = filename
            self.save_settings()
            self.update_single_attachment_display()
            self.log(f"📎 Tekli mail eki seçildi: {os.path.basename(filename)}")
            messagebox.showinfo("Başarılı", f"Tekli mail eki seçildi:\n{os.path.basename(filename)}")
    
    def remove_single_attachment(self):
        """Tekli mail ekini kaldır"""
        self.settings["single_attachment_path"] = ""
        self.save_settings()
        self.update_single_attachment_display()
        self.log("❌ Tekli mail eki kaldırıldı")
        messagebox.showinfo("Tamamlandı", "Tekli mail eki kaldırıldı")
    
    def update_single_attachment_display(self):
        """Tekli mail ek dosya görüntüsünü güncelle"""
        attachment = self.settings.get("single_attachment_path", "")
        if attachment and os.path.exists(attachment):
            filename = os.path.basename(attachment)
            filesize = os.path.getsize(attachment) / 1024  # KB
            if filesize > 1024:
                size_str = f"{filesize/1024:.1f} MB"
            else:
                size_str = f"{filesize:.1f} KB"
            self.single_attachment_label.configure(
                text=f"✅ {filename} ({size_str})",
                text_color=("#2ECC71", "#27AE60")
            )
        else:
            self.single_attachment_label.configure(
                text="Seçili dosya yok",
                text_color=("#999999", "#666666")
            )
    
    def save_single_email_config(self):
        """Tekli e-posta ayarlarını kaydet"""
        try:
            # E-posta doğrulama
            email = self.single_email_entry.get().strip()
            if email:
                email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
                if not email_pattern.match(email):
                    messagebox.showerror("Hata", "Geçersiz e-posta adresi!")
                    return
            
            self.settings["single_email"] = email
            self.settings["single_subject"] = self.single_subject_entry.get()
            self.settings["single_message"] = self.single_message_text.get("1.0", "end-1c")
            self.settings["single_interval_days"] = int(self.single_interval_entry.get())
            
            if self.save_settings():
                messagebox.showinfo("Başarılı", "Tekli e-posta ayarları kaydedildi!")
                self.log("✅ Tekli e-posta ayarları kaydedildi.")
                self.check_single_email_status()
        except ValueError:
            messagebox.showerror("Hata", "Aralık için geçerli bir sayı girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme hatası: {str(e)}")
    
    def send_single_email_now(self):
        """Tekli e-postayı hemen gönder"""
        if not self.settings.get("single_email"):
            messagebox.showerror("Hata", "E-posta adresi girilmedi!")
            return
        
        if not self.settings.get("single_subject") or not self.settings.get("single_message"):
            messagebox.showerror("Hata", "Konu ve mesaj girilmedi!")
            return
        
        response = messagebox.askyesno(
            "E-posta Gönder",
            f"{self.settings['single_email']} adresine e-posta gönderilsin mi?\n\nGönderim sonrası süre sıfırlanacak."
        )
        
        if response:
            self.log(f"📧 Tekli gönderim: {self.settings['single_email']}")
            thread = threading.Thread(target=self._send_single_email_thread)
            thread.daemon = True
            thread.start()
    
    def _send_single_email_thread(self):
        """Tekli e-posta gönderim thread'i"""
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            smtp = smtplib.SMTP(self.settings["smtp_server"], self.settings["smtp_port"])
            smtp.starttls(context=context)
            smtp.login(self.settings["email"], self.settings["password"])
            
            msg = MIMEMultipart()
            sender_name = self.settings.get("sender_name", "")
            if sender_name:
                msg['From'] = f"{sender_name} <{self.settings['email']}>"
            else:
                msg['From'] = self.settings["email"]
            msg['To'] = self.settings["single_email"]
            msg['Subject'] = self.settings["single_subject"]
            msg.attach(MIMEText(self.settings["single_message"], 'plain'))
            
            # Tekli mail için ayrı ek dosya
            attachment_path = self.settings.get("single_attachment_path", "")
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    msg.attach(part)
            
            smtp.send_message(msg)
            smtp.quit()
            
            # Tarihi güncelle
            self.settings["single_last_sent_date"] = datetime.now().isoformat()
            self.save_settings()
            
            self.after(0, self.log, f"✅ Tekli e-posta gönderildi: {self.settings['single_email']}")
            self.after(0, messagebox.showinfo, "Başarılı", f"E-posta başarıyla gönderildi!\n{self.settings['single_email']}")
            self.after(0, self.check_single_email_status)
            
        except Exception as e:
            self.after(0, self.log, f"❌ Tekli e-posta hatası: {str(e)}")
            self.after(0, messagebox.showerror, "Hata", f"Gönderim hatası:\n{str(e)}")



def main():
    app = ModernEmailApp()
    app.mainloop()


if __name__ == "__main__":
    main()
