"""LLM istemcisi.
Sağlayıcılar:
- gemini     : Google google_search grounding ile gerçek web verisine dayanır.
- openrouter : 300+ modele tek anahtarla erişim (OpenAI-uyumlu). ":online" ile web araması.
- openai     : OpenAI veya OpenAI-uyumlu özel endpoint (base_url).

research_and_draft(): hedefi araştırır, kişiye özel mail taslağı + (varsa) gerçek mail döndürür.
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

LENGTH_PROMPTS = {
    "short":  "Gövde KISA olsun: 2-3 kısa paragraf, doğrudan ve öz. Net bir kapanış içersin.",
    "medium": "Gövde ORTA uzunlukta olsun: 4-5 paragraf, dengeli detay seviyesi. Net bir kapanış/çağrı içersin.",
    "long":   "Gövde UZUN ve DETAYLI olsun: 6-8 paragraf, somut örnekler, derinlemesine anlatım, güçlü argümanlar. Net bir kapanış/çağrı içersin.",
}

# Sağlayıcı varsayılanları
PROVIDERS = {
    "gemini":     {"base": "", "label": "Google Gemini (web araması dahil)"},
    "openrouter": {"base": "https://openrouter.ai/api/v1", "label": "OpenRouter (çok model)"},
    "openai":     {"base": "https://api.openai.com/v1", "label": "OpenAI / Özel"},
}

# Hazır model önerileri (slug'lar zamanla değişir; düzenlenebilir + canlı çekilebilir).
MODEL_PRESETS = {
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3-flash"],
    "openrouter": [
        # Anthropic
        "anthropic/claude-sonnet-4.6",
        "anthropic/claude-opus-4.7",
        "anthropic/claude-opus-4.6",
        "anthropic/claude-3.5-haiku",
        # OpenAI
        "openai/gpt-5.4",
        "openai/gpt-5.5",
        "openai/gpt-4o-mini",
        # Google
        "google/gemini-2.5-flash",
        "google/gemini-2.5-pro",
        "google/gemini-3-flash",
        # DeepSeek (ucuz)
        "deepseek/deepseek-v4-flash",
        "deepseek/deepseek-chat",
        "deepseek/deepseek-r1",
        # Çin / açık ağırlık
        "moonshotai/kimi-k2.6",
        "qwen/qwen-2.5-72b-instruct",
        "z-ai/glm-4.6",
        "minimax/minimax-m2",
        # Meta / Mistral / xAI
        "meta-llama/llama-3.3-70b-instruct",
        "mistralai/mistral-large",
        "x-ai/grok-4",
        # Ücretsiz denemelik
        "deepseek/deepseek-r1:free",
        "meta-llama/llama-3.3-70b-instruct:free",
    ],
    "openai": ["gpt-4o-mini", "gpt-5.4"],
}


def fetch_openrouter_models(api_key: str = ""):
    """OpenRouter'ın güncel model listesini canlı çeker (slug'lar hiç eskimesin diye).
    Listeleme için anahtar şart değil."""
    if not requests:
        return []
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    r = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json().get("data", [])
    return sorted({m["id"] for m in data if m.get("id")})


def _system_prompt(brief, profile, tone, lang, signature, length="medium"):
    tone_desc = TONES.get(tone, TONES["samimi"])
    lang_name = "Türkçe" if lang == "tr" else "İngilizce"
    length_desc = LENGTH_PROMPTS.get(length, LENGTH_PROMPTS["medium"])
    prof = (f"\n\nGÖNDERENİN PROFİLİ (mailleri bu kişinin ağzından, onun deneyim/becerilerine "
            f"atıfla yaz; metinde PDF'den gelen biçim bozuklukları olabilir, anlamlı yorumla):\n"
            f"{profile.strip()}") if profile else ""
    sig = f"\n\nİMZA olarak şunu kullan:\n{signature.strip()}" if signature else ""
    return f"""Sen deneyimli bir e-posta asistanısın. Görevin: verilen hedefi araştırıp, \
ona özel, AKICI ve doğal bir e-posta yazmak.

KURALLAR:
- Dil: {lang_name}. Üslup: {tone_desc}.
- Mail kişisel ve spesifik olsun: hedefin kurumuna/rolüne ve gönderenin profiline somut \
atıf yap. Klişe, jenerik, şablon kokan cümlelerden kaçın.
- Hedef bir URL ise (ör. LinkedIn profili veya web sitesi), o sayfayı/kişiyi araştır; \
kişinin adını, rolünü, şirketini ve ilgili detayları çıkar ve maile yansıt.
- GERÇEK bilgi kullan; bilmediğini uydurma, dürüst ve genel geç.
- Konu kısa ve dikkat çekici olsun. {length_desc}
- E-posta adresi için: yalnızca açıkça yayınlanmış gerçek bir adres bulursan ver ve \
"verified" işaretle. Bulamazsan email'i boş bırak ("unknown"); ADRES UYDURMA.
- Çıktıyı SADECE şu JSON ile ver, başka hiçbir şey yazma:
{{"email":"<gerçek mail veya boş>","email_confidence":"verified|unknown",
"subject":"<konu>","body":"<mail gövdesi>","research_notes":"<1-2 cümle: hedef hakkında ne buldun>"}}

GÖNDERENİN İSTEĞİ (mailin amacı/konusu): {brief.strip()}{prof}{sig}"""


def _parse_json(text: str) -> Optional[Dict]:
    if not text:
        return None
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e != -1 and e > s:
        try:
            return json.loads(text[s:e + 1])
        except Exception:
            return None
    return None


class LLMClient:
    def __init__(self, provider: str, api_key: str, model: str,
                 base_url: str = "", online: bool = True):
        self.provider = provider
        self.api_key = api_key
        self.model = model.strip()
        self.base_url = (base_url or PROVIDERS.get(provider, {}).get("base", "")).rstrip("/")
        self.online = online  # gemini=grounding, openrouter=:online web aramasi

    # ---------- public ----------
    def test(self):
        try:
            txt, _ = self._chat("Sadece 'OK' yaz.", web=False)
            return (("OK" in (txt or "").upper()), txt or "boş yanıt")
        except Exception as e:
            return False, str(e)

    def research_and_draft(self, target, brief, profile, tone, lang, signature,
                            length="medium") -> Dict:
        sys = _system_prompt(brief, profile, tone, lang, signature, length)
        user = (f"HEDEF: {target}\n\nBu hedefi araştır (kurum ne yapıyor, kişinin rolü, "
                f"güncel bilgiler, web sitesi, iletişim). Sonra JSON taslağı üret.")
        text, sources = self._chat(f"{sys}\n\n{user}", web=self.online)
        p = _parse_json(text) or {}
        return {
            "email": (p.get("email") or "").strip(),
            "email_confidence": p.get("email_confidence", "unknown"),
            "subject": p.get("subject", "").strip() or "(konu üretilemedi)",
            "body": p.get("body", "").strip() or (text or "").strip(),
            "research_notes": p.get("research_notes", ""),
            "sources": sources,
            "raw": text,
        }

    # ---------- routing ----------
    def _chat(self, prompt, web):
        if not requests:
            raise RuntimeError("'requests' kütüphanesi gerekli.")
        if self.provider == "gemini":
            return self._gemini(prompt, web)
        return self._openai_like(prompt, web)

    def _gemini(self, prompt, web):
        model = self.model or "gemini-2.5-flash"
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={self.api_key}")
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        if web:
            # google_search: arama · url_context: prompttaki linkleri (LinkedIn vb.) okur
            body["tools"] = [{"google_search": {}}, {"url_context": {}}]
        r = requests.post(url, json=body, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"Gemini {r.status_code}: {r.text[:300]}")
        cand = (r.json().get("candidates") or [{}])[0]
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts)
        sources = []
        for ch in (cand.get("groundingMetadata") or {}).get("groundingChunks", []) or []:
            w = ch.get("web") or {}
            if w.get("uri"):
                sources.append({"title": w.get("title", w["uri"]), "url": w["uri"]})
        return text, sources

    def _openai_like(self, prompt, web):
        model = self.model
        # OpenRouter: ":online" web arama eklentisi
        if web and self.provider == "openrouter" and ":online" not in model:
            model = model + ":online"
        headers = {"Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json"}
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/omercangumus"
            headers["X-Title"] = "EmailAI"
        r = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={"model": model,
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7},
            timeout=60,
        )
        if r.status_code != 200:
            raise RuntimeError(f"API {r.status_code}: {r.text[:300]}")
        data = r.json()
        msg = data["choices"][0]["message"]
        text = msg.get("content") or ""
        # OpenRouter :online bazen kaynakları annotations'ta döndürür
        sources = []
        for ann in msg.get("annotations", []) or []:
            cit = ann.get("url_citation") or {}
            if cit.get("url"):
                sources.append({"title": cit.get("title", cit["url"]), "url": cit["url"]})
        return text, sources
