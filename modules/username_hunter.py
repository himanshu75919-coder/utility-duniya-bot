# -*- coding: utf-8 -*-
"""
🕵️ USERNAME HUNTER (v71.8)
==========================
Ek username daalo → bot check karta hai ki wo username **kaun-kaun si PUBLIC
sites** par mojood hai (jaise github.com/rahul_99, reddit.com/user/rahul_99).

⚠️ Ye LEGAL hai aur aise hi rahega:
  • Sirf **public profile pages** check hoti hain (jaise koi browser me naam daalta hai)
  • Koi login / password / session / OTP **nahi** — sirf open pages
  • Koi "hacking" nahi — ye wahi kaam hai jo Sherlock naam ka famous
    open-source tool karta hai (security researchers use karte hain)
  • Jo site block kare (403/429) usko "⚪ check nahi ho paya" me daal dete hain —
    kuch bhi jor-zabardasti nahi

Kaam kaise karta hai:
  1. Username validate (3-30 chars: a-z 0-9 . _ -)
  2. ~36 sites ko EK SAATH (12 workers) GET karta hai
  3. 200 → mila | 404/410 → nahi mila | 403/429/5xx → check nahi ho paya
  4. Kabhi crash nahi karta — sab try/except me, hamesha dict return
"""

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from modules.core import httpio   # v72.0: shared engine (speed + auto-retry)
log = logging.getLogger(__name__)

UA = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.8",
}

# (naam, category, url-template, marker?)
#   marker ho to: 200 + marker page me mile tabhi "mila" (warna nahi mila)
SITES = (
    # (naam, category, url-template, marker?, bad-marker?)
    #   marker     = 200 ke saath ye text mile   → "mila"
    #                (marker me {} ho to wahan username lagta hai)
    #   bad-marker = 200 par bhi ye text mile    → "nahi mila" (soft-404 trap)
    # ---------------- DEV / CODE ----------------
    ("GitHub",        "dev",     "https://github.com/{}"),
    ("GitLab",        "dev",     "https://gitlab.com/{}"),
    ("Bitbucket",     "dev",     "https://bitbucket.org/{}"),
    ("Gitea.com",     "dev",     "https://gitea.com/{}"),
    ("Dev.to",        "dev",     "https://dev.to/{}"),
    ("Hashnode",      "dev",     "https://hashnode.com/@{}", None, "User not found"),
    ("Replit",        "dev",     "https://replit.com/@{}"),
    ("Kaggle",        "dev",     "https://www.kaggle.com/{}"),
    ("Docker Hub",    "dev",     "https://hub.docker.com/u/{}"),
    ("Hugging Face",  "dev",     "https://huggingface.co/{}"),
    ("Keybase",       "dev",     "https://keybase.io/{}"),
    ("Codewars",      "dev",     "https://www.codewars.com/users/{}"),
    ("Pastebin",      "dev",     "https://pastebin.com/u/{}"),
    ("Disqus",        "dev",     "https://disqus.com/by/{}"),
    # ---------------- SOCIAL ----------------
    ("Reddit",        "social",  "https://www.reddit.com/user/{}"),
    ("Instagram",     "social",  "https://www.instagram.com/{}/"),
    ("YouTube",       "social",  "https://www.youtube.com/@{}"),
    ("Snapchat",      "social",  "https://www.snapchat.com/add/{}"),
    ("Telegram",      "social",  "https://t.me/{}", "tgme_page_title"),
    ("Bluesky",       "social",
     "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={}.bsky.social",
     '"did"'),
    # ---------------- CREATIVE ----------------
    ("Behance",       "creative", "https://www.behance.net/{}"),
    ("Dribbble",      "creative", "https://dribbble.com/{}"),
    # ---------------- MUSIC ----------------
    ("SoundCloud",    "music",   "https://soundcloud.com/{}"),
    ("Bandcamp",      "music",   "https://{}.bandcamp.com"),
    # ---------------- VIDEO / LIVE ----------------
    ("Vimeo",         "video",   "https://vimeo.com/{}"),
    ("Twitch",        "video",   "https://www.twitch.tv/{}", "{} - Twitch"),
    ("Kick",          "video",   "https://kick.com/api/v2/channels/{}"),
    # ---------------- GAMING ----------------
    ("Chess.com",     "gaming",  "https://www.chess.com/member/{}"),
    ("Lichess",       "gaming",  "https://lichess.org/@/{}"),
    ("Steam",         "gaming",  "https://steamcommunity.com/id/{}",
     "actual_persona_name", "could not be found"),
    # ---------------- OTHER ----------------
    ("About.me",      "other",   "https://about.me/{}"),
    ("Gravatar",      "other",   "https://gravatar.com/{}"),
    ("Substack",      "other",   "https://{}.substack.com"),
)

_USER_RE = re.compile(r"^[A-Za-z0-9._-]{3,30}$")
_CACHE: dict = {}
_CACHE_TTL = 600          # 10 min — itni der me kuch nahi badalta


def _clean(raw: str) -> str:
    return str(raw or "").strip().lstrip("@").strip()


def _check_one(session: requests.Session, site: tuple, uname: str, timeout: int) -> dict:
    """Ek site check karo. Kabhi raise nahi karta.

    v71.8: marker aur bad-marker dono support (soft-404 walon ke liye zaroori).
    """
    name, cat = site[0], site[1]
    url = site[2].replace("{}", uname)
    marker = site[3] if len(site) > 3 else None
    bad = site[4] if len(site) > 4 else None
    out = {"site": name, "cat": cat, "url": url, "status": "unknown"}
    try:
        r = session.get(url, headers=UA, timeout=timeout, allow_redirects=True)
        code = int(r.status_code)
        body = r.text or ""
        _mk = (str(marker).replace("{}", uname) in body) if marker else False
        _bd = (str(bad).replace("{}", uname) in body) if bad else False
        if code == 200:
            if bad and _bd:
                out["status"] = "not_found"
            elif marker:
                out["status"] = "found" if _mk else "not_found"
            else:
                out["status"] = "found"
        elif code in (400, 404, 410):
            out["status"] = "not_found"
        else:
            out["status"] = "unknown"
    except Exception as e:                                    # noqa: BLE001
        log.debug("uhunt %s fail: %s", name, type(e).__name__)
    return out


def hunt_username(raw: str, timeout: int = 8, workers: int = 12) -> dict:
    """Username ko public sites par dhoondho. Hamesha dict (kabhi exception nahi).

    Return: {"ok": True, "username": ..., "found": [{site,cat,url}...],
             "not_found": int, "unknown": [site...], "checked": int, "ms": float}
    """
    t0 = time.time()
    try:
        uname = _clean(raw)
    except Exception:                                         # noqa: BLE001
        uname = ""
    if not _USER_RE.match(uname or ""):
        return {"ok": False,
                "error": ("Username samajh nahi aaya. 3-30 characters, sirf "
                          "a-z 0-9 . _ - chalte hain (jaise <code>rahul_99</code>).")}

    ck = "uhunt:" + uname.lower()
    hit = _CACHE.get(ck)
    if hit and time.time() - hit[1] < _CACHE_TTL:
        return {**hit[0], "cached": True}

    found, unknown, nf = [], [], 0
    try:
        session = httpio.session()
        with ThreadPoolExecutor(max_workers=max(4, min(int(workers), 20))) as ex:
            futs = [ex.submit(_check_one, session, s, uname, timeout) for s in SITES]
            for f in as_completed(futs, timeout=35):
                try:
                    r = f.result(timeout=1)
                except Exception:                             # noqa: BLE001
                    continue
                st = r.get("status")
                if st == "found":
                    found.append({"site": r["site"], "cat": r["cat"], "url": r["url"]})
                elif st == "unknown":
                    unknown.append(str(r["site"]))
                else:
                    nf += 1
    except Exception as e:                                    # noqa: BLE001
        log.warning("uhunt pool fail: %s", type(e).__name__)

    _order = {"dev": 0, "social": 1, "creative": 2, "music": 3, "video": 4,
              "gaming": 5, "other": 6}
    found.sort(key=lambda x: (_order.get(x["cat"], 9), x["site"].lower()))

    res = {"ok": True, "username": uname, "found": found, "not_found": nf,
           "unknown": unknown, "checked": len(SITES),
           "ms": round((time.time() - t0) * 1000, 1)}
    _CACHE[ck] = (res, time.time())
    return res
