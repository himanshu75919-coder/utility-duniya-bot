# -*- coding: utf-8 -*-
"""
Universal Video & Social Media Downloader Engine (v31 PRO)
==========================================================
v67: sirf 4 platforms — Instagram, YouTube, Facebook, TikTok.
(baaki 23 services user ke order par POORI TARAH DELETE kar di gayi hain)

ENGINE CHAIN (Instagram):  parth-dl  ->  yt-dlp  ->  og:video scrape  ->  mirrors
ENGINE:                    yt-dlp     (Instagram, YouTube, Facebook, TikTok)

2026 fixes:
- kkinstagram mirror dead tha -> hataya, yt-dlp engine add kiya (verified working).
- Instagram rate-limit (429) ke liye auto-retry + optional cookie support.
- 48 MB se bada file Telegram Bot API me upload nahi hota -> us case me clean DIRECT LINK
  bhej diya jata hai (kaam rukta nahi).

Optional env (Render Environment me daal sakte hain — Instagram reliable karne ke liye):
  IG_COOKIE=/IG_COOKIES_FILE=   -> Instagram sessionid ya cookies.txt path
"""

import io
import os
import re
import time
import asyncio
import tempfile
import shutil
import subprocess
import threading

import requests
from modules.core import httpio   # v72.0: shared engine (speed + auto-retry)
# v85: link sanitizer — &amp; / markdown / fbclid wale gande links andar na aayein
try:
    from modules.core import urlclean as _UC
except Exception:  # noqa: BLE001
    _UC = None
from PIL import Image
from bs4 import BeautifulSoup


def _clean_incoming(url: str) -> str:
    """Engine ke andar aane wala link saaf karo (fail ho to original)."""
    try:
        if _UC is not None:
            _c = _UC.clean_link(url)
            if _c:
                return _c
    except Exception:  # noqa: BLE001
        pass
    try:
        if url is None:
            return ""
        if isinstance(url, bytes):
            return url.decode("utf-8", "ignore").strip()
        return str(url).strip()
    except Exception:  # noqa: BLE001
        return ""

try:
    import parth_dl
except ImportError:
    parth_dl = None

# v106: ⚡ IG FAST ENGINE — Instagram ke KHUD ke public JSON API se 1-5 second
# me post/reel/TV/carousel/profile-photo (+ cookie ho to story/highlight).
# Race me SABSE PEHLE chalta hai; fail/cooldown par 0.001s me None → purane
# engines (parth/embed/og/yt-dlp) waise hi chalte rehte hain.
try:
    from modules import ig_fast as IGF
except Exception:                                               # noqa: BLE001
    IGF = None

# v105.2: yt_dlp LAZY — boot me ~39 MB RAM nahi khata. Pehli download
# par import hota hai. Lock se concurrent first-use par adhoora None nahi milega.
yt_dlp = None
_yt_dlp_tried = False
_YTDLP_LOCK = threading.Lock()


def _ytdlp():
    """Pehli zaroorat par thread-safe import; fail par None (hamesha safe)."""
    global yt_dlp, _yt_dlp_tried
    if yt_dlp is not None:
        return yt_dlp
    if _yt_dlp_tried:
        return None
    with _YTDLP_LOCK:
        if yt_dlp is not None:
            return yt_dlp
        if _yt_dlp_tried:
            return None
        try:
            import yt_dlp as _m
            yt_dlp = _m
        except ImportError:
            yt_dlp = None
        finally:
            _yt_dlp_tried = True
    return yt_dlp

DESKTOP_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
BOT_UA = {
    "User-Agent": "TelegramBot (like TwitterBot)"
}
FB_UA = {
    "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
}

# v105.2: 512MB Render free instance me ek media result RAM me rehta hai;
# safe default/cap 48MB. Bigger-memory hosts can raise it via MEMORY_LIMIT_MB.
# Explicit MAX_TG_MB bhi 512MB par 48 par clamp hota hai (buffer/encode/upload peak).
def _tg_cap_mb() -> int:
    try:
        _limit = int(float(os.environ.get("MEMORY_LIMIT_MB") or 512))
    except Exception:                                            # noqa: BLE001
        _limit = 512
    _free_safe = _limit <= 512
    try:
        _raw = (os.environ.get("MAX_TG_MB") or "").strip()
        if _raw:
            _requested = max(20, min(400, int(_raw)))
            return min(_requested, 48) if _free_safe else _requested
    except Exception:                                            # noqa: BLE001
        pass
    try:
        from modules.core import bigfile as _BF
        _default = 96 if _BF.enabled() else 48
    except Exception:                                            # noqa: BLE001
        _default = 48
    return min(_default, 48) if _free_safe else _default

MAX_TG_MB = _tg_cap_mb()

# ffmpeg detection: system ka, warna imageio-ffmpeg ka bundled binary (Render pe bhi chal jata hai)
_FFMPEG_LOC = shutil.which("ffmpeg")
if not _FFMPEG_LOC:
    try:
        import imageio_ffmpeg
        _FFMPEG_LOC = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        _FFMPEG_LOC = None
_HAS_FFMPEG = bool(_FFMPEG_LOC)

# v67: sirf 4 platform (Instagram, YouTube, Facebook, TikTok) — baaki 23
#      services user ke order par POORI TARAH DELETE kar di gayi hain.
SUPPORTED_SITES = (
    "instagram.com", "instagr.am", "youtube.com", "youtu.be", "facebook.com", "fb.watch",
    "tiktok.com",
)


# =====================================================================================
# HELPERS
# =====================================================================================
def is_instagram_url(url: str) -> bool:
    try:
        url = _clean_incoming(url) or url   # v85: markdown/gandagi me bhi pehchano
    except Exception:  # noqa: BLE001
        pass
    u = (url or "").lower()
    return "instagram.com" in u or "instagr.am" in u


def is_supported_video_url(url: str) -> bool:
    try:
        url = _clean_incoming(url) or url   # v85: markdown/gandagi me bhi pehchano
    except Exception:  # noqa: BLE001
        pass
    u = (url or "").lower()
    return any(s in u for s in SUPPORTED_SITES)


def platform_name(url: str) -> str:
    try:
        url = _clean_incoming(url) or ""   # v86: junk-proof (int/bytes par crash tha)
    except Exception:  # noqa: BLE001
        pass
    if not isinstance(url, str):
        return "Social Media"
    u = (url or "").lower()
    table = [
        ("instagram.com", "Instagram"), ("instagr.am", "Instagram"),
        ("youtube.com", "YouTube"), ("youtu.be", "YouTube"),
        ("facebook.com", "Facebook"), ("fb.watch", "Facebook"),
        ("tiktok.com", "TikTok"),
    ]
    for key, name in table:
        if key in u:
            return name
    try:
        return (url.split("//")[1].split("/")[0]).replace("www.", "").title()
    except Exception:
        return "Social Media"


def classify_instagram_url(url: str) -> str:
    """Classifies Instagram URL into 'reel', 'story', 'highlight', 'profile' or 'post'"""
    if not isinstance(url, str):                       # v78: None/list par crash hota tha
        url = "" if url is None else str(url)
    try:
        if _UC is not None:                            # v85: &amp; wale links bhi classify hon
            _c = _UC.clean_link(url)
            if _c:
                url = _c
    except Exception:  # noqa: BLE001
        pass
    u = url.lower().split("?")[0]
    if "/reel/" in u or "/reels/" in u or "/tv/" in u:
        return "reel"
    if "/stories/" in u or "/s/" in u or "/highlight/" in u:   # v86: share/highlight bhi story
        return "story"
    if "/p/" in u:
        return "post"
    if _ig_profile_user(url):                          # v86: /username → profile photo
        return "profile"
    return "general"


# v86: ye paths profile NAHI hain (Instagram ke system pages)
_IG_RESERVED = frozenset({
    "p", "reel", "reels", "tv", "stories", "s", "highlight", "explore",
    "accounts", "direct", "about", "developer", "embed", "directory",
    "web", "graphql", "api", "static", "support", "help", "terms",
})


def _ig_profile_user(url: str):
    """instagram.com/<username> ho to username, warna ''. (v86: profile-pic feature)"""
    try:
        m = re.search(r"instagr(?:am\.com|am?\.am)/([A-Za-z0-9._]{1,30})(?:[/?#]|$)", url or "",
                      re.IGNORECASE)
        if not m:
            return ""
        _u = m.group(1).strip().strip(".").lower()
        if not _u or _u in _IG_RESERVED or _u.startswith(("http", "www.")):
            return ""
        return m.group(1).strip().strip(".")
    except Exception:  # noqa: BLE001
        return ""


def _call_capped(fn, timeout: float, *a, **kw):
    """v68: kisi bhi (slow ho sakne wale) function ko TIME LIMIT me chalao.

    Asli wajah jise pakda gaya: hub API (loader.to) 40+ second leta tha —
    isi se "bots slow hai" ki shikayat thi. Ab hub ko sirf 6-12 second milte
    hain; jawab na aaye to seedha tez local engine (yt-dlp) chalta hai.
    """
    if fn is None:
        return None
    from concurrent.futures import ThreadPoolExecutor
    _ex = ThreadPoolExecutor(max_workers=1)
    try:
        _fut = _ex.submit(fn, *a, **kw)
        try:
            return _fut.result(timeout=timeout)
        except Exception:                                        # noqa: BLE001
            return None
    finally:
        _ex.shutdown(wait=False)      # thread background me khatam ho jayega


def _is_yt_url(url: str) -> bool:
    _u = (url or "").lower()
    return ("youtube.com" in _u) or ("youtu.be" in _u)


# jin errors par dobara koshish ka faayda nahi (video hi nahi hai)
_DL_HARD_FAIL = ("video unavailable", "video is private", "is private",
                 "removed by the uploader",
                 "has been terminated", "members-only", "age-restricted",
                 "sign in to confirm your age", "is live", "live event",
                 "not available in your country", "unsupported url",
                 "no video formats found")


def _retryable(err: str) -> bool:
    """Agla client set try karna chahiye ya nahi?"""
    _e = (err or "").lower()
    if not _e:
        return True
    return not any(k in _e for k in _DL_HARD_FAIL)


def cookies_path() -> str:
    """v66: cookies.txt kahan save hoga (admin bot ko file bhejkar deta hai)."""
    d = (os.environ.get("DATA_DIR") or os.environ.get("IG_DATA_DIR") or "").strip()
    if not d or not os.path.isdir(d):
        try:
            from modules.core.vault import db_path as _dbp   # bot ka DB folder
            d = os.path.dirname(os.path.abspath(_dbp()))
        except Exception:                                        # noqa: BLE001
            d = tempfile.gettempdir()
    try:
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
    except Exception:                                            # noqa: BLE001
        d = tempfile.gettempdir()
    return os.path.join(d, "yt_cookies.txt")


def save_cookies_text(text: str):
    """Admin ke bheje cookies.txt ko disk par likho (DB me bhi rakha jaata hai)."""
    txt = (text if isinstance(text, str) else "").strip()   # v78: non-str par crash
    if len(txt) < 40 or "youtube.com" not in txt and ".instagram.com" not in txt:
        return None
    try:
        path = cookies_path()
        with open(path, "w", encoding="utf-8") as f:
            if not txt.startswith("# Netscape"):
                f.write("# Netscape HTTP Cookie File\n")
            f.write(txt + "\n")
        return path
    except Exception:                                            # noqa: BLE001
        try:
            path = os.path.join(tempfile.gettempdir(), "ud_yt_cookies.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(txt + "\n")
            return path
        except Exception:                                        # noqa: BLE001
            return None


def cookies_status() -> dict:
    """Cookies lagi hain ya nahi — /cookies command ke liye."""
    p = _cookiefile()
    ok, n = bool(p), 0
    if p:
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                n = sum(1 for ln in f if ln and not ln.startswith("#"))
        except Exception:                                        # noqa: BLE001
            n = 0
    return {"set": bool(ok and n), "path": p or "", "lines": n}


def _cookiefile():
    """Instagram/yt-dlp cookies file (env, ya bot ko bheji hui file)."""
    p = (os.getenv("IG_COOKIES_FILE") or os.getenv("YTDLP_COOKIES_FILE") or "").strip()
    if p and os.path.isfile(p):
        return p
    # v66: bot ko bheja gaya cookies.txt (admin ne Telegram par bheja)
    for _p in (cookies_path(),
               os.path.join(tempfile.gettempdir(), "ud_yt_cookies.txt")):
        try:
            if _p and os.path.isfile(_p) and os.path.getsize(_p) > 40:
                return _p
        except Exception:                                        # noqa: BLE001
            continue
    # IG_COOKIE="sessionid=xxxx" jaisa diya ho to temp cookies.txt bana dete hain
    raw = (os.getenv("IG_COOKIE") or os.getenv("YTDLP_COOKIES") or "").strip()
    if raw:
        if os.path.isfile(raw):
            return raw
        try:
            fd, path = tempfile.mkstemp(suffix="cookies.txt")
            with os.fdopen(fd, "w") as f:
                if raw.startswith("# Netscape"):
                    f.write(raw)
                else:
                    sid = raw.replace("sessionid=", "").strip()
                    f.write("# Netscape HTTP Cookie File\n")
                    f.write(f".instagram.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\t{sid}\n")
            return path
        except Exception:
            return None
    return None


def _size_mb(b):
    return round(len(b) / (1024 * 1024), 2) if b else 0


# =====================================================================================
# ENGINE 1 — parth-dl (Instagram ka fast core, jaisa pehle tha)
# =====================================================================================
def _ig_parth(clean: str, media_cat: str):
    if not parth_dl:
        return None
    try:
        info = parth_dl.get_info(clean)
    except Exception:
        return None
    try:
        m_type = info.get("type", "")
        title = info.get("title", "")

        # Carousel
        if m_type == "carousel" or len(info.get("images", []) or []) > 1 or len(info.get("entries", []) or []) > 1:
            items = []
            entries = info.get("entries", []) or []
            for entry in entries[:20]:   # v86: IG carousel max 20 (pehle 10)
                e_kind = entry.get("kind", "")
                e_formats = entry.get("formats", [])
                if e_kind == "video" and e_formats:
                    # v105.2: stream + size cap BEFORE buffering.
                    _cv = _http_get_capped(e_formats[0].get("url"), 15,
                                           headers=DESKTOP_UA, timeout=15, want="video")
                    if _cv and len(_cv) > 1000:
                        items.append({"type": "video", "bytes": _cv})
                elif e_formats:
                    _ci = _http_get_capped(e_formats[0].get("url"), 15,
                                           headers=DESKTOP_UA, timeout=12, want="image")
                    if _ci:
                        _jb = _jpeg_fit(_ci)   # v86: size-capped JPEG
                        if _jb:
                            items.append({"type": "photo", "bytes": _jb})
            if not items and info.get("images"):
                for img_obj in info.get("images", [])[:20]:   # v86: 20 tak
                    u = img_obj.get("url")
                    if u:
                        _ci2 = _http_get_capped(u, 15, headers=DESKTOP_UA,
                                                timeout=12, want="image")
                        if _ci2:
                            _jb2 = _jpeg_fit(_ci2)   # v86: size-capped JPEG
                            if _jb2:
                                items.append({"type": "photo", "bytes": _jb2})
            if items:
                return {"ok": True, "type": "carousel", "category": media_cat, "title": title,
                        "items": items, "count": len(items), "platform": "Instagram", "engine": "parth-dl"}

        # Video / Reel
        if m_type == "video" or (info.get("formats") and len(info["formats"]) > 0):
            formats = info.get("formats", [])
            v_url = formats[0].get("url") if formats else None
            if v_url:
                _rv = _http_get_capped(v_url, MAX_TG_MB, headers=DESKTOP_UA,
                                       timeout=25, want="video")
                if _rv and len(_rv) > 1000:
                    _dv, _dw, _dh = _probe_data(_rv)   # v105: asli naap
                    return {"ok": True, "type": "video", "category": "reel" if media_cat == "reel" else "video",
                            "title": title, "bytes": _rv, "size_mb": _size_mb(_rv),
                            "duration": int(_dv or 0),
                            "quality": f"{_dh}p" if _dh else None,
                            "platform": "Instagram", "engine": "parth-dl"}

        # Single Photo
        if m_type in ("image", "photo") or (info.get("images") and len(info["images"]) > 0):
            img_url = info["images"][0].get("url") if info.get("images") else None
            if img_url:
                _ri = _http_get_capped(img_url, 15, headers=DESKTOP_UA,
                                       timeout=12, want="image")
                if _ri and len(_ri) > 1000:
                    _photo = _jpeg_fit(_ri, max_px=2400, quality=94)
                    if _photo:
                        return {"ok": True, "type": "photo", "category": "post", "title": title,
                                "bytes": _photo, "size_mb": _size_mb(_photo),
                                "platform": "Instagram", "engine": "parth-dl"}
    except Exception:
        return None
    return None


# =====================================================================================
# ENGINE 2 — yt-dlp (Instagram + 20+ platforms)
# =====================================================================================

# ===========================================================================
#  v56: FRIENDLY DOWNLOAD ERRORS
#  Render log (2026-10-05, 03:01 PM) me ye tha:
#     ERROR: [youtube] yaQCKQMiLo: Sign in to confirm you're not a bot.
#     Use --cookies-from-browser or --cookies for the authentication.
#  User ko aisa technical wall of text kabhi nahi dikhna chahiye. Yahan har
#  known yt-dlp failure ka saaf Hindi + solution hai. Ye module-level state
#  hai kyunki yt-dlp ke exceptions andar hi swallow ho jaate hain — warna
#  user ko khali "download fail" milta tha aur wajah pata hi nahi chalti.
# ===========================================================================
_LAST_ERR: dict = {"msg": "", "at": 0.0}


def _remember(exc) -> None:
    """Aakhri yt-dlp/network error yaad rakho (friendly message ke liye)."""
    try:
        _LAST_ERR["msg"] = str(exc)[:500]
        _LAST_ERR["at"] = time.time()
    except Exception:  # noqa: BLE001
        pass


def last_dl_error() -> str:
    """Aakhri error — 10 minute se purana ho to bhool jao (stale message na aaye)."""
    try:
        if time.time() - _LAST_ERR["at"] > 600:
            return ""
    except Exception:  # noqa: BLE001
        return ""
    return _LAST_ERR["msg"]


_DL_ERR_MAP = (
    # ---- YouTube bot-check (aaj kal ka sabse common) ----
    (("sign in to confirm you're not a bot", "sign in to confirm you’re not a bot",
      "confirm you're not a bot", "not a bot"),
     "🤖 <b>YouTube ne bot-check laga diya</b> (ye server ke IP par lagta hai).\n"
     "✅ <b>Aise theek hoga:</b>\n"
     "  1️⃣ <b>360p / 480p</b> chuno — chhoti quality par check kam lagta hai\n"
     "  2️⃣ 1-2 minute ruk ke <b>dobara try</b> karo (YouTube ka check khud hat jata hai)\n"
     "  3️⃣ Admin: <code>/cookies</code> se apni YouTube cookies bhej dein = pakka ilaaj\n"
     "💳 <b>Aapka credit nahi kata.</b>"),
    # ---- v107: carousel slide-index wali galat upstream error ----
    (("out of range", "media number"),
     "📸 <b>Ye link carousel ki ek specific slide ka tha</b> jo post me ab "
     "available nahi (Instagram ne slide hata di ya index purana hai).\\n"
     "✅ Poore post ka link bhejo — <b>poori album</b> aa jayegi. "
     "<b>Credit nahi kata.</b>"),
    # ---- login / private ----
    (("sign in to confirm your age", "age-restricted", "inappropriate for some users"),
     "🔞 <b>Ye video age-restricted hai</b> (YouTube login maangta hai).\n"
     "✅ Koi doosra public video try karo. <b>Credit nahi kata.</b>"),
    (("private video", "this video is private"),
     "🔒 <b>Ye video private hai</b> — sirf owner dekh sakta hai.\n"
     "✅ Public video ka link bhejo. <b>Credit nahi kata.</b>"),
    (("members-only", "available to this channel's members", "join this channel"),
     "👑 <b>Ye members-only video hai</b> (channel ki paid membership chahiye).\n"
     "✅ Free video try karo. <b>Credit nahi kata.</b>"),
    (("video unavailable", "this video is unavailable", "removed by the uploader",
      "no longer available", "has been terminated"),
     "🚫 <b>Ye video YouTube par ab available nahi hai</b> (delete / hata diya gaya).\n"
     "✅ Koi doosra link bhejo. <b>Credit nahi kata.</b>"),
    (("not available in your country", "geo-restricted", "blocked in your country",
      "not available on this platform"),
     "🌍 <b>Ye video aapke/server ke region me blocked hai.</b>\n"
     "✅ Koi doosra video try karo. <b>Credit nahi kata.</b>"),
    (("is live", "live event will begin", "premieres in", "live stream"),
     "🔴 <b>Ye live stream / premiere hai</b> — live video download nahi ho sakta.\n"
     "✅ Stream khatam hone ke baad try karo. <b>Credit nahi kata.</b>"),
    # ---- format / link issues ----
    (("requested format is not available", "no video formats found", "no formats found"),
     "🎞️ <b>Is video ki ye quality available nahi hai.</b>\n"
     "✅ Doosri quality chuno (720p / 480p). <b>Credit nahi kata.</b>"),
    (("unsupported url", "no suitable extractor", "not a valid url",
      "is not a valid url", "unable to extract"),
     "🔗 <b>Ye link supported nahi hai</b> ya link adhoora hai.\n"
     "✅ Poora link copy karke bhejo (browser ke address bar se). <b>Credit nahi kata.</b>"),
    (("login required", "requested content is not available", "rate-limit",
      "too many requests", "http error 429"),
     "⏳ <b>Platform ne thodi der ke liye rok laga di hai</b> (rate-limit).\n"
     "✅ <b>2-3 minute</b> ruk ke dobara try karo. <b>Credit nahi kata.</b>"),
    (("http error 403", "forbidden", "access denied"),
     "🛡️ <b>Platform ne is download ko block kiya hai</b> (403).\n"
     "✅ 1-2 minute baad dobara try karo. <b>Credit nahi kata.</b>"),
    # ---- network ----
    (("timed out", "timeout", "read timeout", "connection reset",
      "connection aborted", "temporary failure in name resolution"),
     "🌐 <b>Internet/server se connection slow ya toot gaya.</b>\n"
     "✅ <b>10 second</b> baad dobara try karo. <b>Credit nahi kata.</b>"),
    (("file is larger than", "max-filesize", "filesize"),
     "📦 <b>Video file Telegram ki limit (48MB) se badi hai.</b>\n"
     "✅ <b>Chhoti quality</b> (480p / 360p) chuno, ya ✂️ <b>Media Studio → Video compress</b> "
     "use karo. <b>Credit nahi kata.</b>"),
)


def friendly_dl_error(raw: str = "", platform: str = "") -> str:
    """yt-dlp ka technical error → saaf Hindi message + solution.

    `raw` khali ho to aakhri yaad kiya gaya error use hota hai.
    """
    msg = (raw or last_dl_error() or "").lower()
    for keys, friendly in _DL_ERR_MAP:
        if any(k in msg for k in keys):
            return friendly
    p = f"{platform} " if platform else ""
    return (f"❌ {p}download abhi nahi ho paya.\n"
            "✅ 1-2 minute baad <b>dobara try karo</b> — pehli koshish me "
            "platform server ko jawab nahi deta.\n"
            "💳 <b>Koi credit nahi kata.</b>")


# v107: user ko KABHI bhi raw technical/upstream string nahi dikhni chahiye
# (10 Oct ko user ko "Media number out of range." jaisa upstream kachra dikha
# tha). Jo message pehle se saaf Hinglish/emoji wala hai wahi pass hota hai,
# baaki sab friendly_dl_error se hokar jaata hai.
_SAFE_MARKS = ("🔐", "⚠️", "🔒", "❌", "✅", "🌐", "🤖", "🚫", "👑",
               "📦", "🎞️", "🔗", "⏳", "🛡️", "🔴", "🌍", "📸",
               "💳", "🩸", "🎯", "📥", "🔥", "🧲", "📌")


def user_safe_error(reason: str = "", platform: str = "") -> str:
    """Raw upstream error → user-safe Hinglish. Saaf message ko chhedta nahi.

    Jo message pehle se Hinglish/emoji wala hai (hamara khud ka likha hua) wo
    jaisa hai waisa jaata hai; raw upstream kachra ("Media number out of
    range.", "HTTP 403: {...}") friendly message me badal jaata hai.
    """
    r = (reason or "").strip()
    if not r:
        return friendly_dl_error("", platform)
    if any(m in r for m in _SAFE_MARKS):
        return r
    try:  # Devanagari (Hindi) text = hamara likha hua = safe
        if any("\u0900" <= ch <= "\u097F" for ch in r):
            return r
    except Exception:                                              # noqa: BLE001
        pass
    return friendly_dl_error(r, platform)


# ======================================================================
#  v65: 🚀 SPEED + 🤖 YOUTUBE BOT-CHECK FIX
# ======================================================================
#  Problem 1 (aapke log me dikha): "Sign in to confirm you're not a bot".
#     YouTube ko yt-dlp ka web client BOT lagta tha. Hal: alag player-client
#     (android_vr / tv / ios) se baat karo — in par bot check nahi lagta.
#  Problem 2: download ~2 minute leta tha. Hal:
#     (a) progressive single-file format pehle (ffmpeg merge nahi = 3x tez)
#     (b) 16 parallel chunks (pehle 4)
#     (c) socket timeout 15s -> 8s (atka hua connection jaldi chhoot jaye)
#     (d) hard deadline hook — 75 second se zyada lage to kaam rok kar
#         user ko turant direct link de do (2 minute wait khatam)
# ======================================================================
# v66: ye order ASLI TEST se nikala gaya hai (7 client set, live video par).
#      android_vr = 1.3s ✅ | tv_embedded = 1.2s ✅ | android = 1.1s ✅
#      (pehle "tv+tv_simply" tha jo fail hota hai — "page needs to be reloaded")
YT_CLIENT_SETS = (
    ("android_vr",),              # ✅ sabse tez + bot check nahi lagta
    ("tv_embedded",),             # ✅ backup 1 (sabse zyada format deta hai)
    ("android",),                 # ✅ backup 2
    ("web_safari", "web"),        # ✅ backup 3
)

FAST_DEADLINE = 30        # v68: 45 -> 30 second (user ka target: 30s me video)
BAD_CLIENT_SECONDS = 900  # bot-check wala client 15 min ke liye "bad" mark

# ======================================================================
# v68: 🚀 SPEED ENGINE — 3 naye hathiyar
# ======================================================================
#  1) CIRCUIT BREAKER: jo client "Sign in to confirm you're not a bot" de de,
#     use 15 minute ke liye bad mark kar do — agli baar seedha sahi client
#     par jao (log me 5 error line aane ka karan yahi tha = 20s barbaad).
#  2) PARALLEL INFO: 4 client ko EK SAATH try karo (threads) — jo pehle
#     safal ho wahi jeeta. 12s ka kaam ~2s me.
#  3) RESULT CACHE: ek hi video dobara maanga gaya (viral reel) to memory
#     se TURANT — 0.1 second me.
# ======================================================================
_BAD_CLIENTS = {}                    # client-name -> expiry timestamp
_CLIENT_LOCK = threading.Lock()
_DL_MEM = {}                         # url-key -> (bytes, meta, ts)
_DL_MEM_ORDER = []                   # LRU order (key list)
_DL_MEM_BYTES = 0
_DL_MEM_MAX_BYTES = 12 * 1024 * 1024       # v107: 20→12 MB (512 MB RAM plan; bada file disk cache sambhalta hai)
_DL_MEM_TTL = 2 * 3600                     # 2 ghante
_DL_MEM_LOCK = threading.Lock()


def _mark_client_bad(clients, err: str = "") -> None:
    """Bot-check / reload error dene wale client ko 15 min ke liye hata do."""
    if not clients:
        return
    _e = ((err or "") + " " + (last_dl_error() or "")).lower()
    if not any(k in _e for k in ("not a bot", "needs to be reloaded", "sign in",
                                 "cookies", "error code: 152", "unavailable")):
        return
    exp = time.time() + BAD_CLIENT_SECONDS
    with _CLIENT_LOCK:
        for c in clients:
            _BAD_CLIENTS[c] = exp


def _client_is_bad(clients) -> bool:
    """Ye client set filhaal 'bad' hai? (bad wale aakhir me jaate hain)"""
    now = time.time()
    with _CLIENT_LOCK:
        return any(_BAD_CLIENTS.get(c, 0) > now for c in (clients or ()))


def _ordered_client_sets(sets):
    """Achhe clients pehle, bad wale aakhir me (par poori tarah nahi hataye)."""
    _good = [c for c in sets if not _client_is_bad(c)]
    _bad = [c for c in sets if _client_is_bad(c)]
    return tuple(_good + _bad) or tuple(sets)


def _mem_key(url: str, tag: str = "") -> str:
    return (tag + "|" + (url or "").strip())[:300]


def _mem_get(url: str, tag: str = ""):
    """Cache se nikalo (viral video dobara = 0.1 second)."""
    k = _mem_key(url, tag)
    with _DL_MEM_LOCK:
        item = _DL_MEM.get(k)
        if not item:
            return None
        data, meta, ts = item
        if time.time() - ts > _DL_MEM_TTL:
            _DL_MEM.pop(k, None)
            return None
        try:
            _DL_MEM_ORDER.remove(k); _DL_MEM_ORDER.append(k)
        except Exception:                                        # noqa: BLE001
            pass
        return data, meta


def _mem_put(url: str, data, meta, tag: str = "") -> None:
    """Cache me daalo (100 MB se upar kuch nahi — RAM safe)."""
    global _DL_MEM_BYTES
    try:
        if not data or len(data) > 12 * 1024 * 1024:     # v82: RAM me sirf chhoti files
            return
        k = _mem_key(url, tag)
        with _DL_MEM_LOCK:
            old = _DL_MEM.get(k)
            if old:
                _DL_MEM_BYTES -= len(old[0])
            _DL_MEM[k] = (data, meta, time.time())
            try:
                _DL_MEM_ORDER.remove(k)
            except Exception:                                    # noqa: BLE001
                pass
            _DL_MEM_ORDER.append(k)
            _DL_MEM_BYTES += len(data)
            while _DL_MEM_BYTES > _DL_MEM_MAX_BYTES and _DL_MEM_ORDER:
                _old_k = _DL_MEM_ORDER.pop(0)
                _it = _DL_MEM.pop(_old_k, None)
                if _it:
                    _DL_MEM_BYTES -= len(_it[0])
    except Exception:                                            # noqa: BLE001
        pass


def dl_cache_stats() -> dict:
    """Cache kitna bhara hai (/speed command ke liye)."""
    with _DL_MEM_LOCK:
        return {"items": len(_DL_MEM), "mb": round(_DL_MEM_BYTES / 1048576, 1),
                "bad_clients": len([1 for v in _BAD_CLIENTS.values() if v > time.time()])}
# =====================================================================================
#  v74.3: 💾 DISK CACHE — restart/deploy ke baad bhi cache zinda rehta hai
#  (RAM cache restart par udd jaata tha — isliye "phir se slow" hota tha)
# =====================================================================================
_DISK_MAX_BYTES = 150 * 1024 * 1024      # 150 MB tak
_DISK_MAX_FILE = 12 * 1024 * 1024        # 12 MB se bada file disk par nahi (RAM/hub)


def _disk_dir() -> str:
    d = (os.getenv("UDL_CACHE_DIR") or "").strip() \
        or os.path.join(tempfile.gettempdir(), "udl_cache")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:                                            # noqa: BLE001
        pass
    return d


def _disk_key(url: str, tag: str = "") -> str:
    import hashlib
    return hashlib.md5(_mem_key(url, tag).encode("utf-8", "ignore")).hexdigest()


def _disk_gc() -> None:
    """Purani files hatao (150 MB se upar kabhi nahi)."""
    try:
        d = _disk_dir()
        items = []
        for f in os.listdir(d):
            fp = os.path.join(d, f)
            try:
                items.append((os.path.getmtime(fp), os.path.getsize(fp), fp))
            except Exception:                                    # noqa: BLE001
                pass
        total = sum(i[1] for i in items)
        for _mt, _sz, fp in sorted(items):
            if total <= _DISK_MAX_BYTES:
                break
            try:
                os.remove(fp)
                total -= _sz
            except Exception:                                    # noqa: BLE001
                pass
    except Exception:                                            # noqa: BLE001
        pass


def disk_get(url: str, tag: str = ""):
    """Disk se nikalo — (bytes, meta) ya None. Turbo fast (local file read)."""
    try:
        d = _disk_dir()
        k = _disk_key(url, tag)
        mf = os.path.join(d, k + ".json")
        bf = os.path.join(d, k + ".bin")
        if not (os.path.isfile(mf) and os.path.isfile(bf)):
            return None
        if (time.time() - os.path.getmtime(bf)) > _DL_MEM_TTL:
            return None
        import json as _json
        with open(mf, "r", encoding="utf-8") as fh:
            meta = _json.load(fh)
        with open(bf, "rb") as fh:
            data = fh.read()
        if not data:
            return None
        try:
            os.utime(bf, None)                                   # LRU touch
        except Exception:                                        # noqa: BLE001
            pass
        return data, meta
    except Exception:                                            # noqa: BLE001
        return None


def disk_put(url: str, data, meta, tag: str = "") -> None:
    """Disk par likho (chhote files hi — bade hub/RAM se)."""
    try:
        if not data or len(data) > _DISK_MAX_FILE:
            return
        import json as _json
        d = _disk_dir()
        k = _disk_key(url, tag)
        with open(os.path.join(d, k + ".bin"), "wb") as fh:
            fh.write(data)
        with open(os.path.join(d, k + ".json"), "w", encoding="utf-8") as fh:
            _json.dump(_safe_meta(meta), fh, ensure_ascii=False, default=str)
        _disk_gc()
    except Exception:                                            # noqa: BLE001
        pass


def _safe_meta(meta) -> dict:
    """meta ko JSON-safe banao (bytes/objects hatao)."""
    out = {}
    for k, v in (meta or {}).items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, (list, tuple)) and all(isinstance(x, (str, int, float, bool)) for x in v):
            out[k] = list(v)
    out.pop("bytes", None)
    return out


def disk_cache_stats() -> dict:
    try:
        d = _disk_dir()
        n = mb = 0
        for f in os.listdir(d):
            try:
                mb += os.path.getsize(os.path.join(d, f))
                n += 1
            except Exception:                                    # noqa: BLE001
                pass
        return {"files": n, "mb": round(mb / 1048576, 1)}
    except Exception:                                            # noqa: BLE001
        return {"files": 0, "mb": 0}


# =====================================================================================
#  v74.3: 🏁 PARALLEL RACE — jo engine pehle result de, wahi jeete (sum ki jagah max)
# =====================================================================================
def _race(fns, timeout: float = 25.0):
    """Memory-safe race: max 2 engines active; next starts only after a failure.

    Old code ek saath 8 engines kholta tha; ek hi link ke multiple full video
    downloads + background losers Render free ki 512MB limit paar kara sakte the.
    Winner milte hi queued engines cancel; fallback list/quality intact.
    """
    from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
    fns = [f for f in (fns or []) if callable(f)]
    if not fns:
        return None
    if len(fns) == 1:
        try:
            r = fns[0]()
            return r if (r and r.get("ok")) else None
        except Exception:                                        # noqa: BLE001
            return None
    workers = min(2, len(fns))
    ex = ThreadPoolExecutor(max_workers=workers)
    todo = iter(fns)
    active = {}
    deadline = time.monotonic() + max(0.1, float(timeout))
    try:
        for _ in range(workers):
            try:
                fn = next(todo)
            except StopIteration:
                break
            active[ex.submit(fn)] = fn
        while active:
            remain = deadline - time.monotonic()
            if remain <= 0:
                break
            done, _ = wait(tuple(active), timeout=remain, return_when=FIRST_COMPLETED)
            if not done:
                break
            winner = None
            for fut in done:
                active.pop(fut, None)
                try:
                    result = fut.result()
                except Exception:                                # noqa: BLE001
                    result = None
                if result and result.get("ok"):
                    winner = result
                    break
                try:
                    fn = next(todo)
                except StopIteration:
                    continue
                active[ex.submit(fn)] = fn
            if winner is not None:
                return winner
    except Exception:                                            # noqa: BLE001
        pass
    finally:
        for fut in active:
            fut.cancel()
        try:
            ex.shutdown(wait=False, cancel_futures=True)
        except TypeError:                                        # Python <3.9 fallback
            ex.shutdown(wait=False)
    return None


SOCK_TIMEOUT = 7          # v74.3: ek connection par max 7 second (jaldi fallback)


def _ytdlp_opts(extra=None, clients=None):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": SOCK_TIMEOUT,
        "concurrent_fragment_downloads": 16,   # v65: 4 -> 16 chunks parallel
        "buffersize": 1024 * 1024,
        "http_chunk_size": 10485760,           # 10 MB ke chunks me maango
        "extractor_retries": 1,
        "noprogress": True,
        "nopart": False,
        "nocheckcertificate": True,
        "extract_flat": False,
        "retries": 1,                          # v65: 2 -> 1 (jaldi fallback)
        "fragment_retries": 3,
        "geo_bypass": True,
        "http_headers": {"User-Agent": DESKTOP_UA["User-Agent"]},
    }
    # v65: YouTube player-client (bot check ka asli ilaaj)
    opts["extractor_args"] = {
        "youtube": {
            "player_client": list(clients or YT_CLIENT_SETS[0]),
            "player_skip": ["configs"],
        },
    }
    cf = _cookiefile()
    if cf:
        opts["cookiefile"] = cf
    if _HAS_FFMPEG:
        opts["ffmpeg_location"] = _FFMPEG_LOC
    if extra:
        opts.update(extra)
    return opts


def _info_one(url: str, clients):
    """Ek client set se info — thread me chalta hai."""
    if not _ytdlp():
        return None
    try:
        with yt_dlp.YoutubeDL(_ytdlp_opts({"skip_download": True},
                                          clients=clients)) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:                                        # noqa: BLE001
        _remember(e)              # v56: friendly message ke liye wajah
        _mark_client_bad(clients, str(e))
        return None


def _ytdlp_info(url: str, clients=None):
    """Info nikalo — YouTube par bot-check se bachne ke liye client ladder.

    v68: 🚀 ab clients EK SAATH (parallel) try hote hain — jo pehle safal
    wahi jeeta. Pehle ek-ek karke 4 x 3s = 12s barbaad hota tha.
    """
    if not _ytdlp():
        return None
    _u = (url or "").lower()
    _is_yt = ("youtube.com" in _u) or ("youtu.be" in _u)
    _sets = (clients,) if clients else (YT_CLIENT_SETS if _is_yt else (None,))
    _sets = _ordered_client_sets(_sets)          # bad clients aakhir me

    if len(_sets) > 1:
        from concurrent.futures import ThreadPoolExecutor
        _ex = ThreadPoolExecutor(max_workers=min(3, len(_sets)))
        try:
            _futs = {_ex.submit(_info_one, url, _cl): _cl for _cl in _sets}
            try:
                from concurrent.futures import as_completed
                for _f in as_completed(_futs, timeout=FAST_DEADLINE):
                    _info = _f.result()
                    if _info:
                        return _info
            except Exception:                                     # noqa: BLE001
                pass
        finally:
            _ex.shutdown(wait=False)      # baaki threads background me khatam
        return None

    # non-YouTube (Instagram etc.) — jaisa tha waisa
    for _cl in _sets:
        for attempt in range(2 if _cl is None else 1):
            _info = _info_one(url, _cl)
            if _info:
                return _info
            if _cl is None and attempt == 0:
                time.sleep(2)             # Instagram 429 rate-limit ke liye
    return None


def _ytdlp_download_bytes(url: str, max_mb: int = MAX_TG_MB):
    """yt-dlp se download karke bytes deta hai. Bada file ho to (None, meta) deta hai."""
    if not _ytdlp():
        return None, None
    tmp = tempfile.mkdtemp(prefix="udl_")
    try:
        cap = max_mb - 3
        if _HAS_FFMPEG:
            # 360p + audio merge (YouTube ab progressive formats nahi deta, isliye merge zaroori hai)
            # v59: pehle PROGRESSIVE (single file, merge nahi) — YouTube ab bhi
            # 360p/720p progressive (itag 18/22) deta hai. Merge karne se ffmpeg
            # chalta hai jo 3x slow tha. Progressive mile to wahi lo.
            fmt = ("18/"                                   # 360p mp4 + audio (fastest)
                   "22/"                                   # 720p mp4 + audio
                   f"b[ext=mp4][filesize_approx<{cap}M]/"
                   f"b[filesize_approx<{cap}M]/"
                   f"bv*[height<=360][filesize_approx<{cap//2}M]+ba[filesize_approx<{cap//2}M]/"
                   "bv*[height<=480]+ba/bv*[height<=360]+ba/"
                   "b[height<=360]/b/best")
        else:
            # ffmpeg nahi hai -> sirf single-file (progressive) formats, warna merge fail hota hai
            fmt = (f"b[ext=mp4][filesize<{cap}M]/b[ext=mp4][filesize_approx<{cap}M]/"
                   f"b[filesize<{cap}M]/b[filesize_approx<{cap}M]/"
                   "b[height<=360]/b[height<=480]/b[height<=720]/b/best")
        # v68: cache check — yahi link pehle download hua ho to TURANT
        #      (pehle yahan galti se `h` likha tha jo is function me nahi hai
        #       — us se YouTube tool NameError de deta tha. Ab theek.)
        _cached = _mem_get(url, "plain")
        if _cached:
            return _cached
        # v66/v68: har client se koshish — bad clients aakhir me
        _sets = _ordered_client_sets(tuple(YT_CLIENT_SETS[:3])) if _is_yt_url(url) else (None,)
        _hard_end = time.time() + FAST_DEADLINE
        info = None
        path = None
        for _i, _cl in enumerate(_sets):
            if _i and time.time() > _hard_end:
                break
            _budget = FAST_DEADLINE if _i == 0 else 8
            _deadline = min(_hard_end, time.time() + _budget)

            def _hook(st, _dl=_deadline):                         # noqa: BLE001
                if time.time() > _dl:
                    raise TimeoutError("fast-deadline")

            opts = _ytdlp_opts({
                "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
                "format": fmt,
                "noplaylist": True,
                "merge_output_format": "mp4" if _HAS_FFMPEG else None,
                "quiet": True,
                "no_warnings": True,
                "ignoreerrors": False,
            }, clients=_cl)
            opts["progress_hooks"] = [_hook]
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                path = _pick_file(tmp)
                if path:
                    if os.path.getsize(path) > max_mb * 1024 * 1024:
                        return None, info
                    with open(path, "rb") as fh:
                        data = fh.read()
                    _mem_put(url, data, info, "plain")     # v68: agli baar instant
                    return data, info
            except Exception as e:                                # noqa: BLE001
                _remember(e)
                _mark_client_bad(_cl, str(e))       # v68: bot-check wala hata do
                if not _retryable(str(e)):
                    break
        return None, info
    except Exception as e:                                    # noqa: BLE001
        _remember(e)          # v56: friendly message ke liye wajah yaad rakho
        return None, None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _pick_file(tmp: str):
    """v65: download ke baad sahi file chuno — .part/.ytdl not, merge par .mp4 pehle."""
    try:
        good = []
        for f in os.listdir(tmp):
            fp = os.path.join(tmp, f)
            if not os.path.isfile(fp) or f.endswith((".part", ".ytdl", ".temp")):
                continue
            sz = os.path.getsize(fp)
            if sz >= 1000:
                good.append((f.endswith(".mp4"), sz, fp))
        if not good:
            return None
        good.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return good[0][2]
    except Exception:                                            # noqa: BLE001
        return None


def _ytdlp_direct_link(url: str):
    """Bada file: direct CDN link nikaal deta hai (browser me turant chalega)."""
    info = _ytdlp_info(url)
    if not info:
        return None, None, None
    fmts = info.get("formats") or []

    def _progressive(f):
        proto = (f.get("protocol") or "").lower()
        return ("m3u8" not in proto) and ("dash" not in proto) and f.get("vcodec") not in (None, "none") \
               and f.get("acodec") not in (None, "none")

    pool = [f for f in fmts if f.get("url") and _progressive(f)]
    if not pool:
        pool = [f for f in fmts if f.get("url") and f.get("vcodec") not in (None, "none")]
    best = None
    for f in sorted(pool, key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True):
        best = f
        break
    if not best and fmts:
        best = fmts[-1]
    if best:
        size = best.get("filesize") or best.get("filesize_approx")
        if not size:
            tbr = best.get("tbr") or 0
            dur = info.get("duration") or 0
            if tbr and dur:
                size = (tbr * 1000 / 8) * dur          # bits/sec -> bytes
        return best.get("url"), info.get("title") or "Video", size
    return info.get("url"), info.get("title") or "Video", None


def _ig_ytdlp(clean: str, media_cat: str):
    info = _ytdlp_info(clean)
    if not info:
        return None
    try:
        entries = info.get("entries") or []
        # Instagram carousel / multi-media post
        if entries and len(entries) > 1:
            items = []
            for e in entries[:20]:   # v86: IG carousel max 20 (pehle 10)
                # v95: pehle KIND dekho — photo entry ko video-format download
                # se mat khincho ("No video formats found" aata tha = photo skip)
                is_vid = (e.get("vcodec") not in (None, "none")) or (e.get("ext") in ("mp4", "mov", "webm"))
                if is_vid:
                    u = e.get("url") or e.get("webpage_url")
                    if not u:
                        continue
                    # v86: per-item 15MB cap (20 items x 48MB = OOM pakka tha)
                    data, _meta = _ytdlp_download_bytes(u, max_mb=15)
                    if not data:
                        continue
                    items.append({"type": "video", "bytes": data})
                else:
                    _raw3 = _ytdlp_direct_image_bytes(e)   # v95: seedha CDN (yt-dlp photo par fail hota hai)
                    if not _raw3:
                        continue
                    _jb3 = _jpeg_fit(_raw3)   # v86: size-capped JPEG
                    if _jb3:
                        items.append({"type": "photo", "bytes": _jb3})
            if items:
                return {"ok": True, "type": "carousel", "category": media_cat,
                        "title": info.get("title") or "", "items": items, "count": len(items),
                        "platform": "Instagram", "engine": "yt-dlp"}
            return None

        data, info2 = _ytdlp_download_bytes(clean, max_mb=MAX_TG_MB)
        if not data or len(data) <= 1000:
            # v95: photo post par video-format download fail ("No video formats
            # found") — info me jo seedha CDN/format URL hai wahi pakad lo
            _raw1 = _ytdlp_direct_image_bytes(info)
            if _raw1 and len(_raw1) > 1000:
                data, info2 = _raw1, (info2 or info)
        if data and len(data) > 1000:
            is_vid = bool(info2 and (info2.get("vcodec") not in (None, "none")))
            if is_vid:
                return {"ok": True, "type": "video", "category": "reel" if media_cat == "reel" else "video",
                        "title": (info2 or {}).get("title") or info.get("title") or "",
                        "bytes": data, "size_mb": _size_mb(data),
                        "platform": "Instagram", "engine": "yt-dlp"}
            try:
                _photo = _jpeg_fit(data, max_px=2400, quality=94)
                if not _photo:
                    return None
                return {"ok": True, "type": "photo", "category": "post", "title": info.get("title") or "",
                        "bytes": _photo, "size_mb": _size_mb(_photo),
                        "platform": "Instagram", "engine": "yt-dlp"}
            except Exception:
                return None
        return None
    except Exception:
        return None


# =====================================================================================
# ENGINE 3 — og:video / og:image scrape (aakhri fallback)
# =====================================================================================
def _og_scrape(clean: str, media_cat: str, allow_photo: bool = True):
    """og:* tags se media nikaalo.

    v79: `allow_photo=False` par `og:image` (post ka COVER frame) kabhi result
    nahi banta. Pehle aisa hi hota tha: ye branch sirf ek HTML GET hai isliye
    race me hamesha pehle jeet jaata, jabki video engines 10-25 second lete
    hain — natija: user **reel** bhejta aur use **photo** mil jaati.
    """
    for headers in (FB_UA, BOT_UA, DESKTOP_UA):
        try:
            r = httpio.get(clean, headers=headers, timeout=15,
                           allow_redirects=True, stream=True)
            if r.status_code != 200:
                try: r.close()
                except Exception: pass
                continue
            ctype = str(r.headers.get("content-type", "") or "").lower()
            if "video" in ctype or "octet-stream" in ctype:
                _raw_direct = _read_response_capped(r, MAX_TG_MB * 1048576)
                try: r.close()
                except Exception: pass
                if _raw_direct and ("video" in ctype or b"ftyp" in _raw_direct[:32]):
                    return {"ok": True, "type": "video", "category": "reel" if media_cat == "reel" else "video",
                            "bytes": _raw_direct, "size_mb": _size_mb(_raw_direct),
                            "title": "", "platform": "Instagram", "engine": "direct-scrape"}
                continue
            _page = _read_response_capped(r, 2 * 1048576, minimum=500)
            _encoding = getattr(r, "encoding", None) or "utf-8"
            try: r.close()
            except Exception: pass
            if not _page:
                continue
            if b"ftyp" in _page[:32]:
                return {"ok": True, "type": "video", "category": "reel" if media_cat == "reel" else "video",
                        "bytes": _page, "size_mb": _size_mb(_page),
                        "title": "", "platform": "Instagram", "engine": "direct-scrape"}
            _html = _page.decode(_encoding, errors="replace")
            soup = BeautifulSoup(_html, "html.parser")
            og_video = (soup.find("meta", {"property": "og:video"})
                        or soup.find("meta", {"property": "og:video:secure_url"})
                        or soup.find("meta", {"name": "twitter:player:stream"}))
            og_image = soup.find("meta", {"property": "og:image"}) or soup.find("meta", {"name": "twitter:image"})
            title_m = soup.find("meta", {"property": "og:title"})
            title = title_m.get("content", "")[:80] if title_m else ""
            if og_video and og_video.get("content"):
                _rv = _http_get_capped(og_video["content"], MAX_TG_MB,
                                       headers=DESKTOP_UA, timeout=20, want="video")
                if _rv and len(_rv) > 1000:
                    return {"ok": True, "type": "video", "category": "reel" if media_cat == "reel" else "video",
                            "bytes": _rv, "size_mb": _size_mb(_rv), "title": title,
                            "platform": "Instagram", "engine": "og:video"}
            if not allow_photo:
                continue        # video chahiye tha — cover frame se kaam nahi
            if og_image and og_image.get("content"):
                _ri = _http_get_capped(og_image["content"], 15,
                                       headers=DESKTOP_UA, timeout=15, want="image")
                _photo = _jpeg_fit(_ri, max_px=2400, quality=94) if _ri else None
                if _photo:
                    return {"ok": True, "type": "photo", "category": media_cat, "title": title,
                            "bytes": _photo, "size_mb": _size_mb(_photo),
                            "platform": "Instagram", "engine": "og:image"}
        except Exception:
            continue
    return None


# =====================================================================================
# MAIN INSTAGRAM PIPELINE (purana name bhi kaam karta rahega)
# =====================================================================================
def _ig_code_of(url: str) -> str:
    """Instagram post/reel/TV link se shortcode nikalta hai."""
    try:
        if _UC is not None:                            # v85: ganda link saaf karke dekho
            _c = _UC.clean_link(url)
            if _c:
                url = _c
    except Exception:  # noqa: BLE001
        pass
    # v85: instagr.am short links (share sheet se aate hain) bhi chalenge
    m = (re.search(r"instagram\.com/(?:[^/?#]+/)?(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", url or "")
         or re.search(r"instagr\.am/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", url or ""))
    return m.group(1) if m else ""


def _ig_embed(clean: str, media_cat: str):
    """🆕 v79 — 4th engine: public /embed/ page se ASLI video file.

    Instagram ka normal page bot ke IP par 429/login-wall de deta hai, par
    `/embed/` (website par lagane wala page) public rehta hai aur uske andar
    `"videoUrl":"https://scontent...mp4"` hoti hai — seedhi CDN file.
    Isse reel tab bhi aa jaati hai jab parth/yt-dlp/og teeno has jaate hain.
    """
    code = _ig_code_of(clean)
    if not code:
        return None
    cat = "reel" if media_cat == "reel" else (media_cat or "video")
    for path in (f"/reel/{code}/embed/captioned/", f"/p/{code}/embed/captioned/",
                 f"/p/{code}/embed/"):
        try:
            r = httpio.get("https://www.instagram.com" + path, headers=FB_UA,  # v95: crawler UA = data page
                           timeout=14, allow_redirects=True)
            if r.status_code != 200 or len(r.text or "") < 400:
                continue
            html = (r.text or "").replace("\\u0026", "&").replace("\\/", "/")
            m_v = (re.search(r'"videoUrl":"(https?://[^"]+?\.mp4[^"]*)"', html)
                   or re.search(r'"video_versions":\[\{"url":"(https?://[^"]+?)"', html)
                   or re.search(r'"video_url":"(https?://[^"]+?\.mp4[^"]*)"', html))
            if not m_v:   # v103: triple-escaped JSON wale embed variants
                _hd = _deep_unescape(r.text or "")
                m_v = (re.search(r'"video_versions":\s*\[\s*\{\s*"url"\s*:\s*"(https?://[^"]+?)"', _hd)
                       or re.search(r'"video_url"\s*:\s*"(https?://[^"]+?\.mp4[^"]*)"', _hd)
                       or re.search(r'"videoUrl"\s*:\s*"(https?://[^"]+?\.mp4[^"]*)"', _hd))
            if not m_v:
                continue                       # photo post / sirf HLS (kaam ka nahi)
            v_url = m_v.group(1)
            if ".m3u8" in v_url:
                continue                       # HLS ko sirf yt-dlp pack kar sakta hai
            hdr = dict(DESKTOP_UA)
            hdr["Referer"] = "https://www.instagram.com/"
            _rv = _http_get_capped(v_url, MAX_TG_MB, headers=hdr,
                                   timeout=30, want="video")
            if _rv and len(_rv) > 20000:
                t_m = re.search(r'"title":"([^"]{0,80})"', html)
                return {"ok": True, "type": "video", "category": cat,
                        "bytes": _rv, "size_mb": _size_mb(_rv),
                        "title": (t_m.group(1) if t_m else ""),
                        "platform": "Instagram", "engine": "embed-mp4"}
        except Exception:                                          # noqa: BLE001
            continue
    return None


def _ig_wayback(clean: str, media_cat: str):
    """v103: archive.org snapshot se ASLI media (viral/purane posts ka safety net).

    Hamara IP IG block kare to bhi wayback ke paas saved copy mil sakti hai.
    Media URL khud scontent ka ho aur mara hua ho to wayback ke `if_` raw
    redirect se file nikalte hain (wo archive karta hai)."""
    code = _ig_code_of(clean)
    if not code:
        return None
    want_video = media_cat in ("reel", "video", "igtv")
    for path in (f"reel/{code}/", f"p/{code}/"):
        try:
            r = httpio.get("http://archive.org/wayback/available",
                           params={"url": "instagram.com/" + path}, timeout=10)
            import json as _json
            j = _json.loads(r.text or "{}")
            snap = (j.get("archived_snapshots") or {}).get("closest") or {}
            if not snap.get("url"):
                continue
            rs = httpio.get(snap["url"], headers=DESKTOP_UA, timeout=18,
                            allow_redirects=True)
            html = _deep_unescape(rs.text or "")
            if len(html) < 500:
                continue
            mv = (re.search(r'"video_versions":\s*\[\s*\{\s*"url"\s*:\s*"(https?://[^"]+?)"', html)
                  or re.search(r'"video(?:Url|_url)"\s*:\s*"(https?://[^"]+?\.mp4[^"]*)"', html)
                  or re.search(r'(https://scontent[^"\s\\]+?\.mp4[^"\s\\]*)', html))
            if mv:
                v0 = mv.group(1)
                if ".m3u8" not in v0:
                    for cand in (v0, "https://web.archive.org/web/2if_/" + v0):
                        try:
                            hdr = dict(DESKTOP_UA)
                            hdr["Referer"] = "https://web.archive.org/"
                            _rv = _http_get_capped(cand, MAX_TG_MB, headers=hdr,
                                                   timeout=35, want="video")
                            if _rv and len(_rv) > 20000:
                                return {"ok": True, "type": "video",
                                        "category": media_cat or "reel",
                                        "bytes": _rv,
                                        "size_mb": _size_mb(_rv),
                                        "title": "", "platform": "Instagram",
                                        "engine": "wayback"}
                        except Exception:                        # noqa: BLE001
                            continue
            if not want_video:
                mi = re.search(r'(https://scontent[^"\s\\]+?\.(?:jpg|jpeg)[^"\s\\]*)', html)
                if mi:
                    for cand in (mi.group(1),
                                 "https://web.archive.org/web/2if_/" + mi.group(1)):
                        try:
                            _ri = _http_get_capped(cand, 15, headers=DESKTOP_UA,
                                                   timeout=20, want="image")
                            jb = _jpeg_fit(_ri) if _ri else None
                            if jb:
                                return {"ok": True, "type": "photo",
                                        "category": media_cat or "post", "bytes": jb,
                                        "size_mb": _size_mb(jb), "title": "",
                                        "platform": "Instagram", "engine": "wayback"}
                        except Exception:                        # noqa: BLE001
                            continue
        except Exception:                                        # noqa: BLE001
            continue
    return None


def _ig_jina(clean: str, media_cat: str):
    """v103: r.jina.ai (free reader proxy) embed page khulta hai unke IP se —
    hamara datacenter IP IG block kare tab bhi video URL mil jaati hai."""
    code = _ig_code_of(clean)
    if not code:
        return None
    try:
        r = httpio.get(f"https://r.jina.ai/https://www.instagram.com/p/{code}/embed/captioned/",
                       headers={"User-Agent": "Mozilla/5.0", "X-Timeout": "12"},
                       timeout=16)
        txt = _deep_unescape(r.text or "")
        if len(txt) < 300:
            return None
        mv = re.search(r'(https?://[^"\s\)]+?\.mp4[^"\s\)]*)', txt)
        if not mv or ".m3u8" in mv.group(1):
            return None
        hdr = dict(DESKTOP_UA)
        hdr["Referer"] = "https://www.instagram.com/"
        _rv = _http_get_capped(mv.group(1), MAX_TG_MB, headers=hdr,
                               timeout=35, want="video")
        if _rv and len(_rv) > 20000:
            return {"ok": True, "type": "video", "category": media_cat or "reel",
                    "bytes": _rv, "size_mb": _size_mb(_rv),
                    "title": "", "platform": "Instagram", "engine": "jina-embed"}
    except Exception:                                            # noqa: BLE001
        return None
    return None


# =====================================================================================
# v104 🏆 IG HD ENGINE — r.jina.ai ka RENDERED page.
# Datacenter IP par IG hamare page me sirf og:image (640px, e35-compressed)
# deta hai — isliye "post ka link = blurry ek photo" wali shikayat thi.
# Jina apne IP se page FULL render karta hai aur markdown me page ke RAW
# media URLs Leak hote hain: carousel ki HAR photo, 1080px se 3072px tak,
# aur public reels ke mp4 (jab render me aa jaayein). Suggested-post grid
# ko perma-link code check + "Discover something new" marker se kaata hai.
# Private account → {ok:False, private:True} signal (caller honest note lagata hai).
# =====================================================================================
def _ig_efg_res(u: str) -> int:
    """scontent URL ke efg=/stp= token se photo ki resolution (px). Unknown → 640."""
    try:
        import base64 as _b64
        import urllib.parse as _up
        m = re.search(r"[?&]efg=([^&\s)\"']+)", u)
        if m:
            raw = _up.unquote(m.group(1))
            raw += "=" * (-len(raw) % 4)
            j = _b64.b64decode(raw)
            txt = j.decode("utf-8", "ignore")
            m2 = re.search(r"\.(\d{3,4})\.", txt)
            if m2:
                return int(m2.group(1))
        m3 = re.search(r"_s(\d{3,4})x", u)
        if m3:
            return int(m3.group(1))
        m4 = re.search(r"/(\d{3,4})x\d{3,4}/", u)
        if m4:
            return int(m4.group(1))
    except Exception:                                            # noqa: BLE001
        pass
    return 640


def _ig_jina_hd(clean: str, media_cat: str):
    """v104: jina render se post/carousel HD (ya video) — kabhi exception nahi."""
    try:
        if not clean or "instagr" not in clean:
            return None
        r = httpio.get("https://r.jina.ai/" + str(clean).rstrip("/") + "/",
                       headers={"User-Agent": "Mozilla/5.0", "X-Timeout": "18"},
                       timeout=26)
        if r.status_code != 200:
            return None
        txt = _deep_unescape(r.text or "")
        if len(txt) < 300:
            return None
        low_all = txt.lower()
        if "profile is private" in low_all or "account is private" in low_all:
            return {"ok": False, "private": True}
        # region = post ka hissa; 'Discover/Suggested' ke baad sab ANYA post hai
        cut = len(txt)
        for _mk in ("Discover something new", "Suggested for you", "More posts",
                    "You Might Also Like", "See everyday moments"):
            i = txt.find(_mk)
            if i != -1:
                cut = min(cut, i)
        region = txt[:cut]
        our_code = (_ig_code_of(clean) or "").lower()
        hdr = dict(DESKTOP_UA)
        hdr["Referer"] = "https://www.instagram.com/"

        # ---- 1) VIDEO (reel ka mp4 render me aa gaya to) ----
        mv = re.search(r"(https://[^\s)\"']+?\.mp4[^\s)\"']*)", region)
        if mv:
            data = _http_get_capped(mv.group(1), MAX_TG_MB, headers=hdr,
                                    timeout=45, want="video")
            if data and len(data) > 30000:
                _tt = re.search(r'Title:\s*(.{0,70})', txt)
                return {"ok": True, "type": "video", "category": media_cat or "reel",
                        "bytes": data, "size_mb": _size_mb(data),
                        "title": (_tt.group(1).strip() if _tt else ""),
                        "platform": "Instagram", "engine": "jina-hd"}

        # ---- 2) PHOTOS: markdown lines → image URL + uska permalink ----
        cands = {}   # asset media-id -> (res, url)
        for _ln in region.splitlines():
            if ".jpg" not in _ln.lower() and ".jpeg" not in _ln.lower() \
                    and ".png" not in _ln.lower() and ".webp" not in _ln.lower():
                continue
            _ll = _ln.lower()
            if "profile picture" in _ll or "profile_pic" in _ll or "rsrc.php" in _ll:
                continue
            imgs = re.findall(r'!?\[[^\]]*\]\((https?://[^)\s]+\.(?:jpg|jpeg|png|webp)[^)\s]*)', _ln)
            if not imgs:
                imgs = re.findall(r'(https?://[a-z0-9.\-]*(?:cdninstagram|instagram)\.com/[^)\s"\']+\.(?:jpg|jpeg|png|webp)[^)\s"\']*)', _ln)
            if not imgs:
                continue
            link_m = re.search(r'\]\((https?://(?:www\.)?instagr(?:am\.com|\.am)/[^\s)]+)\)\s*$', _ln)
            if link_m and our_code:
                _lc = re.search(r"/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", link_m.group(1))
                if _lc and _lc.group(1).lower() != our_code:
                    continue          # suggested post ki photo — ye post NAHI
            for _u in imgs[:1]:
                if "cdninstagram.com" not in _u and "instagram.com" not in _u:
                    continue
                res = _ig_efg_res(_u)
                fn = re.sub(r"[?#].*$", "", _u).rsplit("/", 1)[-1].lower()
                key_m = re.match(r"\d+_(\d+)_", fn)
                key = (key_m.group(1) if key_m else fn) or _u[:60]
                if key not in cands or res > cands[key][0]:
                    cands[key] = (res, _u)
        if cands:
            items = []
            # v105: user order — "usi quality me jis quality ka post ho".
            # IG original 1080-3072px tak hota hai; Telegram photo-safety ke
            # liye 2400px cap (uske neeche JPEG q93 = practically original).
            # Album ki SAARI photos (IG max 20; hum 12 tak bhejte hain).
            for _res, _u in sorted(cands.values(), key=lambda x: -x[0])[:12]:
                raw = _http_get_capped(_u, 24, headers=hdr, timeout=22, want="image")
                if not raw:
                    continue
                jb = _jpeg_fit(raw, max_px=2400, quality=93)
                if jb:
                    items.append({"type": "photo", "bytes": jb,
                                  "src_res": _res})
            if len(items) >= 2:
                _tt = re.search(r'Title:\s*(.{0,70})', txt)
                return {"ok": True, "type": "carousel", "category": media_cat or "post",
                        "bytes": None, "title": (_tt.group(1).strip() if _tt else ""),
                        "items": items, "count": len(items),
                        "platform": "Instagram", "engine": "jina-hd"}
            if len(items) == 1 and int(items[0].get("src_res") or 640) > 700:
                raw1 = items[0]["bytes"]
                return {"ok": True, "type": "photo", "category": media_cat or "post",
                        "title": "", "bytes": raw1, "size_mb": _size_mb(raw1),
                        "platform": "Instagram", "engine": "jina-hd"}
        return None
    except Exception:                                            # noqa: BLE001
        return None


def _ig_ensure_playable(data: bytes) -> bytes:
    """v105: Telegram streaming ke liye h264 + aac chahiye. loader.to kabhi
    VP9/HEVC deti hai → ffmpeg se H264 re-encode (reels chhoti hoti hain).
    Kuch bigde to original bytes wapas (file chalegi, preview na sahi).
    Kabhi exception nahi phenkta."""
    tmp = None
    try:
        if not _HAS_FFMPEG or not data or len(data) < 50000:
            return data
        tmp = tempfile.mkdtemp(prefix="igp_")
        src = os.path.join(tmp, "in.mp4")
        out = os.path.join(tmp, "out.mp4")
        with open(src, "wb") as f:
            f.write(data)
        cp = subprocess.run([_FFMPEG_LOC, "-hide_banner", "-i", src],
                            capture_output=True, timeout=30)
        txt = (cp.stderr or b"").decode(errors="ignore")
        if re.search(r"Video:\s*h264", txt):
            return data                                   # already playable
        dur = 60.0
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", txt)
        if m:
            dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        cp2 = _ffmpeg_gated(
            [_FFMPEG_LOC, "-y", "-i", src, "-c:v", "libx264", "-preset",
             "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "96k",
             "-movflags", "+faststart", out],
            min(300, 60 + int(dur) * 3))
        if (cp2.returncode == 0 and os.path.exists(out)
                and os.path.getsize(out) > 5000
                and os.path.getsize(out) <= int(MAX_TG_MB) * 1048576):
            with open(out, "rb") as f:
                return f.read()
    except Exception:                                            # noqa: BLE001
        pass
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    return data


def _ig_loader_reel(clean: str, media_cat: str):
    """v105 KA DHAMAKA: loader.to sirf YouTube nahi — Instagram reel/highlight
    ka VIDEO bhi nikaal deta hai (uska server IG-blocked IP nahi hai). Live
    proof 10 Oct: public reel → 12-19s me genuine MP4. Quality wahi jo IG
    anonymous ko deta hai (aksar 360-640p) — par publicly available best yahi
    hai, aur label hum FILE NAAPkar lagate hain (jhooth kabhi nahi)."""
    try:
        if not clean or "instagr" not in clean or not _ig_code_of(clean):
            return None
        import urllib.parse as _up
        api = ("https://loader.to/ajax/download.php?format=1080&url="
               + _up.quote(str(clean).strip(), safe=""))
        r = httpio.get(api, headers=_LOADER_UA, timeout=25)
        if r.status_code != 200:
            return None
        j = r.json()
        if not isinstance(j, dict) or not j.get("success"):
            return None
        purl = j.get("progress_url") or ""
        if not (isinstance(purl, str) and purl.startswith("http")):
            return None
        dl = ""
        end = time.time() + 26.0
        while time.time() < end:
            time.sleep(4)
            try:
                done, dl, _t, _f = _loader_poll_once(purl)
            except Exception:                                    # noqa: BLE001
                continue
            if done:
                break
        if not dl:
            return None
        data = _http_get_capped(dl, MAX_TG_MB, headers=_LOADER_UA, timeout=50,
                                want="video")
        if not data or len(data) < 20000:
            return None
        data = _ig_ensure_playable(data)
        _dur, _w, _h = _probe_data(data)
        _q = f"{_h}p" if _h else "reel"
        return {"ok": True, "type": "video", "category": media_cat or "reel",
                "bytes": data, "size_mb": _size_mb(data),
                "duration": int(_dur or 0), "quality": _q, "title": "",
                "platform": "Instagram", "engine": "loader-ig"}
    except Exception:                                            # noqa: BLE001
        return None


def _jpeg_fit(raw: bytes, max_px: int = 2160, quality: int = 94):  # v105: q90→94 = practically original
    """Photo ko Telegram-safe JPEG banao (badi photo = OOM + 10MB photo limit).

    Returns bytes ya None. Kabhi exception nahi.
    """
    try:
        if not raw or len(raw) < 200:
            return None
        im = Image.open(io.BytesIO(raw))
        w, h = im.size                  # header read: pixels not decoded yet
        # 40MP hard stop avoids a compressed giant image expanding past free RAM.
        if w <= 0 or h <= 0 or w * h > 40_000_000:
            return None
        # Resize BEFORE RGB decode; JPEG draft/thumbnail path can keep the peak small.
        if max(w, h) > max_px:
            im.thumbnail((max_px, max_px), Image.LANCZOS)
        im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality)
        out = buf.getvalue()
        # ab bhi 9MB se bada? quality ghatao (Telegram photo limit ~10MB)
        if len(out) > 9 * 1024 * 1024:
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=75)
            out = buf.getvalue()
        return out if out and len(out) > 200 else None
    except Exception:  # noqa: BLE001
        return None



def _deep_unescape(s: str, rounds: int = 4) -> str:
    """v95: embed HTML triple-escaped JSON hota hai (`\\\"src\\\"`) — stable hone tak kholo."""
    if not isinstance(s, str):
        return ""
    try:
        out = s or ""
        for _ in range(max(1, int(rounds))):
            new = (out.replace("\\u0026", "&").replace("\\/", "/")
                      .replace('\\"', '"').replace("\\\\", "\\"))
            if new == out:
                break
            out = new
        return out
    except Exception:  # noqa: BLE001
        return s or ""


def _ig_album_candidates(html: str):
    """v95: embed HTML se carousel photo URLs — PURE function (network nahi).

    Returns: [url, ...] carousel-order me, deduped, best-quality per photo.
    - NAYA format (2026): `display_resources:[{src,config_width}...]` — har
      photo ke 3-4 size hote hain, sabse bada (1080) uthate hain.
    - PURANA format: `display_url` / `image_versions2` candidates / <img>.
    """
    found = []  # (width, url) — width 0 = unknown (purana pattern)
    if not isinstance(html, str):
        return []
    try:
        h = _deep_unescape(html or "")
    except Exception:  # noqa: BLE001
        return []
    if not h or len(h) < 400:
        return []
    # carousel ho to SIRF sidecar-children window scan karo — window ke baahar
    # ke display_resources related-posts/profile ke hote hain (galat photos!).
    _scan = h
    _sc_at = h.find('"edge_sidecar_to_children"')
    if _sc_at != -1:
        _scan = h[_sc_at:_sc_at + 100000]
    # (1) display_resources blocks — har block = 1 photo, max width lo
    try:
        for _bm in re.finditer(r'"display_resources"\s*:\s*\[(.*?)\]', _scan, re.DOTALL):
            _blk = _bm.group(1)[:8000]
            _pairs = re.findall(r'"src"\s*:\s*"(https?://[^"]+?)"\s*,\s*"config_width"\s*:\s*(\d+)', _blk)
            _pairs += [(_u2, _w2) for (_w2, _u2) in
                       re.findall(r'"config_width"\s*:\s*(\d+)[^}]{0,400}?"src"\s*:\s*"(https?://[^"]+?)"', _blk)]
            _best = None
            for (_u, _w) in _pairs:
                try:
                    _w = int(_w)
                except Exception:  # noqa: BLE001
                    _w = 0
                if _best is None or _w > _best[0]:
                    _best = (_w, _u)
            if _best and _best[1]:
                found.append(_best)
    except Exception:  # noqa: BLE001
        pass
    # blocks mile to baaki patterns bhi window me (related-thumbs na ghuse);
    # na mile to poora page (purana format / single photo)
    _rest = _scan if found else h
    # (2) purana GraphQL display_url
    try:
        for _u in re.findall(r'"display_url"\s*:\s*"(https?://[^"]+?)"',_rest):
            found.append((0, _u))
    except Exception:  # noqa: BLE001
        pass
    # (3) image_versions2 candidates (v85 ka pattern toot gaya tha: `\\.` kabhi
    #     match nahi hota tha kyunki `\/` pehle hi `/` ban chuka hota hai)
    try:
        for _u in re.findall(r'"url"\s*:\s*"(https?://[^"]*?scontent[^"]*?\.(?:jpg|jpeg|png)[^"]*?)"',_rest):
            found.append((0, _u))
    except Exception:  # noqa: BLE001
        pass
    # (4) seedha <img> tags (captioned embed cover render karta hai)
    try:
        for _u in re.findall(r'<img[^>]+src="(https?://[^"]*?scontent[^"]+?)"',_rest):
            found.append((0, _u))
    except Exception:  # noqa: BLE001
        pass
    # filter + dedupe (filename key — alag size ka URL same photo hota hai)
    best = {}
    for (_w, _u) in found:
        try:
            if not _u or " " in _u:
                continue
            _lu = _u.lower()
            if any(_b in _lu for _b in ("profile_pic", "150x150", "s150x", "t51.2885-19")):
                continue
            if 0 < _w < 240:
                continue      # chhoti thumbnail — asli post photo 640+
            _key = re.sub(r"[?#].*$", "", _u.rsplit("/", 1)[-1]) or re.sub(r"[?#].*$", "", _u)
            if _key not in best or _w > best[_key][0]:
                best[_key] = (_w, _u)
        except Exception:  # noqa: BLE001
            continue
    return [_u for (_w, _u) in best.values()]


def _ytdlp_direct_image_bytes(info):
    """v95: yt-dlp info se seedha CDN bytes (photo entries ke liye).

    Photo entry ko `_ytdlp_download_bytes` (VIDEO format string) se khincho to
    `No video formats found` aata hai — isliye formats/thumbnails ka URL seedha
    httpio se uthate hain. Kuch na mile to None (caller agla engine try kare).
    """
    try:
        if not isinstance(info, dict):
            return None
        _cands = []
        if info.get("url"):
            _cands.append(info["url"])
        try:
            for _f in (info.get("formats") or [])[-3:]:
                if isinstance(_f, dict) and _f.get("url"):
                    _cands.append(_f["url"])
        except Exception:  # noqa: BLE001
            pass
        try:
            for _t in (info.get("thumbnails") or [])[-2:]:
                if isinstance(_t, dict) and _t.get("url"):
                    _cands.append(_t["url"])
        except Exception:  # noqa: BLE001
            pass
        for _u in _cands:
            try:
                if not _u or not str(_u).startswith("http"):
                    continue
                _r = _http_get_capped(str(_u), 15, headers=DESKTOP_UA,
                                      timeout=12, want="image")
                if _r and len(_r) > 1000:
                    return _r
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass
    return None


def _ig_embed_album(clean: str, media_cat: str):
    """v85 engine, v95 FIX: carousel ki SAARE photos (/embed/ page se).

    v95: Instagram ne embed HTML badal diya — `display_url` GAYAB, ab har photo
    `display_resources:[{src,config_width}...]` (triple-escaped JSON) me hai.
    Isi wajah se 10-photo carousel par 1 photo milti thi (og:image thumbnail).
    Ab `_ig_album_candidates` naya + purana dono format padhta hai.
    """
    code = _ig_code_of(clean)
    if not code:
        return None
    for path in (f"/p/{code}/embed/captioned/", f"/p/{code}/embed/",
                 f"/reel/{code}/embed/captioned/"):
        for _ua in (FB_UA, DESKTOP_UA):   # v95: 2 UAs (datacenter IP par 429 se bachao)
            try:
                r = httpio.get("https://www.instagram.com" + path, headers=_ua,
                               timeout=14, allow_redirects=True)
                if r.status_code != 200 or len(r.text or "") < 400:
                    continue
                urls = _ig_album_candidates(r.text or "")
                if not urls:
                    continue
                items = []
                for u in urls[:20]:
                    try:
                        _ri = _http_get_capped(u, 15, headers=DESKTOP_UA,
                                               timeout=10, want="image")
                        if not _ri or len(_ri) < 2000:
                            continue
                        jb = _jpeg_fit(_ri)
                        if jb:
                            items.append({"type": "photo", "bytes": jb})
                        if len(items) >= 20:
                            break
                    except Exception:  # noqa: BLE001
                        continue
                if len(items) >= 2:
                    _h2 = _deep_unescape(r.text or "")[:20000]
                    t_m = re.search(r'"title"\s*:\s*"([^"]{0,80})"', _h2)
                    return {"ok": True, "type": "carousel", "category": media_cat or "post",
                            "bytes": None, "title": (t_m.group(1) if t_m else ""),
                            "items": items, "count": len(items),
                            "platform": "Instagram", "engine": "embed-album"}
                if len(items) == 1:
                    # v95: 1 bhi mile to bekaar nahi — single photo hi sahi
                    return {"ok": True, "type": "photo", "category": media_cat or "post",
                            "title": "", "bytes": items[0]["bytes"],
                            "size_mb": _size_mb(items[0]["bytes"]),
                            "platform": "Instagram", "engine": "embed-album-1"}
            except Exception:  # noqa: BLE001
                continue
    return None


def _ig_profile_pic(clean: str, username: str = ""):
    """🆕 v86 — 6th engine: public profile ki HD photo (`profile_pic_url_hd`).

    instagram.com/<username> bhejo → profile photo (1080px HD, public page ke
    andar embedded hoti hai — login nahi chahiye). Private/deleted par None.
    """
    user = username or _ig_profile_user(clean)
    if not user:
        return None
    for headers in (DESKTOP_UA, FB_UA, BOT_UA):
        try:
            r = httpio.get(f"https://www.instagram.com/{user}/", headers=headers,
                           timeout=14, allow_redirects=True)
            if r.status_code != 200 or len(r.text or "") < 500:
                continue
            html = (r.text or "").replace("\\u0026", "&").replace("\\/", "/")
            m = (re.search(r'"profile_pic_url_hd"\s*:\s*"(https?://[^"]+?)"', html)
                 or re.search(r'"profile_pic_url"\s*:\s*"(https?://[^"]+?)"', html))
            if not m:
                # fallback: og:image (profile page ka cover = chhoti profile pic)
                try:
                    soup = BeautifulSoup(r.text, "html.parser")
                    _og = soup.find("meta", {"property": "og:image"})
                    _url = _og.get("content", "") if _og else ""
                except Exception:  # noqa: BLE001
                    _url = ""
                if not _url:
                    continue
            else:
                _url = m.group(1)
            _ri = _http_get_capped(_url, 15, headers=DESKTOP_UA,
                                   timeout=15, want="image")
            if not _ri or len(_ri) < 2000:
                continue
            jb = _jpeg_fit(_ri)
            if not jb:
                continue
            _nm = re.search(r'"full_name"\s*:\s*"([^"]{0,60})"', html)
            return {"ok": True, "type": "photo", "category": "profile",
                    "title": f"@{user}" + (f" ({_nm.group(1)})" if _nm else ""),
                    "bytes": jb, "size_mb": _size_mb(jb),
                    "platform": "Instagram", "engine": "profile-hd"}
        except Exception:  # noqa: BLE001
            continue
    return None


def _ig_kind_ok(res, want_video: bool) -> bool:
    """Race ka referee (v79): category ke hisaab se hi result qabool ho.

    reel/video/story ke liye `type: photo` (cover frame) KABHI jeet nahi
    sakta — isi se "reel bhejo, photo lo" wali shikayat khatam hoti hai.
    """
    if not res or not res.get("ok"):
        return False
    t = str(res.get("type") or "").lower()
    if want_video:
        return t in ("video", "link")
    return t in ("video", "photo", "carousel", "link", "images")


def download_instagram_media(url: str) -> dict:
    # v103: REEL/TV intent ORIGINAL link se pakdo — insta_clean /reel/ → /p/ kar
    #     deta hai, phir classify "post" bolta tha = cover photo jeet jaati thi
    #     (user bug: "reel ka link bheja, photo aa gayi"). Ye flag aage cache +
    #     referee + engine budget sab ko batata hai ki YAHAN VIDEO CHAHIYE.
    _v103_raw = str(url or "")
    _vid_from_raw = bool(re.search(r"instagr(?:am\.com|\.it|am\.am)/(?:reel|reels|tv)/",
                                   _v103_raw, re.I))
    # v85: ganda link (&amp;/markdown/fbclid) pehle saaf — engines ko canonical post URL
    url = _clean_incoming(url)
    try:
        if _UC is not None:
            _ic = _UC.insta_clean(url)
            if _ic:
                url = _ic
    except Exception:  # noqa: BLE001
        pass
    clean = url.split("?")[0].rstrip("/")
    if not clean.startswith("http"):
        clean = "https://" + clean.lstrip("/")
    media_cat = classify_instagram_url(clean)
    if _vid_from_raw and media_cat not in ("reel", "story"):
        media_cat = "reel"          # v103: canonical ne type chhupa liya tha
    want_video = bool(_vid_from_raw or media_cat in ("reel", "video", "igtv")
                      or "/reel" in clean or "/tv/" in clean)
    # v86: PROFILE link (/username) → HD profile photo (login nahi chahiye)
    if media_cat == "profile":
        # v106: IG FAST engine pehle — 1 API call me HD photo (~1s)
        if IGF is not None:
            try:
                _ppf = IGF.fetch_profile_pic(_ig_profile_user(clean))
                if _ppf and _ppf.get("ok"):
                    return _ppf
            except Exception:                                     # noqa: BLE001
                pass
        _pp = _ig_profile_pic(clean)
        if _pp and _pp.get("ok"):
            return _pp
        _pu = _ig_profile_user(clean) or "ye"
        return {"ok": False, "category": "profile",
                "error": (f"📸 @{_pu} ki profile photo nahi mili — account private/deleted ho "
                          "sakta hai, ya username me spelling mistake. Public profile ka sahi link bhejo.")}
    # v106: STORY FAST-FAIL — Instagram story bina LOGIN cookie ke koi bhi
    # service nahi de sakti (IG ki apni privacy limit). Pehle 30-55 second ki
    # race chalti thi aur phir bhi fail — ab TURANT saaf jawab milta hai.
    # Cookie lagi ho (/cookies ya IG_COOKIE env) to story bhi isi engine se
    # aati hai — race me IGF.fetch_media story engine ban kar chalta hai.
    if media_cat == "story" and IGF is not None and not IGF.has_login_cookie():
        return {"ok": False, "category": "story", "need_login": True,
                "error": ("🔐 Instagram STORY bina login ke kisi ko nahi milti — ye "
                          "Instagram ki apni privacy limit hai (story sirf logged-in "
                          "logon ko dikhti hai).\n\n"
                          "✅ ILAAJ: Bot me apni Instagram cookie lagao — /cookies "
                          "command bhejo, wahan poora tarika likha hai. Cookie lagte "
                          "hi story + highlight download ON ho jaayega.\n\n"
                          "ℹ️ Reel/post ka link bhejoge to wo bina cookie ke bhi "
                          "1-5 second me aa jaayega.")}

    # v74.3: cache check (RAM → DISK) — dobara link par turant
    # v103: cache par BHI referee lagta hai — reel ke liye purani "cover photo"
    #     cache kabhi serve nahi hogi (galat entry turant delete bhi ho jaati hai).
    _mc = _mem_get(clean, "ig") or disk_get(clean, "ig")
    if _mc and not _ig_kind_ok(dict(_mc[1] or {}), want_video):
        try:
            with _DL_MEM_LOCK:
                _DL_MEM.pop(_mem_key(clean, "ig"), None)
            _dk = _disk_key(clean, "ig")
            if _dk and os.path.exists(_dk):
                os.remove(_dk)
        except Exception:                                        # noqa: BLE001
            pass
        _mc = None
    if _mc:
        _d, _m = _mc
        _o = dict(_m or {})
        _o.update({"ok": True, "bytes": _d, "size_mb": _size_mb(_d), "cached": True})
        return _o

    # v74.3: 🏁 teeno engine EK SAATH (pehle ek-ek karke 25+ second lag jate the)
    # v77: poora race HEAVY GATE ke andar — ek request 3 engines (parth +
    #      yt-dlp + scrape) ek saath chalata hai; 3-4 users ek saath aayein to
    #      RAM 512 MB (free plan) phat jaati thi = OOM kill = "bot crash".
    hit = None

    # v79: reel/video/story ke liye sirf VIDEO result qabool hota hai (referee
    # `_ig_kind_ok`) — isse "reel bhejo, cover photo lo" wala bug khatam.
    # 4th engine `_ig_embed` bhi juda (public /embed/ page, login wall ke paar),
    # aur budget 22s -> 26s kiya, kyunki video engines aksar 23-25s lete the
    # = deadline ke bahar = bekaar "fail". (User ne 33s tak progress dekha tha.)
    # v86: "story" want_video se HATA — photo-story bhi hoti hai! (Pehle photo wali
    # story referee se reject ho jaati thi = "story download fail" ki ek wajah.)

    def _eng(fn):
        """Engine ka result referee se guzaaro; na-qabil-e-qabool ho to None."""
        def _g():
            try:
                r = fn()
            except Exception:                                   # noqa: BLE001
                return None
            return r if _ig_kind_ok(r, want_video) else None
        return _g

    # v104: og ka slot ab "pehle jina-HD (public post = poori album HD),
    #         phir hi blurry 640px og" — HD available hote hi og kabhi
    #         nahi jeetega; private account par honest 🔒 note ke saath og.
    _jina_note = {}

    def _hd_then_og():
        try:
            jr = _ig_jina_hd(clean, media_cat)
        except Exception:                                        # noqa: BLE001
            jr = None
        if jr and jr.get("private"):
            _jina_note["private"] = True
            jr = None
        if _ig_kind_ok(jr, want_video):
            return jr
        o = _og_scrape(clean, media_cat, allow_photo=not want_video)
        if o and o.get("ok") and _jina_note.get("private") and not o.get("note"):
            o = dict(o)
            o["note"] = ("🔒 Ye post PRIVATE account ki hai — Instagram server "
                         "khud sirf preview photo deta hai. Public accounts ki "
                         "posts/carousels full HD (saari photos) aati hain.")
        return o

    # v105.2: fast/public path pehle — parth carousel/reel aksar 1-5s me milta
    # hai. yt-dlp sabse aakhir me; common post success par uski ~39MB import aur
    # background fetch start hi nahi hoti. Loader.to video bhi yt-dlp se pehle.
    # v106: ⚡ IG FAST ENGINE SABSE PEHLE — Instagram ke apne JSON API se
    # post/reel/TV/carousel 1-5s me (pehle race 20-55s leta tha). 429 cooldown
    # par ye 0.001s me None deta hai, phir purane engines waise hi chalte hain.
    # v107: 📊 LIVE AUDIT (10 Oct 2026, datacenter IP se naap kar):
    #   parth-dl      1.5-1.7s ✅ (carousel 6 items + reel video 6.6 MB)
    #   embed_album   0.7-1.2s ✅ (carousel; reel par sirf cover photo)
    #   og_scrape     ~1.1s    ✅ (photo only, low-res)
    #   ig_fast API   0.4-0.6s ❌ (datacenter IP par login-wall — cookie ke bina)
    #   yt-dlp        3-5s     ❌ (IG par login-wall; "No video formats")
    #   loader-ig     ~30s     ✅ (reel video — LAST RESCUE, slow par zinda)
    #   wayback/jina  0-9s     ❌ (null)
    #   ⇒ order = jo asal me jeetta hai pehle; slow rescue aakhir me.
    #   Budget: video 55→40s (loader 30s rescue + margin), post 34→26s.
    _fns = []
    if IGF is not None:
        _fns.append(_eng(lambda: IGF.fetch_media(clean, media_cat)))
    if want_video:
        _fns.extend([_eng(lambda: _ig_parth(clean, media_cat)),
                     _eng(lambda: _ig_embed(clean, media_cat)),
                     _eng(lambda: _ig_ytdlp(clean, media_cat)),
                     _eng(lambda: _ig_loader_reel(clean, media_cat)),
                     _eng(lambda: _ig_jina_hd(clean, media_cat)),
                     _eng(lambda: _ig_wayback(clean, media_cat))])
        _budget = 40.0   # v107: 55→40 (loader-ig 30s rescue + 10s margin)
    else:
        _fns.extend([_eng(lambda: _ig_parth(clean, media_cat)),
                     _eng(lambda: _ig_embed_album(clean, media_cat)),
                     _eng(lambda: _ig_embed(clean, media_cat)),
                     _eng(_hd_then_og),
                     _eng(lambda: _ig_ytdlp(clean, media_cat)),
                     _eng(lambda: _ig_jina_hd(clean, media_cat))])
        _budget = 26.0   # v107: 34→26 (photo engines sab <2s me jeet-te hain)

    try:
        from modules.core import heavy as _hg
    except Exception:                                            # noqa: BLE001
        _hg = None
    if _hg is None:
        hit = _race(_fns, timeout=_budget)
    else:
        try:
            with _hg.gate("media"):
                hit = _race(_fns, timeout=_budget)
        except _hg.HeavyBusy:
            return {"ok": False, "busy": True,
                    "error": _hg.HeavyBusy("timeout").user_msg}

    # v85: race me \"single photo\" jeet gaya par /p/ post carousel ho sakta hai
    # (6-7 photos me se 1 mili = user ki shikayat) — album engine se ek baar
    # aur dekho; 2+ milein to wahi bhejo.
    if hit and not want_video and hit.get("type") == "photo" and media_cat == "post":
        try:
            _alb = _ig_embed_album(clean, media_cat)
            if _alb and _alb.get("ok") and len(_alb.get("items") or []) >= 2:
                hit = _alb
        except Exception:  # noqa: BLE001
            pass

    if hit:
        try:
            if hit.get("bytes"):
                _m2 = {k: v for k, v in hit.items() if k != "bytes"}
                _mem_put(clean, hit["bytes"], _m2, "ig")
                disk_put(clean, hit["bytes"], _m2, "ig")
        except Exception:                                        # noqa: BLE001
            pass
        return hit

    if media_cat == "story":
        return {"ok": False, "category": "story",
                "error": ("📸 Instagram Story nahi mili. 3 wajah ho sakti hain: (1) Story 24 ghante "
                          "me expire ho gayi, (2) account private hai, (3) Instagram ne bina-login "
                          "story block kar di. Reel/photo post ka link bhejo — wo pakka chalega.")}
    if media_cat == "reel":
        return {"ok": False, "category": "reel",
                "error": ("⚠️ Is Reel ka VIDEO Instagram ke server se nahi mila "
                          "(login-wall / embed off / post limited). 30-60 second baad "
                          "dobara try karo.\n\n"
                          "ℹ️ Reel par kabhi galat cheez (cover photo) nahi bhejenge — "
                          "isliye ye error dikh raha hai. Post/story ka link hamesha chalega.")}
    return {"ok": False, "category": media_cat,
            "error": "📸 Media nahi nikal paya — dekho post public hai kya (private/age-restrict post nahi chalti)."}


def _read_response_capped(r, cap_bytes: int, minimum: int = 1001):
    """Existing streamed response -> bounded bytes; caller closes response."""
    try:
        _buf = bytearray()
        for chunk in r.iter_content(262144):
            if chunk:
                _buf += chunk
            if len(_buf) > int(cap_bytes):
                return None
        return bytes(_buf) if len(_buf) >= int(minimum) else None
    except Exception:                                            # noqa: BLE001
        return None


def _http_get_capped(url: str, max_mb: int, headers=None, timeout: int = 40,
                     want: str = "video"):
    """v96: URL se bytes (size cap + content-type guard). Fail → None (kabhi exception nahi)."""
    try:
        cap = int(max_mb) * 1048576
        if not url or not str(url).startswith("http") or cap <= 0:
            return None
        r = httpio.get(str(url), headers=headers or DESKTOP_UA, timeout=timeout, stream=True)
        try:
            if r.status_code != 200:
                return None
            try:
                ct = str(r.headers.get("content-type") or "").lower()
            except Exception:  # noqa: BLE001
                ct = ""
            if "text/html" in ct:
                return None
            if want == "video" and ct and ("video" not in ct) and ("octet-stream" not in ct):
                return None
            if want == "image" and ct and ("image" not in ct) and ("octet-stream" not in ct):
                return None
            # v105.2: bytearray in-place grow; full cap is checked while streaming.
            return _read_response_capped(r, cap, minimum=1001)
        finally:
            try:
                r.close()
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001
        return None


def _tt_tikwm(url: str, max_mb: int = MAX_TG_MB):
    """v96: TikTok via tikwm keyless API — video (no-watermark) + photo slideshow.

    yt-dlp TikTok par aksar block hota hai (datacenter IP); tikwm ka API seedha
    CDN mp4 deta hai. Fail → None (caller yt-dlp fallback chalata hai).
    """
    try:
        import urllib.parse as _up
        if not url or "tiktok.com" not in str(url).lower():
            return None
        api = "https://www.tikwm.com/api/?url=" + _up.quote(str(url).strip(), safe="")
        r = httpio.get(api, timeout=25)
        if r.status_code != 200:
            return None
        try:
            j = r.json()
        except Exception:  # noqa: BLE001
            return None
        if not isinstance(j, dict) or j.get("code") != 0:
            return None
        d = j.get("data") or {}
        if not isinstance(d, dict):
            return None
        title = str(d.get("title") or "")
        if not title:
            try:
                au = d.get("author") or {}
                if isinstance(au, dict) and au.get("nickname"):
                    title = "@" + str(au.get("nickname"))
            except Exception:  # noqa: BLE001
                pass
        try:
            dur = int(d.get("duration") or 0)
        except Exception:  # noqa: BLE001
            dur = 0
        # (1) photo slideshow — images[] (yt-dlp ye support hi nahi karta)
        imgs = d.get("images") or []
        # v97: photo-post par PHOTOS jeettin hain (play to auto-slideshow hai) —
        # user ne photo link bheja = saari photos (IG carousel jaisa)
        if imgs:
            items = []
            for iu in imgs[:10]:
                try:
                    raw = _http_get_capped(iu, 15, timeout=20, want="image")
                    if not raw:
                        continue
                    jb = _jpeg_fit(raw)
                    if jb:
                        items.append({"type": "photo", "bytes": jb})
                except Exception:  # noqa: BLE001
                    continue
            if len(items) >= 2:
                return {"ok": True, "type": "carousel", "platform": "TikTok", "title": title,
                        "items": items, "count": len(items), "engine": "tikwm-photo"}
            if len(items) == 1:
                return {"ok": True, "type": "photo", "platform": "TikTok", "title": title,
                        "bytes": items[0]["bytes"], "size_mb": _size_mb(items[0]["bytes"]),
                        "engine": "tikwm-photo"}
            return None
        # (2) video — best-that-fits (HD bada ho to chhota try karo)
        for key in ("hdplay", "play", "wmplay"):
            vu = d.get(key)
            if not vu or not str(vu).startswith("http"):
                continue
            data = _http_get_capped(vu, max_mb,
                                    headers={"User-Agent": "Mozilla/5.0",
                                             "Referer": "https://www.tiktok.com/"},
                                    timeout=60, want="video")
            if data:
                return {"ok": True, "type": "video", "platform": "TikTok", "title": title,
                        "bytes": data, "size_mb": _size_mb(data), "duration": dur,
                        "quality": ("HD" if key == "hdplay"
                                    else ("no-watermark" if key == "play" else "watermark")),
                        "engine": "tikwm"}
        return None
    except Exception:  # noqa: BLE001
        return None


def _fb_native(url: str, max_mb: int = MAX_TG_MB):
    """v96: Facebook public video — page ke browser_native_hd/sd_url = seedha mp4.

    fbcdn links login-free hote hain (oe= expiry ke saath). Reel/watch/share sab
    chalte hain (redirect follow hota hai). Fail → None (yt-dlp fallback).
    """
    try:
        u = str(url or "").strip()
        lu = u.lower()
        if ("facebook.com" not in lu and "fb.watch" not in lu) or len(u) < 20:
            return None
        r = httpio.get(u, headers=DESKTOP_UA, timeout=25, allow_redirects=True)
        if r.status_code != 200 or len(r.text or "") < 5000:
            return None
        h = (r.text or "").replace("\\u0026", "&").replace("\\/", "/")
        vu = ""
        for pat in (r'"browser_native_hd_url"\s*:\s*"(https?://[^"]+)"',
                    r'"browser_native_sd_url"\s*:\s*"(https?://[^"]+)"'):
            m = re.search(pat, h)
            if m:
                vu = m.group(1)
                break
        if not vu:
            return None
        data = _http_get_capped(vu, max_mb, timeout=60, want="video")
        if not data:
            return None
        title = ""
        try:
            import html as _h
            tm = re.search(r'<meta property="og:title"[^>]+content="([^"]{1,120})', r.text or "")
            if tm:
                title = _h.unescape(_h.unescape(tm.group(1)))
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "type": "video", "platform": "Facebook", "title": title,
                "bytes": data, "size_mb": _size_mb(data), "engine": "fb-native"}
    except Exception:  # noqa: BLE001
        return None


# =====================================================================================
# v97: YOUTUBE COOKIELESS ENGINE (loader.to job + poll + download)
# =====================================================================================
# YouTube datacenter IP par "Sign in to confirm you're not a bot" deta hai (cookies
# ke bina yt-dlp mar jaata hai). loader.to ka ajax endpoint bina-login 360/720/1080p
# mp4 bana deta hai: job start → progress poll → savenow CDN link → download.
# Same IP se generate + download = captcha nahi aata (hub ke link doosre IP se
# khincho to captcha aata tha — isi liye hub path mara hua tha).
_LOADER_UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/120.0 Safari/537.36"),
              "Referer": "https://loader.to/"}
_LOADER_JOBS = {}
_LOADER_LOCK = threading.Lock()


def _lkey(url: str) -> str:
    """YouTube URL → video id (cache/job key). Non-YT → ''."""
    try:
        u = str(url or "")
        m = (re.search(r"[?&]v=([A-Za-z0-9_-]{6,20})", u)
             or re.search(r"youtu\.be/([A-Za-z0-9_-]{6,20})", u)
             or re.search(r"/(?:shorts|embed|live|v)/([A-Za-z0-9_-]{6,20})", u))
        return m.group(1) if m else ""
    except Exception:  # noqa: BLE001
        return ""


def _loader_height(h) -> int:
    """Maangi height → loader format (360/480/720/1080)."""
    try:
        h = int(h)
    except Exception:  # noqa: BLE001
        return 360
    if h >= 1080:
        return 1080
    if h >= 720:
        return 720
    if h >= 480:
        return 480
    return 360


def _loader_start(url: str, height: int):
    """loader.to job start → progress_url ya None (fast-fail)."""
    try:
        if not _lkey(url):
            return None
        import urllib.parse as _up
        api = ("https://loader.to/ajax/download.php?format=%d&url=%s"
               % (_loader_height(height), _up.quote(str(url).strip(), safe="")))
        r = httpio.get(api, headers=_LOADER_UA, timeout=25)
        if r.status_code != 200:
            return None
        j = r.json()
        if not isinstance(j, dict):
            return None
        purl = j.get("progress_url") or ""
        return purl if isinstance(purl, str) and purl.startswith("http") else None
    except Exception:  # noqa: BLE001
        return None


def _loader_poll_once(purl: str):
    """Ek poll → (done, download_url, title, format_echo)."""
    r = httpio.get(purl, headers=_LOADER_UA, timeout=25)
    j = r.json()
    if not isinstance(j, dict):
        return False, "", "", ""
    dl = j.get("download_url") or ""
    done = (j.get("success") == 1) or bool(dl)
    return done, (dl if isinstance(dl, str) else ""), str(j.get("title") or ""), str(j.get("format") or "")


def _loader_run(url: str, height: int, wait: float):
    """gen + poll loop (max ~wait sec) → (download_url, title, format)."""
    purl = _loader_start(url, height)
    if not purl:
        return None, "", ""
    end = time.time() + max(6.0, float(wait or 0))
    title, fmt, errs = "", "", 0
    while time.time() < end:
        time.sleep(5)
        try:
            done, dl, title, fmt = _loader_poll_once(purl)
        except Exception:  # noqa: BLE001
            errs += 1
            if errs >= 3:
                break
            continue
        errs = 0
        if done:
            return (dl or None), title, fmt
    return None, title, fmt


def _loader_cache_put(key, state, dl="", title="", fmt=""):
    try:
        with _LOADER_LOCK:
            _LOADER_JOBS[key] = (state, dl, time.time(), title, fmt)
            if len(_LOADER_JOBS) > 50:   # Fortress: cache kabhi unlimited nahi
                for _k in sorted(_LOADER_JOBS, key=lambda x: _LOADER_JOBS[x][2])[:15]:
                    _LOADER_JOBS.pop(_k, None)
    except Exception:  # noqa: BLE001
        pass


def yt_loader_prewarm(url: str, height: int = 720) -> bool:
    """Picker dikhte hi background job (non-blocking) — tap par turant pickup."""
    try:
        vid = _lkey(url)
        if not vid:
            return False
        key = (vid, _loader_height(height))
        with _LOADER_LOCK:
            st = _LOADER_JOBS.get(key)
            if st and time.time() - st[2] < 1500:
                return True
        _loader_cache_put(key, "run")

        def _job():
            try:
                dl, title, fmt = _loader_run(url, _loader_height(height), 150)
                _loader_cache_put(key, ("done" if dl else "fail"), dl or "", title, fmt)
            except Exception:  # noqa: BLE001
                _loader_cache_put(key, "fail")
        threading.Thread(target=_job, daemon=True).start()
        return True
    except Exception:  # noqa: BLE001
        return False


def _yt_loader(url: str, height: int = 360, wait: float = 30, max_mb: int = MAX_TG_MB):
    """Warm job pickup, warna inline run. Returns video-dict ya None."""
    try:
        vid = _lkey(url)
        if not vid:
            return None
        h = _loader_height(height)
        key = (vid, h)
        with _LOADER_LOCK:
            st = _LOADER_JOBS.get(key)
        dl, title, fmt = "", "", ""
        if st and st[0] == "done" and time.time() - st[2] < 1500 and st[1]:
            dl, title, fmt = st[1], st[3], st[4]
        elif st and st[0] == "run" and time.time() - st[2] < 1500:
            end = time.time() + max(6.0, float(wait or 0))
            while time.time() < end:
                time.sleep(4)
                with _LOADER_LOCK:
                    st2 = _LOADER_JOBS.get(key)
                if not st2:
                    break
                if st2[0] == "done" and st2[1]:
                    dl, title, fmt = st2[1], st2[3], st2[4]
                    break
                if st2[0] == "fail":
                    break
        else:
            dl, title, fmt = _loader_run(url, h, wait)
        if not dl:
            return None
        data = _http_get_capped(dl, max_mb, headers=_LOADER_UA, timeout=60, want="video")
        if not data:
            return None
        return {"ok": True, "type": "video", "platform": "YouTube", "title": title or "",
                "bytes": data, "size_mb": _size_mb(data),
                # v104: loader.to ka v2 API ab ASLI 720/1080 deta hai (live nap:
                # format=720 → 1280x720 @ ~1 Mbps). Purana "720→360p" darr-map
                # hisaab galat kar raha tha; asli label ab _yt_honest decide
                # karega (file naap kar).
                "quality": f"{h}p",
                "engine": "loader.to"}
    except Exception:  # noqa: BLE001
        return None


# =====================================================================================
# v98 REAL-HD — loader ladder (360/480/720) NAKLI nikla, sirf 1080 ASLI hai.
# Live proof (8 Oct, ffprobe): "720"→360x640, "480"→240x426, "360"→144x256,
# "1080"→608x1080 asli @8Mbps. Isliye: 1080-master lao → verify → ffmpeg HD.
# =====================================================================================
_HD_MASTER_CAP_MB = 700    # master disk par stream (RAM-safe); 15-min 1080 ≈ 900MB
_HD_MAX_DUR = 900          # 15 min se lambi video ka HD possible nahi (honest message)


def _ff_probe(path):
    """`ffmpeg -i` ke stderr se (duration-sec, width, height). Fail → (0,0,0)."""
    try:
        if not _HAS_FFMPEG or not path or not os.path.exists(path):
            return 0, 0, 0
        cp = subprocess.run([_FFMPEG_LOC, "-hide_banner", "-i", str(path)],
                            capture_output=True, timeout=30)
        txt = ((cp.stderr or b"").decode(errors="ignore"))[-3000:]
        dur = 0.0
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", txt)
        if m:
            dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        w = h = 0
        m2 = re.search(r"Video:.*?,\s*(\d{2,5})x(\d{2,5})[,\s]", txt)
        if m2:
            w, h = int(m2.group(1)), int(m2.group(2))
        return dur, w, h
    except Exception:  # noqa: BLE001
        return 0, 0, 0


def _hd_pick(master_mb, master_h, req):
    """Single-shot target: sabse badi height jo ~46MB me samaaye. Junk → 360."""
    try:
        mb = float(master_mb or 0)
        mh = int(master_h or 0)
        rq = int(req or 0)
    except Exception:  # noqa: BLE001
        return 360
    if mb <= 0 or mh <= 0:
        return 360
    lad = [h for h in (1080, 720, 480, 360) if h <= rq] or [360]
    for h in lad:
        est = mb * ((h / mh) ** 2) * 0.45
        if est <= 46:
            return h
    return 360


def _dl_to_path(url, path, max_mb, headers=None, timeout=120, want="video"):
    """Stream-to-disk (RAM-safe) + size cap + content-type guard. Ok → True."""
    try:
        cap = int(max_mb) * 1048576
        if not url or not str(url).startswith("http") or cap <= 0:
            return False
        r = httpio.get(str(url), headers=headers or DESKTOP_UA, timeout=timeout,
                       stream=True)
        try:
            if r.status_code != 200:
                return False
            try:
                ct = str(r.headers.get("content-type") or "").lower()
            except Exception:  # noqa: BLE001
                ct = ""
            if "text/html" in ct:
                return False
            if want == "video" and ct and ("video" not in ct) and ("octet-stream" not in ct):
                return False
            n = 0
            with open(path, "wb") as f:
                for chunk in r.iter_content(262144):
                    if chunk:
                        f.write(chunk)
                        n += len(chunk)
                    if n > cap:
                        return False
            return n > 1000
        finally:
            try:
                r.close()
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001
        return False


def _hd_transcode(master, out, tgt, dur):
    """ffmpeg disk→disk HD. Ok → True (output ≥5KB), warna False."""
    try:
        cp = _ffmpeg_gated(
            [_FFMPEG_LOC, "-y", "-i", master, "-vf", f"scale=-2:{int(tgt)}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out],
            min(900, 120 + int(dur or 0) * 10))
        return (cp.returncode == 0 and os.path.exists(out)
                and os.path.getsize(out) >= 5000)
    except Exception:  # noqa: BLE001
        return False


def _yt_loader_hd(url, height=720, wait=120, max_mb=MAX_TG_MB):
    """v98 REAL HD: 1080-master → verify → ffmpeg target.

    Returns video-dict, ya {"ok": False, "fatal": True} (bahut lambi video),
    ya None (legacy chain try karo)."""
    tmp = None
    try:
        vid = _lkey(url)
        if not vid:
            return None
        try:
            rq = int(height or 720)
        except Exception:  # noqa: BLE001
            rq = 720
        req = 1080 if rq >= 1080 else (720 if rq >= 720 else (480 if rq >= 480 else 360))
        if not _HAS_FFMPEG:
            return None
        # --- 1080-master: prewarm pickup, warna inline job ---
        key = (vid, 1080)
        with _LOADER_LOCK:
            st = _LOADER_JOBS.get(key)
        dl, title = "", ""
        if st and st[0] == "done" and time.time() - st[2] < 1500 and st[1]:
            dl, title = st[1], st[3]
        elif st and st[0] == "run" and time.time() - st[2] < 1500:
            end = time.time() + max(10.0, float(wait or 0))
            while time.time() < end:
                time.sleep(4)
                with _LOADER_LOCK:
                    st2 = _LOADER_JOBS.get(key)
                if not st2:
                    break
                if st2[0] == "done" and st2[1]:
                    dl, title = st2[1], st2[3]
                    break
                if st2[0] == "fail":
                    break
        else:
            dl, title, _fmt = _loader_run(url, 1080, wait)
        if not dl:
            return None
        tmp = tempfile.mkdtemp(prefix="yhd_")
        master = os.path.join(tmp, "master.mp4")
        if not _dl_to_path(dl, master, _HD_MASTER_CAP_MB, headers=_LOADER_UA,
                           timeout=180):
            return None
        dur, _w, mh = _ff_probe(master)
        if mh < 700:   # master nakli/chhota → legacy chain
            return None
        if dur > _HD_MAX_DUR:
            return {"ok": False, "fatal": True,
                    "error": ("🎞️ Ye video bahut lambi hai "
                              f"({int(dur) // 60} min) — HD me convert possible nahi. "
                              "Chhoti videos/Shorts bhejo, turant HD milegi. "
                              "Credit nahi katta.")}
        mmb = os.path.getsize(master) / 1048576
        if req == 1080 and mmb <= int(max_mb):
            with open(master, "rb") as f:
                data = f.read()
            return {"ok": True, "type": "video", "platform": "YouTube",
                    "title": title or "", "bytes": data, "size_mb": _size_mb(data),
                    "duration": int(dur), "quality": "1080p", "engine": "loader-hd"}
        tgt = _hd_pick(mmb, mh, req)
        out = os.path.join(tmp, "hd.mp4")
        if not _hd_transcode(master, out, tgt, dur):
            return None
        if os.path.getsize(out) / 1048576 > int(max_mb):
            tgt2 = {1080: 720, 720: 480, 480: 360}.get(tgt)   # estimate miss → ek neeche
            if not tgt2:
                return None
            out2 = os.path.join(tmp, "hd2.mp4")
            if not _hd_transcode(master, out2, tgt2, dur):
                return None
            if os.path.getsize(out2) / 1048576 > int(max_mb):
                return None
            out, tgt = out2, tgt2
        with open(out, "rb") as f:
            data = f.read()
        d = {"ok": True, "type": "video", "platform": "YouTube",
             "title": title or "", "bytes": data, "size_mb": _size_mb(data),
             "duration": int(dur), "quality": f"{tgt}p HD", "engine": "loader-hd"}
        if tgt < req:
            d["note_quality"] = (f"{req}p me file 48MB se badi thi — "
                                 f"asli {tgt}p HD bheja hai")
        return d
    except Exception:  # noqa: BLE001
        return None
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


# =====================================================================================
# UNIVERSAL DOWNLOADER (Instagram + YouTube + FB + X + TikTok + ...)
# =====================================================================================
def _download_video_media_raw(url: str, max_mb: int = MAX_TG_MB) -> dict:
    url = _clean_incoming(url)   # v85: &amp;/markdown/fbclid saaf
    # v47: YouTube ke liye hub ka naya /youtube-download (hub v2.2 — proxy link IP-lock free)
    if re.search(r"(youtube\.com|youtu\.be)/", url):
        # v68: hub ko sirf 6 second — jawab na aaye to tez local engine chalta hai
        _hres = _call_capped(_hub_youtube_download, 6, url, max_mb) or {"ok": False}
        if _hres.get("ok"):
            return _hres
        # v97: cookieless loader (hub thanda/mara ho tab bhi YT chale)
        try:
            _lres = _yt_loader(url, 720, wait=30, max_mb=max_mb)
        except Exception:  # noqa: BLE001
            _lres = None
        if _lres and _lres.get("ok"):
            return _lres

    # --- Instagram: 3-engine chain ---
    if is_instagram_url(url):
        res = download_instagram_media(url)
        if res.get("ok"):
            return res
        # Chain fail -> yt-dlp direct link (bada file / login wall case)
        link, title, size = _ytdlp_direct_link(url)
        if link:
            return {"ok": True, "type": "link", "platform": "Instagram", "title": title or "",
                    "size_mb": round((size or 0) / (1024 * 1024), 2) if size else 0,
                    "direct_url": link, "note": "Video mil gayi par upload limit se badi hai — ye direct link use karo (browser me turant chalegi).",
                    "reason": res.get("error", "")}
        return res

    # v96: TikTok — tikwm keyless API pehle (fast + watermark-free); fail → yt-dlp neeche
    if "tiktok.com" in url.lower():
        try:
            _tt = _tt_tikwm(url, max_mb)
        except Exception:  # noqa: BLE001
            _tt = None
        if _tt and _tt.get("ok"):
            return _tt
    # v96: Facebook — native mp4 scrape pehle; fail → yt-dlp neeche
    _lu96 = url.lower()
    if "facebook.com" in _lu96 or "fb.watch" in _lu96:
        try:
            _fb = _fb_native(url, max_mb)
        except Exception:  # noqa: BLE001
            _fb = None
        if _fb and _fb.get("ok"):
            return _fb
    # --- Baaki platforms: yt-dlp ---
    if not _ytdlp():
        return {"ok": False, "error": "yt-dlp engine load nahi hua (requirements.txt install check karo)."}

    # v74.3: 🚀 pehle DOWNLOAD hi try karo — pehle info (3-10s) phir download (3-10s)
    #        dono hota tha = double wajib time. Ab ek hi extraction me kaam hota hai.
    plat = platform_name(url)
    data1, info1 = _ytdlp_download_bytes(url, max_mb=max_mb)
    if data1 and len(data1) > 1000:
        return {"ok": True, "type": "video", "platform": plat,
                "title": (info1 or {}).get("title") or "",
                "bytes": data1, "size_mb": _size_mb(data1),
                "duration": (info1 or {}).get("duration") or 0,
                "engine": "yt-dlp (fast)"}

    info = _ytdlp_info(url)
    # v82: TikTok PHOTO/slideshow post — yt-dlp ye support nahi karta; og:image se photo bhejo
    if not info and "tiktok.com" in url.lower() and "/photo/" in url.lower():
        _ph = _og_scrape(url, "photo", allow_photo=True)
        if _ph and _ph.get("ok") and _ph.get("bytes"):
            return _ph
    if not info:
        return {"ok": False, "error": friendly_dl_error(
            "yt-dlp ye link handle nahi kar paya")}

    # Playlist / carousel (max 10)
    entries = info.get("entries") or []
    if entries and len(entries) > 1:
        items = []
        for e in entries[:10]:
            u = e.get("url") or e.get("webpage_url")
            if not u:
                continue
            data, meta = _ytdlp_download_bytes(u, max_mb=max_mb)
            if data and len(data) > 1000:
                is_h = (e.get("vcodec") not in (None, "none"))
                if is_h:
                    items.append({"type": "video", "bytes": data})
                else:
                    items.append({"type": "video", "bytes": data})
        if items:
            return {"ok": True, "type": "carousel", "platform": plat, "title": info.get("title") or "",
                    "items": items, "count": len(items), "engine": "yt-dlp"}

    data, info2 = _ytdlp_download_bytes(url, max_mb=max_mb)
    if data and len(data) > 1000:
        return {"ok": True, "type": "video", "platform": plat, "title": info.get("title") or "",
                "bytes": data, "size_mb": _size_mb(data), "duration": info.get("duration") or 0,
                "engine": "yt-dlp"}

    # Bada file ya download fail -> direct link do
    link, title, size = _ytdlp_direct_link(url)
    if link:
        mb = round((size or 0) / (1024 * 1024), 2) if size else 0
        return {"ok": True, "type": "link", "platform": plat, "title": title or "",
                "direct_url": link, "size_mb": mb,
                "note": (f"File {mb} MB ki hai (Telegram upload limit {max_mb} MB). "
                         "Neeche wale direct link se browser ya IDM me download kar lo.") if mb else
                        "Direct link taiyar hai — browser ya IDM me turant download ho jayegi."}
    return {"ok": False, "error": "Download failed. The site blocked it or the link is private."}


def _download_video_gated(url: str, max_mb: int = MAX_TG_MB) -> dict:
    """v77: `_download_video_media_raw` + HEAVY GATE (OOM se bachao).

    Kyun: download karte waqt yt-dlp file ko /tmp me likhta hai, phir poora
    bytes RAM me aata hai (48 MB limit) + merge ho to ffmpeg bhi chalta hai.
    Ek request ka peak ~150 MB. 512 MB wale free instance par 3-4 log ek
    saath link bhejein to Linux OOM killer BOT ko hi maar deta tha — isliye
    bot "baar-baar crash" karta hua lagta tha (asli mein RAM bhaari ho gayi
    thi, code me bug nahi). Ab 2 kaam ek saath chalte hain, baaki 25 second
    queue me rukte hain (user ko saaf 'busy' jawab, credit nahi katta),
    isliye RAM chhat ko chhoo-ti hi nahi.
    """
    try:
        from modules.core import heavy as _hg
    except Exception:                                          # noqa: BLE001
        _hg = None
    if _hg is None:
        return _download_video_media_raw(url, max_mb)
    try:
        with _hg.gate("media"):
            return _download_video_media_raw(url, max_mb)
    except _hg.HeavyBusy:
        return {"ok": False, "busy": True,
                "error": _hg.HeavyBusy("timeout").user_msg}


async def download_instagram_async(url: str) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, download_instagram_media, url)


def _remote_size(url: str, ua: str = "Mozilla/5.0 (bot)") -> int:
    """File ka size bina poora download kiye (Range request + Content-Length/-Range)."""
    try:
        r = httpio.get(url, headers={"User-Agent": ua, "Range": "bytes=0-1048575"},
                         timeout=25, stream=True)
        try:
            cr = r.headers.get("Content-Range") or ""
            m = re.search(r"/(\d+)\s*$", cr)
            if m:
                return int(m.group(1))
            cl = r.headers.get("Content-Length")
            if cl and str(r.status_code) == "200":
                return int(cl)
            if cl and str(r.status_code) == "206" and "/" not in cr:
                return int(cl)
            return 0
        except Exception:  # noqa: BLE001
            return 0
        finally:
            r.close()
    except Exception:  # noqa: BLE001
        return 0


def _hub_youtube_download(url: str, max_mb: int) -> dict:
    """v48: YouTube best (1080p FHD) quality — hub v2.4 ke loader.to 1080p links se.

    Order: 1080p → 480p backup → direct link (bada file). Truncated video kabhi nahi bhejte.
    """
    try:
        from modules import api_hub as hub
    except Exception:
        return {"ok": False}
    if not hub.hub_ready():
        return {"ok": False}
    info = hub.hub_yt_download(url, kind="video")
    if not info.get("ok"):
        return {"ok": False}
    q = str(info.get("quality") or "").strip()
    hd = bool(info.get("hd"))
    eng = f"hub ({info.get('source', 'youtube-download')}" + (f" • {q}" if q else "") + ")"
    cap = int(max_mb * 1048576)

    cands = []
    for _u, _ql in ((info.get("best_url"), q),
                    (info.get("direct_url"), q),
                    (info.get("backup_url"), info.get("backup_quality") or "")):
        if _u and _u not in [c[0] for c in cands]:
            cands.append((_u, _ql))

    for cand, ql in cands:
        try:
            size = _remote_size(cand)
            if size and size > cap:                     # 1080p > 48MB → agla (chhota) link try karo
                continue
            r = httpio.get(cand, timeout=600,
                             headers={"User-Agent": "Mozilla/5.0 (bot)",
                                      "Referer": "https://loader.to/"}, stream=True)
            if r.status_code != 200:
                continue
            # v96: loader backend ab captcha-HTML deta hai (video nahi) —
            # aise link turant chhodo (pehle 52KB HTML "video" ban jaata tha)
            try:
                _ct96 = str(r.headers.get("content-type") or "").lower()
            except Exception:  # noqa: BLE001
                _ct96 = ""
            if "text/html" in _ct96:
                try:
                    r.close()
                except Exception:  # noqa: BLE001
                    pass
                continue
            _buf = bytearray()
            too_big = False
            for chunk in r.iter_content(262144):
                if chunk:
                    _buf += chunk
                if len(_buf) > cap:                     # limit cross → truncated file NAHI bhejenge
                    too_big = True
                    break
            try:
                r.close()
            except Exception:  # noqa: BLE001
                pass
            if too_big or len(_buf) <= 10_000:
                continue
            data = bytes(_buf)
            return {"ok": True, "type": "video", "platform": "YouTube",
                    "title": info.get("title") or "", "bytes": data, "size_mb": _size_mb(data),
                    "duration": info.get("duration") or 0,
                    "quality": ql or ("1080p" if hd else ""),
                    "engine": eng}
        except Exception:                                  # noqa: BLE001
            continue

    # Sab links limit se bade → direct link (user browser/IDM se poora 1080p lega)
    big = info.get("best_url") or info.get("direct_url") or ""
    if big:
        sz = _remote_size(big)
        mb = round(sz / 1048576, 2) if sz else 0
        return {"ok": True, "type": "link", "platform": "YouTube",
                "title": info.get("title") or "", "direct_url": big, "size_mb": mb,
                "quality": q, "engine": eng,
                "note": (f"Video {q or 'HD'} quality me ready hai — file {mb} MB ki hai "
                         f"(Telegram upload limit {max_mb} MB). Neeche wale direct link se "
                         "poora video 1080p me download ho jayega.") if mb else
                        "Video ready hai — direct link se poori quality me download karein."}
    return {"ok": False}


def download_video_media(url: str, max_mb: int = MAX_TG_MB) -> dict:
    """v74.3: 3-layer cache — RAM → DISK → network. Dobara link = TURANT (restart ke baad bhi)."""
    _c = _mem_get(url, "media")
    if _c:
        _data, _meta = _c
        _out = dict(_meta or {})
        _out.update({"ok": True, "bytes": _data, "size_mb": _size_mb(_data),
                     "cached": True})
        return _out
    _d = disk_get(url, "media")                 # v74.3: restart ke baad bhi instant
    if _d:
        _data, _meta = _d
        _out = dict(_meta or {})
        _out.update({"ok": True, "bytes": _data, "size_mb": _size_mb(_data),
                     "cached": True})
        _mem_put(url, _data, _meta, "media")    # RAM me bhi daal do (agle liye)
        return _out
    _res = _download_video_gated(url, max_mb)
    try:
        if _res.get("ok") and _res.get("bytes"):
            _meta = {k: v for k, v in _res.items() if k != "bytes"}
            _mem_put(url, _res["bytes"], _meta, "media")
            disk_put(url, _res["bytes"], _meta, "media")        # v74.3: disk par bhi
    except Exception:                                            # noqa: BLE001
        pass
    return _res


async def download_video_async(url: str, max_mb: int = MAX_TG_MB) -> dict:
    """v68: cache + timeout — 30 second se zyada kabhi nahi rukta."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, download_video_media, url, max_mb)


# ============================================================
#  v52: 🎞️ YOUTUBE QUALITY SELECTOR (360/480/720/1080)
# ============================================================
# YouTube ab sirf best (1080p+) deta hai. Ab user khud quality chunta hai —
# bot available heights fetch karta hai, user tap karta hai, usi height me download.

# User ke liye standard options (upar jo available ho wo hi dikhenge)
YT_QUALITY_OPTIONS = [1080, 720, 480, 360]


# v59: YouTube quality CACHE — pehle har baar 5-20 second lagta tha
_YT_QUAL_CACHE: dict = {}
_YT_QUAL_LOCK = __import__("threading").Lock()
_YT_QUAL_TTL = 6 * 3600          # 6 ghante


def yt_cached_qualities(url: str) -> list:
    """Cache me qualities hain to turant do, warna [] (kabhi block nahi karta)."""
    try:
        k = (url or "").strip()
        if not k:
            return []
        hit = _YT_QUAL_CACHE.get(k)
        if hit and (time.time() - hit[0]) < _YT_QUAL_TTL:
            return list(hit[1])
    except Exception:                                          # noqa: BLE001
        pass
    return []


def yt_warm_qualities(url: str) -> None:
    """Background me qualities nikaal ke cache me daal do (user ko wait nahi)."""
    try:
        def _job():
            try:
                q = yt_available_qualities(url)
                if q:
                    with _YT_QUAL_LOCK:
                        _YT_QUAL_CACHE[(url or "").strip()] = (time.time(), list(q))
                        if len(_YT_QUAL_CACHE) > 300:
                            for kk in sorted(_YT_QUAL_CACHE,
                                             key=lambda x: _YT_QUAL_CACHE[x][0])[:80]:
                                _YT_QUAL_CACHE.pop(kk, None)
            except Exception:                                  # noqa: BLE001
                pass
        import threading
        threading.Thread(target=_job, daemon=True).start()
    except Exception:                                          # noqa: BLE001
        pass


def yt_available_qualities(url: str) -> list:
    """YouTube link ke available heights (standard options me se, high→low).

    Sirf metadata fetch hota hai (video download NAHI) — fast hai.
    Koi option nahi mila to khali list (caller default 1080 use karega).
    """
    if not _ytdlp():
        return []
    try:
        info = _ytdlp_info(url)
        if not info:
            return []
        heights = {f.get("height") for f in (info.get("formats") or []) if f.get("height")}
        opts = [h for h in YT_QUALITY_OPTIONS if h in heights]
        # 1080 se upar bhi available ho to wo bhi dikhao (2160/1440)
        extra = sorted([h for h in heights if h > 1080], reverse=True)[:2]
        return extra + opts
    except Exception:
        return []


def _ffmpeg_gated(cmd: list, timeout: int = 900) -> subprocess.CompletedProcess:
    """v77: heavy gate ke saath ffmpeg chalao.

    Slot na mila (bheed / RAM pressure) -> returncode 124 + `stderr` me saaf
    line. Callers already `returncode != 0` handle karte hain, isliye user ko
    "kaam fail" dikhega — par bot zinda rahega. Purana behaviour: 4 ffmpeg ek
    saath = OOM kill = poora bot restart.
    """
    try:
        from modules.core import heavy as _hg
    except Exception:                                          # noqa: BLE001
        _hg = None
    if _hg is None:
        return subprocess.run(cmd, capture_output=True, timeout=timeout)
    try:
        with _hg.gate("ffmpeg"):
            return subprocess.run(cmd, capture_output=True, timeout=timeout)
    except _hg.HeavyBusy as e:
        return subprocess.CompletedProcess(cmd, 124, b"", str(e.user_msg).encode())


def downscale_video(data: bytes, target_h: int, max_mb: int = MAX_TG_MB) -> dict:
    """MP4 bytes ko chhoti height par scale karo (ffmpeg, bot server par).

    1080p video aaya aur user ne 480p maanga -> ffmpeg se 480p me convert.
    Returns {ok, bytes, size_mb} ya {ok: False, error|too_big}.
    """
    if not _HAS_FFMPEG:
        return {"ok": False, "error": "ffmpeg server par nahi hai"}
    tmp = tempfile.mkdtemp(prefix="qsc_")
    src, out = os.path.join(tmp, "in.mp4"), os.path.join(tmp, "out.mp4")
    try:
        with open(src, "wb") as f:
            f.write(data)
        # v77: ffmpeg encode bhi gate ke andar (1080p -> 480p re-encode sabse
        #      zyada RAM/CPU leta hai; 2-3 log ek saath karein to OOM pakka)
        cp = _ffmpeg_gated(
            [_FFMPEG_LOC, "-y", "-i", src, "-vf", f"scale=-2:{int(target_h)}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out],
            900)
        if cp.returncode != 0 or not os.path.exists(out) or os.path.getsize(out) < 5000:
            return {"ok": False,
                    "error": (cp.stderr or b"").decode(errors="ignore")[-160:]}
        if os.path.getsize(out) > max_mb * 1024 * 1024:
            return {"ok": False, "too_big": True,
                    "size_mb": round(os.path.getsize(out) / 1048576, 2)}
        with open(out, "rb") as f:
            d = f.read()
        return {"ok": True, "bytes": d, "size_mb": _size_mb(d)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _probe_data(data: bytes):
    """v104: bytes ki ASLI resolution naapo (temp file → _ff_probe). Fail → (0,0,0)."""
    tmp = None
    try:
        if not data or len(data) < 4096:
            return 0.0, 0, 0
        tmp = tempfile.mkdtemp(prefix="vhon_")
        p = os.path.join(tmp, "v.mp4")
        with open(p, "wb") as f:
            f.write(data)
        return _ff_probe(p)
    except Exception:                                            # noqa: BLE001
        return 0.0, 0, 0
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def _yt_honest(res: dict, req_h: int) -> dict:
    """v104 TRUST — label file se MILAN hona chahiye, warna jhooth.

    Jo file bheji ja rahi hai uski asli height naapi jaati hai. Asli height
    maangti quality SE KAM nikli → label THEEK hota hai + user ko saaf note.
    (User ki shikayat: '720 choose kiya, 360 jaisa blurry file'.)"""
    try:
        if (not isinstance(res, dict) or not res.get("ok")
                or res.get("type") != "video" or not res.get("bytes")):
            return res
        _d, _w, _h = _probe_data(res["bytes"])
        try:
            req = int(req_h)
        except Exception:  # noqa: BLE001
            req = 0
        if not _h or not req:
            return res
        if _h < req:
            res["quality"] = f"{_h}p"
            res["engine"] = (str(res.get("engine") or "?")) + f" (napa:{_h}p)"
            res["note_quality"] = (
                f"⚠️ Source me sirf ASLI {_h}p maujood tha — {req}p ka nakli "
                "version (blurry upscale) bhejna theek nahi laga. Ye asli "
                f"{_h}p file hai.")
        elif _d and not res.get("duration"):
            res["duration"] = int(_d)
        return res
    except Exception:                                            # noqa: BLE001
        return res


def _yt_quality_download(url: str, height: int, max_mb: int = MAX_TG_MB) -> dict:
    """v68: cache ke saath — wahi video+quality dobara = TURANT."""
    _c = _mem_get(url, f"res{int(height)}")
    if _c:
        _data, _meta = _c
        _out = dict(_meta or {})
        _out.update({"ok": True, "bytes": _data, "size_mb": _size_mb(_data),
                     "cached": True})
        return _out
    _res = _yt_honest(_yt_quality_download_raw(url, height, max_mb), height)  # v104
    try:
        if _res.get("ok") and _res.get("bytes"):
            _meta = {k: v for k, v in _res.items() if k != "bytes"}
            _mem_put(url, _res["bytes"], _meta, f"res{int(height)}")
    except Exception:                                            # noqa: BLE001
        pass
    return _res


def _yt_quality_download_raw(url: str, height: int, max_mb: int = MAX_TG_MB) -> dict:
    """v104 ordering (user ki '720 = blurry' shikayat ka ilaaj):

    1) loader.to seedha MAANGI height par — uska v2 API ab ASLI 720/1080
       deta hai (live naap: 1280x720 @1.1Mbps) aur prewarm-job turant milta
       hai (~10-40s). Purane code me ye master-ladder ke PEECHE daba tha.
    2) Master ladder (1080-master → ffmpeg) — HD (720/1080) par backup.
    3) Direct yt-dlp — fmt "18/22" order fix ke saath (ab 22 pehle).
    4) Hub + downscale — source ki asli height nappkar, upscale kabhi nahi.
    Label hamesha NAAP kar (call-site _yt_quality_download → _yt_honest).
    Result contract = _hub_youtube_download."""
    h = int(height)
    # 1) Loader direct-height (360/480/720/1080 format valid + real, live-verified)
    _l = _yt_loader(url, h, wait=30, max_mb=max_mb)
    if _l and _l.get("ok"):
        return _l
    if h >= 720:
        # 2) HD hi chahiye to master-ladder backup; loader ne size cap me
        #    1080 nahi pakda to bhi yeahi raasta sahi hai
        _hd10 = _yt_loader_hd(url, 1080 if h >= 1080 else 720, wait=120, max_mb=max_mb)
        if _hd10 and _hd10.get("ok"):
            return _hd10
        if _hd10 and _hd10.get("fatal"):
            return _hd10
        if h >= 1080:
            # v68: hub ko 12 second — warna seedha tez engines
            _hd = _call_capped(_hub_youtube_download, 12, url, max_mb)
            if _hd and _hd.get("ok"):
                return _hd
            h = 720
    # 3) Direct local download (YouTube datacenter IP ab allow karta hai)
    data, info = yt_download_at_height(url, h, max_mb)
    if data and len(data) > 1000:
        return {"ok": True, "type": "video", "platform": "YouTube",
                "title": (info or {}).get("title") or "", "bytes": data,
                "size_mb": _size_mb(data), "duration": (info or {}).get("duration") or 0,
                "quality": f"{h}p", "engine": "direct"}
    # 4) Fallback: hub ka best-quality link + bot par ffmpeg downscale
    hubres = _hub_youtube_download(url, max_mb)
    if not hubres.get("ok") or hubres.get("type") != "video" or not hubres.get("bytes"):
        # v56: pehle yahan khali {"ok": False} jaata tha — user ko wajah pata
        # nahi chalti thi (Render log me "Sign in to confirm you're not a bot"
        # tha, user ko sirf "DOWNLOAD FAILED" milta tha).
        if not hubres.get("error"):
            hubres["error"] = friendly_dl_error(platform="YouTube")
        return hubres                                        # link/error waisa hi
    # v104: pehle hub ki file ki ASLI height naapo. Hub aksar 360p "best"
    # deta hai — use ffmpeg se 720 karke "720p" bolna hi wo dhoka tha jiski
    # user ne shikayat ki. Source chhota → waisa hi bhejo (label theek hoga).
    _dh2, _wh2, _hh2 = _probe_data(hubres["bytes"])
    if _hh2 and _hh2 <= h:
        hubres["note_quality"] = (f"Hub ke paas sirf asli {_hh2}p tha — "
                                  f"{h}p ka nakli upscale nahi bheja. "
                                  "Neeche original link se aap khud HD le sakte hain.")
        return hubres
    ds = downscale_video(hubres["bytes"], h, max_mb)
    if not ds.get("ok"):
        if ds.get("too_big"):
            return {"ok": True, "type": "link", "platform": "YouTube",
                    "title": hubres.get("title") or "",
                    "direct_url": hubres.get("direct_url") or "",
                    "size_mb": ds["size_mb"], "quality": f"{h}p",
                    "engine": "hub",
                    "note": (f"{h}p convert hone ke baad bhi file "
                             f"{ds['size_mb']} MB ki hai (Telegram limit {max_mb} MB). "
                             "Neeche ka original link use karo.")}
        hubres["note_quality"] = "chhoti quality convert nahi ho payi — original HD bheja hai"
        return hubres
    hubres["bytes"] = ds["bytes"]
    hubres["size_mb"] = ds["size_mb"]
    hubres["quality"] = f"{h}p"
    hubres["engine"] = (hubres.get("engine") or "hub") + f" → {h}p"
    return hubres


def yt_download_at_height(url: str, height: int, max_mb: int = MAX_TG_MB):
    """Diya gaya height par YouTube video download (bestvideo+audio merge -> mp4).

    Returns (bytes|None, info|None) — _ytdlp_download_bytes jaisa contract.
    """
    if not _ytdlp():
        return None, None
    tmp = tempfile.mkdtemp(prefix="udl_q_")
    try:
        cap = max_mb - 3
        h = int(height)
        if _HAS_FFMPEG:
            # v104 FIX — pehle "18/22/" PEHLE tha = itag 18 (360p) hamesha jeet
            # jaata tha, 720 maangne par bhi BLURRY 360 milta tha. Ab: 22 (asli
            # 720p progressive) pehle, phir height-fitting best, 18 SIRF aakhri
            # sahara (us par bhi label _yt_honest se NAAP kar asli hota hai).
            fmt = ((f"22/" if h >= 720 else "")
                   + f"b[height<={h}][ext=mp4][filesize_approx<{cap}M]/"
                   f"b[height<={h}][filesize_approx<{cap}M]/"
                   f"bv*[height<={h}][filesize_approx<{cap//2}M]+ba[filesize_approx<{cap//2}M]/"
                   f"bv*[height<={h}]+ba/b[height<={h}]/18/b/best")
        else:
            fmt = (f"b[ext=mp4][height<={h}][filesize<{cap}M]/b[height<={h}][filesize_approx<{cap}M]/"
                   f"b[height<={h}]/b/best")
        # v68: cache — yahi video+quality pehle bani ho to TURANT
        _cached = _mem_get(url, f"q{h}")
        if _cached:
            return _cached
        # v66/v68: client ladder — bot-check wale clients aakhir me
        _sets = _ordered_client_sets(tuple(YT_CLIENT_SETS[:3])) if _is_yt_url(url) else (None,)
        _hard_end = time.time() + FAST_DEADLINE
        info = None
        for _i, _cl in enumerate(_sets):
            if _i and time.time() > _hard_end:
                break
            _budget = FAST_DEADLINE if _i == 0 else 8
            _deadline = min(_hard_end, time.time() + _budget)

            def _hook(st, _dl=_deadline):                         # noqa: BLE001
                if time.time() > _dl:
                    raise TimeoutError("fast-deadline")

            opts = _ytdlp_opts({
                "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
                "format": fmt,
                "noplaylist": True,
                "merge_output_format": "mp4" if _HAS_FFMPEG else None,
                "quiet": True,
                "no_warnings": True,
                "ignoreerrors": False,
            }, clients=_cl)
            opts["progress_hooks"] = [_hook]
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                path = _pick_file(tmp)
                if path:
                    if os.path.getsize(path) > max_mb * 1024 * 1024:
                        return None, info
                    with open(path, "rb") as fh:
                        data = fh.read()
                    _mem_put(url, data, info, f"q{h}")
                    return data, info
            except Exception as e:                                # noqa: BLE001
                _remember(e)
                _mark_client_bad(_cl, str(e))
                if not _retryable(str(e)):
                    break
        return None, info
    except Exception as e:                                    # noqa: BLE001
        _remember(e)          # v56: friendly message ke liye wajah yaad rakho
        return None, None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
