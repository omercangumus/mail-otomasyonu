"""E-posta bulma.
- Hunter API anahtarı varsa: gerçek, doğrulanmış mail (confidence='verified').
- Yoksa: ad + domain'den yaygın kalıp tahmini (confidence='guessed').
Hiçbir zaman 'uydurulmuş ama doğrulanmış gibi' mail döndürmez.
"""
import re
import logging
from typing import Dict, Optional, List

# Kalıp tahmini yapılmaması gereken domain'ler (sosyal medya, platform siteleri)
_SOCIAL_DOMAINS = {
    "linkedin.com", "twitter.com", "x.com", "facebook.com", "instagram.com",
    "github.com", "youtube.com", "medium.com", "tiktok.com", "reddit.com",
}


def _is_social_domain(domain: str) -> bool:
    """Domain sosyal medya / platform sitesi mi? Kalıp tahmini anlamsız."""
    if not domain:
        return False
    d = domain.lower().lstrip("www.")
    return any(d == s or d.endswith("." + s) for s in _SOCIAL_DOMAINS)

try:
    import requests
except Exception:
    requests = None

log = logging.getLogger("finder")

_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def normalize(s: str) -> str:
    s = (s or "").translate(_TR).lower()
    return re.sub(r"[^a-z]", "", s)


def domain_from(text: str) -> Optional[str]:
    """'acme.com', 'https://acme.com/x' veya 'info@acme.com' -> 'acme.com'."""
    if not text:
        return None
    text = text.strip()
    m = re.search(r"@([\w.-]+\.\w+)", text)
    if m:
        return m.group(1).lower()
    m = re.search(r"https?://([\w.-]+\.\w+)", text)
    if m:
        return m.group(1).lower().replace("www.", "")
    m = re.match(r"^([\w-]+\.\w{2,})$", text)
    if m:
        return m.group(1).lower().replace("www.", "")
    return None


def split_name(full: str) -> (str, str):
    parts = [p for p in re.split(r"\s+", (full or "").strip()) if p]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[-1]


def guess_patterns(full_name: str, domain: str) -> List[str]:
    first, last = split_name(full_name)
    f, l = normalize(first), normalize(last)
    if not domain:
        return []
    out = []
    if f and l:
        out += [f"{f}.{l}@{domain}", f"{f}{l}@{domain}",
                f"{f[0]}{l}@{domain}", f"{f}_{l}@{domain}"]
    if f:
        out.append(f"{f}@{domain}")
    seen, res = set(), []
    for e in out:
        if e not in seen:
            seen.add(e)
            res.append(e)
    return res


def hunter_find(domain: str, full_name: str, api_key: str) -> Optional[Dict]:
    if not (requests and domain and api_key):
        return None
    first, last = split_name(full_name)
    try:
        r = requests.get(
            "https://api.hunter.io/v2/email-finder",
            params={"domain": domain, "first_name": first,
                    "last_name": last, "api_key": api_key},
            timeout=15,
        )
        if r.status_code != 200:
            log.warning("Hunter %s: %s", r.status_code, r.text[:200])
            return None
        data = r.json().get("data", {})
        if data.get("email"):
            score = data.get("score") or 0
            return {"email": data["email"],
                    "confidence": "verified" if score >= 70 else "guessed",
                    "score": score}
    except Exception as e:
        log.error("Hunter hatası: %s", e)
    return None


def find_email(full_name: str, domain: Optional[str], hunter_key: str = "",
               llm_found: Optional[str] = None) -> Dict:
    """En iyi maili döndürür: {email, confidence, source}."""
    # 1) LLM araştırma sonucu gerçek mail bulduysa — en öncelikli
    if llm_found and "@" in llm_found:
        return {"email": llm_found.strip(), "confidence": "verified",
                "source": "araştırma (profilde açık mail)", "score": None}
    # 2) Hunter (en güvenilir harici doğrulama)
    if hunter_key and domain and not _is_social_domain(domain):
        res = hunter_find(domain, full_name, hunter_key)
        if res:
            res["source"] = "hunter"
            return res
    # 3) Kalıp tahmini — sadece kurumsal domain'lerde (linkedin vb. DEĞİL)
    if domain and not _is_social_domain(domain):
        patt = guess_patterns(full_name, domain)
        if patt:
            return {"email": patt[0], "confidence": "guessed",
                    "source": "kalıp tahmini", "alternatives": patt[1:], "score": None}
    return {"email": "", "confidence": "unknown", "source": "—", "score": None}
