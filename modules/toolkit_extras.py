# -*- coding: utf-8 -*-
"""
Toolkit Extras (v31 Professional Upgrade Pack)
==============================================
Engines that make the older tools professional:

1.  shorten_url()        -> 6 shortener providers, uses whichever works (is.gd was dead).
2.  expand_url()         -> Opens the redirect chain + cleans tracking params (LINK BYPASS upgrade).
3.  check_link_safety()  -> Real multi-signal link safety analyzer (OpenPhish live feed + urlscan.io
                            + 15 heuristics).
4.  rate_from_per_hundred() + village_compound_interest() -> the INTEREST CALC engine.
5.  file_size_human()    -> bytes to MB/GB.
"""

import re
import time
from urllib.parse import quote, urlparse, parse_qs, urlunparse

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
        reasons.append("🔀 Ye shortened/redirect link hai — asli destination chhupi thi (ab khol di).")
    if exp.get("hops", 0) >= 3:
        risk += 12
        reasons.append(f"🔁 {exp['hops']} times (signs of multi-hop cloaking).")

    # --- B) host structure ---
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host_no_port):
        risk += 30
        reasons.append("🧮 A raw IP address instead of a domain — 95% of phishing comes this way.")
    if "xn--" in host_no_port:
        risk += 25
        reasons.append("🔤 Punycode (xn--) domain — milte-julte foreign characters se dhokha diya ja sakta hai.")
    if "@" in target.split("://", 1)[-1].split("/")[0]:
        risk += 35
        reasons.append("🎭 URL me '@' ka jhol — asli site '@' ke baad hai, ye dhokha hai.")
    labels = host_no_port.split(".")
    if len(labels) >= 5:
        risk += 15
        reasons.append(f"🧩 Too many subdomains ({len(labels)} parts) — the brand looks faked.")
    tld = "." + labels[-1] if labels else ""
    if tld in SUSPICIOUS_TLDS:
        risk += 18
        reasons.append(f"🌍 '{tld}' TLD is heavily used in scams/phishing.")
    if host_no_port.count("-") >= 2:
        risk += 8
        reasons.append("➖ 2+ hyphens in the domain (a common brand-mimicry pattern).")

    # --- C) HTTPS + port ---
    if p.scheme != "https":
        risk += 12
        reasons.append("🔓 Connection 'http' hai (secure nahi) — kabhi form ya OTP na dalo.")
    if ":" in host and not host.endswith((":443", ":80")):
        risk += 15
        reasons.append(f"🚪 Unusual port ({host.split(':')[-1]}) — normal websites do not use this.")

    # --- D) lure words + brand combos ---
    low = (host_no_port + path_q).lower()
    hit_words = [w for w in LURE_WORDS if w in low]
    if hit_words:
        add = min(30, sum(LURE_WORDS[w] for w in hit_words))
        risk += add
        reasons.append("🎣 Suspicious words found: " + ", ".join(hit_words[:6]))
    brand_hit = [b for b in BRANDS if b in low]
    # Brand + free hosting/other domain me = impersonation
    if brand_hit and not any(host_no_port.endswith(b + ".com") or host_no_port == b + ".com"
                             or host_no_port.endswith(b + ".in") or host_no_port == b + ".in" for b in brand_hit):
        risk += 22
        reasons.append("🏦 Brand name used but not the official domain: " + ", ".join(brand_hit[:4]) +
                       f" (asli site {brand_hit[0]}.com/.in expected)")
    if any(x in host_no_port for x in ("vercel.app", "netlify.app", "pages.dev", "workers.dev", "web.app",
                                       "firebaseapp.com", "duckdns.org", "myftp.org", "000webhostapp.com",
                                       "github.io", "glitch.me", "repl.co", "blogspot.")) and (hit_words or brand_hit):
        risk += 12
        reasons.append("🆓 Free hosting domain par bank/login jaisa page — scam ka common joda.")

    # --- E) OpenPhish live feed ---
    _load_openphish()
    if _PHISH_CACHE["urls"]:
        if target in _PHISH_CACHE["urls"] or any(u.startswith(target) for u in _PHISH_CACHE["urls"] if len(u) > 20):
            risk += 60
            reasons.append("🚨 Ye link OpenPhish ke LIVE phishing feed me hai (pakka scam).")
        elif host_no_port in _PHISH_CACHE["hosts"]:
            risk += 50
            reasons.append("🚨 This domain name is in the OpenPhish live phishing feed.")
    signals["openphish_size"] = len(_PHISH_CACHE["urls"])

    # --- F) urlscan.io reputation ---
    scans = _urlscan_reputation(host_no_port) if host_no_port else -1
    signals["urlscan_scans"] = scans
    if scans == 0:
        reasons.append("🆕 Ye domain urlscan.io par kabhi scan nahi hua (naya / kam jaana-mana).")

    # --- G) length / entropy signals ---
    if len(target) > 120:
        risk += 8
        reasons.append("📏 The link is very long (tracking/obfuscation).")
    if re.search(r"(login|verify|kyc|otp|bank|update)[-_]?(page|form|verify|secure|account)", low):
        risk += 15
        reasons.append("📋 The URL path has a 'fake login page' pattern.")

    risk = max(0, min(100, risk))
    if risk >= 60:
        verdict, level, advice = "DANGEROUS 🚨", "danger", ("Ye link KABHI na kholo aur na forward karo. Kisi bhi link par OTP, password ya UPI PIN kabhi na dalo." 
                                                           "Never enter an OTP, password or UPI PIN on any link.")
    elif risk >= 25:
        verdict, level, advice = "SUSPICIOUS ⚠️", "suspicious", ("Sambhal ke — site pata ho tabhi kholo. Login ya payment details na dalo."
                                                                  "Do not enter login or payment details.")
    elif risk > 0:
        verdict, level, advice = "LOW RISK ✅", "low", "Only minor signals. Normal browsing is fine."
    else:
        verdict, level, advice = "SAFE ✅", "safe", "No suspicious signal found. Still, never share an OTP or PIN."

    if not reasons:
        reasons.append("✅ No redirect, IP, punycode, lure-word or phishing-feed match found.")
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


# =====================================================================================
# 5) EMI flexible input parser
# =====================================================================================


# =====================================================================================
# 6) GAON WALA VYAAJ (Compound only) — Bihar/UP ka chakravriddhi byaaj system
# =====================================================================================
def rate_from_per_hundred(per_hundred: float) -> float:
    """'₹100 par ₹5 mahina' ko monthly % me badalta hai (5 -> 5%)."""
    try:
        return round(float(per_hundred), 4)
    except Exception:
        return 0.0


def _add_months(d, months: int):
    """Date me mahine jodta hai (31 Jan + 1 month = 28/29 Feb — safe)."""
    y, m = divmod((d.month - 1) + months, 12)
    new_y, new_m = d.year + y, m + 1
    import calendar
    last_day = calendar.monthrange(new_y, new_m)[1]
    return d.replace(year=new_y, month=new_m, day=min(d.day, last_day))


def village_compound_interest(principal: float, monthly_rate_pct: float, months: int) -> dict:
    """
    CHAKRAVRIDDHI (compound) byaaj — jaisa gaon/kasbe me vyaaj lene wale ka hisaab hota hai:
    jo byaaj har mahine nahi diya jata, wo principal me jud kar agle mahine byaaj bhi deta hai.

    principal        : jitna paisa liya (₹)
    monthly_rate_pct : mahine ka byaaj % (₹100 par ₹5 = 5)
    months           : kitne mahine ka hisaab
    """
    months = max(1, int(months))
    r = max(0.0, float(monthly_rate_pct)) / 100.0

    rows = []
    balance = float(principal)
    total_interest = 0.0
    for m in range(1, months + 1):
        interest = balance * r                      # is mahine ka byaaj
        balance = balance + interest                # byaaj principal me jud gaya
        total_interest += interest
        rows.append({
            "month": m,
            "opening": balance - interest,
            "interest": interest,
            "closing": balance,
        })

    # Milestones (jaldi samajh aane ke liye)
    def at(m):
        return rows[m - 1]["closing"] if 0 < m <= len(rows) else None

    return {
        "ok": True,
        "principal": float(principal),
        "monthly_rate": float(monthly_rate_pct),
        "months": months,
        "per_hundred_note": f"₹{monthly_rate_pct:g} per ₹100 every month",
        "first_month_interest": rows[0]["interest"] if rows else 0.0,
        "total_interest": total_interest,
        "total_payable": principal + total_interest,
        "double_amount": principal * 2,
        "rows": rows,
        "milestones": {k: v for k, v in {
            "6 months": at(6) if months >= 6 else None,
            "12 months": at(12) if months >= 12 else None,
            "24 months": at(24) if months >= 24 else None,
            "36 months": at(36) if months >= 36 else None,
        }.items() if v is not None},
    }


# =====================================================================================
# 7) EMI FULL REPORT — "kitne mahine / kitne din me poora chukega"
# =====================================================================================


# =====================================================================================
# 8) Helpers
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
