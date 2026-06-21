#!/usr/bin/env python3
"""EmailAI - AI destekli e-posta otomasyonu.
Sekmeler: Ayarlar | Profilim | AI Mail | Toplu Gönderim | Günlük
LLM olmadan da Toplu Gönderim ve manuel gönderim çalışır.
"""
import os
import sys
import time
import threading
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")

try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
except ImportError as e:
    print(f"Eksik kütüphane: {e}\nÖnce kurulum scriptini çalıştırın (install.sh / install.bat).")
    sys.exit(1)

from core.settings import Settings
from core import email_service, finder, profile as profile_mod
from core.llm import LLMClient, TONES

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT = "#1E88E5"
OK_C = "#27AE60"
WARN_C = "#E67E22"
ERR_C = "#C0392B"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EmailAI — Akıllı E-posta Asistanı")
        self.geometry("980x720")
        self.minsize(860, 620)
        self.s = Settings()
        self.draft_cards = []   # AI sekmesi sonuç kartları
        self._build()

    # ================= layout =================
    def _build(self):
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        self.t_settings = self.tabs.add("⚙️  Ayarlar")
        self.t_profile = self.tabs.add("👤  Profilim")
        self.t_ai = self.tabs.add("✨  AI Mail")
        self.t_bulk = self.tabs.add("📨  Toplu Gönderim")
        self.t_log = self.tabs.add("📋  Günlük")
        self._build_settings()
        self._build_profile()
        self._build_ai()
        self._build_bulk()
        self._build_log()

    # ---- helpers ----
    def _label(self, parent, text, size=12, bold=True, pad=(10, 0)):
        ctk.CTkLabel(parent, text=text,
                     font=ctk.CTkFont(size=size, weight="bold" if bold else "normal")
                     ).pack(anchor="w", pady=pad)

    def _entry(self, parent, key, show=None, placeholder=""):
        e = ctk.CTkEntry(parent, show=show, placeholder_text=placeholder)
        e.pack(fill="x", pady=(4, 0))
        val = self.s.get(key)
        if val:
            e.insert(0, str(val))
        return e

    # ================= AYARLAR =================
    def _build_settings(self):
        sc = ctk.CTkScrollableFrame(self.t_settings, fg_color="transparent")
        sc.pack(fill="both", expand=True)

        self._label(sc, "SMTP (Mail Gönderimi)", 16)
        self.e_sender = self._entry(sc, "sender_name", placeholder="Ad Soyad")
        self._label(sc, "Gönderen Adı")
        self.e_server = self._entry(sc, "smtp_server")
        self._label(sc, "SMTP Sunucu")
        self.e_port = self._entry(sc, "smtp_port")
        self._label(sc, "SMTP Port")
        self.e_email = self._entry(sc, "email", placeholder="seninmailin@gmail.com")
        self._label(sc, "E-posta")
        self.e_pass = self._entry(sc, "smtp_password", show="●",
                                  placeholder="Gmail Uygulama Şifresi")
        self._label(sc, "Uygulama Şifresi (keyring'de saklanır)")
        ctk.CTkButton(sc, text="🔌 SMTP Bağlantısını Test Et", fg_color=OK_C,
                      command=self._test_smtp).pack(fill="x", pady=12)

        self._label(sc, "Yapay Zeka (LLM)", 16, pad=(20, 0))
        self.opt_provider = ctk.CTkOptionMenu(sc, values=["gemini", "openai"],
                                              command=lambda *_: None)
        self.opt_provider.set(self.s.get("llm_provider", "gemini"))
        self.opt_provider.pack(fill="x", pady=(4, 0))
        self._label(sc, "Sağlayıcı (gemini = Google, openai = OpenAI-uyumlu)")
        self.e_model = self._entry(sc, "llm_model",
                                   placeholder="gemini-2.5-flash / gpt-4o-mini")
        self._label(sc, "Model")
        self.e_baseurl = self._entry(sc, "llm_base_url",
                                     placeholder="OpenAI-uyumlu için base URL (ops.)")
        self._label(sc, "Base URL (sadece openai sağlayıcısı için)")
        self.e_apikey = self._entry(sc, "llm_api_key", show="●",
                                    placeholder="Kendi API anahtarın")
        self._label(sc, "LLM API Anahtarı (keyring'de saklanır)")
        self.chk_ground = ctk.CTkCheckBox(sc, text="Google Search grounding (Gemini, uydurmayı azaltır)")
        if self.s.get("use_grounding", True):
            self.chk_ground.select()
        self.chk_ground.pack(anchor="w", pady=8)
        ctk.CTkButton(sc, text="🤖 LLM Bağlantısını Test Et", fg_color=ACCENT,
                      command=self._test_llm).pack(fill="x", pady=8)

        self._label(sc, "E-posta Bulucu (opsiyonel)", 16, pad=(20, 0))
        self.e_hunter = self._entry(sc, "hunter_api_key", show="●",
                                    placeholder="Hunter.io API anahtarı (gerçek mail için)")
        self._label(sc, "Hunter API Anahtarı — boşsa kalıp tahmini yapılır (doğrulanmaz)")

        ctk.CTkButton(sc, text="💾 Tüm Ayarları Kaydet", height=42,
                      command=self._save_settings).pack(fill="x", pady=24)

    def _save_settings(self):
        try:
            self.s.set("sender_name", self.e_sender.get())
            self.s.set("smtp_server", self.e_server.get())
            self.s.set("smtp_port", int(self.e_port.get() or 587))
            self.s.set("email", self.e_email.get())
            self.s.set("smtp_password", self.e_pass.get())
            self.s.set("llm_provider", self.opt_provider.get())
            self.s.set("llm_model", self.e_model.get())
            self.s.set("llm_base_url", self.e_baseurl.get())
            self.s.set("llm_api_key", self.e_apikey.get())
            self.s.set("use_grounding", bool(self.chk_ground.get()))
            self.s.set("hunter_api_key", self.e_hunter.get())
            self.s.save()
            messagebox.showinfo("Tamam", "Ayarlar kaydedildi.\nSırlar keyring'de güvende.")
        except ValueError:
            messagebox.showerror("Hata", "Port sayı olmalı.")

    def _test_smtp(self):
        def run():
            ok, msg = email_service.test_connection(
                self.e_server.get(), int(self.e_port.get() or 587),
                self.e_email.get(), self.e_pass.get())
            self.after(0, lambda: (messagebox.showinfo if ok else messagebox.showerror)(
                "SMTP", msg))
        threading.Thread(target=run, daemon=True).start()

    def _make_llm(self):
        key = self.e_apikey.get() or self.s.get("llm_api_key")
        if not key:
            return None
        return LLMClient(self.opt_provider.get(), key, self.e_model.get(),
                         self.e_baseurl.get(), bool(self.chk_ground.get()))

    def _test_llm(self):
        client = self._make_llm()
        if not client:
            messagebox.showwarning("LLM", "Önce API anahtarı gir.")
            return

        def run():
            ok, msg = client.test()
            self.after(0, lambda: (messagebox.showinfo if ok else messagebox.showerror)(
                "LLM", msg if ok else f"Başarısız:\n{msg}"))
        threading.Thread(target=run, daemon=True).start()

    # ================= PROFİLİM =================
    def _build_profile(self):
        f = ctk.CTkFrame(self.t_profile, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=8, pady=8)
        self._label(f, "Seni tanıtan metin / CV", 16)
        ctk.CTkLabel(f, text="AI maillerini SENİN ağzından yazsın diye kullanılır. "
                             "CV yükle ya da serbestçe yaz.",
                     text_color="#aaa", justify="left").pack(anchor="w")
        bf = ctk.CTkFrame(f, fg_color="transparent")
        bf.pack(fill="x", pady=8)
        ctk.CTkButton(bf, text="📄 CV Yükle (PDF/TXT)", command=self._load_cv).pack(side="left", padx=4)
        ctk.CTkButton(bf, text="Temizle", fg_color=ERR_C,
                      command=lambda: self.txt_profile.delete("1.0", "end")).pack(side="left", padx=4)
        self.txt_profile = ctk.CTkTextbox(f, height=260)
        self.txt_profile.pack(fill="both", expand=True, pady=6)
        self.txt_profile.insert("1.0", self.s.get("profile_text", ""))

        self._label(f, "İmza")
        self.txt_sig = ctk.CTkTextbox(f, height=80)
        self.txt_sig.pack(fill="x", pady=6)
        self.txt_sig.insert("1.0", self.s.get("signature", ""))
        ctk.CTkButton(f, text="💾 Profili Kaydet", command=self._save_profile).pack(fill="x", pady=10)

    def _load_cv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CV", "*.pdf *.txt *.md"), ("Tümü", "*.*")])
        if not path:
            return
        text = profile_mod.extract_text(path)
        if text == "__NO_PYPDF__":
            messagebox.showwarning("PDF", "PDF okumak için 'pypdf' gerekli.\n"
                                          "pip install pypdf — ya da TXT yükle / metni yapıştır.")
            return
        if not text.strip():
            messagebox.showwarning("CV", "Metin çıkarılamadı. TXT dene veya elle yapıştır.")
            return
        self.txt_profile.delete("1.0", "end")
        self.txt_profile.insert("1.0", text)

    def _save_profile(self):
        self.s.set("profile_text", self.txt_profile.get("1.0", "end-1c"))
        self.s.set("signature", self.txt_sig.get("1.0", "end-1c"))
        self.s.save()
        messagebox.showinfo("Tamam", "Profil kaydedildi.")

    # ================= AI MAIL =================
    def _build_ai(self):
        f = ctk.CTkFrame(self.t_ai, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=8, pady=8)

        top = ctk.CTkFrame(f)
        top.pack(fill="x")
        self._label(top, "Mailin amacı (brief)", 13)
        self.txt_brief = ctk.CTkTextbox(top, height=64)
        self.txt_brief.pack(fill="x", padx=8, pady=(0, 6))
        self.txt_brief.insert("1.0", "Örn: Hocama yüksek lisans tez savunmama davet maili.")

        self._label(top, "Hedefler — her satıra bir tane "
                         "(Ad Soyad, şirket/site veya LinkedIn URL ya da direkt mail)", 13)
        self.txt_targets = ctk.CTkTextbox(top, height=90)
        self.txt_targets.pack(fill="x", padx=8, pady=(0, 6))
        self.txt_targets.insert("1.0",
                                "Ahmet Yılmaz, beko.com\n"
                                "Prof. Dr. X, firat.edu.tr\n"
                                "ali@firma.com")

        row = ctk.CTkFrame(top, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=6)
        self.opt_tone = ctk.CTkOptionMenu(row, values=list(TONES.keys()))
        self.opt_tone.set(self.s.get("default_tone", "samimi"))
        self.opt_tone.pack(side="left", padx=4)
        self.opt_lang = ctk.CTkOptionMenu(row, values=["tr", "en"])
        self.opt_lang.set(self.s.get("default_lang", "tr"))
        self.opt_lang.pack(side="left", padx=4)
        self.chk_html = ctk.CTkCheckBox(row, text="HTML mail")
        self.chk_html.pack(side="left", padx=8)
        self.btn_gen = ctk.CTkButton(row, text="✨ Araştır & Taslak Üret",
                                     fg_color=ACCENT, command=self._generate)
        self.btn_gen.pack(side="right", padx=4)

        self.ai_status = ctk.CTkLabel(f, text="", text_color="#aaa")
        self.ai_status.pack(anchor="w", padx=8)

        self.results = ctk.CTkScrollableFrame(f, label_text="Sonuçlar")
        self.results.pack(fill="both", expand=True, pady=6)

        self.btn_send_sel = ctk.CTkButton(f, text="🚀 Onaylananları Gönder", height=42,
                                          fg_color=OK_C, command=self._send_selected,
                                          state="disabled")
        self.btn_send_sel.pack(fill="x", pady=6)

    def _generate(self):
        client = self._make_llm()
        if not client:
            messagebox.showwarning("LLM", "AI üretimi için Ayarlar'da API anahtarı gerekli. "
                                          "(Anahtarsız Toplu Gönderim sekmesini kullanabilirsin.)")
            return
        targets = [t.strip() for t in self.txt_targets.get("1.0", "end-1c").splitlines() if t.strip()]
        if not targets:
            messagebox.showwarning("Hedef", "En az bir hedef gir.")
            return
        brief = self.txt_brief.get("1.0", "end-1c")
        prof = self.txt_profile.get("1.0", "end-1c")
        sig = self.txt_sig.get("1.0", "end-1c")
        tone, lang = self.opt_tone.get(), self.opt_lang.get()
        hunter = self.e_hunter.get() or self.s.get("hunter_api_key")

        for c in self.draft_cards:
            c["frame"].destroy()
        self.draft_cards.clear()
        self.btn_gen.configure(state="disabled", text="Üretiliyor…")
        self.btn_send_sel.configure(state="disabled")

        def run():
            for i, tgt in enumerate(targets):
                self.after(0, lambda i=i, n=len(targets): self.ai_status.configure(
                    text=f"Araştırılıyor… {i+1}/{n}"))
                try:
                    res = client.research_and_draft(tgt, brief, prof, tone, lang, sig)
                except Exception as e:
                    res = {"email": "", "email_confidence": "unknown",
                           "subject": "(hata)", "body": f"Üretim hatası: {e}",
                           "sources": [], "research_notes": ""}
                # mail çözümü: araştırma + Hunter + kalıp
                dom = finder.domain_from(tgt) or finder.domain_from(res.get("email", ""))
                name = tgt.split(",")[0].strip()
                if "@" in tgt:  # kullanıcı direkt mail verdiyse
                    chosen = {"email": finder.domain_from(tgt) and tgt.strip(),
                              "confidence": "verified", "source": "kullanıcı"}
                    chosen["email"] = tgt.strip() if "@" in tgt else ""
                else:
                    chosen = finder.find_email(
                        name, dom, hunter_key=hunter,
                        llm_found=res.get("email") if res.get("email_confidence") == "verified" else None)
                self.after(0, self._add_card, tgt, res, chosen)
            self.after(0, lambda: (self.ai_status.configure(text="Hazır. Düzenle, onayla, gönder."),
                                   self.btn_gen.configure(state="normal", text="✨ Araştır & Taslak Üret"),
                                   self.btn_send_sel.configure(state="normal")))
        threading.Thread(target=run, daemon=True).start()

    def _add_card(self, target, res, chosen):
        card = ctk.CTkFrame(self.results, border_width=1)
        card.pack(fill="x", pady=6, padx=4)

        conf = chosen.get("confidence", "unknown")
        badge = {"verified": ("✓ doğrulandı", OK_C),
                 "guessed": ("≈ tahmin (DOĞRULANMADI)", WARN_C),
                 "unknown": ("✗ mail bulunamadı", ERR_C)}.get(conf, ("?", "#888"))
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=8, pady=(8, 0))
        chk = ctk.CTkCheckBox(head, text=target)
        if conf == "verified":
            chk.select()
        chk.pack(side="left")
        ctk.CTkLabel(head, text=badge[0], text_color=badge[1],
                     font=ctk.CTkFont(size=11, weight="bold")).pack(side="right")

        e_mail = ctk.CTkEntry(card)
        e_mail.pack(fill="x", padx=8, pady=4)
        e_mail.insert(0, chosen.get("email", ""))
        e_subj = ctk.CTkEntry(card)
        e_subj.pack(fill="x", padx=8, pady=2)
        e_subj.insert(0, res.get("subject", ""))
        t_body = ctk.CTkTextbox(card, height=140)
        t_body.pack(fill="x", padx=8, pady=4)
        t_body.insert("1.0", res.get("body", ""))

        if res.get("research_notes"):
            ctk.CTkLabel(card, text="🔎 " + res["research_notes"], text_color="#9aa",
                         wraplength=820, justify="left").pack(anchor="w", padx=8)
        if res.get("sources"):
            src = " · ".join(s["url"] for s in res["sources"][:4])
            ctk.CTkLabel(card, text="Kaynaklar: " + src, text_color="#678",
                         wraplength=820, justify="left").pack(anchor="w", padx=8, pady=(0, 8))
        else:
            ctk.CTkLabel(card, text="", height=2).pack()

        self.draft_cards.append({"frame": card, "chk": chk, "mail": e_mail,
                                 "subj": e_subj, "body": t_body})

    def _send_selected(self):
        chosen = [c for c in self.draft_cards if c["chk"].get()]
        valid = [c for c in chosen if "@" in c["mail"].get()]
        if not valid:
            messagebox.showwarning("Gönder", "Onaylı ve geçerli mailli kart yok.")
            return
        if not messagebox.askyesno("Onay", f"{len(valid)} mail gönderilecek. Devam?"):
            return
        cfg = self._smtp_cfg()
        if not cfg:
            return
        html = bool(self.chk_html.get())
        delay = float(self.s.get("send_delay_sec", 2.0))
        self.btn_send_sel.configure(state="disabled", text="Gönderiliyor…")

        def run():
            ok = err = 0
            for c in valid:
                s, m = email_service.send_email(
                    cfg["server"], cfg["port"], cfg["email"], cfg["password"],
                    cfg["sender"], c["mail"].get(), c["subj"].get(),
                    c["body"].get("1.0", "end-1c"), html=html)
                if s:
                    ok += 1
                    self.after(0, self._log, f"✅ {c['mail'].get()}")
                else:
                    err += 1
                    self.after(0, self._log, f"❌ {c['mail'].get()}: {m}")
                time.sleep(delay)
            self.after(0, lambda: (self.btn_send_sel.configure(
                state="normal", text="🚀 Onaylananları Gönder"),
                messagebox.showinfo("Bitti", f"Başarılı: {ok}\nHatalı: {err}")))
        threading.Thread(target=run, daemon=True).start()

    # ================= TOPLU GÖNDERİM =================
    def _build_bulk(self):
        sc = ctk.CTkScrollableFrame(self.t_bulk, fg_color="transparent")
        sc.pack(fill="both", expand=True)
        ctk.CTkLabel(sc, text="Aynı maili çok kişiye. (LLM gerekmez.)",
                     text_color="#aaa").pack(anchor="w", pady=4)
        self._label(sc, "Konu")
        self.b_subj = ctk.CTkEntry(sc)
        self.b_subj.pack(fill="x", pady=(4, 0))
        self.b_subj.insert(0, self.s.get("bulk_subject", ""))
        self._label(sc, "Mesaj  (kişiselleştirme için {ad} kullanabilirsin)")
        self.b_msg = ctk.CTkTextbox(sc, height=150)
        self.b_msg.pack(fill="x", pady=(4, 0))
        self.b_msg.insert("1.0", self.s.get("bulk_message", ""))
        self.b_html = ctk.CTkCheckBox(sc, text="HTML olarak gönder")
        self.b_html.pack(anchor="w", pady=6)

        self._label(sc, "Alıcılar — her satır:  mail  veya  mail, Ad")
        self.b_to = ctk.CTkTextbox(sc, height=140)
        self.b_to.pack(fill="x", pady=(4, 0))
        self.b_to.insert("1.0", "\n".join(self.s.get("bulk_recipients", [])))
        rf = ctk.CTkFrame(sc, fg_color="transparent")
        rf.pack(fill="x", pady=6)
        ctk.CTkButton(rf, text="📥 Dosyadan Yükle", command=self._import_bulk).pack(side="left", padx=4)
        self.b_att = ctk.CTkLabel(rf, text="Ek: yok", text_color="#888")
        self.b_att.pack(side="left", padx=10)
        ctk.CTkButton(rf, text="Ek Seç", command=self._pick_att).pack(side="left", padx=4)
        ctk.CTkButton(rf, text="Ek Kaldır", fg_color=ERR_C,
                      command=lambda: (self.s.set("attachment_path", ""),
                                       self.b_att.configure(text="Ek: yok"))).pack(side="left", padx=4)
        self._att_path = self.s.get("attachment_path", "")
        if self._att_path:
            self.b_att.configure(text="Ek: " + os.path.basename(self._att_path))

        ctk.CTkButton(sc, text="🚀 Toplu Gönder", height=42, fg_color=OK_C,
                      command=self._send_bulk).pack(fill="x", pady=16)

    def _pick_att(self):
        p = filedialog.askopenfilename()
        if p:
            self._att_path = p
            self.s.set("attachment_path", p)
            self.b_att.configure(text="Ek: " + os.path.basename(p))

    def _import_bulk(self):
        p = filedialog.askopenfilename(filetypes=[("Metin/CSV", "*.txt *.csv"), ("Tümü", "*.*")])
        if not p:
            return
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                lines = [l.strip() for l in f if "@" in l]
            self.b_to.delete("1.0", "end")
            self.b_to.insert("1.0", "\n".join(lines))
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _send_bulk(self):
        cfg = self._smtp_cfg()
        if not cfg:
            return
        rows = [r.strip() for r in self.b_to.get("1.0", "end-1c").splitlines() if "@" in r]
        if not rows:
            messagebox.showwarning("Alıcı", "Alıcı listesi boş.")
            return
        subj = self.b_subj.get()
        body = self.b_msg.get("1.0", "end-1c")
        html = bool(self.b_html.get())
        self.s.set("bulk_subject", subj)
        self.s.set("bulk_message", body)
        self.s.set("bulk_recipients", rows)
        self.s.save()
        if not messagebox.askyesno("Onay", f"{len(rows)} kişiye gönderilecek. Devam?"):
            return
        delay = float(self.s.get("send_delay_sec", 2.0))

        def run():
            ok = err = 0
            for r in rows:
                parts = [x.strip() for x in r.split(",")]
                mail = parts[0]
                ad = parts[1] if len(parts) > 1 else ""
                b = body.replace("{ad}", ad)
                s, m = email_service.send_email(
                    cfg["server"], cfg["port"], cfg["email"], cfg["password"],
                    cfg["sender"], mail, subj, b, html=html,
                    attachment_path=self._att_path or None)
                if s:
                    ok += 1
                    self.after(0, self._log, f"✅ {mail}")
                else:
                    err += 1
                    self.after(0, self._log, f"❌ {mail}: {m}")
                time.sleep(delay)
            self.after(0, lambda: messagebox.showinfo("Bitti", f"Başarılı: {ok}\nHatalı: {err}"))
        threading.Thread(target=run, daemon=True).start()

    # ================= GÜNLÜK =================
    def _build_log(self):
        self.log_box = ctk.CTkTextbox(self.t_log)
        self.log_box.pack(fill="both", expand=True, padx=6, pady=6)
        self._log("Hazır.")

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        try:
            self.log_box.insert("end", f"[{ts}] {msg}\n")
            self.log_box.see("end")
        except Exception:
            print(msg)

    # ================= ortak =================
    def _smtp_cfg(self):
        email = self.e_email.get() or self.s.get("email")
        pwd = self.e_pass.get() or self.s.get("smtp_password")
        if not (email and pwd):
            messagebox.showwarning("SMTP", "Ayarlar'da e-posta ve şifre gir.")
            self.tabs.set("⚙️  Ayarlar")
            return None
        return {"server": self.e_server.get() or self.s.get("smtp_server"),
                "port": int(self.e_port.get() or self.s.get("smtp_port", 587)),
                "email": email, "password": pwd,
                "sender": self.e_sender.get() or self.s.get("sender_name", "")}


if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception as e:
        log.critical("Çöktü: %s", e)
        try:
            from tkinter import messagebox
            messagebox.showerror("Kritik Hata", str(e))
        except Exception:
            print("Kritik hata:", e)
