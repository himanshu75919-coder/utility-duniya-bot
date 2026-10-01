# -*- coding: utf-8 -*-
"""
Toolkit Extras (v31 Professional Upgrade Pack)
==============================================
Yahan wo naye engines hain jo purane tools ko "professional" banate hain:

1.  shorten_url()        -> 6 shortener providers, jo chale wahi use hota hai (is.gd dead tha).
2.  expand_url()         -> Redirect chain kholta hai + tracking params saaf karta hai (LINK BYPASS upgrade).
3.  check_link_safety()  -> Real multi-signal link safety analyzer (OpenPhish live feed + urlscan.io
                            + 15+ heuristics). Pehle sirf 8 keyword match tha.
4.  calc_interest()      -> INTEREST CALC tool ka poora engine (ye tool pehle TOOTA hua tha).
5.  parse_emi_input()    -> EMI tool ab flexible input leta hai (amount, rate, months).
6.  file_size_human()    -> bytes ko MB/GB me.
"""

import base64
import re
import time
from datetime import datetime
from html import escape as hesc
from urllib.parse import quote, unquote, urlparse, parse_qs, urlunparse

import requests

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# =====================================================================================
# 1) URL SHORTENER — multi-provider (jo chale wahi)
# =====================================================================================
def _sh_dag(url):
    r = requests.get("https://da.gd/shorten", params={"url": url}, headers=UA, timeout=8)
    t = r.text.strip()
    return t if r.status_code == 200 and t.startswith("http") else None


def _sh_spoo(url):
    r = requests.post("https://spoo.me/", data={"url": url}, headers={**UA, "Accept": "application/json"}, timeout=8)
    if r.status_code in (200, 201):
        try:
            j = r.json()
            u = j.get("short_url") or j.get("short") or j.get("url")
            return u.replace("http://", "https://", 1) if u else None
        except Exception:
            m = re.search(r"https?://spoo\.me/\S+", r.text)
            return m.group(0) if m else None
    return None


def _sh_cleanuri(url):
    r = requests.post("https://cleanuri.com/api/v1/shorten", data={"url": url}, headers=UA, timeout=8)
    if r.status_code == 200:
        try:
            return r.json().get("result_url")
        except Exception:
            return None
    return None


def _sh_clck(url):
    r = requests.get("https://clck.ru/--", params={"url": url}, headers=UA, timeout=8)
    t = r.text.strip()
    return t if r.status_code == 200 and t.startswith("http") else None


def _sh_tiny(url):
    r = requests.get("https://tinyurl.com/api-create.php", params={"url": url}, headers=UA, timeout=8)
    t = r.text.strip()
    return t if r.status_code == 200 and "tinyurl.com" in t else None


def _sh_isgd(url):
    r = requests.get("https://is.gd/create.php", params={"format": "simple", "url": url}, headers=UA, timeout=8)
    t = r.text.strip()
    return t if r.status_code == 200 and t.startswith("https://is.gd/") else None


SHORTENER_PROVIDERS = [
    ("da.gd", _sh_dag),
    ("spoo.me", _sh_spoo),
    ("cleanuri", _sh_cleanuri),
    ("clck.ru", _sh_clck),
    ("tinyurl", _sh_tiny),
    ("is.gd", _sh_isgd),
]


def shorten_url(url: str, want: int = 2) -> list:
    """Ek ya zyada working short links return karta hai: [(provider, short_url), ...]"""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    out = []
    for name, fn in SHORTENER_PROVIDERS:
        if len(out) >= want:
            break
        try:
            s = fn(url)
            if s and s.strip() and s.strip() != url:
                out.append((name, s.strip()))
        except Exception:
            continue
    return out


# =====================================================================================
# 2) URL EXPANDER — redirect chain + tracking cleaner (LINK BYPASS upgrade)
# =====================================================================================
TRACK_PARAMS_PREFIX = ("utm_", "pk_", "mc_", "ga_", "fb_")
TRACK_PARAMS_EXACT = {
    "fbclid", "gclid", "dclid", "msclkid", "igshid", "igsh", "si", "ref", "ref_src",
    "ref_url", "source", "spm", "yclid", "_openstat", "wt_mc", "twclid", "ttclid",
    "share_id", "shareId", "share", "share_source", "feature", "app", "mibextid", "sfnsn",
}


def clean_tracking(url: str) -> str:
    """Tracking/ad params hata kar saaf URL banata hai."""
    try:
        p = urlparse(url)
        if not p.query:
            return url
        q = parse_qs(p.query, keep_blank_values=True)
        clean = {k: v for k, v in q.items()
                 if not (k.lower().startswith(TRACK_PARAMS_PREFIX) or k.lower() in TRACK_PARAMS_EXACT)}
        new_query = "&".join(f"{quote(str(k))}={quote(str(v[0]))}" for k, v in clean.items())
        return urlunparse((p.scheme, p.netloc, p.path, p.params, new_query, ""))
    except Exception:
        return url


SHORTENER_HOSTS = (
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "v.gd", "ow.ly", "buff.ly", "rebrand.ly",
    "cutt.ly", "shorturl.at", "rb.gy", "tiny.cc", "s.id", "clck.ru", "da.gd", "spoo.me", "cleanuri.com",
    "shortlink", "lnkd.in", "t.ly", "shrtco.de", "9qr.de", "bl.ink", "short.gy", "urlz.fr", "adf.ly",
    "shorte.st", "linkvertise.com", "za.gl", "fc.lc", "cuty.io", "tii.ai", "gplinks.co", "mdiskshortner",
    "droplink.co", "dn.majh", "tei.ai", "indianshortner", "omg10.com", "ez4short.com", "tnlink.in",
)


def expand_url(url: str, max_hops: int = 6):
    """Redirect chain follow karta hai aur final + cleaned URL deta hai.
    Returns dict: {ok, original, final, cleaned, chain: [...], hops, is_shortener}"""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    chain = []
    cur = url
    is_short = False
    try:
        s = requests.Session()
        for _ in range(max_hops):
            r = s.get(cur, headers=UA, timeout=10, allow_redirects=False, stream=True)
            chain.append(cur)
            if urlparse(cur).netloc.lower().replace("www.", "") in [h.replace("www.", "") for h in SHORTENER_HOSTS]:
                is_short = True
            if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
                nxt = r.headers["Location"]
                if nxt.startswith("/"):
                    p = urlparse(cur)
                    nxt = f"{p.scheme}://{p.netloc}{nxt}"
                if nxt in chain:
                    break
                cur = nxt
                continue
            break
        # Final URL ka clean version (agar redirect nahi hua to bhi)
        if not chain:
            chain = [url]
        final = chain[-1]
        # Kabhi kabhi redirect ke baad bhi tracking params bache hote hain
        cleaned = clean_tracking(final)
        return {
            "ok": True,
            "original": url,
            "final": final,
            "cleaned": cleaned,
            "chain": chain,
            "hops": max(0, len(chain) - 1),
            "is_shortener": is_short,
        }
    except Exception as e:
        final = chain[-1] if chain else url
        return {
            "ok": False,
            "original": url,
            "error": str(e)[:120],
            "final": final,
            "cleaned": clean_tracking(final),
            "chain": chain or [url],
            "hops": max(0, len(chain or [url]) - 1),
            "is_shortener": False,
        }


# =====================================================================================
# 3) LINK SAFETY CHECKER — real multi-signal analyzer
# =====================================================================================
_PHISH_CACHE = {"ts": 0, "hosts": set(), "urls": set()}


def _load_openphish():
    """OpenPhish public feed (free, no key) — 6 ghante cache."""
    if time.time() - _PHISH_CACHE["ts"] < 6 * 3600 and _PHISH_CACHE["urls"]:
        return
    try:
        r = requests.get("https://openphish.com/feed.txt", headers=UA, timeout=12)
        if r.status_code == 200:
            urls, hosts = set(), set()
            for line in r.text.splitlines():
                u = line.strip()
                if u.startswith("http"):
                    urls.add(u)
                    try:
                        hosts.add(urlparse(u).netloc.lower())
                    except Exception:
                        pass
            if urls:
                _PHISH_CACHE.update({"ts": time.time(), "hosts": hosts, "urls": urls})
    except Exception:
        pass


def _urlscan_reputation(host: str):
    """urlscan.io public search (no key needed for search API)."""
    try:
        r = requests.get("https://urlscan.io/api/v1/search/",
                         params={"q": f"page.domain:{host}", "size": "20"},
                         headers=UA, timeout=10)
        if r.status_code == 200:
            j = r.json()
            total = j.get("total", len(j.get("results", [])))
            return total
    except Exception:
        pass
    return -1


SUSPICIOUS_TLDS = {".top", ".xyz", ".tk", ".ml", ".ga", ".cf", ".gq", ".zip", ".mov", ".click",
                   ".work", ".loan", ".date", ".review", ".country", ".stream", ".download", ".racing",
                   ".win", ".bid", ".party", ".trade", ".men", ".icu", ".cyou", ".monster", ".rest"}
BRANDS = ["paytm", "phonepe", "googlepay", "gpay", "sbi", "hdfc", "icici", "axis", "kotak", "pnb", "bob",
          "amazon", "flipkart", "myntra", "irctc", "netflix", "hotstar", "jio", "airtel", "vi", "bsnl",
          "instagram", "facebook", "whatsapp", "telegram", "uidai", "aadhaar", "pan", "incometax",
          "gst", "epfo", "postoffice", "indiapost", "upi", "bhim", "rupay"]
LURE_WORDS = {"login": 12, "verify": 12, "secure": 8, "update": 8, "kyc": 15, "otp": 15, "bank": 10,
              "refund": 12, "lottery": 20, "bonus": 12, "winner": 18, "prize": 18, "free": 8,
              "gift": 12, "claim": 15, "unlock": 10, "recovery": 12, "wallet": 8, "upi": 10,
              "support": 6, "account": 8, "payment": 8, "reward": 12, "cashback": 10, "offer": 6}


def check_link_safety(raw_url: str) -> dict:
    """
    Professional multi-signal link safety check.
    Returns: {ok, verdict, risk(0-100), level, reasons[], advice, signals{}, final_url, chain}
    """
    url = raw_url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    exp = expand_url(url)
    target = exp.get("final", url) if exp.get("ok") else url
    p = urlparse(target)
    host = (p.netloc or "").lower()
    host_no_port = host.split(":")[0]
    path_q = (p.path or "") + ("?" + p.query if p.query else "")

    risk = 0
    reasons = []
    signals = {
        "redirect_hops": exp.get("hops", 0),
        "final_url": target,
        "https": p.scheme == "https",
        "host": host_no_port or "?",
    }

    # --- A) redirect chain (shorteners chhupate hain asli destination) ---
    if exp.get("is_shortener"):
        risk += 18
        reasons.append("🔀 Shortened/redirect link hai — asli destination chhupa hua tha (khola gaya).")
    if exp.get("hops", 0) >= 3:
        risk += 12
        reasons.append(f"🔁 {exp['hops']} baar redirect ho raha hai (multi-hop cloaking ke signs).")

    # --- B) host structure ---
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host_no_port):
        risk += 30
        reasons.append("🧮 Domain ki jagah seedha IP address hai — 95% phishing isi tarah aata hai.")
    if "xn--" in host_no_port:
        risk += 25
        reasons.append("🔤 Punycode (xn--) domain — milte-julte foreign characters se dhokha diya ja sakta hai.")
    if "@" in target.split("://", 1)[-1].split("/")[0]:
        risk += 35
        reasons.append("🎭 URL me '@' trick — asli site '@' ke baad hoti hai, isliye ye dhoka hai.")
    labels = host_no_port.split(".")
    if len(labels) >= 5:
        risk += 15
        reasons.append(f"🧩 Bahut saare subdomain ({len(labels)} parts) — brand ko fake banaya gaya lag raha hai.")
    tld = "." + labels[-1] if labels else ""
    if tld in SUSPICIOUS_TLDS:
        risk += 18
        reasons.append(f"🌍 '{tld}' TLD scam/phishing me bahut use hota hai.")
    if host_no_port.count("-") >= 2:
        risk += 8
        reasons.append("➖ Domain me 2+ hyphen (brand mimicry ka common pattern).")

    # --- C) HTTPS + port ---
    if p.scheme != "https":
        risk += 12
        reasons.append("🔓 Connection 'http' hai (not secure) — form/OTP kabhi na daalein.")
    if ":" in host and not host.endswith((":443", ":80")):
        risk += 15
        reasons.append(f"🚪 Unusual port ({host.split(':')[-1]}) — normal websites ise use nahi karte.")

    # --- D) lure words + brand combos ---
    low = (host_no_port + path_q).lower()
    hit_words = [w for w in LURE_WORDS if w in low]
    if hit_words:
        add = min(30, sum(LURE_WORDS[w] for w in hit_words))
        risk += add
        reasons.append("🎣 Suspicious words mile: " + ", ".join(hit_words[:6]))
    brand_hit = [b for b in BRANDS if b in low]
    # Brand + free hosting/other domain me = impersonation
    if brand_hit and not any(host_no_port.endswith(b + ".com") or host_no_port == b + ".com"
                             or host_no_port.endswith(b + ".in") or host_no_port == b + ".in" for b in brand_hit):
        risk += 22
        reasons.append("🏦 Brand ka naam lekin official domain nahi: " + ", ".join(brand_hit[:4]) +
                       f" (asli site {brand_hit[0]}.com/.in hoti hai)")
    if any(x in host_no_port for x in ("vercel.app", "netlify.app", "pages.dev", "workers.dev", "web.app",
                                       "firebaseapp.com", "duckdns.org", "myftp.org", "000webhostapp.com",
                                       "github.io", "glitch.me", "repl.co", "blogspot.")) and (hit_words or brand_hit):
        risk += 12
        reasons.append("🆓 Free hosting domain par bank/login jaisa page — scam ke liye popular combo.")

    # --- E) OpenPhish live feed ---
    _load_openphish()
    if _PHISH_CACHE["urls"]:
        if target in _PHISH_CACHE["urls"] or any(u.startswith(target) for u in _PHISH_CACHE["urls"] if len(u) > 20):
            risk += 60
            reasons.append("🚨 Ye link OpenPhish ke LIVE phishing feed me hai (pakka scam).")
        elif host_no_port in _PHISH_CACHE["hosts"]:
            risk += 50
            reasons.append("🚨 Is domain ka naam OpenPhish live phishing feed me hai.")
    signals["openphish_size"] = len(_PHISH_CACHE["urls"])

    # --- F) urlscan.io reputation ---
    scans = _urlscan_reputation(host_no_port) if host_no_port else -1
    signals["urlscan_scans"] = scans
    if scans == 0:
        reasons.append("🆕 urlscan.io par ye domain kabhi scan nahi hua (naya/less-known).")

    # --- G) length / entropy signals ---
    if len(target) > 120:
        risk += 8
        reasons.append("📏 Link bahut lamba hai (tracking/obfuscation).")
    if re.search(r"(login|verify|kyc|otp|bank|update)[-_]?(page|form|verify|secure|account)", low):
        risk += 15
        reasons.append("📋 URL path me 'fake login page' jaisa pattern mila.")

    risk = max(0, min(100, risk))
    if risk >= 60:
        verdict, level, advice = "DANGEROUS 🚨", "danger", ("Ye link KABHI na kholein, na kisi ko bhejein. " 
                                                           "OTP/password/UPI PIN kisi bhi link me kabhi na daalein.")
    elif risk >= 25:
        verdict, level, advice = "SUSPICIOUS ⚠️", "suspicious", ("Ehtiyat karein — sirf tab kholein jab aapko site ka "
                                                                  "pata ho. Login/payment details na dein.")
    elif risk > 0:
        verdict, level, advice = "LOW RISK ✅", "low", "Chhote-chhote minor signals hain. Normal browsing theek hai."
    else:
        verdict, level, advice = "SAFE ✅", "safe", "Koi suspicious signal nahi mila. Phir bhi OTP/PIN kabhi share na karein."

    if not reasons:
        reasons.append("✅ Koi redirect, IP, punycode, lure-word ya phishing-feed match nahi mila.")
    return {
        "ok": True,
        "verdict": verdict,
        "level": level,
        "risk": risk,
        "reasons": reasons,
        "advice": advice,
        "signals": signals,
        "final_url": target,
        "cleaned_url": exp.get("cleaned", target),
        "chain": exp.get("chain", []),
    }


# =====================================================================================
# 4) INTEREST CALCULATOR (ye tool pehle TOOTA hua tha — ab poora engine)
# =====================================================================================
def calc_interest(principal: float, rate_pct: float, months: int, mode: str = "both") -> dict:
    """Simple + Compound interest calculation (poore breakdown ke saath)."""
    months = max(1, int(months))
    years = months / 12.0
    simple = principal * (rate_pct / 100.0) * years

    # Compound (monthly compounding — banks/EMI jaisa)
    r = (rate_pct / 100.0) / 12.0
    comp_amount = principal * ((1 + r) ** months) if r > 0 else principal
    compound = comp_amount - principal

    # Quarterly / half-yearly / yearly compounding bhi dikhate hain (FD comparison)
    def comp_with(freq_per_year):
        rr = (rate_pct / 100.0) / freq_per_year
        n = freq_per_year * years
        return principal * ((1 + rr) ** n) - principal

    return {
        "ok": True,
        "principal": principal,
        "rate": rate_pct,
        "months": months,
        "years": round(years, 2),
        "simple_interest": simple,
        "simple_total": principal + simple,
        "compound_monthly": compound,
        "compound_monthly_total": comp_amount,
        "compound_quarterly": comp_with(4),
        "compound_halfyearly": comp_with(2),
        "compound_yearly": comp_with(1),
        "mode": mode,
    }


# =====================================================================================
# 5) EMI flexible input parser
# =====================================================================================
def parse_emi_input(text: str):
    """
    Flexible EMI input parser. Ye sab chalega:
      "100000"            -> 1,00,000 @ 10.5% / 12 months
      "100000 10.5"       -> amount + rate
      "100000 24"         -> amount + 24 months (rate default)
      "5,00,000 9% 24m"   -> Indian commas + % + m/mahine
      "3 lakh 9.5% 2 saal"
    Returns (principal, rate, months) ya (None, None, None)
    """
    raw = (text or "").strip().lower().replace("₹", " ").replace("rs.", " ").replace("rs", " ")
    s = re.sub(r"(?<=\d),(?=\d)", "", raw)          # Indian/standard thousand separators
    s = re.sub(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|lakhs)\b", lambda m: str(float(m.group(1)) * 100000), s)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*(?:crore|cr)\b", lambda m: str(float(m.group(1)) * 10000000), s)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*(?:hazaar|hazar|k)\b", lambda m: str(float(m.group(1)) * 1000), s)

    months = None
    rate = None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|mo|months?|mahine|mahina)\b", s)
    if m:
        months = float(m.group(1))
        s = s.replace(m.group(0), " ")
    m = re.search(r"rate\s*=?\s*(\d+(?:\.\d+)?)", s)
    if m:
        rate = float(m.group(1))
        s = s.replace(m.group(0), " ")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent|pct)", s)
    if m:
        rate = float(m.group(1))
        s = s.replace(m.group(0), " ")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:y|yr|years?|saal|varsh)\b", s)
    if m:
        months = float(m.group(1)) * 12
        s = s.replace(m.group(0), " ")

    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    if not nums:
        return None, None, None

    principal = nums[0]
    for v in nums[1:]:
        if rate is None and months is None:
            if (not float(v).is_integer()) and v <= 60:
                rate = v
            else:
                months = v
        elif rate is None:
            if v <= 60:
                rate = v
        elif months is None:
            months = v

    if rate is None:
        rate = 10.5
    if months is None:
        months = 12
    months = int(min(max(months, 1), 480))
    rate = max(0.0, min(float(rate), 60.0))
    return principal, rate, months


# =====================================================================================
# 6) Helper
# =====================================================================================
def file_size_human(n) -> str:
    try:
        n = float(n)
    except Exception:
        return "N/A"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.2f} {unit}" if unit not in ("B",) else f"{int(n)} B"
        n /= 1024.0
    return f"{n:.2f} TB"
