#!/usr/bin/env python3
"""EmailAI — AI destekli e-posta asistanı (sade arayüz).
Sol menü: Oluştur · Toplu · Profil · Ayarlar.
LLM olmadan da Toplu/manuel gönderim çalışır.
"""
import os
import re
import sys
import time
import datetime
import threading
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")

try:
    import customtkinter as ctk
    from tkinter import messagebox, filedialog
except ImportError as e:
    print(f"Eksik kütüphane: {e}\nÖnce BASLAT.bat / BASLAT.command çalıştır.")
    sys.exit(1)

from core.settings import Settings
from core import email_service as es, finder, profile as profile_mod
from core.llm import LLMClient, TONES, MODEL_PRESETS, PROVIDERS, fetch_openrouter_models

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT = "#3B82F6"
ACCENT_H = "#2563EB"
OK = "#22C55E"
WARN = "#F59E0B"
DANGER = "#EF4444"
MUTED = "#94A3B8"
CARD = "#1F2630"

PROVIDER_LABELS = {"Google Gemini": "gemini", "OpenRouter": "openrouter", "OpenAI / Özel": "openai"}
LABEL_BY_PROVIDER = {v: k for k, v in PROVIDER_LABELS.items()}
SMTP_PRESETS = {"Gmail": ("smtp.gmail.com", 587), "Outlook": ("smtp.office365.com", 587),
                "Yandex": ("smtp.yandex.com", 465), "Özel": ("", 0)}

# Mail amacı şablonları — "hep tez yazıyor" sorununu çözer
PURPOSES = {
    "Serbest (aşağıya kendim yazacağım)": "",
    "İş / staj başvurusu": "Bu kişiye/şirkete iş veya staj başvurusu maili. Profilimdeki deneyim ve becerilerden somut örneklerle neden uygun olduğumu anlat.",
    "İşbirliği / ortaklık teklifi": "Bu kişiye/şirkete işbirliği veya ortaklık teklifi maili.",
    "Etkinlik / toplantı daveti": "Bu kişiyi bir etkinliğe veya toplantıya davet maili.",
    "Soğuk satış / tanıtım": "Bu kişiye ürün/hizmet tanıtımı ve kısa, fayda odaklı bir soğuk satış maili.",
    "Takip / nazik hatırlatma": "Önceki bir konunun nazik takibi / hatırlatması maili.",
    "Teşekkür": "Bu kişiye içten bir teşekkür maili.",
    "Tez / akademik davet": "Hocama/akademisyene yüksek lisans tez savunmama davet maili.",
}


def _seconds_until(hhmm: str) -> float:
    """'HH:MM' -> o saate kadar saniye (geçmişse yarına). Boş/geçersiz -> 0 (hemen)."""
    s = (hhmm or "").strip()
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if not m:
        return 0.0
    h, mi = int(m.group(1)), int(m.group(2))
    if not (0 <= h < 24 and 0 <= mi < 60):
        return 0.0
    now = datetime.datetime.now()
    target = now.replace(hour=h, minute=mi, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    return max(0.0, (target - now).total_seconds())


def font(size=13, bold=False):
    return ctk.CTkFont(size=size, weight="bold" if bold else "normal")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EmailAI")
        self.geometry("1000x700")
        self.minsize(900, 600)
        self.s = Settings()
        self.draft_cards = []
        self._att = self.s.get("attachment_path", "")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_content()
        self.show("compose")

    # ===================== SIDEBAR =====================
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color="#161B22")
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

        ctk.CTkLabel(sb, text="✉  EmailAI", font=font(22, True)).pack(pady=(26, 6))
        ctk.CTkLabel(sb, text="akıllı mail asistanı", text_color=MUTED,
                     font=font(11)).pack(pady=(0, 24))

        self.nav = {}
        for key, label, icon in [("compose", "Oluştur", "✨"), ("bulk", "Toplu Gönder", "📨"),
                                 ("profile", "Profil", "👤"), ("settings", "Ayarlar", "⚙️")]:
            b = ctk.CTkButton(sb, text=f"  {icon}   {label}", anchor="w", height=44,
                              corner_radius=10, fg_color="transparent", text_color="#E6EDF3",
                              hover_color="#222B36", font=font(14),
                              command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=14, pady=3)
            self.nav[key] = b

        # durum göstergeleri (alt)
        status = ctk.CTkFrame(sb, fg_color="transparent")
        status.pack(side="bottom", fill="x", padx=16, pady=18)
        self.dot_smtp = ctk.CTkLabel(status, text="● Mail: —", font=font(12), text_color=MUTED)
        self.dot_smtp.pack(anchor="w", pady=2)
        self.dot_ai = ctk.CTkLabel(status, text="● Yapay zeka: —", font=font(12), text_color=MUTED)
        self.dot_ai.pack(anchor="w", pady=2)

    def _refresh_status(self):
        smtp_ok = bool(self.s.get("email") and self.s.get("smtp_password"))
        ai_ok = bool(self.s.get("llm_api_key"))
        self.dot_smtp.configure(text="● Mail: " + ("hazır" if smtp_ok else "eksik"),
                                text_color=OK if smtp_ok else MUTED)
        self.dot_ai.configure(text="● Yapay zeka: " + ("hazır" if ai_ok else "eksik"),
                              text_color=OK if ai_ok else MUTED)

    # ===================== CONTENT =====================
    def _build_content(self):
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self.pages = {}
        for key, builder in [("compose", self._page_compose), ("bulk", self._page_bulk),
                             ("profile", self._page_profile), ("settings", self._page_settings)]:
            frame = ctk.CTkFrame(self.content, fg_color="transparent")
            frame.grid(row=0, column=0, sticky="nsew")
            builder(frame)
            self.pages[key] = frame
        self._refresh_status()

    def show(self, key):
        for k, b in self.nav.items():
            b.configure(fg_color=ACCENT if k == key else "transparent")
        self.pages[key].tkraise()

    def _header(self, parent, title, subtitle=""):
        ctk.CTkLabel(parent, text=title, font=font(24, True)).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(parent, text=subtitle, text_color=MUTED, font=font(13)).pack(anchor="w", pady=(2, 14))
        else:
            ctk.CTkLabel(parent, text="", height=8).pack()

    def _card(self, parent, title):
        c = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12)
        c.pack(fill="x", pady=8)
        ctk.CTkLabel(c, text=title, font=font(15, True)).pack(anchor="w", padx=16, pady=(14, 4))
        inner = ctk.CTkFrame(c, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(0, 14))
        return inner

    def _field(self, parent, label, key="", show=None, placeholder=""):
        ctk.CTkLabel(parent, text=label, font=font(12), text_color=MUTED).pack(anchor="w", pady=(8, 2))
        e = ctk.CTkEntry(parent, show=show, placeholder_text=placeholder, height=36)
        e.pack(fill="x")
        if key and self.s.get(key):
            e.insert(0, str(self.s.get(key)))
        return e

    # ===================== OLUŞTUR =====================
    def _page_compose(self, p):
        self._header(p, "✨ AI ile Mail Oluştur", "Kime + ne yazılacağını söyle, gerisini AI halletsin.")
        box = ctk.CTkScrollableFrame(p, fg_color="transparent")
        box.pack(fill="both", expand=True)

        ip = self._card(box, "1 · Amaç & detay")
        ctk.CTkLabel(ip, text="Mail ne hakkında?", font=font(12), text_color=MUTED).pack(anchor="w", pady=(0, 2))
        self.o_purpose = ctk.CTkOptionMenu(ip, values=list(PURPOSES.keys()), command=self._on_purpose)
        self.o_purpose.set(list(PURPOSES.keys())[0])
        self.o_purpose.pack(fill="x")
        ctk.CTkLabel(ip, text="Detay (serbest yaz: bağlam, ne istediğin, özel notlar)",
                     font=font(12), text_color=MUTED).pack(anchor="w", pady=(8, 2))
        self.t_brief = ctk.CTkTextbox(ip, height=70, font=font(13))
        self.t_brief.pack(fill="x")

        tp = self._card(box, "2 · Kime?  (her satıra biri: Ad Soyad, şirket/site ya da LinkedIn linki)")
        self.t_targets = ctk.CTkTextbox(tp, height=90, font=font(13))
        self.t_targets.pack(fill="x")
        self.t_targets.insert("1.0", "Ahmet Yılmaz, beko.com\nhttps://www.linkedin.com/in/ornek\nali@firma.com")

        op = self._card(box, "3 · Üslup & zamanlama")
        row = ctk.CTkFrame(op, fg_color="transparent")
        row.pack(fill="x")
        self.o_tone = ctk.CTkOptionMenu(row, values=list(TONES.keys()), width=120)
        self.o_tone.set(self.s.get("default_tone", "samimi"))
        self.o_tone.pack(side="left", padx=(0, 8))
        self.o_lang = ctk.CTkOptionMenu(row, values=["tr", "en"], width=70)
        self.o_lang.set(self.s.get("default_lang", "tr"))
        self.o_lang.pack(side="left", padx=8)
        self.c_html = ctk.CTkCheckBox(row, text="HTML")
        self.c_html.pack(side="left", padx=10)
        ctk.CTkLabel(row, text="Saat:", font=font(12), text_color=MUTED).pack(side="left", padx=(14, 4))
        self.sch_compose = ctk.CTkEntry(row, width=80, placeholder_text="HH:MM")
        self.sch_compose.pack(side="left")
        ctk.CTkLabel(row, text="(boş=hemen)", font=font(11), text_color=MUTED).pack(side="left", padx=6)

        self.b_gen = ctk.CTkButton(box, text="✨  Araştır & Taslak Üret", height=46, corner_radius=12,
                                   fg_color=ACCENT, hover_color=ACCENT_H, font=font(15, True),
                                   command=self._generate)
        self.b_gen.pack(fill="x", pady=10)
        self.ai_status = ctk.CTkLabel(box, text="", text_color=MUTED, font=font(12))
        self.ai_status.pack(anchor="w")

        self.results = ctk.CTkScrollableFrame(box, label_text="Taslaklar", height=260)
        self.results.pack(fill="both", expand=True, pady=6)

        self.b_send_sel = ctk.CTkButton(p, text="🚀  Onaylananları Gönder", height=46, corner_radius=12,
                                        fg_color=OK, hover_color="#16A34A", font=font(15, True),
                                        state="disabled", command=self._send_selected)
        self.b_send_sel.pack(fill="x", pady=(8, 0))

    def _llm(self):
        key = self.s.get("llm_api_key")
        if not key:
            return None
        return LLMClient(self.s.get("llm_provider", "gemini"), key,
                         self.s.get("llm_model", ""), self.s.get("llm_base_url", ""),
                         bool(self.s.get("use_grounding", True)))

    def _on_purpose(self, label):
        tmpl = PURPOSES.get(label, "")
        self.t_brief.delete("1.0", "end")
        if tmpl:
            self.t_brief.insert("1.0", tmpl)

    def _bump_ai(self, n=1):
        self.s.set("ai_requests", int(self.s.get("ai_requests", 0)) + n)
        self.s.save()
        if hasattr(self, "ai_count_lbl"):
            try:
                self.ai_count_lbl.configure(text=f"Toplam AI isteği: {self.s.get('ai_requests', 0)}")
            except Exception:
                pass

    def _generate(self):
        client = self._llm()
        if not client:
            messagebox.showwarning("Yapay zeka yok",
                                   "AI üretimi için Ayarlar'da bir API anahtarı gir.\n"
                                   "(Anahtarsız 'Toplu Gönder'i kullanabilirsin.)")
            self.show("settings")
            return
        targets = [t.strip() for t in self.t_targets.get("1.0", "end-1c").splitlines() if t.strip()]
        if not targets:
            messagebox.showwarning("Hedef yok", "En az bir kişi gir.")
            return
        brief = self.t_brief.get("1.0", "end-1c")
        prof = self.s.get("profile_text", "")
        sig = self.s.get("signature", "")
        tone, lang = self.o_tone.get(), self.o_lang.get()
        hunter = self.s.get("hunter_api_key")

        for c in self.draft_cards:
            c["frame"].destroy()
        self.draft_cards.clear()
        self.b_gen.configure(state="disabled", text="Üretiliyor…")
        self.b_send_sel.configure(state="disabled")

        def run():
            for i, tgt in enumerate(targets):
                self.after(0, lambda i=i, n=len(targets): self.ai_status.configure(
                    text=f"🔎 Araştırılıyor…  {i+1}/{n}"))
                try:
                    res = client.research_and_draft(tgt, brief, prof, tone, lang, sig)
                except Exception as e:
                    res = {"email": "", "email_confidence": "unknown", "subject": "(hata)",
                           "body": f"Üretim hatası: {e}", "sources": [], "research_notes": ""}
                if "@" in tgt:
                    chosen = {"email": tgt.strip(), "confidence": "verified", "source": "kullanıcı"}
                else:
                    dom = finder.domain_from(tgt) or finder.domain_from(res.get("email", ""))
                    name = tgt.split(",")[0].strip()
                    chosen = finder.find_email(
                        name, dom, hunter_key=hunter,
                        llm_found=res.get("email") if res.get("email") else None)
                self.after(0, self._add_card, tgt, res, chosen)
                self.after(0, self._bump_ai, 1)
            self.after(0, lambda: (self.ai_status.configure(text="✓ Hazır. Düzenle, onayla, gönder."),
                                   self.b_gen.configure(state="normal", text="✨  Araştır & Taslak Üret"),
                                   self.b_send_sel.configure(state="normal")))
        threading.Thread(target=run, daemon=True).start()

    def _add_card(self, target, res, chosen):
        card = ctk.CTkFrame(self.results, fg_color=CARD, corner_radius=10)
        card.pack(fill="x", pady=6, padx=4)
        conf = chosen.get("confidence", "unknown")
        badge = {"verified": ("✓ doğrulandı", OK), "guessed": ("≈ tahmin (kontrol et)", WARN),
                 "unknown": ("✗ mail yok", DANGER)}.get(conf, ("?", MUTED))

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=12, pady=(10, 2))
        chk = ctk.CTkCheckBox(head, text=target, font=font(13, True))
        if conf == "verified":
            chk.select()
        chk.pack(side="left")
        ctk.CTkLabel(head, text=badge[0], text_color=badge[1], font=font(11, True)).pack(side="right")

        e_mail = ctk.CTkEntry(card, height=32)
        e_mail.pack(fill="x", padx=12, pady=3)
        e_mail.insert(0, chosen.get("email", ""))
        e_subj = ctk.CTkEntry(card, height=32)
        e_subj.pack(fill="x", padx=12, pady=3)
        e_subj.insert(0, res.get("subject", ""))
        t_body = ctk.CTkTextbox(card, height=130, font=font(12))
        t_body.pack(fill="x", padx=12, pady=3)
        t_body.insert("1.0", res.get("body", ""))
        if res.get("research_notes"):
            ctk.CTkLabel(card, text="🔎 " + res["research_notes"], text_color=MUTED,
                         wraplength=720, justify="left", font=font(11)).pack(anchor="w", padx=12)
        if res.get("sources"):
            src = " · ".join(s["url"] for s in res["sources"][:3])
            ctk.CTkLabel(card, text="Kaynak: " + src, text_color="#5B7", wraplength=720,
                         justify="left", font=font(11)).pack(anchor="w", padx=12, pady=(0, 10))
        else:
            ctk.CTkLabel(card, text="", height=4).pack()
        self.draft_cards.append({"frame": card, "chk": chk, "mail": e_mail, "subj": e_subj, "body": t_body})

    def _send_selected(self):
        valid = [c for c in self.draft_cards if c["chk"].get() and es.valid_email(c["mail"].get())]
        if not valid:
            messagebox.showwarning("Gönder", "Onaylı + geçerli mailli taslak yok.")
            return
        cfg = self._smtp_cfg()
        if not cfg:
            return
        wait = _seconds_until(self.sch_compose.get())
        when = "hemen" if wait <= 0 else f"saat {self.sch_compose.get().strip()}'de"
        if not messagebox.askyesno("Onay", f"{len(valid)} mail {when} gönderilecek." +
                                   ("\n(Zamanlı: uygulama açık kalmalı.)" if wait > 0 else "") + "\nDevam?"):
            return
        html = bool(self.c_html.get())
        delay = float(self.s.get("send_delay_sec", 2.0))
        self.b_send_sel.configure(state="disabled", text="Sırada…" if wait > 0 else "Gönderiliyor…")

        def run():
            if wait > 0:
                self.after(0, lambda: self.ai_status.configure(
                    text=f"⏰ {self.sch_compose.get().strip()} bekleniyor…", text_color=WARN))
                time.sleep(wait)
            ok = err = 0
            for c in valid:
                s, m = es.send_email(cfg["server"], cfg["port"], cfg["email"], cfg["password"],
                                     cfg["sender"], c["mail"].get(), c["subj"].get(),
                                     c["body"].get("1.0", "end-1c"), html=html)
                ok, err = (ok + 1, err) if s else (ok, err + 1)
                time.sleep(delay)
            self.after(0, lambda: (self.b_send_sel.configure(state="normal", text="🚀  Onaylananları Gönder"),
                                   self.ai_status.configure(text="", text_color=MUTED),
                                   messagebox.showinfo("Bitti", f"Başarılı: {ok}\nHatalı: {err}")))
        threading.Thread(target=run, daemon=True).start()

    # ===================== TOPLU =====================
    def _page_bulk(self, p):
        self._header(p, "📨 Toplu Gönderim", "Aynı maili çok kişiye. Yapay zeka gerekmez.")
        box = ctk.CTkScrollableFrame(p, fg_color="transparent")
        box.pack(fill="both", expand=True)
        ip = self._card(box, "Mail içeriği")
        self.bk_subj = ctk.CTkEntry(ip, placeholder_text="Konu", height=36)
        self.bk_subj.pack(fill="x", pady=(0, 6))
        self.bk_subj.insert(0, self.s.get("bulk_subject", ""))
        ctk.CTkLabel(ip, text="Mesaj  ({ad} ile kişiselleştir)", text_color=MUTED, font=font(12)).pack(anchor="w")
        self.bk_msg = ctk.CTkTextbox(ip, height=140, font=font(13))
        self.bk_msg.pack(fill="x", pady=4)
        self.bk_msg.insert("1.0", self.s.get("bulk_message", ""))
        self.bk_html = ctk.CTkCheckBox(ip, text="HTML olarak gönder")
        self.bk_html.pack(anchor="w", pady=6)

        rp = self._card(box, "Alıcılar  (her satır:  mail   ya da   mail, Ad)")
        self.bk_to = ctk.CTkTextbox(rp, height=130, font=font(13))
        self.bk_to.pack(fill="x")
        self.bk_to.insert("1.0", "\n".join(self.s.get("bulk_recipients", [])))
        rr = ctk.CTkFrame(rp, fg_color="transparent")
        rr.pack(fill="x", pady=8)
        ctk.CTkButton(rr, text="📥 Dosyadan Yükle", width=140, command=self._import_bulk).pack(side="left", padx=4)
        self.bk_att = ctk.CTkLabel(rr, text="Ek: yok", text_color=MUTED, font=font(12))
        self.bk_att.pack(side="left", padx=12)
        ctk.CTkButton(rr, text="Ek Seç", width=80, command=self._pick_att).pack(side="left", padx=4)
        ctk.CTkButton(rr, text="Kaldır", width=80, fg_color=DANGER, hover_color="#B91C1C",
                      command=self._clear_att).pack(side="left", padx=4)
        if self._att:
            self.bk_att.configure(text="Ek: " + os.path.basename(self._att))

        sch = ctk.CTkFrame(p, fg_color="transparent")
        sch.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(sch, text="⏰ Gönderim saati (HH:MM, boş=hemen):", font=font(12),
                     text_color=MUTED).pack(side="left", padx=(2, 6))
        self.sch_bulk = ctk.CTkEntry(sch, width=90, placeholder_text="HH:MM")
        self.sch_bulk.pack(side="left")
        ctk.CTkLabel(sch, text="zamanlıysa uygulama açık kalmalı", font=font(11),
                     text_color=MUTED).pack(side="left", padx=8)
        ctk.CTkButton(p, text="🚀  Toplu Gönder", height=46, corner_radius=12, fg_color=OK,
                      hover_color="#16A34A", font=font(15, True), command=self._send_bulk).pack(fill="x", pady=(8, 0))

    def _pick_att(self):
        p = filedialog.askopenfilename()
        if p:
            self._att = p
            self.s.set("attachment_path", p)
            self.s.save()
            self.bk_att.configure(text="Ek: " + os.path.basename(p))

    def _clear_att(self):
        self._att = ""
        self.s.set("attachment_path", "")
        self.s.save()
        self.bk_att.configure(text="Ek: yok")

    def _import_bulk(self):
        p = filedialog.askopenfilename(filetypes=[("Metin/CSV", "*.txt *.csv"), ("Tümü", "*.*")])
        if not p:
            return
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                lines = [l.strip() for l in f if "@" in l]
            self.bk_to.delete("1.0", "end")
            self.bk_to.insert("1.0", "\n".join(lines))
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _send_bulk(self):
        cfg = self._smtp_cfg()
        if not cfg:
            return
        rows = [r.strip() for r in self.bk_to.get("1.0", "end-1c").splitlines() if "@" in r]
        if not rows:
            messagebox.showwarning("Alıcı yok", "Alıcı listesi boş.")
            return
        subj, body = self.bk_subj.get(), self.bk_msg.get("1.0", "end-1c")
        html = bool(self.bk_html.get())
        self.s.set("bulk_subject", subj); self.s.set("bulk_message", body)
        self.s.set("bulk_recipients", rows); self.s.save()
        if not messagebox.askyesno("Onay", f"{len(rows)} kişiye gönderilecek. Devam?"):
            return
        delay = float(self.s.get("send_delay_sec", 2.0))
        wait = _seconds_until(self.sch_bulk.get())

        def run():
            if wait > 0:
                time.sleep(wait)
            ok = err = 0
            for r in rows:
                parts = [x.strip() for x in r.split(",")]
                mail = parts[0]; ad = parts[1] if len(parts) > 1 else ""
                s, m = es.send_email(cfg["server"], cfg["port"], cfg["email"], cfg["password"],
                                     cfg["sender"], mail, subj, body.replace("{ad}", ad),
                                     html=html, attachment_path=self._att or None)
                ok, err = (ok + 1, err) if s else (ok, err + 1)
                time.sleep(delay)
            self.after(0, lambda: messagebox.showinfo("Bitti", f"Başarılı: {ok}\nHatalı: {err}"))
        threading.Thread(target=run, daemon=True).start()

    # ===================== PROFİL =====================
    def _page_profile(self, p):
        self._header(p, "👤 Profilim", "AI mailleri SENİN ağzından yazsın diye. CV yükle ya da yaz.")
        box = ctk.CTkScrollableFrame(p, fg_color="transparent")
        box.pack(fill="both", expand=True)
        ip = self._card(box, "Hakkımda / CV")
        rr = ctk.CTkFrame(ip, fg_color="transparent")
        rr.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(rr, text="📄 CV Yükle (PDF/TXT)", command=self._load_cv).pack(side="left", padx=4)
        ctk.CTkButton(rr, text="Temizle", fg_color=DANGER, hover_color="#B91C1C", width=90,
                      command=lambda: self.pf_text.delete("1.0", "end")).pack(side="left", padx=4)
        self.pf_text = ctk.CTkTextbox(ip, height=230, font=font(13))
        self.pf_text.pack(fill="x")
        self.pf_text.insert("1.0", self.s.get("profile_text", ""))

        sp = self._card(box, "İmza")
        self.pf_sig = ctk.CTkTextbox(sp, height=80, font=font(13))
        self.pf_sig.pack(fill="x")
        self.pf_sig.insert("1.0", self.s.get("signature", ""))

        ctk.CTkButton(p, text="💾  Profili Kaydet", height=44, corner_radius=12, fg_color=ACCENT,
                      hover_color=ACCENT_H, font=font(14, True), command=self._save_profile).pack(fill="x", pady=(8, 0))

    def _load_cv(self):
        path = filedialog.askopenfilename(filetypes=[("CV", "*.pdf *.txt *.md"), ("Tümü", "*.*")])
        if not path:
            return
        text = profile_mod.extract_text(path)
        if text == "__NO_PYPDF__":
            messagebox.showwarning("PDF", "PDF için 'pypdf' gerekli. TXT yükle ya da metni yapıştır.")
            return
        if not text.strip():
            messagebox.showwarning("CV", "Metin çıkarılamadı. TXT dene veya elle yapıştır.")
            return
        self.pf_text.delete("1.0", "end")
        self.pf_text.insert("1.0", text)

    def _save_profile(self):
        self.s.set("profile_text", self.pf_text.get("1.0", "end-1c"))
        self.s.set("signature", self.pf_sig.get("1.0", "end-1c"))
        self.s.save()
        messagebox.showinfo("Tamam", "Profil kaydedildi.")

    # ===================== AYARLAR =====================
    def _page_settings(self, p):
        self._header(p, "⚙️ Ayarlar", "Bir kere doldur, keyring'de güvenle saklanır.")
        box = ctk.CTkScrollableFrame(p, fg_color="transparent")
        box.pack(fill="both", expand=True)

        # --- Mail hesabı ---
        m = self._card(box, "📧 Mail Hesabı")
        ctk.CTkLabel(m, text="Servis", font=font(12), text_color=MUTED).pack(anchor="w", pady=(4, 2))
        cur_srv = "Gmail"
        for n, (srv, _) in SMTP_PRESETS.items():
            if srv == self.s.get("smtp_server"):
                cur_srv = n
        self.set_service = ctk.CTkOptionMenu(m, values=list(SMTP_PRESETS.keys()),
                                             command=self._on_service)
        self.set_service.set(cur_srv)
        self.set_service.pack(fill="x")
        self.set_email = self._field(m, "E-posta", "email", placeholder="seninmailin@gmail.com")
        self.set_pass = self._field(m, "Şifre (Gmail: Uygulama Şifresi)", "smtp_password", show="●")
        self.adv = ctk.CTkFrame(m, fg_color="transparent")
        self.set_server = self._field(self.adv, "SMTP Sunucu", "smtp_server")
        self.set_port = self._field(self.adv, "Port", "smtp_port")
        if cur_srv == "Özel":
            self.adv.pack(fill="x")
        rr = ctk.CTkFrame(m, fg_color="transparent")
        rr.pack(fill="x", pady=8)
        ctk.CTkButton(rr, text="🔌 Bağlantıyı Test Et", command=self._test_smtp).pack(side="left")
        self.smtp_msg = ctk.CTkLabel(rr, text="", font=font(12), text_color=MUTED)
        self.smtp_msg.pack(side="left", padx=10)

        # --- Yapay zeka ---
        a = self._card(box, "🤖 Yapay Zeka")
        prov = self.s.get("llm_provider", "gemini")
        ctk.CTkLabel(a, text="Sağlayıcı", font=font(12), text_color=MUTED).pack(anchor="w", pady=(4, 2))
        self.set_provider = ctk.CTkOptionMenu(a, values=list(PROVIDER_LABELS.keys()),
                                              command=self._on_provider)
        self.set_provider.set(LABEL_BY_PROVIDER.get(prov, "Google Gemini"))
        self.set_provider.pack(fill="x")
        ctk.CTkLabel(a, text="Model (listeden seç ya da elle yaz)", font=font(12),
                     text_color=MUTED).pack(anchor="w", pady=(8, 2))
        self.set_model = ctk.CTkComboBox(a, values=MODEL_PRESETS.get(prov, []))
        self.set_model.set(self.s.get("llm_model") or (MODEL_PRESETS.get(prov, [""])[0]))
        self.set_model.pack(fill="x")
        self.btn_fetch = ctk.CTkButton(a, text="🔄 OpenRouter'dan tüm modelleri çek",
                                       height=30, fg_color="transparent", border_width=1,
                                       border_color=MUTED, text_color=MUTED, hover_color="#222B36",
                                       font=font(12), command=self._fetch_models)
        self.btn_fetch.pack(anchor="w", pady=(6, 0))
        if prov != "openrouter":
            self.btn_fetch.pack_forget()
        self.set_apikey = self._field(a, "API Anahtarı", "llm_api_key", show="●",
                                      placeholder="kendi anahtarın")
        self.base_wrap = ctk.CTkFrame(a, fg_color="transparent")
        self.set_baseurl = self._field(self.base_wrap, "Base URL (sadece OpenAI/Özel)", "llm_base_url",
                                       placeholder="https://...")
        if prov == "openai":
            self.base_wrap.pack(fill="x")
        self.set_online = ctk.CTkCheckBox(a, text="İnternet araması (Gemini grounding / OpenRouter :online)")
        if self.s.get("use_grounding", True):
            self.set_online.select()
        self.set_online.pack(anchor="w", pady=10)
        ctk.CTkLabel(a, text="Anahtar: Gemini → aistudio.google.com/apikey · OpenRouter → openrouter.ai/keys",
                     font=font(11), text_color=MUTED, wraplength=620, justify="left").pack(anchor="w")
        rr2 = ctk.CTkFrame(a, fg_color="transparent")
        rr2.pack(fill="x", pady=8)
        ctk.CTkButton(rr2, text="🤖 LLM Test Et", command=self._test_llm).pack(side="left")
        self.llm_msg = ctk.CTkLabel(rr2, text="", font=font(12), text_color=MUTED)
        self.llm_msg.pack(side="left", padx=10)

        # --- Mail bulucu ---
        h = self._card(box, "🔎 E-posta Bulucu (opsiyonel)")
        self.set_hunter = self._field(h, "Hunter.io API anahtarı — boşsa kalıp tahmini (doğrulanmaz)",
                                      "hunter_api_key", show="●")

        u = self._card(box, "📊 Kullanım")
        self.ai_count_lbl = ctk.CTkLabel(u, text=f"Toplam AI isteği: {self.s.get('ai_requests', 0)}",
                                         font=font(13))
        self.ai_count_lbl.pack(anchor="w")
        ctk.CTkLabel(u, text="Her 'Araştır & Taslak Üret' = hedef kişi sayısı kadar AI isteği.",
                     font=font(11), text_color=MUTED).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(p, text="💾  Tüm Ayarları Kaydet", height=46, corner_radius=12, fg_color=ACCENT,
                      hover_color=ACCENT_H, font=font(15, True), command=self._save_settings).pack(fill="x", pady=(8, 0))

    def _on_service(self, name):
        srv, port = SMTP_PRESETS[name]
        if name == "Özel":
            self.adv.pack(fill="x")
        else:
            self.adv.pack_forget()
            self.set_server.delete(0, "end"); self.set_server.insert(0, srv)
            self.set_port.delete(0, "end"); self.set_port.insert(0, str(port))

    def _on_provider(self, label):
        prov = PROVIDER_LABELS[label]
        self.set_model.configure(values=MODEL_PRESETS.get(prov, []))
        self.set_model.set(MODEL_PRESETS.get(prov, [""])[0])
        if prov == "openai":
            self.base_wrap.pack(fill="x")
        else:
            self.base_wrap.pack_forget()
        if prov == "openrouter":
            self.btn_fetch.pack(anchor="w", pady=(6, 0))
        else:
            self.btn_fetch.pack_forget()

    def _fetch_models(self):
        self.llm_msg.configure(text="modeller çekiliyor…", text_color=MUTED)

        def run():
            try:
                ids = fetch_openrouter_models(self.set_apikey.get())
            except Exception:
                ids = []
            if ids:
                cur = self.set_model.get()
                self.after(0, lambda: (self.set_model.configure(values=ids),
                                       self.set_model.set(cur if cur in ids else ids[0]),
                                       self.llm_msg.configure(text=f"{len(ids)} model yüklendi ✓",
                                                              text_color=OK)))
            else:
                self.after(0, lambda: self.llm_msg.configure(
                    text="çekilemedi (internet?)", text_color=DANGER))
        threading.Thread(target=run, daemon=True).start()

    def _save_settings(self):
        try:
            self.s.set("smtp_server", self.set_server.get() or "smtp.gmail.com")
            self.s.set("smtp_port", int(self.set_port.get() or 587))
            self.s.set("email", self.set_email.get())
            self.s.set("smtp_password", self.set_pass.get())
            self.s.set("llm_provider", PROVIDER_LABELS[self.set_provider.get()])
            self.s.set("llm_model", self.set_model.get())
            self.s.set("llm_base_url", self.set_baseurl.get())
            self.s.set("llm_api_key", self.set_apikey.get())
            self.s.set("use_grounding", bool(self.set_online.get()))
            self.s.set("hunter_api_key", self.set_hunter.get())
            self.s.save()
            self._refresh_status()
            messagebox.showinfo("Tamam", "Ayarlar kaydedildi.")
        except ValueError:
            messagebox.showerror("Hata", "Port sayı olmalı.")

    def _test_smtp(self):
        self.smtp_msg.configure(text="bağlanıyor…", text_color=MUTED)

        def run():
            ok, msg = es.test_connection(self.set_server.get() or "smtp.gmail.com",
                                         int(self.set_port.get() or 587),
                                         self.set_email.get(), self.set_pass.get())
            self.after(0, lambda: self.smtp_msg.configure(
                text=msg.split("\n")[0], text_color=OK if ok else DANGER))
            if not ok:
                self.after(0, lambda: messagebox.showerror("SMTP", msg))
        threading.Thread(target=run, daemon=True).start()

    def _test_llm(self):
        key = self.set_apikey.get()
        if not key:
            self.llm_msg.configure(text="önce anahtar gir", text_color=WARN)
            return
        client = LLMClient(PROVIDER_LABELS[self.set_provider.get()], key, self.set_model.get(),
                           self.set_baseurl.get(), bool(self.set_online.get()))
        self.llm_msg.configure(text="test ediliyor…", text_color=MUTED)

        def run():
            ok, msg = client.test()
            self.after(0, self._bump_ai, 1)
            self.after(0, lambda: self.llm_msg.configure(
                text="çalışıyor ✓" if ok else "başarısız", text_color=OK if ok else DANGER))
            if not ok:
                self.after(0, lambda: messagebox.showerror("LLM", msg))
        threading.Thread(target=run, daemon=True).start()

    # ===================== ortak =====================
    def _smtp_cfg(self):
        email = self.s.get("email"); pwd = self.s.get("smtp_password")
        if not (email and pwd):
            messagebox.showwarning("Mail ayarı yok", "Önce Ayarlar'da mail hesabını gir.")
            self.show("settings")
            return None
        return {"server": self.s.get("smtp_server", "smtp.gmail.com"),
                "port": int(self.s.get("smtp_port", 587)), "email": email, "password": pwd,
                "sender": self.s.get("sender_name", "") or email.split("@")[0]}


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
