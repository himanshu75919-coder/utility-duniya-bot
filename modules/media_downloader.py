# -*- coding: utf-8 -*-
"""
Universal Video & Social Media Downloader Engine (v31 PRO)
==========================================================
Pehle sirf Instagram chalta tha. Ab 3-engine chain + 20+ platforms:

ENGINE CHAIN (Instagram):  parth-dl  ->  yt-dlp  ->  og:video scrape  ->  mirrors
ENGINE (baaki sites):      yt-dlp     (YouTube, Shorts, FB, X/Twitter, TikTok, Snapchat,
                                        Pinterest, Reddit, Vimeo, Dailymotion, Threads...)

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

import requests
from PIL import Image
from bs4 import BeautifulSoup

try:
    import parth_dl
except ImportError:
    parth_dl = None

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

DESKTOP_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}
BOT_UA = {
    "User-Agent": "TelegramBot (like TwitterBot)"
}
FB_UA = {
    "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
}

MAX_TG_MB = 48  # Telegram Bot API upload limit ~50MB (safety margin)

# ffmpeg detection: system ka, warna imageio-ffmpeg ka bundled binary (Render pe bhi chal jata hai)
_FFMPEG_LOC = shutil.which("ffmpeg")
if not _FFMPEG_LOC:
    try:
        import imageio_ffmpeg
        _FFMPEG_LOC = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        _FFMPEG_LOC = None
_HAS_FFMPEG = bool(_FFMPEG_LOC)

SUPPORTED_SITES = (
    "instagram.com", "instagr.am", "youtube.com", "youtu.be", "facebook.com", "fb.watch",
    "twitter.com", "x.com", "tiktok.com", "snapchat.com", "pinterest.com", "pin.it",
    "reddit.com", "redd.it", "vimeo.com", "dailymotion.com", "threads.net", "threads.com",
    "likee.video", "sharechat.com", "mojapp.in", "triller.co", "bilibili.com", "twitch.tv",
    "linkedin.com", "tumblr.com", "vk.com", "ok.ru", "kwai.com", "rumble.com", "streamable.com",
    "imgur.com", "9gag.com", "ifunny.co",
)


# =====================================================================================
# HELPERS
# =====================================================================================
def is_instagram_url(url: str) -> bool:
    u = (url or "").lower()
    return "instagram.com" in u or "instagr.am" in u


def is_supported_video_url(url: str) -> bool:
    u = (url or "").lower()
    return any(s in u for s in SUPPORTED_SITES)


def platform_name(url: str) -> str:
    u = (url or "").lower()
    table = [
        ("instagram.com", "Instagram"), ("instagr.am", "Instagram"), ("youtube.com", "YouTube"),
        ("youtu.be", "YouTube"), ("facebook.com", "Facebook"), ("fb.watch", "Facebook"),
        ("twitter.com", "X (Twitter)"), ("x.com", "X (Twitter)"), ("tiktok.com", "TikTok"),
        ("snapchat.com", "Snapchat"), ("pinterest.com", "Pinterest"), ("pin.it", "Pinterest"),
        ("reddit.com", "Reddit"), ("vimeo.com", "Vimeo"), ("dailymotion.com", "Dailymotion"),
        ("threads.net", "Threads"), ("sharechat.com", "ShareChat"), ("sharechat", "ShareChat"),
        ("likee", "Likee"), ("mojapp.in", "Moj"), ("twitch.tv", "Twitch"), ("linkedin.com", "LinkedIn"),
        ("bilibili.com", "Bilibili"), ("rumble.com", "Rumble"), ("snssh", "Social"),
    ]
    for key, name in table:
        if key in u:
            return name
    try:
        return (url.split("//")[1].split("/")[0]).replace("www.", "").title()
    except Exception:
        return "Social Media"


def classify_instagram_url(url: str) -> str:
    """Classifies Instagram URL into 'reel', 'story', or 'post'"""
    u = url.lower().split("?")[0]
    if "/reel/" in u or "/reels/" in u or "/tv/" in u:
        return "reel"
    if "/stories/" in u:
        return "story"
    if "/p/" in u:
        return "post"
    return "general"


def _cookiefile():
    """Instagram/yt-dlp cookies file (agar user ne env me di ho)."""
    p = (os.getenv("IG_COOKIES_FILE") or os.getenv("YTDLP_COOKIES_FILE") or "").strip()
    if p and os.path.isfile(p):
        return p
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
            for entry in entries[:10]:
                e_kind = entry.get("kind", "")
                e_formats = entry.get("formats", [])
                if e_kind == "video" and e_formats:
                    r_v = requests.get(e_formats[0].get("url"), headers=DESKTOP_UA, timeout=15)
                    if r_v.status_code == 200 and len(r_v.content) > 1000:
                        items.append({"type": "video", "bytes": r_v.content})
                elif e_formats:
                    r_img = requests.get(e_formats[0].get("url"), headers=DESKTOP_UA, timeout=12)
                    if r_img.status_code == 200:
                        try:
                            im = Image.open(io.BytesIO(r_img.content)).convert("RGB")
                            buf = io.BytesIO()
                            im.save(buf, format="JPEG", quality=95)
                            items.append({"type": "photo", "bytes": buf.getvalue()})
                        except Exception:
                            pass
            if not items and info.get("images"):
                for img_obj in info.get("images", [])[:10]:
                    u = img_obj.get("url")
                    if u:
                        r_img = requests.get(u, headers=DESKTOP_UA, timeout=12)
                        if r_img.status_code == 200:
                            try:
                                im = Image.open(io.BytesIO(r_img.content)).convert("RGB")
                                buf = io.BytesIO()
                                im.save(buf, format="JPEG", quality=95)
                                items.append({"type": "photo", "bytes": buf.getvalue()})
                            except Exception:
                                pass
            if items:
                return {"ok": True, "type": "carousel", "category": media_cat, "title": title,
                        "items": items, "count": len(items), "platform": "Instagram", "engine": "parth-dl"}

        # Video / Reel
        if m_type == "video" or (info.get("formats") and len(info["formats"]) > 0):
            formats = info.get("formats", [])
            v_url = formats[0].get("url") if formats else None
            if v_url:
                r_v = requests.get(v_url, headers=DESKTOP_UA, timeout=25)
                if r_v.status_code == 200 and len(r_v.content) > 1000:
                    return {"ok": True, "type": "video", "category": "reel" if media_cat == "reel" else "video",
                            "title": title, "bytes": r_v.content, "size_mb": _size_mb(r_v.content),
                            "platform": "Instagram", "engine": "parth-dl"}

        # Single Photo
        if m_type in ("image", "photo") or (info.get("images") and len(info["images"]) > 0):
            img_url = info["images"][0].get("url") if info.get("images") else None
            if img_url:
                r_img = requests.get(img_url, headers=DESKTOP_UA, timeout=12)
                if r_img.status_code == 200 and len(r_img.content) > 1000:
                    im = Image.open(io.BytesIO(r_img.content)).convert("RGB")
                    buf = io.BytesIO()
                    im.save(buf, format="JPEG", quality=95)
                    return {"ok": True, "type": "photo", "category": "post", "title": title,
                            "bytes": buf.getvalue(), "size_mb": _size_mb(buf.getvalue()),
                            "platform": "Instagram", "engine": "parth-dl"}
    except Exception:
        return None
    return None


# =====================================================================================
# ENGINE 2 — yt-dlp (Instagram + 20+ platforms)
# =====================================================================================
def _ytdlp_opts(extra=None):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 25,
        "nocheckcertificate": True,
        "extract_flat": False,
        "retries": 2,
        "fragment_retries": 2,
        "http_headers": {"User-Agent": DESKTOP_UA["User-Agent"]},
    }
    cf = _cookiefile()
    if cf:
        opts["cookiefile"] = cf
    if _HAS_FFMPEG:
        opts["ffmpeg_location"] = _FFMPEG_LOC
    if extra:
        opts.update(extra)
    return opts


def _ytdlp_info(url: str):
    if not yt_dlp:
        return None
    for attempt in range(2):
        try:
            with yt_dlp.YoutubeDL(_ytdlp_opts({"skip_download": True})) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception:
            if attempt == 0:
                time.sleep(3)   # Instagram 429 rate-limit ke liye thoda wait
                continue
            return None
    return None


def _ytdlp_download_bytes(url: str, max_mb: int = MAX_TG_MB):
    """yt-dlp se download karke bytes deta hai. Bada file ho to (None, meta) deta hai."""
    if not yt_dlp:
        return None, None
    tmp = tempfile.mkdtemp(prefix="udl_")
    try:
        cap = max_mb - 3
        if _HAS_FFMPEG:
            # 360p + audio merge (YouTube ab progressive formats nahi deta, isliye merge zaroori hai)
            fmt = (f"bv*[height<=360][filesize_approx<{cap//2}M]+ba[filesize_approx<{cap//2}M]/"
                   f"b[filesize_approx<{cap}M]/bv*[height<=480]+ba/bv*[height<=360]+ba/"
                   f"b[height<=360]/b/best")
        else:
            # ffmpeg nahi hai -> sirf single-file (progressive) formats, warna merge fail hota hai
            fmt = (f"b[ext=mp4][filesize<{cap}M]/b[ext=mp4][filesize_approx<{cap}M]/"
                   f"b[filesize<{cap}M]/b[filesize_approx<{cap}M]/"
                   "b[height<=360]/b[height<=480]/b[height<=720]/b/best")
        opts = _ytdlp_opts({
            "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
            "format": fmt,
            "noplaylist": True,
            "merge_output_format": "mp4" if _HAS_FFMPEG else None,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
        })
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        path = None
        for f in os.listdir(tmp):
            if os.path.getsize(os.path.join(tmp, f)) > 1000:
                path = os.path.join(tmp, f)
                break
        if not path:
            return None, info
        if os.path.getsize(path) > max_mb * 1024 * 1024:
            return None, info
        with open(path, "rb") as fh:
            return fh.read(), info
    except Exception:
        return None, None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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
            for e in entries[:10]:
                u = e.get("url") or e.get("webpage_url")
                if not u:
                    continue
                data, _meta = _ytdlp_download_bytes(u, max_mb=MAX_TG_MB)
                if not data:
                    continue
                is_vid = (e.get("vcodec") not in (None, "none")) or (e.get("ext") in ("mp4", "mov", "webm"))
                if is_vid:
                    items.append({"type": "video", "bytes": data})
                else:
                    try:
                        im = Image.open(io.BytesIO(data)).convert("RGB")
                        buf = io.BytesIO()
                        im.save(buf, format="JPEG", quality=95)
                        items.append({"type": "photo", "bytes": buf.getvalue()})
                    except Exception:
                        items.append({"type": "photo", "bytes": data})
            if items:
                return {"ok": True, "type": "carousel", "category": media_cat,
                        "title": info.get("title") or "", "items": items, "count": len(items),
                        "platform": "Instagram", "engine": "yt-dlp"}
            return None

        data, info2 = _ytdlp_download_bytes(clean, max_mb=MAX_TG_MB)
        if data and len(data) > 1000:
            is_vid = bool(info2 and (info2.get("vcodec") not in (None, "none")))
            if is_vid:
                return {"ok": True, "type": "video", "category": "reel" if media_cat == "reel" else "video",
                        "title": (info2 or {}).get("title") or info.get("title") or "",
                        "bytes": data, "size_mb": _size_mb(data),
                        "platform": "Instagram", "engine": "yt-dlp"}
            try:
                im = Image.open(io.BytesIO(data)).convert("RGB")
                buf = io.BytesIO()
                im.save(buf, format="JPEG", quality=95)
                return {"ok": True, "type": "photo", "category": "post", "title": info.get("title") or "",
                        "bytes": buf.getvalue(), "size_mb": _size_mb(buf.getvalue()),
                        "platform": "Instagram", "engine": "yt-dlp"}
            except Exception:
                return None
        return None
    except Exception:
        return None


# =====================================================================================
# ENGINE 3 — og:video / og:image scrape (aakhri fallback)
# =====================================================================================
def _og_scrape(clean: str, media_cat: str):
    for headers in (FB_UA, BOT_UA, DESKTOP_UA):
        try:
            r = requests.get(clean, headers=headers, timeout=15, allow_redirects=True)
            if r.status_code != 200 or len(r.content) < 500:
                continue
            ctype = r.headers.get("content-type", "")
            if "video" in ctype or b"ftyp" in r.content[:20]:
                return {"ok": True, "type": "video", "category": "reel" if media_cat == "reel" else "video",
                        "bytes": r.content, "size_mb": _size_mb(r.content),
                        "title": "", "platform": "Instagram", "engine": "direct-scrape"}
            soup = BeautifulSoup(r.text, "html.parser")
            og_video = (soup.find("meta", {"property": "og:video"})
                        or soup.find("meta", {"property": "og:video:secure_url"})
                        or soup.find("meta", {"name": "twitter:player:stream"}))
            og_image = soup.find("meta", {"property": "og:image"}) or soup.find("meta", {"name": "twitter:image"})
            title_m = soup.find("meta", {"property": "og:title"})
            title = title_m.get("content", "")[:80] if title_m else ""
            if og_video and og_video.get("content"):
                r_v = requests.get(og_video["content"], headers=DESKTOP_UA, timeout=20)
                if r_v.status_code == 200 and len(r_v.content) > 1000:
                    return {"ok": True, "type": "video", "category": "reel" if media_cat == "reel" else "video",
                            "bytes": r_v.content, "size_mb": _size_mb(r_v.content), "title": title,
                            "platform": "Instagram", "engine": "og:video"}
            if og_image and og_image.get("content"):
                r_i = requests.get(og_image["content"], headers=DESKTOP_UA, timeout=15)
                if r_i.status_code == 200 and len(r_i.content) > 1000:
                    try:
                        im = Image.open(io.BytesIO(r_i.content)).convert("RGB")
                        buf = io.BytesIO()
                        im.save(buf, format="JPEG", quality=95)
                        return {"ok": True, "type": "photo", "category": media_cat, "title": title,
                                "bytes": buf.getvalue(), "size_mb": _size_mb(buf.getvalue()),
                                "platform": "Instagram", "engine": "og:image"}
                    except Exception:
                        pass
        except Exception:
            continue
    return None


# =====================================================================================
# MAIN INSTAGRAM PIPELINE (purana name bhi kaam karta rahega)
# =====================================================================================
def download_instagram_media(url: str) -> dict:
    clean = url.split("?")[0].rstrip("/")
    if not clean.startswith("http"):
        clean = "https://" + clean.lstrip("/")
    media_cat = classify_instagram_url(clean)

    for engine in (_ig_parth, _ig_ytdlp, _og_scrape):
        try:
            result = engine(clean, media_cat)
        except Exception:
            result = None
        if result and result.get("ok"):
            return result

    if media_cat == "story":
        return {"ok": False, "category": "story",
                "error": "Instagram Story sirf 24 ghante rehti hai. Expire ho gayi ya private story bina login nahi milti."}
    if media_cat == "reel":
        return {"ok": False, "category": "reel",
                "error": ("Instagram ne ye Reel block kar di (rate-limit/login wall). 30-60 second baad dobara try karo, ya doosra link bhejo."
                          "Try again after 30-60 seconds, or set the IG_COOKIES_FILE env to make it always work.")}
    return {"ok": False, "category": media_cat,
            "error": "Media nahi nikal paya — dekho post public hai kya (private/age-restrict post nahi chalti)."}


# =====================================================================================
# UNIVERSAL DOWNLOADER (Instagram + YouTube + FB + X + TikTok + ...)
# =====================================================================================
def download_video_media(url: str, max_mb: int = MAX_TG_MB) -> dict:
    _hubres = _hub_twitter_download(url, max_mb)
    if _hubres.get("ok"):
        return _hubres
    url = (url or "").strip()
    # v47: YouTube ke liye hub ka naya /youtube-download (hub v2.2 — proxy link IP-lock free)
    if re.search(r"(youtube\.com|youtu\.be)/", url):
        _hres = _hub_youtube_download(url, max_mb)
        if _hres.get("ok"):
            return _hres

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

    # --- Baaki platforms: yt-dlp ---
    if not yt_dlp:
        return {"ok": False, "error": "yt-dlp engine load nahi hua (requirements.txt install check karo)."}

    info = _ytdlp_info(url)
    if not info:
        return {"ok": False, "error": "yt-dlp ye link handle nahi kar paya. Link public hai kya check karo."}

    plat = platform_name(url)

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


async def download_instagram_async(url: str) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, download_instagram_media, url)


def _remote_size(url: str, ua: str = "Mozilla/5.0 (bot)") -> int:
    """File ka size bina poora download kiye (Range request + Content-Length/-Range)."""
    try:
        r = requests.get(url, headers={"User-Agent": ua, "Range": "bytes=0-1048575"},
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
            r = requests.get(cand, timeout=600,
                             headers={"User-Agent": "Mozilla/5.0 (bot)",
                                      "Referer": "https://loader.to/"}, stream=True)
            if r.status_code != 200:
                continue
            data = b""
            too_big = False
            for chunk in r.iter_content(262144):
                data += chunk
                if len(data) > cap:                     # limit cross → truncated file NAHI bhejenge
                    too_big = True
                    break
            try:
                r.close()
            except Exception:  # noqa: BLE001
                pass
            if too_big or len(data) <= 10_000:
                continue
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


def _hub_twitter_download(url: str, max_mb: int) -> dict:
    """v45: X/Twitter video user ke hub se (fallback purana engine)."""
    try:
        from modules import api_hub as hub
    except Exception:
        return {"ok": False}
    if not hub.hub_ready() or not re.search(r"(twitter\.com|x\.com)/", url or ""):
        return {"ok": False}
    res = hub.hub_twitter_video(url)
    if not res.get("ok"):
        return {"ok": False}
    try:
        r = requests.get(res["url"], headers=DESKTOP_UA, timeout=90, stream=True)
        if r.status_code != 200:
            return {"ok": False}
        buf = io.BytesIO()
        for chunk in r.iter_content(262144):
            buf.write(chunk)
            if buf.tell() > max_mb * 1048576 * 1.05:
                break
        data = buf.getvalue()
        if len(data) < 50_000:
            return {"ok": False}
        return {"ok": True, "type": "video", "bytes": data,
                "size_mb": round(len(data) / 1048576, 2),
                "engine": res.get("source", "hub/twitter-video"),
                "title": res.get("title") or "", "duration": 0}
    except Exception:
        return {"ok": False}


async def download_video_async(url: str, max_mb: int = MAX_TG_MB) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, download_video_media, url, max_mb)
