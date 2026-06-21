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
from core.llm import LLMClient, MODEL_PRESETS, fetch_openrouter_models
from core.i18n import (
    t, set_ui_lang, get_ui_lang, get_purposes, get_tone_labels,
    tone_key_from_label, get_length_labels, length_value_from_label,
    get_smtp_presets, get_provider_labels, get_label_by_provider,
    UI_LANG_LABELS, UI_LANG_BY_CODE
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT = "#3B82F6"
ACCENT_H = "#2563EB"
OK = "#22C55E"
WARN = "#F59E0B"
DANGER = "#EF4444"
MUTED = "#94A3B8"
CARD = "#1F2630"


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
        set_ui_lang(self.s.get("ui_lang", "tr"))
        self.draft_cards = []
        self._att = self.s.get("attachment_path", "")
        self._comp_att = self.s.get("comp_attachment_path", "")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_content()
        self.show("compose")

    # ===================== SIDEBAR =====================
    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color="#161B22")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        ctk.CTkLabel(self.sidebar_frame, text="✉  EmailAI", font=font(22, True)).pack(pady=(26, 6))
        ctk.CTkLabel(self.sidebar_frame, text=t("app_subtitle"), text_color=MUTED,
                     font=font(11)).pack(pady=(0, 24))

        self.nav = {}
        for key, label, icon in [("compose", t("nav_compose"), "✨"), ("bulk", t("nav_bulk"), "📨"),
                                 ("profile", t("nav_profile"), "👤"), ("settings", t("nav_settings"), "⚙️")]:
            b = ctk.CTkButton(self.sidebar_frame, text=f"  {icon}   {label}", anchor="w", height=44,
                               corner_radius=10, fg_color="transparent", text_color="#E6EDF3",
                               hover_color="#222B36", font=font(14),
                               command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=14, pady=3)
            self.nav[key] = b

        # Dil Seçimi (sol panel en alt)
        lang_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        lang_frame.pack(side="bottom", fill="x", padx=16, pady=(10, 18))
        ctk.CTkLabel(lang_frame, text=t("lang_label") + ":", font=font(12), text_color=MUTED).pack(side="left", padx=(0, 6))
        
        lang_list = list(UI_LANG_LABELS.keys())
        saved_ui_lang = self.s.get("ui_lang", "tr")
        display_name = UI_LANG_BY_CODE.get(saved_ui_lang, "Türkçe")
        
        self.sidebar_lang_opt = ctk.CTkOptionMenu(
            lang_frame, values=lang_list, width=105, height=28, font=font(12),
            command=self._on_sidebar_lang_change
        )
        self.sidebar_lang_opt.set(display_name)
        self.sidebar_lang_opt.pack(side="left")

        # durum göstergeleri (alt, dilin hemen üstü)
        status = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        status.pack(side="bottom", fill="x", padx=16, pady=(10, 0))
        self.dot_smtp = ctk.CTkLabel(status, text=t("status_mail") + "—", font=font(12), text_color=MUTED)
        self.dot_smtp.pack(anchor="w", pady=2)
        self.dot_ai = ctk.CTkLabel(status, text=t("status_ai") + "—", font=font(12), text_color=MUTED)
        self.dot_ai.pack(anchor="w", pady=2)

    def _on_sidebar_lang_change(self, display_name):
        lang_code = UI_LANG_LABELS[display_name]
        if lang_code != get_ui_lang():
            active_page = "compose"
            for k, b in self.nav.items():
                if b.cget("fg_color") == ACCENT:
                    active_page = k
                    break
            
            self.s.set("ui_lang", lang_code)
            self.s.save()
            set_ui_lang(lang_code)
            
            # Eski arayüzü yok et ve yenisini çiz
            self.sidebar_frame.destroy()
            self.content.destroy()
            self._build_sidebar()
            self._build_content()
            self.show(active_page)

    def _refresh_status(self):
        smtp_ok = bool(self.s.get("email") and self.s.get("smtp_password"))
        ai_ok = bool(self.s.get("llm_api_key"))
        self.dot_smtp.configure(text=t("status_mail") + (t("status_ready") if smtp_ok else t("status_missing")),
                                text_color=OK if smtp_ok else MUTED)
        self.dot_ai.configure(text=t("status_ai") + (t("status_ready") if ai_ok else t("status_missing")),
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
        self._header(p, t("compose_title"), t("compose_sub"))
        box = ctk.CTkScrollableFrame(p, fg_color="transparent")
        box.pack(fill="both", expand=True)

        ip = self._card(box, t("card_purpose"))
        ctk.CTkLabel(ip, text=t("purpose_label"), font=font(12), text_color=MUTED).pack(anchor="w", pady=(0, 2))
        purposes_dict = get_purposes()
        self.o_purpose = ctk.CTkOptionMenu(ip, values=list(purposes_dict.keys()), command=self._on_purpose)
        self.o_purpose.set(list(purposes_dict.keys())[0])
        self.o_purpose.pack(fill="x")
        ctk.CTkLabel(ip, text=t("detail_label"),
                     font=font(12), text_color=MUTED).pack(anchor="w", pady=(8, 2))
        self.t_brief = ctk.CTkTextbox(ip, height=70, font=font(13))
        self.t_brief.pack(fill="x")
        self.t_brief.insert("1.0", self.s.get("compose_brief", ""))
        self.t_brief.bind("<KeyRelease>", self._auto_save_compose)

        tp = self._card(box, t("card_target"))
        self.t_targets = ctk.CTkTextbox(tp, height=90, font=font(13))
        self.t_targets.pack(fill="x")
        self.t_targets.insert("1.0", self.s.get("compose_targets", t("target_ph")))
        self.t_targets.bind("<KeyRelease>", self._auto_save_compose)

        op = self._card(box, t("card_tone"))
        row = ctk.CTkFrame(op, fg_color="transparent")
        row.pack(fill="x")
        
        tone_labels = get_tone_labels()
        self.o_tone = ctk.CTkOptionMenu(row, values=list(tone_labels.values()), width=110, command=self._on_compose_change)
        def_tone_key = self.s.get("default_tone", "samimi")
        self.o_tone.set(tone_labels.get(def_tone_key, tone_labels.get("samimi", "Samimi")))
        self.o_tone.pack(side="left", padx=(0, 8))
        
        self.o_lang = ctk.CTkOptionMenu(row, values=["tr", "en"], width=70, command=self._on_compose_change)
        self.o_lang.set(self.s.get("default_lang", "tr"))
        self.o_lang.pack(side="left", padx=8)
        
        # Uzunluk seçici
        ctk.CTkLabel(row, text=t("length_label"), font=font(12), text_color=MUTED).pack(side="left", padx=(10, 4))
        length_labels = get_length_labels()
        self.o_length = ctk.CTkOptionMenu(row, values=length_labels, width=130, command=self._on_compose_change)
        
        saved_len = self.s.get("compose_length", "")
        if saved_len in length_labels:
            self.o_length.set(saved_len)
        else:
            med_label = ""
            for lbl in length_labels:
                if length_value_from_label(lbl) == "medium":
                    med_label = lbl
                    break
            if not med_label:
                med_label = length_labels[1] if len(length_labels) > 1 else length_labels[0]
            self.o_length.set(med_label)
        self.o_length.pack(side="left", padx=8)
        
        self.c_html = ctk.CTkCheckBox(row, text=t("html_label"), command=self._on_compose_change)
        if self.s.get("compose_html", False):
            self.c_html.select()
        self.c_html.pack(side="left", padx=10)
        
        ctk.CTkLabel(row, text=t("time_label"), font=font(12), text_color=MUTED).pack(side="left", padx=(14, 4))
        self.sch_compose = ctk.CTkEntry(row, width=80, placeholder_text="HH:MM")
        self.sch_compose.insert(0, self.s.get("compose_schedule", ""))
        self.sch_compose.pack(side="left")
        self.sch_compose.bind("<KeyRelease>", self._auto_save_compose)
        ctk.CTkLabel(row, text=t("time_empty"), font=font(11), text_color=MUTED).pack(side="left", padx=6)

        # Attachment row in Compose page
        att_row = ctk.CTkFrame(op, fg_color="transparent")
        att_row.pack(fill="x", pady=(10, 0))
        self.comp_att_lbl = ctk.CTkLabel(att_row, text=t("att_none"), text_color=MUTED, font=font(12))
        self.comp_att_lbl.pack(side="left", padx=(2, 12))
        ctk.CTkButton(att_row, text=t("btn_pick_att"), width=80, command=self._pick_comp_att).pack(side="left", padx=4)
        ctk.CTkButton(att_row, text=t("btn_remove"), width=80, fg_color=DANGER, hover_color="#B91C1C",
                      command=self._clear_comp_att).pack(side="left", padx=4)
        if self._comp_att:
            self.comp_att_lbl.configure(text=t("att_prefix") + os.path.basename(self._comp_att))

        self.b_gen = ctk.CTkButton(box, text=t("btn_generate"), height=46, corner_radius=12,
                                   fg_color=ACCENT, hover_color=ACCENT_H, font=font(15, True),
                                   command=self._generate)
        self.b_gen.pack(fill="x", pady=10)
        self.ai_status = ctk.CTkLabel(box, text="", text_color=MUTED, font=font(12))
        self.ai_status.pack(anchor="w")

        self.results = ctk.CTkScrollableFrame(box, label_text=t("drafts_label"), height=260)
        self.results.pack(fill="both", expand=True, pady=6)

        self.b_send_sel = ctk.CTkButton(p, text=t("btn_send_sel"), height=46, corner_radius=12,
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
        tmpl = get_purposes().get(label, "")
        self.t_brief.delete("1.0", "end")
        if tmpl:
            self.t_brief.insert("1.0", tmpl)
        self._auto_save_compose()

    def _on_compose_change(self, val=None):
        self._auto_save_compose()

    def _auto_save_compose(self, event=None):
        self.s.set("compose_brief", self.t_brief.get("1.0", "end-1c"))
        self.s.set("compose_targets", self.t_targets.get("1.0", "end-1c"))
        self.s.set("default_tone", tone_key_from_label(self.o_tone.get()))
        self.s.set("default_lang", self.o_lang.get())
        self.s.set("compose_length", self.o_length.get())
        self.s.set("compose_html", bool(self.c_html.get()))
        self.s.set("compose_schedule", self.sch_compose.get())
        self.s.save()

    def _bump_ai(self, n=1):
        self.s.set("ai_requests", int(self.s.get("ai_requests", 0)) + n)
        self.s.save()
        if hasattr(self, "ai_count_lbl"):
            try:
                self.ai_count_lbl.configure(text=t("ai_count", count=self.s.get('ai_requests', 0)))
            except Exception:
                pass

    def _generate(self):
        client = self._llm()
        if not client:
            messagebox.showwarning(t("no_ai_title"), t("no_ai_msg"))
            self.show("settings")
            return
        targets = [t_line.strip() for t_line in self.t_targets.get("1.0", "end-1c").splitlines() if t_line.strip()]
        if not targets:
            messagebox.showwarning(t("no_target_title"), t("no_target_msg"))
            return
        brief = self.t_brief.get("1.0", "end-1c")
        prof = self.s.get("profile_text", "")
        sig = self.s.get("signature", "")
        tone_val = tone_key_from_label(self.o_tone.get())
        lang = self.o_lang.get()
        length_val = length_value_from_label(self.o_length.get())
        hunter = self.s.get("hunter_api_key")

        for c in self.draft_cards:
            c["frame"].destroy()
        self.draft_cards.clear()
        self.b_gen.configure(state="disabled", text=t("generating"))
        self.b_send_sel.configure(state="disabled")

        def run():
            for i, tgt in enumerate(targets):
                self.after(0, lambda i=i, n=len(targets): self.ai_status.configure(
                    text=t("researching", i=i+1, n=n)))
                try:
                    res = client.research_and_draft(tgt, brief, prof, tone_val, lang, sig, length=length_val)
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
            self.after(0, lambda: (self.ai_status.configure(text=t("gen_done")),
                                   self.b_gen.configure(state="normal", text=t("btn_generate")),
                                   self.b_send_sel.configure(state="normal")))
        threading.Thread(target=run, daemon=True).start()

    def _add_card(self, target, res, chosen):
        card = ctk.CTkFrame(self.results, fg_color=CARD, corner_radius=10)
        card.pack(fill="x", pady=6, padx=4)
        conf = chosen.get("confidence", "unknown")
        badge = {"verified": (t("badge_verified"), OK), "guessed": (t("badge_guessed"), WARN),
                 "unknown": (t("badge_unknown"), DANGER)}.get(conf, ("?", MUTED))

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
            ctk.CTkLabel(card, text=t("source_prefix") + src, text_color="#5B7", wraplength=720,
                         justify="left", font=font(11)).pack(anchor="w", padx=12, pady=(0, 10))
        else:
            ctk.CTkLabel(card, text="", height=4).pack()
        self.draft_cards.append({"frame": card, "chk": chk, "mail": e_mail, "subj": e_subj, "body": t_body})

    def _send_selected(self):
        valid = [c for c in self.draft_cards if c["chk"].get() and es.valid_email(c["mail"].get())]
        if not valid:
            messagebox.showwarning(t("send_title"), t("no_valid_draft"))
            return
        cfg = self._smtp_cfg()
        if not cfg:
            return
        wait = _seconds_until(self.sch_compose.get())
        when = t("when_now") if wait <= 0 else f"{t('time_label')} {self.sch_compose.get().strip()}"
        
        msg_text = f"{len(valid)} mail {when} gönderilecek." if get_ui_lang() == "tr" else f"{len(valid)} email(s) will be sent {when}."
        if wait > 0:
            msg_text += t("scheduled_note")
        msg_text += t("continue_q")
        
        if not messagebox.askyesno(t("confirm_title"), msg_text):
            return
        html = bool(self.c_html.get())
        delay = float(self.s.get("send_delay_sec", 2.0))
        self.b_send_sel.configure(state="disabled", text=t("queued") if wait > 0 else t("sending"))

        def run():
            if wait > 0:
                self.after(0, lambda: self.ai_status.configure(
                    text=f"⏰ {self.sch_compose.get().strip()} bekleniyor…", text_color=WARN))
                time.sleep(wait)
            ok = err = 0
            for c in valid:
                s, m = es.send_email(cfg["server"], cfg["port"], cfg["email"], cfg["password"],
                                     cfg["sender"], c["mail"].get(), c["subj"].get(),
                                     c["body"].get("1.0", "end-1c"), html=html,
                                     attachment_path=self._comp_att or None)
                ok, err = (ok + 1, err) if s else (ok, err + 1)
                time.sleep(delay)
            success_prompt = f"Başarılı: {ok}\nHatalı: {err}" if get_ui_lang() == "tr" else f"Success: {ok}\nFailed: {err}"
            self.after(0, lambda: (self.b_send_sel.configure(state="normal", text=t("btn_send_sel")),
                                   self.ai_status.configure(text="", text_color=MUTED),
                                   messagebox.showinfo(t("done_title"), success_prompt)))
        threading.Thread(target=run, daemon=True).start()

    # ===================== TOPLU =====================
    def _page_bulk(self, p):
        self._header(p, t("bulk_title"), t("bulk_sub"))
        box = ctk.CTkScrollableFrame(p, fg_color="transparent")
        box.pack(fill="both", expand=True)
        ip = self._card(box, t("card_content"))
        self.bk_subj = ctk.CTkEntry(ip, placeholder_text=t("subject_ph"), height=36)
        self.bk_subj.pack(fill="x", pady=(0, 6))
        self.bk_subj.insert(0, self.s.get("bulk_subject", ""))
        self.bk_subj.bind("<KeyRelease>", self._auto_save_bulk)
        ctk.CTkLabel(ip, text=t("bulk_msg_label"), text_color=MUTED, font=font(12)).pack(anchor="w")
        self.bk_msg = ctk.CTkTextbox(ip, height=140, font=font(13))
        self.bk_msg.pack(fill="x", pady=4)
        self.bk_msg.insert("1.0", self.s.get("bulk_message", ""))
        self.bk_msg.bind("<KeyRelease>", self._auto_save_bulk)
        self.bk_html = ctk.CTkCheckBox(ip, text=t("html_send"), command=self._auto_save_bulk)
        if self.s.get("bulk_html", False):
            self.bk_html.select()
        self.bk_html.pack(anchor="w", pady=6)

        rp = self._card(box, t("card_recipients"))
        self.bk_to = ctk.CTkTextbox(rp, height=130, font=font(13))
        self.bk_to.pack(fill="x")
        self.bk_to.insert("1.0", "\n".join(self.s.get("bulk_recipients", [])))
        self.bk_to.bind("<KeyRelease>", self._auto_save_bulk)
        rr = ctk.CTkFrame(rp, fg_color="transparent")
        rr.pack(fill="x", pady=8)
        ctk.CTkButton(rr, text=t("btn_import"), width=140, command=self._import_bulk).pack(side="left", padx=4)
        self.bk_att = ctk.CTkLabel(rr, text=t("att_none"), text_color=MUTED, font=font(12))
        self.bk_att.pack(side="left", padx=12)
        ctk.CTkButton(rr, text=t("btn_pick_att"), width=80, command=self._pick_att).pack(side="left", padx=4)
        ctk.CTkButton(rr, text=t("btn_remove"), width=80, fg_color=DANGER, hover_color="#B91C1C",
                      command=self._clear_att).pack(side="left", padx=4)
        if self._att:
            self.bk_att.configure(text=t("att_prefix") + os.path.basename(self._att))

        sch = ctk.CTkFrame(p, fg_color="transparent")
        sch.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(sch, text=t("schedule_label"), font=font(12),
                     text_color=MUTED).pack(side="left", padx=(2, 6))
        self.sch_bulk = ctk.CTkEntry(sch, width=90, placeholder_text="HH:MM")
        self.sch_bulk.insert(0, self.s.get("bulk_schedule", ""))
        self.sch_bulk.pack(side="left")
        self.sch_bulk.bind("<KeyRelease>", self._auto_save_bulk)
        ctk.CTkLabel(sch, text=t("schedule_note"), font=font(11),
                     text_color=MUTED).pack(side="left", padx=8)
        ctk.CTkButton(p, text=t("btn_bulk_send"), height=46, corner_radius=12, fg_color=OK,
                      hover_color="#16A34A", font=font(15, True), command=self._send_bulk).pack(fill="x", pady=(8, 0))

    def _pick_att(self):
        p = filedialog.askopenfilename(
            filetypes=[
                ("PDF", "*.pdf"),
                ("Images (Görseller)", "*.png *.jpg *.jpeg"),
                ("Word Documents (Word)", "*.docx *.doc"),
                ("Documents (Belgeler)", "*.docx *.doc *.txt *.csv *.xlsx *.pdf"),
                (t("filetype_all"), "*.*")
            ]
        )
        if p:
            self._att = p
            self.s.set("attachment_path", p)
            self.s.save()
            self.bk_att.configure(text=t("att_prefix") + os.path.basename(p))

    def _clear_att(self):
        self._att = ""
        self.s.set("attachment_path", "")
        self.s.save()
        self.bk_att.configure(text=t("att_none"))

    def _pick_comp_att(self):
        p = filedialog.askopenfilename(
            filetypes=[
                ("PDF", "*.pdf"),
                ("Images (Görseller)", "*.png *.jpg *.jpeg"),
                ("Word Documents (Word)", "*.docx *.doc"),
                ("Documents (Belgeler)", "*.docx *.doc *.txt *.csv *.xlsx *.pdf"),
                (t("filetype_all"), "*.*")
            ]
        )
        if p:
            self._comp_att = p
            self.s.set("comp_attachment_path", p)
            self.s.save()
            self.comp_att_lbl.configure(text=t("att_prefix") + os.path.basename(p))

    def _clear_comp_att(self):
        self._comp_att = ""
        self.s.set("comp_attachment_path", "")
        self.s.save()
        self.comp_att_lbl.configure(text=t("att_none"))

    def _import_bulk(self):
        p = filedialog.askopenfilename(filetypes=[(t("filetype_text"), "*.txt *.csv"), (t("filetype_all"), "*.*")])
        if not p:
            return
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                lines = [l.strip() for l in f if "@" in l]
            self.bk_to.delete("1.0", "end")
            self.bk_to.insert("1.0", "\n".join(lines))
            self._auto_save_bulk()
        except Exception as e:
            messagebox.showerror(t("error_title"), str(e))

    def _auto_save_bulk(self, event=None):
        self.s.set("bulk_subject", self.bk_subj.get())
        self.s.set("bulk_message", self.bk_msg.get("1.0", "end-1c"))
        self.s.set("bulk_html", bool(self.bk_html.get()))
        lines = [l.strip() for l in self.bk_to.get("1.0", "end-1c").splitlines() if l.strip()]
        self.s.set("bulk_recipients", lines)
        self.s.set("bulk_schedule", self.sch_bulk.get())
        self.s.save()

    def _send_bulk(self):
        cfg = self._smtp_cfg()
        if not cfg:
            return
        rows = [r.strip() for r in self.bk_to.get("1.0", "end-1c").splitlines() if "@" in r]
        if not rows:
            messagebox.showwarning(t("no_recip_title"), t("no_recip_msg"))
            return
        subj, body = self.bk_subj.get(), self.bk_msg.get("1.0", "end-1c")
        html = bool(self.bk_html.get())
        self.s.set("bulk_subject", subj); self.s.set("bulk_message", body)
        self.s.set("bulk_recipients", rows); self.s.save()
        
        confirm_prompt = f"{len(rows)} kişiye gönderilecek. Devam?" if get_ui_lang() == "tr" else f"Will be sent to {len(rows)} recipients. Continue?"
        if not messagebox.askyesno(t("confirm_title"), confirm_prompt):
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
            success_prompt = f"Başarılı: {ok}\nHatalı: {err}" if get_ui_lang() == "tr" else f"Success: {ok}\nFailed: {err}"
            self.after(0, lambda: messagebox.showinfo(t("done_title"), success_prompt))
        threading.Thread(target=run, daemon=True).start()

    # ===================== PROFİL =====================
    def _page_profile(self, p):
        self._header(p, t("profile_title"), t("profile_sub"))
        box = ctk.CTkScrollableFrame(p, fg_color="transparent")
        box.pack(fill="both", expand=True)
        ip = self._card(box, t("card_about"))
        rr = ctk.CTkFrame(ip, fg_color="transparent")
        rr.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(rr, text=t("btn_upload_cv"), command=self._load_cv).pack(side="left", padx=4)
        ctk.CTkButton(rr, text=t("btn_clear"), fg_color=DANGER, hover_color="#B91C1C", width=90,
                      command=lambda: (self.pf_text.delete("1.0", "end"), self._auto_save_profile())).pack(side="left", padx=4)
        self.pf_text = ctk.CTkTextbox(ip, height=230, font=font(13))
        self.pf_text.pack(fill="x")
        self.pf_text.insert("1.0", self.s.get("profile_text", ""))
        self.pf_text.bind("<KeyRelease>", self._auto_save_profile)

        sp = self._card(box, t("card_signature"))
        self.pf_sig = ctk.CTkTextbox(sp, height=80, font=font(13))
        self.pf_sig.pack(fill="x")
        self.pf_sig.insert("1.0", self.s.get("signature", ""))
        self.pf_sig.bind("<KeyRelease>", self._auto_save_profile)

        ctk.CTkButton(p, text=t("btn_save_profile"), height=44, corner_radius=12, fg_color=ACCENT,
                      hover_color=ACCENT_H, font=font(14, True), command=self._save_profile).pack(fill="x", pady=(8, 0))

    def _load_cv(self):
        path = filedialog.askopenfilename(
            filetypes=[
                (t("cv_title"), "*.pdf *.txt *.md *.docx"),
                ("Word Documents (Word)", "*.docx *.doc"),
                (t("filetype_all"), "*.*")
            ]
        )
        if not path:
            return
        text = profile_mod.extract_text(path)
        if text == "__NO_PDF_LIB__":
            messagebox.showwarning(t("pdf_title"), t("pdf_msg"))
            return
        if not text.strip():
            messagebox.showwarning(t("cv_title"), t("cv_msg"))
            return
        self.pf_text.delete("1.0", "end")
        self.pf_text.insert("1.0", text)
        self._auto_save_profile()

    def _save_profile(self):
        self._auto_save_profile()
        messagebox.showinfo(t("ok_title"), t("profile_saved"))

    def _auto_save_profile(self, event=None):
        self.s.set("profile_text", self.pf_text.get("1.0", "end-1c"))
        self.s.set("signature", self.pf_sig.get("1.0", "end-1c"))
        self.s.save()

    # ===================== AYARLAR =====================
    def _page_settings(self, p):
        self._header(p, t("settings_title"), t("settings_sub"))
        box = ctk.CTkScrollableFrame(p, fg_color="transparent")
        box.pack(fill="both", expand=True)

        # --- Mail hesabı ---
        m = self._card(box, t("card_mail"))
        ctk.CTkLabel(m, text=t("service_label"), font=font(12), text_color=MUTED).pack(anchor="w", pady=(4, 2))
        cur_srv = "Gmail"
        smtp_presets = get_smtp_presets()
        for n, (srv, _) in smtp_presets.items():
            if srv == self.s.get("smtp_server"):
                cur_srv = n
        self.set_service = ctk.CTkOptionMenu(m, values=list(smtp_presets.keys()),
                                             command=self._on_service)
        self.set_service.set(cur_srv)
        self.set_service.pack(fill="x")
        self.set_email = self._field(m, t("email_label"), "email", placeholder=t("email_ph"))
        self.set_email.bind("<KeyRelease>", self._auto_save_settings)
        self.set_pass = self._field(m, t("pass_label"), "smtp_password", show="●")
        self.set_pass.bind("<KeyRelease>", self._auto_save_settings)
        self.adv = ctk.CTkFrame(m, fg_color="transparent")
        self.set_server = self._field(self.adv, t("smtp_server_lbl"), "smtp_server")
        self.set_server.bind("<KeyRelease>", self._auto_save_settings)
        self.set_port = self._field(self.adv, t("smtp_port_lbl"), "smtp_port")
        self.set_port.bind("<KeyRelease>", self._auto_save_settings)
        if cur_srv == t("smtp_custom"):
            self.adv.pack(fill="x")
        rr = ctk.CTkFrame(m, fg_color="transparent")
        rr.pack(fill="x", pady=8)
        ctk.CTkButton(rr, text=t("btn_test_smtp"), command=self._test_smtp).pack(side="left")
        self.smtp_msg = ctk.CTkLabel(rr, text="", font=font(12), text_color=MUTED)
        self.smtp_msg.pack(side="left", padx=10)

        # --- Yapay zeka ---
        a = self._card(box, t("card_ai"))
        prov = self.s.get("llm_provider", "gemini")
        ctk.CTkLabel(a, text=t("provider_label"), font=font(12), text_color=MUTED).pack(anchor="w", pady=(4, 2))
        
        provider_labels = get_provider_labels()
        label_by_provider = get_label_by_provider()
        
        self.set_provider = ctk.CTkOptionMenu(a, values=list(provider_labels.keys()),
                                               command=self._on_provider)
        self.set_provider.set(label_by_provider.get(prov, "Google Gemini"))
        self.set_provider.pack(fill="x")
        ctk.CTkLabel(a, text=t("model_label"), font=font(12),
                     text_color=MUTED).pack(anchor="w", pady=(8, 2))
        self.set_model = ctk.CTkComboBox(a, values=MODEL_PRESETS.get(prov, []))
        self.set_model.set(self.s.get("llm_model") or (MODEL_PRESETS.get(prov, [""])[0]))
        self.set_model.pack(fill="x")
        self.set_model.bind("<KeyRelease>", self._auto_save_settings)
        self.set_model.configure(command=lambda val: self._auto_save_settings())
        
        self.btn_fetch = ctk.CTkButton(a, text=t("btn_fetch_models"),
                                       height=30, fg_color="transparent", border_width=1,
                                       border_color=MUTED, text_color=MUTED, hover_color="#222B36",
                                       font=font(12), command=self._fetch_models)
        self.btn_fetch.pack(anchor="w", pady=(6, 0))
        if prov != "openrouter":
            self.btn_fetch.pack_forget()
        self.set_apikey = self._field(a, t("apikey_label"), "llm_api_key", show="●",
                                      placeholder=t("apikey_ph"))
        self.set_apikey.bind("<KeyRelease>", self._auto_save_settings)
        self.base_wrap = ctk.CTkFrame(a, fg_color="transparent")
        self.set_baseurl = self._field(self.base_wrap, t("baseurl_label"), "llm_base_url",
                                       placeholder="https://...")
        self.set_baseurl.bind("<KeyRelease>", self._auto_save_settings)
        if prov == "openai":
            self.base_wrap.pack(fill="x")
        self.set_online = ctk.CTkCheckBox(a, text=t("online_label"), command=self._auto_save_settings)
        if self.s.get("use_grounding", True):
            self.set_online.select()
        self.set_online.pack(anchor="w", pady=10)
        ctk.CTkLabel(a, text=t("key_hint"),
                     font=font(11), text_color=MUTED, wraplength=620, justify="left").pack(anchor="w")
        rr2 = ctk.CTkFrame(a, fg_color="transparent")
        rr2.pack(fill="x", pady=8)
        ctk.CTkButton(rr2, text=t("btn_test_llm"), command=self._test_llm).pack(side="left")
        self.llm_msg = ctk.CTkLabel(rr2, text="", font=font(12), text_color=MUTED)
        self.llm_msg.pack(side="left", padx=10)

        # --- Mail bulucu ---
        h = self._card(box, t("card_finder"))
        self.set_hunter = self._field(h, t("hunter_label"),
                                      "hunter_api_key", show="●")
        self.set_hunter.bind("<KeyRelease>", self._auto_save_settings)

        u = self._card(box, t("card_usage"))
        self.ai_count_lbl = ctk.CTkLabel(u, text=t("ai_count", count=self.s.get('ai_requests', 0)),
                                         font=font(13))
        self.ai_count_lbl.pack(anchor="w")
        ctk.CTkLabel(u, text=t("ai_count_hint"),
                     font=font(11), text_color=MUTED).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(p, text=t("btn_save_settings"), height=46, corner_radius=12, fg_color=ACCENT,
                      hover_color=ACCENT_H, font=font(15, True), command=self._save_settings).pack(fill="x", pady=(8, 0))

    def _on_service(self, name):
        smtp_presets = get_smtp_presets()
        srv, port = smtp_presets[name]
        if name == t("smtp_custom"):
            self.adv.pack(fill="x")
        else:
            self.adv.pack_forget()
            self.set_server.delete(0, "end"); self.set_server.insert(0, srv)
            self.set_port.delete(0, "end"); self.set_port.insert(0, str(port))
        self._auto_save_settings()

    def _on_provider(self, label):
        prov = get_provider_labels()[label]
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
        self._auto_save_settings()

    def _fetch_models(self):
        self.llm_msg.configure(text=t("fetching_models"), text_color=MUTED)

        def run():
            try:
                ids = fetch_openrouter_models(self.set_apikey.get())
            except Exception:
                ids = []
            if ids:
                cur = self.set_model.get()
                self.after(0, lambda: (self.set_model.configure(values=ids),
                                       self.set_model.set(cur if cur in ids else ids[0]),
                                       self.llm_msg.configure(text=t("models_loaded", count=len(ids)),
                                                              text_color=OK)))
            else:
                self.after(0, lambda: self.llm_msg.configure(
                    text=t("fetch_failed"), text_color=DANGER))
        threading.Thread(target=run, daemon=True).start()

    def _save_settings(self):
        try:
            self._auto_save_settings()
            messagebox.showinfo(t("ok_title"), t("settings_saved"))
        except ValueError:
            messagebox.showerror(t("error_title"), t("port_error"))

    def _auto_save_settings(self, event=None):
        try:
            port_val = self.set_port.get() or "587"
            try:
                port = int(port_val)
            except ValueError:
                port = 587
                
            self.s.set("smtp_server", self.set_server.get() or "smtp.gmail.com")
            self.s.set("smtp_port", port)
            self.s.set("email", self.set_email.get())
            self.s.set("smtp_password", self.set_pass.get())
            self.s.set("llm_provider", get_provider_labels()[self.set_provider.get()])
            self.s.set("llm_model", self.set_model.get())
            self.s.set("llm_base_url", self.set_baseurl.get())
            self.s.set("llm_api_key", self.set_apikey.get())
            self.s.set("use_grounding", bool(self.set_online.get()))
            self.s.set("hunter_api_key", self.set_hunter.get())
            self.s.save()
            self._refresh_status()
        except Exception:
            pass

    def _test_smtp(self):
        self.smtp_msg.configure(text=t("connecting"), text_color=MUTED)

        def run():
            ok, msg = es.test_connection(self.set_server.get() or "smtp.gmail.com",
                                         int(self.set_port.get() or 587),
                                         self.set_email.get(), self.set_pass.get())
            self.after(0, lambda: self.smtp_msg.configure(
                text=msg.split("\n")[0] if ok else t("failed"), text_color=OK if ok else DANGER))
            if not ok:
                self.after(0, lambda: messagebox.showerror("SMTP", msg))
        threading.Thread(target=run, daemon=True).start()

    def _test_llm(self):
        key = self.set_apikey.get()
        if not key:
            self.llm_msg.configure(text=t("enter_key_first"), text_color=WARN)
            return
        client = LLMClient(get_provider_labels()[self.set_provider.get()], key, self.set_model.get(),
                           self.set_baseurl.get(), bool(self.set_online.get()))
        self.llm_msg.configure(text=t("testing"), text_color=MUTED)

        def run():
            ok, msg = client.test()
            self.after(0, self._bump_ai, 1)
            self.after(0, lambda: self.llm_msg.configure(
                text=t("working") if ok else t("failed"), text_color=OK if ok else DANGER))
            if not ok:
                self.after(0, lambda: messagebox.showerror("LLM", msg))
        threading.Thread(target=run, daemon=True).start()

    # ===================== ortak =====================
    def _smtp_cfg(self):
        email = self.s.get("email"); pwd = self.s.get("smtp_password")
        if not (email and pwd):
            messagebox.showwarning(t("no_mail_title"), t("no_mail_msg"))
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
            messagebox.showerror(t("critical_error"), str(e))
        except Exception:
            print("Kritik hata:", e)
