# -*- coding: utf-8 -*-
"""
Toolkit Extras (v31 Professional Upgrade Pack)
==============================================
Engines that make the older tools professional:

1.  shorten_url()        -> 6 shortener providers, uses whichever works (is.gd was dead).
2.  expand_url()         -> Opens the redirect chain + cleans tracking params (LINK BYPASS upgrade).
3.  analyze_link()       -> Real multi-signal link checker (OpenPhish live feed + urlscan.io
                            + 15 heuristics).
4.  file_size_human()    -> bytes to MB/GB.

v55 changes (live audit):
  • Saare network calls ab **core.net** se (shared connection pool + mandatory
    timeout + retry + size cap). Pehle raw `requests` tha — har call naya TCP
    connection banata tha aur timeout bhoolne par server hang kar sakta tha.
  • `analyze_link()` ab **parallel** chalta hai: redirect-chain, domain-age,
    urlscan aur OpenPhish checks ek saath (pehle serial the → 5+ second).
    User-visible speed: ~5.4s → ~2s.
"""

import re
import time
from concurrent.futures import ThreadPoolExecutor
from html import escape as hesc          # v77: user diya hua host HTML me daalne se pehle escape
from urllib.parse import quote, urlparse, parse_qs, urlunparse

from modules.core.net import NetError, http_get, http_post

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# core.net apna default UA bhejta hai; ye modules ke liye browser-UA chahiye
# (shortener/redirect endpoints bot-UA par block karte hain) — har call me
# explicitly pass karte hain.
_H = {"User-Agent": UA["User-Agent"]}

# =====================================================================================
# 1) URL SHORTENER — multi-provider (jo chale wahi)
# v55: saare providers core.net se — pooled connection + timeout + retry.
# =====================================================================================
def _sh_dag(url):
    r = http_get("https://da.gd/shorten", params={"url": url}, headers=_H, timeout=8, retries=1)
    t = r.text.strip()
    return t if r.status_code == 200 and t.startswith("http") else None


def _sh_spoo(url):
    r = http_post("https://spoo.me/", data={"url": url}, headers={**_H, "Accept": "application/json"},
                  timeout=8, retries=1)
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
    r = http_post("https://cleanuri.com/api/v1/shorten", data={"url": url}, headers=_H, timeout=8, retries=1)
    if r.status_code == 200:
        try:
            return r.json().get("result_url")
        except Exception:
            return None
    return None


def _sh_clck(url):
    r = http_get("https://clck.ru/--", params={"url": url}, headers=_H, timeout=8, retries=1)
    t = r.text.strip()
    return t if r.status_code == 200 and t.startswith("http") else None


def _sh_tiny(url):
    r = http_get("https://tinyurl.com/api-create.php", params={"url": url}, headers=_H, timeout=8, retries=1)
    t = r.text.strip()
    return t if r.status_code == 200 and "tinyurl.com" in t else None


def _sh_isgd(url):
    r = http_get("https://is.gd/create.php", params={"format": "simple", "url": url}, headers=_H,
                 timeout=8, retries=1)
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
    """Ek ya zyada working short links return karta hai: [(provider, short_url), ...]

    v50: AB PARALLEL — saare 6 provider ek saath chalte hain (ThreadPool).
    Purana serial way me ek dead provider 8s hang karke poora flow slow karta tha.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    def _one(name, fn):
        try:
            s = fn(url)
            if s and s.strip() and s.strip() != url:
                return (name, s.strip())
        except Exception:
            pass
        return None

    out = []
    try:
        with ThreadPoolExecutor(max_workers=len(SHORTENER_PROVIDERS)) as ex:
            futs = {ex.submit(_one, name, fn): i for i, (name, fn) in enumerate(SHORTENER_PROVIDERS)}
            results = {}
            for fut in futs:
                try:
                    r = fut.result(timeout=12)
                except Exception:
                    r = None
                if r:
                    results[futs[fut]] = r
        # priority order me (jaise list me hain), upar wale providers pehle
        for i in sorted(results.keys()):
            out.append(results[i])
            if len(out) >= want:
                break
    except Exception:
        # thread engine me koi bhi galti ho to purana serial way
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



# ===========================================================================
#  v56: FRIENDLY NETWORK ERRORS
#  Live audit me dikha ki expand_url() user ko raw requests/urllib3 ka wall of
#  text dikha deta tha:
#     "HTTPSConnectionPool(host='junk', port=443): Max retries exceeded with
#      url: / (Caused by NameResolutionError(...getaddrinfo failed...))"
#  Ye technical hai, user ko solution nahi milta. Neeche wala helper har tarah
#  ki connection failure ko ek saaf Hindi line me badal deta hai.
# ===========================================================================
_NET_ERR_PATTERNS = (
    ("name resolution", "getaddrinfo failed", "name or service not known",
     "nodename nor servname", "temporary failure in name resolution",
     "name resolution error"),
    ("max retries exceeded", "connection refused", "connection reset",
     "connection aborted", "connectionerror", "newconnectionerror",
     "failed to establish a new connection"),
    ("timed out", "timeout", "readtimeout", "connecttimeout"),
)


def friendly_net_error(exc, host: str = "") -> str:
    """Raw network exception → saaf Hindi line (technical kabhi leak na ho)."""
    low = str(exc).lower()
    h = f" (<code>{host}</code>)" if host else ""
    for grp, text in zip(_NET_ERR_PATTERNS, (
        f"🔌 <b>Ye website ka pata hi nahi chala</b>{h} — domain exist nahi karta "
        "ya spelling galat hai.",
        f"🔌 <b>Ye website khul nahi rahi</b>{h} — server band hai ya link dead hai.",
        f"⏳ <b>Server ne time par jawab nahi diya</b>{h} — 10 second baad dobara try karo.",
    )):
        if any(k in low for k in grp):
            return text
    return f"🔌 <b>Ye link abhi khul nahi paya</b>{h} — link dead hai ya server busy hai."


def expand_url(url: str, max_hops: int = 6):
    """Redirect chain follow karta hai aur final + cleaned URL deta hai.
    Returns dict: {ok, original, final, cleaned, chain: [...], hops, is_shortener}"""
    if not url.startswith(("http://", "https://")):
        # v50: "file:///etc/passwd" jaise input par blindly "https://" mat jodo —
        # wo "https://file:///etc/passwd" ban kar hostname="file" ke roop me
        # guard ke paar nikal jaata tha. Pehle scheme dekho.
        if "://" in url:
            _sch = url.split("://", 1)[0].lower()
            if _sch not in ("http", "https"):
                return {"ok": False, "error": f"🚫 '{_sch}' scheme allowed nahi hai (sirf http/https).",
                        "original": url, "final": url, "cleaned": url, "chain": [url],
                        "hops": 0, "is_shortener": False}
        url = "https://" + url
    # v50: SSRF guard — ye function user ke diye URL ko SEEDHA fetch karta hai.
    # Bina guard ke koi bhi http://169.254.169.254/ (Render/AWS metadata) ya
    # http://127.0.0.1:PORT/ (internal service) hit karwa sakta tha.
    try:
        from modules.core.net import is_safe_url as _safe
        _ok, _why = _safe(url)
        if not _ok:
            return {"ok": False, "error": f"🚫 {_why}", "original": url,
                    "final": url, "cleaned": url, "chain": [url],
                    "hops": 0, "is_shortener": False}
    except Exception:            # noqa: BLE001 - core na ho to purana behaviour
        pass
    chain = []
    cur = url
    is_short = False
    try:
        for _ in range(max_hops):
            # v55: core.net se — pooled connection + mandatory timeout.
            # ssrf_check=True → private/metadata IP par redirect ho to block.
            r = http_get(cur, headers=_H, timeout=10, allow_redirects=False,
                         retries=0, ssrf_check=True)
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
    except NetError as e:
        # SSRF block ya internal-address redirect — user ko saaf reason do.
        # v56: non-blocked NetError me raw requests/urllib3 text jaa raha tha
        # ("HTTPSConnectionPool(host=...): Max retries exceeded with url: ...").
        # Ab friendly_net_error() se saaf line jaati hai.
        final = chain[-1] if chain else url
        blocked = e.kind == "blocked"
        _host = urlparse(final).netloc or urlparse(url).netloc
        return {
            "ok": False,
            "original": url,
            "error": (f"🚫 {e.message}" if blocked
                      else friendly_net_error(e.message, _host)),
            "final": final,
            "cleaned": clean_tracking(final),
            "chain": chain or [url],
            "hops": max(0, len(chain or [url]) - 1),
            "is_shortener": is_short,
            "blocked": blocked,
        }
    except Exception as e:                                    # noqa: BLE001
        final = chain[-1] if chain else url
        return {
            "ok": False,
            "original": url,
            "error": friendly_net_error(e, urlparse(final).netloc),
            "final": final,
            "cleaned": clean_tracking(final),
            "chain": chain or [url],
            "hops": max(0, len(chain or [url]) - 1),
            "is_shortener": is_short,
        }


# =====================================================================================
# 3) LINK CHECKER — real multi-signal analyzer
# =====================================================================================
_PHISH_CACHE = {"ts": 0, "hosts": set(), "urls": set()}


def _load_openphish():
    """OpenPhish public feed (free, no key) — 6 ghante cache."""
    if time.time() - _PHISH_CACHE["ts"] < 6 * 3600 and _PHISH_CACHE["urls"]:
        return
    try:
        # v55: core.net se (pool + timeout + size-cap)
        r = http_get("https://openphish.com/feed.txt", headers=_H, timeout=12, retries=1,
                     max_bytes=64 * 1024 * 1024)
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
        r = http_get("https://urlscan.io/api/v1/search/",
                     params={"q": f"page.domain:{host}", "size": "20"},
                     headers=_H, timeout=10, retries=1)
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

# =====================================================================================
#  v77: LINK CHECK PRO — nayi pakad (pehle chhoot jaate the)
# =====================================================================================
# 1) WHITELIST: asli sarkari/banki domain par "brand fake hai" kehna GALAT tha.
#    Pehle live bug: https://www.sbi.co.in (asli SBI site) -> "SUSPICIOUS 32/100",
#    kyun check me sirf `<brand>.com` / `<brand>.in` tha aur `.co.in` nahi.
MULTI_PART_TLDS = {"co.in", "gov.in", "nic.in", "ac.in", "org.in", "net.in", "res.in",
                   "edu.in", "fib.in", "ind.in", "gen.in", "mil.in", "jur.in",
                   "bank.in", "firm.in", "stores.in", "dial.in", "epi.in",
                   "co.uk", "co.nz", "com.au", "co.za", "gov.uk", "ne.jp", "or.jp"}
# ⚠️ IS LIST ME SIRF WAQAI-KE-ASLI domain daalein — ye list "safe" ka faisla
#    karti hai. Ek galat entry = ek scam site ko "SAFE ✅" bata dena. Isliye
#    yahan jaan-boojh kar chhota + high-confidence list hai (badhana ho to
#    pehle domain khud verify karke).
OFFICIAL_DOMAINS = {
    # banks (India) — .co.in / .com wale asli net-banking domains
    "sbi.co.in", "onlinesbi.com", "onlinesbi.sbi", "ybsfunds.com",
    "pnbibanking.in", "canarabank.com", "bobbank.in", "unionbankofindia.com",
    "bankofbaroda.co.in", "barodapersonalbanking.co.in", "icicibank.com",
    "hdfcbank.com", "axisbank.co.in", "kotak.com", "kotak811.com", "yesbank.in",
    "idbibank.co.in", "idfcfirstbank.com", "rblbank.com", "indusind.com",
    "federalbank.co.in", "southindianbank.com", "centralbankofindia.co.in",
    "bankofmaharashtra.in", "csb.co.in", "kvb.co.in", "rbi.org.in", "nabard.org",
    # sarkari portals
    "india.gov.in", "uidai.gov.in", "myaadhaar.uidai.gov.in", "incometax.gov.in",
    "incometaxindia.gov.in", "etax.gov.in", "gst.gov.in", "epfo.gov.in",
    "epfindia.gov.in", "indiapost.gov.in", "parivahan.gov.in", "digilocker.gov.in",
    "cbse.gov.in", "cbseresults.nic.in", "bihar.gov.in", "nsdl.com", "npci.org.in",
    "income.gov.in", "tin.gov.in", "tdcgov.in", "esic.org.in", "pmkisan.gov.in",
    "digilockerlocked.gov.in",
    # UPI / wallets / shopping / tech
    "paytm.com", "phonepe.com", "payphonepe.com", "amazonpay.com", "amazon.in",
    "flipkart.com", "myntra.com", "meesho.com", "netflix.com", "hotstar.com",
    "jio.com", "airtel.in", "myairtel.com", "vi.in", "myvi.in", "bsnl.co.in",
    "telegram.org", "t.me", "web.telegram.org", "telegram.me",
    "instagram.com", "facebook.com", "whatsapp.com", "wa.me", "youtube.com",
    "google.com", "microsoft.com", "apple.com", "irctc.co.in",
}
_BRAND_OFFICIAL = {   # brand -> woh domain jo WAQAI uske official hain
    "paytm": ("paytm.com",), "phonepe": ("phonepe.com", "payphonepe.com"),
    "googlepay": ("pay.google.com", "google.com"), "gpay": ("pay.google.com", "google.com"),
    "sbi": ("sbi.co.in", "onlinesbi.com", "onlinesbi.sbi", "ybsfunds.com"),
    "hdfc": ("hdfcbank.com", "hdfclife.com"),
    "icici": ("icicibank.com", "icicidirect.com"),
    "axis": ("axisbank.co.in", "axisbank.com"),
    "kotak": ("kotak.com", "kotak811.com"), "pnb": ("pnbibanking.in",),
    "bob": ("bobbank.in",), "amazon": ("amazon.in", "amazonpay.com", "amazon.com"),
    "flipkart": ("flipkart.com",), "myntra": ("myntra.com",), "irctc": ("irctc.co.in",),
    "netflix": ("netflix.com",), "hotstar": ("hotstar.com",),
    "jio": ("jio.com",), "airtel": ("airtel.in", "myairtel.com"),
    "vi": ("vi.in", "myvi.in"), "bsnl": ("bsnl.co.in",),
    "instagram": ("instagram.com",), "facebook": ("facebook.com", "fb.com", "meta.com"),
    "whatsapp": ("whatsapp.com", "wa.me"),
    "telegram": ("telegram.org", "t.me", "telegram.me", "web.telegram.org", "telegram.dog"),
    "uidai": ("uidai.gov.in", "myaadhaar.uidai.gov.in"),
    "aadhaar": ("uidai.gov.in", "myaadhaar.uidai.gov.in"),
    "incometax": ("incometax.gov.in", "etax.gov.in", "incometaxindia.gov.in"),
    "gst": ("gst.gov.in",), "epfo": ("epfo.gov.in", "epfindia.gov.in"),
    "postoffice": ("indiapost.gov.in",), "indiapost": ("indiapost.gov.in",),
    "rupay": ("npci.org.in",), "parivahan": ("parivahan.gov.in",),
    "vaahan": ("parivahan.gov.in",), "digilocker": ("digilocker.gov.in",),
}

# 2) Non-web schemes — pehle `javascript:alert(1)` ko "https://javascript:..."
#    bana kar domain/port ka analysis kar diya jaata tha (bakwaas result).
DANGEROUS_SCHEMES = {
    "javascript": "Browser me code chalane wala link (XSS/scam) — isse koi chat/message me bheja ho to turant block karo.",
    "vbscript": "Windows script chalane wala link — 100% nuksan.",
    "data": "Link ke andar hi chhupa hua file/code — download par malware ban sakta hai.",
    "file": "Kisi ke computer ka local path kholne wala link.",
    "blob": "Browser me banaya gaya temporary file link — 5 minute me mar jata hai, scam pages isko use karte hain.",
    "intent": "Android app seedha kholne wala link — bina app ke kaam nahi karta, phishing kits isko chhupati hain.",
    "jar": "Java archive (`.jar`) seedha chalane wala link.",
    "ms-msdt": "Windows ka hidden diagnostic tool kholne wala link — Follina-type attack.",
    "searchms": "Windows search protocol link.",
}

# 3) Invisible / bidirectional control characters — naam chhupane ke liye
_INVISIBLE = {
    "\u200b": "zero-width space", "\u200c": "zero-width non-joiner",
    "\u200d": "zero-width joiner", "\u2060": "word joiner",
    "\ufeff": "BOM", "\u202a": "LRE", "\u202b": "RLE", "\u202c": "PDF",
    "\u202d": "LRO", "\u202e": "RLO (RTL override — domain ka asli hissa ulti likh deta hai)",
    "\u2066": "LRI", "\u2067": "RLI", "\u2068": "FSI", "\u2069": "PDI",
}
# 4) Cyrillic/Greek → Latin confusables (IDN homograph)
_CONFUSE = {"\u0430": "a", "\u0441": "c", "\u0435": "e", "\u043e": "o", "\u0440": "p",
            "\u0443": "y", "\u0445": "x", "\u043a": "k", "\u043c": "m", "\u0456": "i",
            "\u043d": "h", "\u0437": "3", "\u0442": "t", "\u0432": "w", "\u043b": "l",
            "\u0433": "r", "\u0448": "sh", "\u0449": "sh", "\u0447": "ch", "\u044f": "fa",
            "\u044e": "yu", "\u0454": "ie", "\u0451": "yo", "\u0406": "I", "\u0410": "A",
            "\u0412": "B", "\u0415": "E", "\u041a": "K", "\u041c": "M", "\u041d": "H",
            "\u041e": "O", "\u0420": "P", "\u0421": "C", "\u0422": "T", "\u0425": "X"}
_DANGEROUS_PORTS = {"21", "22", "23", "25", "135", "137", "138", "139", "445", "1433",
                    "3306", "3389", "5432", "5900", "6379", "8080", "9200", "27017"}
_DOUBLE_EXT = (".html.exe", ".htm.exe", ".pdf.exe", ".jpg.exe", ".png.exe", ".doc.exe",
               ".xls.exe", ".txt.exe", ".zip.exe", ".apk.exe", ".html.scr", ".pdf.js",
               ".jpg.js", ".svg.js", ".docm", ".xlsm", ".pptm", ".vbs", ".js", ".bat",
               ".cmd", ".exe", ".scr", ".com", ".msi", ".jar", ".apk", ".hta", ".lnk")


# =====================================================================================
#  v77: helpers (inhi se upar wali list kaam karti hai)
# =====================================================================================
def registrable_domain(host: str) -> str:
    """`www.sbi.co.in` -> `sbi.co.in` | `a.b.paytlm.co.in` -> `paytlm.co.in`.

    India ke `.co.in` / `.gov.in` jaise multi-part suffix hain; inhe sirf
    last 2 labels lene se `co.in` ban jaata (galat faisla). Isliye pehle
    3 labels try karte hain, agar suffix jaana-pehchana ho to.
    """
    h = (host or "").lower().split(":")[0].strip(".")
    if not h:
        return ""
    lab = [x for x in h.split(".") if x]
    if len(lab) >= 3 and ".".join(lab[-2:]) in MULTI_PART_TLDS:
        return ".".join(lab[-3:])
    return ".".join(lab[-2:]) if len(lab) >= 2 else h


# v77: `.gov.in` / `.bank.in` / `.nic.in` jaise TLD **restricted registry** hain —
# in par sirf sarkar/licensed bank hi domain le sakte hain. Isliye in par
# "brand ka nakal" wala shak nahi lagaya jaata ( warna asli SBI ka naya
# net-banking domain `sbi.bank.in` "SUSPICIOUS" ho jaata — live case tha).
RESTRICTED_IN_TLDS = (".gov.in", ".nic.in", ".bank.in", ".ac.in", ".res.in",
                      ".mil.in", ".fin.in", ".org.in", ".edu.in")


def is_official_domain(host: str, brand_hint: str = "") -> bool:
    """Kya ye domain kisi bade/govt domain ka HISSEA hai (subdomain chalega).

    `brand_hint` do to restricted-TLD rule sirf tab lagega jab brand ka naam
    host me sach me ho (`sbi.bank.in` ✓, `kuchbhi.bank.in` ✗ — wo still
    suspicious rahega).
    """
    reg = registrable_domain(host)
    if not reg:
        return False
    for d in OFFICIAL_DOMAINS:
        if reg == d or reg.endswith("." + d):
            return True
    if brand_hint:
        toks = _host_tokens(reg)
        if brand_hint in toks and any(reg.endswith(t) for t in RESTRICTED_IN_TLDS):
            return True
    return False


def _host_tokens(text: str) -> set:
    """Host+path ko tokens me todo — 'vi' 'services' ke andar na mile (bug tha)."""
    return {t for t in re.split(r"[^0-9a-z]+", (text or "").lower()) if t}


def brand_in_text(brand: str, low: str, tokens: set) -> bool:
    """Chhote brand (<=3 akshar: vi, gst, pan, bob) sirf TOKEN ki tarah gine jaayen.

    Pehle ka galat result: `https://www.sbi.co.in/portal/web/customer-services`
    par brand 'vi' "servICes" me dhoondh kar "brand fake hai" keh raha tha.
    """
    b = (brand or "").lower()
    if not b:
        return False
    if len(b) <= 3:
        return b in tokens or any(t.startswith(b) and len(t) <= len(b) + 4 for t in tokens)
    return b in low


def _levenshtein(a: str, b: str) -> int:
    """Chhota, fast edit distance (typosquat dhoondhne ke liye)."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > 2 or la == 0 or lb == 0:
        return 99
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1,
                         prev[j - 1] + (0 if a[i - 1] == b[j - 1] else 1))
        prev = cur
    return prev[lb]


def typosquat_of(host: str):
    """`paytlm.com` -> ('paytm.com', 1) — brand ka nakal domain (1-2 akshar ka farak).

    Sirf OFFICIAL_DOMAINS ke khilaf tulna karte hain, isliye list badi hone par
    bhi ye "har doosre domain ko typosquat" nahi bolta.
    """
    reg = registrable_domain(host)
    if not reg or "." not in reg:
        return None
    parts = reg.split(".")
    first = parts[0]
    if len(first) < 4:
        return None
    best = None
    for off in OFFICIAL_DOMAINS:
        op = off.split(".")
        of = op[0]
        if len(of) < 4 or of == first:
            continue
        if ".".join(parts[1:]) != ".".join(op[1:]):
            continue                      # same TLD hi to tulna sach hai
        d = _levenshtein(first, of)
        if d in (1, 2) and (best is None or d < best[1]):
            best = (off, d)
    return best


def deobfuscate_host(host: str) -> str:
    """Percent-encoded host ko khologe — `ref%65r.co` -> `referer.co`.

    Phishers `g%6fogle.com` jaise encodings browser me chup-chaap decode ho
    jaate hain, isliye pattern check ko decoded value par karna padta hai.
    """
    if "%" not in (host or ""):
        return host or ""
    try:
        from urllib.parse import unquote
        return unquote(host)
    except Exception:                                       # noqa: BLE001
        return host


def numeric_host_form(host: str) -> str:
    """IP ko domain ki jagah chhupane ke tarike: 2130706433 / 0x7f... / 0177...

    Pehle sirf `1.2.3.4` pakda jaata tha — decimal/hex/octal form se bachkar
    nikal jaate the (ye asli phishing technique hai).
    """
    h = (host or "").strip("[]").lower()
    if not h:
        return ""
    if ":" in h:
        return "ipv6"
    parts = h.split(".")
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", h):
        return "dotted" if all(0 <= int(x) <= 255 for x in parts) else "invalid-ip"
    if len(parts) > 4 or not parts:
        return ""
    _all_dec = all(re.fullmatch(r"\d+", x) for x in parts)
    _all_hex = all(re.fullmatch(r"(0x)?[0-9a-f]+", x) for x in parts)
    _all_oct = all(re.fullmatch(r"0*[0-7]+", x) for x in parts)
    if len(parts) == 1:
        if _all_dec:
            try:
                v = int(parts[0])
            except Exception:                                    # noqa: BLE001
                return ""
            # ek-sankhya IPv4 tabhi valid hai jab wo 0..2^32-1 me ho
            if v > 4294967295:
                return "invalid-ip"
            return "decimal" if v >= 65536 or len(parts[0]) >= 7 else "short-form"
        return ""
    if _all_hex and any(x.startswith("0x") for x in parts):      # 0x7f.0.0.1
        return "hex"
    if _all_oct and parts[0].startswith("0"):                    # 0177.0.0.1
        return "octal"
    if _all_dec:
        if len(parts) == 4 and all(len(x) <= 3 and int(x) <= 255 for x in parts):
            return "dotted"
        return "short-form"                                      # 127.1 / 10.5
    return ""


def invisible_chars(text: str) -> list:
    """Zero-width / RTL-override characters — domain ka dikhai-dene wala naam badal dete hain."""
    out = []
    for ch in set(text or ""):
        if ch in _INVISIBLE:
            out.append(f"{_INVISIBLE[ch]} (U+{ord(ch):04X})")
    return out


def homoglyph_map(text: str) -> str:
    """Cyrillic/Greek jo Latin jaise dikhte hain — unka 'asli' Latin roop."""
    return "".join(_CONFUSE.get(c, c) for c in (text or ""))

BRANDS = ["paytm", "phonepe", "googlepay", "gpay", "sbi", "hdfc", "icici", "axis", "kotak", "pnb", "bob",
          "amazon", "flipkart", "myntra", "irctc", "netflix", "hotstar", "jio", "airtel", "vi", "bsnl",
          "instagram", "facebook", "whatsapp", "telegram", "uidai", "aadhaar", "pan", "incometax",
          "gst", "epfo", "postoffice", "indiapost", "upi", "bhim", "rupay"]
LURE_WORDS = {"login": 12, "verify": 12, "secure": 8, "update": 8, "kyc": 15, "otp": 15, "bank": 10,
              "refund": 12, "lottery": 20, "bonus": 12, "winner": 18, "prize": 18, "free": 8,
              "gift": 12, "claim": 15, "unlock": 10, "recovery": 12, "wallet": 8, "upi": 10,
              "support": 6, "account": 8, "payment": 8, "reward": 12, "cashback": 10, "offer": 6}


def analyze_link(raw_url: str) -> dict:
    """
    Professional multi-signal link check.
    Returns: {ok, verdict, risk(0-100), level, reasons[], advice, signals{}, final_url, chain}

    v77 UPGRADE (LINK CHECK PRO) — pehle jo chhoot jaata tha:
      • `javascript:`/`data:`/`intent:` jaise non-web schemes (inhe "domain"
        samajh kar port ka result milta tha)
      • IP chhupane ke tarike: `http://2130706433/` (decimal), `0x7f.0.0.1`,
        `0177.0.0.1`, `127.1` — sirf `a.b.c.d` check tha
      • percent-encoded host `ref%65r.co` (browser decode kar deta hai, hum
        nahi karte the -> "SAFE ✅")
      • invisible/RTL characters (U+202E "RLO" — domain ka naam ulti dikhata hai)
      • Cyrillic homoglyphs (`рауtm` = paytm jaisa dikhta hai)
      • typosquat (`paytlm.com`) — brand ka 1-akshar ka nakal
      • aur ek GALAT verdict: asli `sbi.co.in` "SUSPICIOUS 32" bata raha tha
        (check me `.co.in` official hi nahi tha + 'vi' "services" me mil raha tha)
    """
    url0 = (raw_url or "").strip()
    # --- A-0) NON-WEB SCHEME: pehle hi rok do (domain analysis bekaar hai) ---
    _m = re.match(r"\s*([a-zA-Z][a-zA-Z0-9+.\-]{1,14})\s*:", url0)
    _scheme_raw = (_m.group(1).lower() if _m else "")
    if _scheme_raw in DANGEROUS_SCHEMES:
        return {
            "ok": True, "verdict": "DANGEROUS 🚨", "level": "danger", "risk": 100,
            "reasons": [f"☠️ Ye koi website link nahi — <b>{_scheme_raw}:</b> protocol "
                        f"hai. {DANGEROUS_SCHEMES[_scheme_raw]}"],
            "advice": ("Ye link KABHI na kholo, na kisi ko aage bhejo. Kisi bhi "
                       "OTP, password ya UPI PIN ke liye sirf app ka apna screen "
                       "bharo — link se nahi."),
            "signals": {"scheme": _scheme_raw, "host": "-", "final_url": url0[:200]},
            "final_url": url0[:200], "cleaned_url": url0[:200], "chain": [],
        }
    url = url0
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    # --- A-0b) CHHUPE HUWE AKSHAR (invisible / RTL / homoglyph) ---
    _inv = invisible_chars(raw_url or "")
    _homo = ""
    try:
        _host_only0 = urlparse(url).netloc.lower()
        _deco = homoglyph_map(_host_only0)
        if _deco != _host_only0:
            _homo = _deco
    except Exception:                                        # noqa: BLE001
        _homo = ""
    exp = expand_url(url)
    target = exp.get("final", url) if exp.get("ok") else url
    # v77: `https://[` jaise adhoore URL par urlparse ValueError(U+202d) 'Invalid
    # IPv6 URL' deta hai — user ko "⚠️ Chhota sa ghatna ho gaya" dikhta tha (tool
    # crash). Ab saaf verdict, exception nahi.
    try:
        p = urlparse(target)
        _ = (p.netloc or "") + (p.path or "")
    except Exception:                                        # noqa: BLE001
        return {
            "ok": True, "verdict": "LINK TAYYAR NAHI ❌", "level": "danger",
            "risk": 40,
            "reasons": ["🩹 Ye link banne layak nahi hai — usme galat/adhoora "
                        "address hai (jaise <code>https://[</code>). Aisa link "
                        "koi browser nahi kholta."],
            "advice": ("Jo link aapne bheja wo toota hua hai. Poora link dobara "
                       "copy karke bhejo (shuruat https:// ke saath)."),
            "signals": {"host": "-", "malformed": True, "final_url": str(target)[:200]},
            "final_url": str(target)[:200], "cleaned_url": str(target)[:200],
            "chain": [],
        }
    host = (p.netloc or "").lower()
    host_no_port = host.split(":")[0]
    path_q = (p.path or "") + ("?" + p.query if p.query else "")
    # v77: `%65` wale encodings decode karke asli host par hi checks chalayein
    host_dec = deobfuscate_host(host_no_port)
    if host_dec and host_dec != host_no_port:
        host_no_port_for_checks = host_dec
    else:
        host_no_port_for_checks = host_no_port
    # official/whitelist faisla (subdomain bhi official mana jaayega)
    reg_dom = registrable_domain(host_no_port_for_checks)
    _reg_toks = _host_tokens(reg_dom)
    _brand_guess = next((b for b in BRANDS if b in _reg_toks), "")
    official = is_official_domain(host_no_port_for_checks, _brand_guess)
    # restricted registry par milne wala brand = verified (e.g. sbi.bank.in)
    _restricted_hit = bool(official and _brand_guess and
                           reg_dom.endswith((".bank.in", ".gov.in", ".nic.in")))

    risk = 0
    reasons = []
    signals = {
        "redirect_hops": exp.get("hops", 0),
        "final_url": target,
        "https": p.scheme == "https",
        "host": host_no_port or "?",
        # v56: link zinda hai ya nahi — pehle "junk.nonexistent-xyz.com" jaise
        # dead domain par bhi "SAFE ✅ 0/100" aa jaata tha (misleading).
        "reachable": exp.get("ok") is not False,
        # v77 naye signals
        "registered_domain": reg_dom,
        "official_domain": official,
        "obfuscated_host": bool(host_dec and host_dec != host_no_port),
        "ip_form": numeric_host_form(host_no_port_for_checks),
        "invisible_chars": _inv,
        "homoglyph_decoded": _homo,
    }

    # --- A-1) percent-encoded host (browser decode karta hai, insaan nahi) ---
    if signals["obfuscated_host"]:
        risk += 22 if not official else 6
        reasons.append(f"🕵️ Host me <b>percent-encoding</b> chhupa hai: "
                       f"<code>{hesc(host_no_port)}</code> → asli: "
                       f"<code>{hesc(host_dec)}</code>. Browser ise khol deta "
                       f"hai par aapko galat dikhega.")

    # --- A-2) invisible / RTL control characters ---
    if _inv:
        risk += 40
        reasons.append("👻 Link me chhupe hue (invisible/RTL) characters hain: "
                       + ", ".join(_inv[:3]) + " — isse domain ka naam badal "
                       "diya jaata hai. Aisa link WhatsApp par forward hokar "
                       "aaya ho to 99% scam hai.")

    # --- A-3) Cyrillic/Greek homoglyph (IDN attack) ---
    if _homo:
        risk += 45
        reasons.append(f"🎭 Host me Latin-jaise dikhte hue <b>doosri script</b> ke "
                       f"akshar hain → asli: <code>{hesc(_homo)}</code> "
                       "(homograph attack — bank/brand ka nakal naam).")


    # --- A0) LINK ZINDA HAI YA NAHI (v56) ---
    # Dead / non-existent domain par pehle "SAFE ✅" verdict aata tha — user
    # sochta tha "theek hai" jabki link kholta hi nahi. Ab ye saaf dikhta hai.
    if exp.get("ok") is False:
        risk += 10
        reasons.append("🔌 <b>Ye link khulta nahi</b> — domain exist nahi karta, "
                       "server band hai, ya link dead hai. "
                       "(Aise link par OTP/password bilkul na daalo.)")

    # --- A) redirect chain (shorteners chhupate hain asli destination) ---
    if exp.get("is_shortener"):
        risk += 18
        reasons.append("🔀 Ye shortened/redirect link hai — asli destination chhupi thi (ab khol di).")
    if exp.get("hops", 0) >= 3:
        risk += 12
        reasons.append(f"🔁 {exp['hops']} times (signs of multi-hop cloaking).")

    # --- B) host structure ---
    _ipf = signals["ip_form"]
    if _ipf in ("dotted", "decimal", "hex", "octal", "short-form", "ipv6",
                "invalid-ip"):
        risk += 30 if _ipf == "dotted" else 34
        if _ipf == "dotted":
            reasons.append("🧮 A raw IP address instead of a domain — 95% of "
                           "phishing comes this way.")
        elif _ipf == "invalid-ip":
            reasons.append("🧮 Adhoora/galat IP jaisa host — aisa address sirf "
                           "browser confuse karne ke liye banaya jaata hai.")
        elif _ipf == "ipv6":
            reasons.append("🧮 Seedha IPv6 address (domain nahi) — normal sites "
                           "aisa link nahi deti.")
        else:
            _dec = ""
            try:
                if _ipf == "decimal":
                    _dec = " → " + ".".join(str((int(host_no_port_for_checks) >> s) & 255)
                                           for s in (24, 16, 8, 0))
                elif _ipf == "hex":
                    _dec = " → " + ".".join(str(int(x, 16)) for x in
                                           host_no_port_for_checks.replace("0x", "").split("."))
                elif _ipf == "octal":
                    _dec = " → " + ".".join(str(int(x, 8)) for x in
                                           host_no_port_for_checks.split("."))
            except Exception:                                # noqa: BLE001
                _dec = ""
            reasons.append(f"🧨 IP ko <b>{_ipf} form</b> me chhupaya gaya "
                           f"hai{_dec} — aisa link browser IP khol leta hai par "
                           "insaan ko domain jaisa dikhta hai. Ye jaan-boojh kar "
                           "kiya gaya dhokha hai.")
    if "xn--" in host_no_port_for_checks:
        risk += 25
        reasons.append("🔤 Punycode (xn--) domain — milte-julte foreign characters se dhokha diya ja sakta hai.")
    if "@" in target.split("://", 1)[-1].split("/")[0]:
        risk += 35
        reasons.append("🎭 URL me '@' ka jhol — asli site '@' ke baad hai, ye dhokha hai.")
    labels = host_no_port_for_checks.split(".")
    if len(labels) >= 5:
        risk += 15 if not official else 0
        reasons.append(f"🧩 Too many subdomains ({len(labels)} parts) — the brand looks faked.")
    tld = "." + labels[-1] if labels else ""
    if tld in SUSPICIOUS_TLDS:
        risk += 18
        reasons.append(f"🌍 '{tld}' TLD is heavily used in scams/phishing.")
    if host_no_port_for_checks.count("-") >= 2:
        risk += 8
        reasons.append("➖ 2+ hyphens in the domain (a common brand-mimicry pattern).")

    # --- B2) v77: double extension / executable disguise -------------------
    _pname = (p.path or "").lower()
    _tail = _pname.rsplit("/", 1)[-1]
    if _tail and any(_tail.endswith(x) for x in _DOUBLE_EXT):
        risk += 45
        reasons.append(f"📦 Link ke aakhir me file ka type chhupa hai "
                       f"(<code>{hesc(_tail[-14:])}</code>) — aisa link kholne "
                       "par aapke phone/PC me program chal padta hai.")

    # --- B3) v77: dangerous port (explicit list, sirf 'unusual' nahi) ------
    if ":" in host and not host.endswith((":443", ":80")):
        _pt = host.split(":")[-1]
        if _pt in _DANGEROUS_PORTS:
            risk += 22
            reasons.append(f"🚪 Port <code>{hesc(_pt)}</code> — ye admin/database "
                           "panels ka port hai (22=SSH, 3389=Remote Desktop, "
                           "6379=Redis). Public website ka link aisa kabhi nahi hota.")

    # --- B4) v77: typosquat (brand ka 1-2 akshar ka nakal) -----------------
    _ty = typosquat_of(host_no_port_for_checks)
    if _ty and not official:
        risk += 40
        reasons.append(f"🅱️ Ye <b>{hesc(_ty[0])}</b> ka nakal lagta hai "
                       f"(<code>{hesc(reg_dom)}</code> — { _ty[1]} akshar ka farak). "
                       "Aisa domain search/ad se aata hai; hamesha khud type karke jao.")

    # --- C) HTTPS + port ---
    if p.scheme != "https":
        risk += 12
        reasons.append("🔓 Connection 'http' hai (secure nahi) — kabhi form ya OTP na dalo.")
    if ":" in host and not host.endswith((":443", ":80")):
        risk += 15
        reasons.append(f"🚪 Unusual port ({host.split(':')[-1]}) — normal websites do not use this.")

    # --- D) lure words + brand combos ---
    # v77 FIX: pehle `low` me plain substring search thi, isliye
    #   • 'vi' (Vodafone) "serv<b>VI</b>ces" me mil jaata tha, aur
    #   • `www.sbi.co.in` (asli SBI) par "brand fake hai" keh diya jaata tha,
    #     kyun ki official check me sirf `<brand>.com` / `<brand>.in` tha.
    # Ab: chhote brand token ki tarah gine jaate hain + official domain
    # whitelist + har brand ke apne asli domain se tulna.
    low = (host_no_port_for_checks + path_q).lower()
    _toks = _host_tokens(low)
    hit_words = [w for w in LURE_WORDS if (w in _toks) or (len(w) > 4 and w in low)]
    brand_hit = [b for b in BRANDS if brand_in_text(b, low, _toks)]

    def _brand_is_official(b: str) -> bool:
        for off in _BRAND_OFFICIAL.get(b, ()):
            if reg_dom == off or reg_dom.endswith("." + off):
                return True
        return False

    if official:
        # Asli sarkari/banki domain: ye checks laagu hi nahi hote
        signals["whitelisted"] = True
        hit_words = []
        fake_brands = []
    else:
        fake_brands = [b for b in brand_hit if not _brand_is_official(b)]
    if hit_words and not official:
        add = min(30, sum(LURE_WORDS[w] for w in hit_words))
        risk += add
        reasons.append("🎣 Suspicious words found: " + ", ".join(hit_words[:6]))
    # Brand + free hosting/other domain me = impersonation
    if fake_brands:
        risk += 22
        exp_hint = ", ".join(_BRAND_OFFICIAL.get(fake_brands[0], ())) or \
            f"{fake_brands[0]}.com/.in"
        reasons.append("🏦 Brand name used but not the official domain: " +
                       ", ".join(fake_brands[:4]) +
                       f" (asli site <code>{hesc(exp_hint)}</code> hoti hai)")
    # brand host ke SUBDOMAIN/prefix me chhupa ho (`sbi.verify.xyz`)
    if not official and brand_hit:
        _first = (reg_dom.split(".") or [""])[0]
        _pre = (host_no_port_for_checks.split(".") or [""])[0]
        for b in brand_hit:
            if _first == b or _pre.startswith(b) and _pre != b and len(_pre) > len(b) + 1:
                risk += 12
                reasons.append(f"🎪 Brand ka naam subdomain/prefix me chipkaya "
                               f" gaya hai (<code>{hesc(_pre[:24])}</code>) — asli "
                               "site aisa nahi karti.")
                break
    if any(x in host_no_port for x in ("vercel.app", "netlify.app", "pages.dev", "workers.dev", "web.app",
                                       "firebaseapp.com", "duckdns.org", "myftp.org", "000webhostapp.com",
                                       "github.io", "glitch.me", "repl.co", "blogspot.")) and (hit_words or brand_hit):
        risk += 12
        reasons.append("🆓 Free hosting domain par bank/login jaisa page — scam ka common joda.")

    # --- E) OpenPhish + E2) domain age + F) urlscan — v55: PARALLEL ---
    # Pehle ye teen checks serial chalti thi (~1-2s each → total 5+s). Ye teeno
    # ek-doosre par depend nahi karte, isliye ab ek saath chalte hain →
    # user-visible time ~max(checks) instead of sum(checks).
    def _age_worker():
        _h = host_no_port_for_checks
        if _h and not numeric_host_form(_h) and "." in _h:
            try:
                from modules.general_tools import domain_age_days as _dom_age
                return _dom_age(_h)
            except Exception:
                return None
        return None

    def _scan_worker():
        return _urlscan_reputation(host_no_port_for_checks) if host_no_port_for_checks else -1

    age: "int | None" = None
    scans = -1
    try:
        with ThreadPoolExecutor(max_workers=3) as ex:
            f_age = ex.submit(_age_worker)
            f_scan = ex.submit(_scan_worker)
            f_phish = ex.submit(_load_openphish)
            try:
                age = f_age.result(timeout=20)
            except Exception:
                age = None
            try:
                scans = f_scan.result(timeout=20)
            except Exception:
                scans = -1
            try:
                f_phish.result(timeout=25)
            except Exception:
                pass
    except Exception:            # noqa: BLE001 - thread engine fail ho to serial fallback
        age = _age_worker()
        scans = _scan_worker()
        _load_openphish()

    # --- E) OpenPhish live feed result ---
    if _PHISH_CACHE["urls"]:
        if target in _PHISH_CACHE["urls"]:
            risk += 60
            reasons.append("🚨 Ye link OpenPhish ke LIVE phishing feed me hai (pakka scam).")
        elif host_no_port in _PHISH_CACHE["hosts"]:
            risk += 50
            reasons.append("🚨 This domain name is in the OpenPhish live phishing feed.")
    signals["openphish_size"] = len(_PHISH_CACHE["urls"])

    # --- E2) DOMAIN AGE (free RDAP) — naye domain se scam sabse zyada ---
    signals["domain_age_days"] = age
    if age is not None and age < 30:
        risk += 20
        reasons.append(f"🆕 Ye domain sirf <b>{age} din</b> purana hai — naye domain se scams sabse zyada hote hain.")
    elif age is not None and age < 90:
        risk += 8
        reasons.append(f"📆 Domain sirf {age} din purana hai (kam jaana-mana).")

    # --- F) urlscan.io reputation ---
    signals["urlscan_scans"] = scans
    if scans == 0:
        reasons.append("🆕 Ye domain urlscan.io par kabhi scan nahi hua (naya / kam jaana-mana).")

    # --- G) length / entropy signals ---
    if len(target) > 120:
        risk += 8
        reasons.append("📏 The link is very long (tracking/obfuscation).")
    # v77: base64/hex payload path (malware/C2 aur credential-steeder ka pattern)
    _seg = [x for x in (p.path or "").split("/") if len(x) >= 24]
    for _sg in _seg[:1]:
        if re.fullmatch(r"[A-Za-z0-9+/=_\-]{24,}", _sg) and \
           (sum(c.isdigit() for c in _sg) >= 3 or sum(c.isupper() for c in _sg) >= 4) and \
           not re.search(r"[.?&=]", _sg):
            risk += 14
            reasons.append("🧾 Path me encoded (base64/hex jaisa) bhaag hai — "
                           "aisa scam links ka data chhupane ke liye use hota hai.")
            break
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

    # v56: dead link ke liye "SAFE" kehna galat tha — jhootha bharosa deta tha.
    if exp.get("ok") is False and level in ("safe", "low"):
        verdict = "LINK KHULTA NAHI 🔌"
        advice = ("Ye link abhi kaam nahi kar raha (domain galat / server band). "
                  "Kisi aur se mila ho to source se dobara verify karo. "
                  "OTP / password / UPI PIN kabhi na dalo.")

    if official:
        _why = ("hamari official list me hai" if not _restricted_hit else
                f"ek <b>restricted registry</b> ({hesc(_brand_guess)}) par hai — "
                "aisa TLD sirf sarkar/licensed bank le sakta hai")
        reasons.insert(0, f"✅ <code>{hesc(reg_dom)}</code> {_why} — isliye "
                          "brand-impersonation ke signals is par nahi lagaye gaye.")
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
