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
    "short":  "Gövde kısa ve öz olmalı: 2-3 kısa paragraf. / Keep the email body short and direct: 2-3 short paragraphs.",
    "medium": "Gövde orta uzunlukta olmalı: 3-4 paragraf. En önemli 2-3 yeteneği veya başarıyı okunabilirliği artırmak için kısa maddeler halinde listele. / Medium length: 3-4 paragraphs. List 2-3 key skills or achievements in clean bullet points for readability.",
    "long":   "Gövde detaylı ve doyurucu olmalı: 4-6 paragraf. Gönderenin özgeçmişini hedefin ihtiyaçlarıyla derinlemesine eşleştir ve 3-4 belirgin başarıyı maddeler halinde vurgula. / Detailed length: 4-6 paragraphs. Deeply map the sender's experience to the target's needs, using 3-4 bullet points to highlight accomplishments.",
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
    
    prof_section = ""
    if profile:
        prof_section = f"\n\nGÖNDERENİN ÖZGEÇMİŞİ / YETENEK VE DENEYİMLERİ (Aşağıdaki bilgiler doğrultusunda kendini tanıt):\n{profile.strip()}"
    
    sig_section = f"\n\nİMZA (Mailin sonuna bu imzayı ekle):\n{signature.strip()}" if signature else ""

    if lang == "tr":
        instructions = f"""Sen üst düzey bir kurumsal iletişim uzmanı ve profesyonel kariyer danışmanısın. Görevin: Alıcıyı (hedefi) araştırıp, ona özel, son derece mantıklı, akıcı, etkileyici ve profesyonel bir e-posta taslağı yazmak.

E-POSTA YAZIM STANDARTLARI (ÇOK ÖNEMLİ):
1. **Giriş ve Kanca (Hook)**: Klasik "Umarım iyisinizdir", "Şirketinizde çalışmak istiyorum" gibi klişe girişlerden kaçın. Doğrudan hedefin projesine, rolüne veya şirketin güncel faaliyetlerine samimi ve ilgili bir atıfta bulunarak başla.
2. **ATS Uyumlu Değer Sunumu (The Value Fit)**: Gönderenin profilindeki/özgeçmişindeki deneyimleri, hedefin sektörü ve olası ihtiyaçları ile eşleştir. Öne çıkan yetenekleri (teknik/sosyal) ve somut başarıları net, okunması kolay bir yapıda (gerekirse kısa ve temiz maddeler halinde) sun.
3. **Mantıksal Akış**: Her paragraf bir ana fikre odaklanmalı, cümleler kısa, öz ve net olmalıdır. Yapay zeka jargonu ("harika", "seçkin", "gurur duymak" gibi abartılı ifadeler) kullanma.
4. **Eylem Çağrısı (CTA)**: Mailin sonunda net, kibar ve hedefin zamanını çalmayacak kısa bir aksiyon çağrısı yap (Örn: "Müsait bir zamanınızda kısa bir tanışma toplantısı gerçekleştirmek isterim", "Özgeçmişimi incelemenizden memnuniyet duyarım").
5. **Biçimlendirme**: Metin standart mail şablonlarına uygun, temiz satır boşlukları içeren ve profesyonel bir düzende olmalıdır.
6. **Dil ve Üslup**: Dil {lang_name} olmalı. Üslup {tone_desc} olacak şekilde ayarlanmalıdır. {length_desc}

KURALLAR:
- E-posta adresi için: Hedefin profilinde veya sitesinde açıkça belirtilen gerçek bir e-posta adresi bulursan "email" alanına yaz ve "email_confidence" değerini "verified" yap. Emin değilsen veya bulamadıysan boş bırak ve "unknown" işaretle. Kesinlikle e-posta adresi uydurma.
- Çıktıyı SADECE aşağıdaki JSON formatında döndür, başka hiçbir açıklama ekleme:
{{"email":"<bulunan gerçek mail veya boş>","email_confidence":"verified|unknown","subject":"<dikkat çekici ve profesyonel konu başlığı>","body":"<e-posta gövdesi>","research_notes":"<alıcı hakkında araştırma notları>"}}"""
    else:
        instructions = f"""You are a senior executive communications expert and professional career strategist. Your goal is to research the recipient (target) and draft a highly logical, compelling, personalized, and ATS-friendly email.

EMAIL WRITING STANDARDS (CRITICAL):
1. **The Hook**: Avoid generic openers like "I hope this email finds you well" or "I am writing to apply...". Start with a direct, personalized, and genuine reference to the recipient's role, company achievements, or domain.
2. **ATS-Aligned Value Mapping**: Map the sender's profile/CV to the recipient's industry and potential pain points. Present top technical/soft skills and concrete accomplishments in a clean, readable layout (use bullet points where appropriate).
3. **Logical Coherence**: Each paragraph must focus on a single message. Keep sentences concise, clear, and impactful. Avoid robotic AI buzzwords (e.g., "delighted," "cutting-edge," "esteemed").
4. **Call to Action (CTA)**: Conclude with a low-friction, polite CTA (e.g., "I would appreciate the chance to discuss this in a brief chat," "I'd be glad to share my resume for review").
5. **Formatting**: Ensure standard email structure with proper line spacing, paragraph breaks, and clean layout.
6. **Tone & Style**: Language must be {lang_name}. Tone must be {tone_desc}. {length_desc}

RULES:
- Email address: If you find an official, publicly available email address of the recipient during research, put it in the "email" field and set "email_confidence" to "verified". Otherwise, leave it blank and set to "unknown". NEVER guess or hallucinate emails.
- Return ONLY the JSON response below without any extra text or markdown formatting outside the JSON block:
{{"email":"<verified email or empty>","email_confidence":"verified|unknown","subject":"<engaging and professional subject line>","body":"<email body>","research_notes":"<notes about what you researched>"}}"""

    return f"{instructions}\n\nMAİL AMACI / DETAYLAR: {brief.strip()}{prof_section}{sig_section}"


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
