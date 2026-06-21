"""LLM istemcisi.
- gemini: google_search grounding ile gerçek web verisine dayanır (uydurmaz).
- openai: OpenAI-uyumlu endpoint (base_url + key). Grounding yok.

research_and_draft(): hedefi araştırır, mail taslağı + (varsa) gerçek mail + kaynak döndürür.
"""
import re
import json
import logging
from typing import Dict, List, Optional

try:
    import requests
except Exception:
    requests = None

log = logging.getLogger("llm")

TONES = {
    "resmi": "resmi, profesyonel ve saygılı",
    "samimi": "sıcak, samimi ama profesyonel",
    "satış": "ikna edici, fayda odaklı, kısa ve net (soğuk satış/outreach)",
    "akademik": "akademik, ölçülü ve nazik",
}


def _system_prompt(brief, profile, tone, lang, signature):
    tone_desc = TONES.get(tone, TONES["samimi"])
    lang_name = "Türkçe" if lang == "tr" else "İngilizce"
    prof = f"\n\nGÖNDERENİN PROFİLİ (mailleri bu kişinin ağzından yaz):\n{profile.strip()}" if profile else ""
    sig = f"\n\nİMZA olarak şunu kullan:\n{signature.strip()}" if signature else ""
    return f"""Sen bir e-posta asistanısın. Görevin: verilen hedef kişi/kurumu \
araştırıp, ona özel, kişiselleştirilmiş bir e-posta taslağı yazmak.

KURALLAR:
- Dil: {lang_name}. Üslup: {tone_desc}.
- Maili yazarken hedefle ilgili GERÇEK, araştırmadan gelen bilgiyi kullan. Bilgi \
yoksa uydurma; genel ama dürüst yaz.
- E-posta adresi için: yalnızca araştırmada açıkça yayınlanmış bir adres bulursan \
onu ver ve "verified" işaretle. Bulamazsan email'i boş bırak ("unknown"); ADRES UYDURMA.
- Çıktıyı SADECE şu JSON formatında ver, başka hiçbir şey yazma:
{{"email":"<bulunan gerçek mail veya boş>","email_confidence":"verified|unknown",
"subject":"<konu>","body":"<mail gövdesi>","research_notes":"<1-2 cümle ne buldun>"}}

GÖNDEREN İSTEĞİ (mailin amacı): {brief.strip()}{prof}{sig}"""


def _parse_json(text: str) -> Optional[Dict]:
    if not text:
        return None
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    # ilk { ... son } arası
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e != -1 and e > s:
        try:
            return json.loads(text[s:e + 1])
        except Exception:
            return None
    return None


class LLMClient:
    def __init__(self, provider: str, api_key: str, model: str,
                 base_url: str = "", use_grounding: bool = True):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.use_grounding = use_grounding

    # ---------- public ----------
    def test(self) -> (bool, str):
        try:
            txt, _ = self._chat("Sadece 'OK' yaz.", grounding=False)
            return (("OK" in (txt or "").upper()), txt or "boş yanıt")
        except Exception as e:
            return False, str(e)

    def research_and_draft(self, target: str, brief: str, profile: str,
                           tone: str, lang: str, signature: str) -> Dict:
        sys = _system_prompt(brief, profile, tone, lang, signature)
        user = (f"HEDEF: {target}\n\nBu hedefi araştır (kurumun ne yaptığı, kişinin rolü, "
                f"güncel bilgiler, web sitesi, iletişim). Sonra JSON formatında mail taslağını üret.")
        text, sources = self._chat(f"{sys}\n\n{user}", grounding=self.use_grounding)
        parsed = _parse_json(text) or {}
        return {
            "email": (parsed.get("email") or "").strip(),
            "email_confidence": parsed.get("email_confidence", "unknown"),
            "subject": parsed.get("subject", "").strip() or "(konu üretilemedi)",
            "body": parsed.get("body", "").strip() or (text or "").strip(),
            "research_notes": parsed.get("research_notes", ""),
            "sources": sources,
            "raw": text,
        }

    # ---------- providers ----------
    def _chat(self, prompt: str, grounding: bool):
        if not requests:
            raise RuntimeError("'requests' kütüphanesi gerekli.")
        if self.provider == "gemini":
            return self._gemini(prompt, grounding)
        return self._openai(prompt)

    def _gemini(self, prompt: str, grounding: bool):
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent?key={self.api_key}")
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        if grounding:
            body["tools"] = [{"google_search": {}}]
        r = requests.post(url, json=body, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"Gemini {r.status_code}: {r.text[:300]}")
        data = r.json()
        cand = (data.get("candidates") or [{}])[0]
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts)
        # kaynaklar
        sources = []
        gm = cand.get("groundingMetadata") or {}
        for ch in gm.get("groundingChunks", []) or []:
            web = ch.get("web") or {}
            if web.get("uri"):
                sources.append({"title": web.get("title", web["uri"]), "url": web["uri"]})
        return text, sources

    def _openai(self, prompt: str):
        base = (self.base_url or "https://api.openai.com/v1").rstrip("/")
        r = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            json={"model": self.model,
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7},
            timeout=60,
        )
        if r.status_code != 200:
            raise RuntimeError(f"API {r.status_code}: {r.text[:300]}")
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        return text, []
