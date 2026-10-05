# -*- coding: utf-8 -*-
"""
Gaming Player Info — v53.0 (PRO REWRITE)
========================================
🔥 FREE FIRE  : public player info (Garena public profile data, free API)
🎮 BGMI/PUBG-M : public stats via provider chain + honest availability gate

v52.3 me kya galat tha (live test se prove hua):
  • **Region codes galat the.** Hardcoded list me `RU` tha jo API me EXIST HI NAHI
    KARTA, aur `EU` / `NA` / `SAC` MISSING the. API ke asli 15 regions:
        BD BR CIS EU ID IND ME NA PK SAC SG TH TW US VN
    Galat region bhejne par API `ACCOUNTS_EMPTY` deta hai — jo bot "player not found"
    samajh leta tha.
  • **Har UID par 404 PLAYER_NOT_FOUND** aa raha tha (7 regions test kiye, sab 404).
    Wajah: ye API region ke hisaab se sirf ~2 "bot accounts" rakhti hai. Jab wo
    exhaust/ban ho jate hain to **sahi UID par bhi NOT_FOUND** aata hai. Bot user ko
    bolta tha *"Region galat ho sakta hai"* — jo **jhooth tha**, aur credit bhi kat
    jata tha.
  • **BGMI**: `kronos-api.pubg.com` DNS hi resolve nahi hota (dead host). Teeno shards
    fail → user ko hamesha ek lamba fallback paragraph milta tha, credit ke saath.
  • Koi cache nahi, koi health pre-check nahi, single point of failure.

v53.0 ab kya karta hai:
  • **Regions API se live validate** hote hain (root endpoint ke `AccountBot` se),
    hardcoded list sirf fallback hai. Galat region par turant saaf message.
  • **Health pre-flight**: lookup se PEHLE `ServiceStatus` + region ka
    `AvailableAccounts` check hota hai. Accounts khatam / service degraded ho to user
    ko **sach** bataya jata hai (`service_busy=True`) — aur **bot credit NAHI katta**
    (kyunki ye user ki galti nahi, service ki galti hai).
  • **Region auto-scan**: user ne region nahi diya to ek hi baar me saare regions
    parallel try hote hain (pehle IND/BD/PK — desi users ke liye sabse common),
    jo pehle mile wahi result. Ab "region galat" wala andhatbaas guess nahi.
  • **BGMI provider chain** + availability gate: koi bhi provider zinda na ho to
    `available=False` aata hai → bot credit nahi katta aur seedha official tarika
    batata hai (chhota, saaf message — 12 line ka paragraph nahi).
  • **TTL cache** — same UID 30 min tak dobara API hit nahi karta.
  • Saare HTTP `core.net` se (pool + timeout + retry + size cap).

Legal: sirf PUBLIC in-game data (gamertag, level, rank, K/D). Koi real identity,
koi phone number, koi "private leaderboard" — kabhi nahi. Kabhi fake data nahi.
"""
from __future__ import annotations

import logging
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Any, Dict, List, Optional

from modules.core.cache import TTLCache, cached_call
from modules.core.net import NetError, http_get, http_get_json
from modules.core.telemetry import note_upstream, tracked as _tracked

log = logging.getLogger("ud.gaming")

__all__ = [
    "ff_player_info", "bgmi_player_info", "ff_service_status", "ff_regions",
    "bgmi_availability", "gaming_cache_snapshot", "FF_REGIONS", "REGION_ALIASES",
]

_UA = os.environ.get(
    "GAMING_UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)
_TIMEOUT = float(os.environ.get("GAMING_TIMEOUT", "12"))
# Region-scan ke liye alag, tight timeouts (audit me TH region 11s leta tha
# jabki healthy jawab ~0.2-0.4s hai — see `_ff_query_one` docstring).
_SCAN_TIMEOUT = float(os.environ.get("FF_SCAN_TIMEOUT", "4"))
_SCAN_DEADLINE = float(os.environ.get("FF_SCAN_DEADLINE", "6"))
_CACHE_TTL = int(os.environ.get("GAMING_CACHE_TTL", "1800"))     # 30 min
_STATUS_TTL = int(os.environ.get("GAMING_STATUS_TTL", "180"))     # 3 min
_FAIL_TTL = 90

FF_API = os.environ.get("FF_API_BASE", "https://freefireapis.lat").rstrip("/")

# API ke asli 15 regions (live verify kiye gaye, 2026-10-05).
# ⚠️ `RU` isme NAHI hai — v52.3 me tha, aur API use reject karti thi.
FF_REGIONS: List[str] = [
    "IND", "BD", "PK", "SG", "ID", "TH", "VN", "BR", "US", "NA",
    "EU", "ME", "TW", "CIS", "SAC",
]

# Desi users ke liye scan order (IND sabse pehle).
_SCAN_ORDER: List[str] = [
    "IND", "BD", "PK", "SG", "ID", "TH", "VN", "BR", "US", "NA",
    "EU", "ME", "TW", "CIS", "SAC",
]

# User jo bhi likhe → canonical region code
REGION_ALIASES: Dict[str, str] = {
    "IND": "IND", "IN": "IND", "INDIA": "IND",
    "BD": "BD", "BANGLADESH": "BD",
    "PK": "PK", "PAKISTAN": "PK",
    "SG": "SG", "SINGAPORE": "SG",
    "ID": "ID", "INDONESIA": "ID", "INDO": "ID",
    "TH": "TH", "THAILAND": "TH",
    "VN": "VN", "VIETNAM": "VN",
    "BR": "BR", "BRAZIL": "BR",
    "US": "US", "USA": "US",
    "NA": "NA", "NORTHAMERICA": "NA", "NORTH AMERICA": "NA",
    "EU": "EU", "EUROPE": "EU",
    "ME": "ME", "MIDDLEEAST": "ME", "MIDDLE EAST": "ME",
    "TW": "TW", "TAIWAN": "TW",
    "CIS": "CIS", "RU": "CIS", "RUSSIA": "CIS",   # RU region exist nahi karta → CIS
    "SAC": "SAC", "SOUTHAMERICA": "SAC", "SOUTH AMERICA": "SAC",
}

_cache = TTLCache(maxsize=int(os.environ.get("GAMING_CACHE_SIZE", "1024")),
                  default_ttl=_CACHE_TTL)
_status_lock = threading.Lock()

_H = {"User-Agent": _UA, "Accept": "application/json"}


def gaming_cache_snapshot() -> dict:
    """Admin /sys card ke liye."""
    return _cache.snapshot()


def _clean_uid(target: str) -> str:
    return re.sub(r"\D", "", str(target or ""))[:15]


def parse_region(text: str) -> Optional[str]:
    r"""User ke message se region code nikalo. None = region nahi diya.

    v55 fix: pehle regex `\b([A-Z]{2,12})\s*$` sirf "7860944073 BR" (space se
    alag) pakadta tha. Users asli me ye sab bhejte hain (live audit me mile):
      "7860944073 (BR)"   ← parens
      "7860944073 - BR"   ← dash
      "7860944073, BR"    ← comma
      "7860944073 BR."    ← trailing dot
    In sabhi me region None return hota tha → bot region scan skip kar deta tha
    (ya galat region me). Ab trailing punctuation/parens strip hote hain.
    """
    t = str(text or "").strip().upper()
    if not t:
        return None
    # trailing punctuation/brackets hatao: (BR), [BR], -BR, :BR, BR. , BR
    t = re.sub(r"[\s\-–—:,;.]+$", "", t)
    t = re.sub(r"[\(\[\{]+([A-Z]{2,12})[\)\]\}]+$", r"\1", t)
    m = re.search(r"\b([A-Z]{2,12})$", t)
    if m:
        return REGION_ALIASES.get(m.group(1))
    return None


def strip_region(text: str) -> str:
    """Message me se region word hata kar sirf UID bachao."""
    t = str(text or "").strip()
    # v55: parens/dash/comma wale formats bhi hatao — "7860944073 (BR)" → "7860944073"
    t = re.sub(r"[\s\-–—:,;]*[\(\[\{]\s*[A-Za-z]{2,12}\s*[\)\]\}]\s*$", "", t)
    t = re.sub(r"\s+[A-Za-z]{2,12}\s*$", "", t)
    # trailing punctuation bhi saaf karo ("7860944073 -" → "7860944073")
    t = re.sub(r"[\s\-–—:,;.]+$", "", t)
    return t.strip()


# ============================================================ FF service status
def ff_service_status(force: bool = False) -> Dict[str, Any]:
    """Free Fire API ka live health + per-region account availability.

    Returns:
      {"ok":bool, "status":"online"/"...", "avg_ms":.., "uptime":..,
       "daily_requests":.., "regions":{code: {"total":n,"available":n,"banned":n}},
       "dead_regions":[...], "error":..}

    3 min cache — har user query par root endpoint hit nahi hota.
    """
    def _work():
        try:
            j = http_get_json(f"{FF_API}/", headers=_H, timeout=_TIMEOUT, retries=1)
        except NetError as e:
            note_upstream("freefireapis.lat", False, e.message[:100])
            return {"ok": False, "error": e.message, "unreachable": True,
                    "status": "unknown", "regions": {}, "dead_regions": []}
        except Exception as e:                                       # noqa: BLE001
            note_upstream("freefireapis.lat", False, str(e)[:100])
            return {"ok": False, "error": str(e)[:80], "unreachable": True,
                    "status": "unknown", "regions": {}, "dead_regions": []}
        res = (j or {}).get("result") or {}
        if not isinstance(res, dict):
            return {"ok": False, "error": "API ne ajeeb jawab diya.", "unreachable": True,
                    "status": "unknown", "regions": {}, "dead_regions": []}
        ss = res.get("ServiceStatus") or {}
        regions: Dict[str, Dict[str, int]] = {}
        dead: List[str] = []

        def _n(v) -> int:
            try:
                return int(str(v).replace(".", "").replace(",", ""))
            except Exception:                                      # noqa: BLE001
                return 0

        for a in (res.get("AccountBot") or []):
            if not isinstance(a, dict):
                continue
            code = str(a.get("Region") or "").strip().upper()
            if not code:
                continue
            avail = _n(a.get("AvailableAccounts"))
            total = _n(a.get("TotalAccounts"))
            banned = _n(a.get("BannedAccounts"))
            regions[code] = {"total": total, "available": avail, "banned": banned}
            if avail <= 0:
                dead.append(code)
        note_upstream("freefireapis.lat", True, "")
        return {
            "ok": True,
            "status": str(ss.get("Status") or "unknown").lower(),
            "avg_ms": str(ss.get("AverageResponseTime") or ""),
            "uptime": str(ss.get("Uptime") or ""),
            "daily_requests": str(ss.get("DailyRequests") or ""),
            "release": str(res.get("ReleaseVersion") or ""),
            "regions": regions,
            "dead_regions": dead,
            "api_regions": sorted(regions.keys()),
        }

    with _status_lock:
        val, _hit = cached_call(_cache, "ff:status", _work,
                                ttl=_STATUS_TTL, fail_ttl=45,
                                is_failure=lambda v: not v.get("ok"))
    return val


def ff_regions() -> List[str]:
    """API ke live-valid region codes (fail ho to hardcoded list)."""
    st = ff_service_status()
    live = [r for r in (st.get("api_regions") or []) if r]
    if live:
        # hamari scan-order ko prefer karo, naye live regions peeche add karo
        ordered = [r for r in _SCAN_ORDER if r in live]
        ordered += [r for r in live if r not in ordered]
        return ordered
    return list(FF_REGIONS)


# ============================================================ FF player lookup
_UID_ERR_HELP = (
    "Valid Free Fire UID bhejo (8-10 digit number).\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "📌 <b>UID kahan milega:</b>\n"
    "Free Fire kholo → upar-left apni <b>profile photo</b> dabao →\n"
    "naam ke neeche <b>UID</b> likha hai (📋 copy icon se copy karo).\n\n"
    "📌 <b>Jaise:</b> <code>1633864660</code>\n"
    "🌍 Region bhi batana ho: <code>1633864660 BR</code>"
)


def _ff_query_one(uid: str, region: str) -> Dict[str, Any]:
    """Ek region par single lookup. Raw result (cache nahi).

    ⚠️ Timeout jaan-boojh kar CHHOTA (4s) hai. Live audit (2026-10-05) me
    healthy API 200-430ms me jawab deti hai, par **TH region consistently
    11.08s** le raha tha — aur kyunki scan parallel tha, wo ek region poore
    15-region scan ko 11 second tak block kar deta tha (baaki 14 sab 0.2s me
    ho chuke the). 4s = healthy jawab ke liye 10x headroom, straggler ke liye
    tight leash.
    """
    try:
        r = http_get(f"{FF_API}/info-player", params={"uid": uid, "region": region},
                     headers=_H, timeout=_SCAN_TIMEOUT, retries=0)
    except NetError as e:
        kind = "timeout" if e.kind == "timeout" else "neterror"
        return {"state": kind, "region": region, "detail": e.message}
    except Exception as e:                                          # noqa: BLE001
        return {"state": "neterror", "region": region, "detail": str(e)[:60]}

    code = r.status_code
    try:
        d = r.json()
    except Exception:                                               # noqa: BLE001
        d = {}
    if not isinstance(d, dict):
        d = {}
    err = str(d.get("error") or "").upper()

    if d.get("success") is True:
        return {"state": "found", "region": region, "data": d}
    if err == "PLAYER_NOT_FOUND" or code == 404:
        return {"state": "notfound", "region": region, "data": d}
    if err == "ACCOUNTS_EMPTY":
        # ⚠️ Ye "player nahi mila" NAHI hai — API ke paas is region me koi
        # query-account bacha hi nahi. Service-side problem.
        return {"state": "accounts_empty", "region": region, "data": d}
    if err == "MISSING_PARAMETERS":
        return {"state": "badparams", "region": region, "data": d}
    if code in (401, 403):
        # ⚠️ v54.1: 403 = API ne humare server (Render IP) ko block/rate-limit
        # kiya hai. Ye "player nahi mila" NAHI hai — isko alag state dete hain
        # warna user ko "UID galat hai" wala jhootha message milta tha.
        return {"state": "blocked", "region": region, "data": d, "detail": f"HTTP {code}"}
    if code == 429:
        return {"state": "ratelimit", "region": region, "data": d}
    if code >= 500:
        return {"state": "servererror", "region": region, "data": d, "detail": f"HTTP {code}"}
    return {"state": "other", "region": region, "data": d,
            "detail": err or d.get("message") or f"HTTP {code}"}


def _ff_build_card(uid: str, region: str, d: dict) -> Dict[str, Any]:
    """API ke raw JSON se saaf player card banao."""
    res = d.get("result") or {}
    bi = res.get("basicInfo") or {}
    si = res.get("socialInfo") or {}
    if not isinstance(bi, dict):
        bi = {}
    if not isinstance(si, dict):
        si = {}

    def _txt(v) -> str:
        if v is None:
            return ""
        if isinstance(v, dict):
            for k in ("text", "name", "value"):
                if isinstance(v.get(k), str):
                    return v[k]
            return ""
        return str(v)

    out = {
        "ok": True,
        "uid": _txt(bi.get("accountId")) or uid,
        "nickname": _txt(bi.get("nickname")) or "—",
        "level": bi.get("level"),
        "exp": bi.get("exp"),
        "region": _txt(bi.get("region")) or region,
        "rank_br": _txt(bi.get("rank")) or "—",
        "rp_br": _txt(bi.get("rankingPoints")) or "—",
        "rank_cs": _txt(bi.get("csRank")) or "—",
        "rp_cs": _txt(bi.get("csRankingPoints")) or "—",
        "max_rank": _txt(bi.get("maxRank")) or "—",
        "prime": bi.get("primeLevel"),
        "liked": bi.get("liked"),
        "last_login": _txt(bi.get("lastLoginAt")) or "—",
        "created": _txt(bi.get("createAt")) or "—",
        "bio": _txt(si.get("signature")).strip(),
        "version": _txt(bi.get("releaseVersion")),
        "clan": _txt(si.get("guildName") or si.get("guild")) or "",
        "source": "freefireapis.lat",
    }

    # ── v54.0: IMAGES ─────────────────────────────────────────────
    # Free Fire API 3 tarah ki public images deta hai jo pehle **ignore** ho
    # jati thin (user ko sirf text milta tha):
    #   1. `profileCard`  → official banner (avatar + nickname + level), ~190KB,
    #                       1692×360 wide — `send_photo` ke liye perfect
    #   2. `inventory.characterImage` → equipped character ka portrait (~14KB)
    #   3. `clothesUrl`   → outfit/loadout breakdown (headgear/torso/weapon…),
    #                       ~2.7MB PNG — isliye on-demand button par bhejte hain,
    #                       har query par 2.7MB download wasteful hai
    # Har image URL optional hai; na ho to handler text-only card bhej deta hai.
    pc = res.get("profileCard") or {}
    cl = res.get("clothesUrl") or {}
    inv = res.get("inventory") or {}
    if not isinstance(pc, dict):
        pc = {}
    if not isinstance(cl, dict):
        cl = {}
    if not isinstance(inv, dict):
        inv = {}

    def _imgurl(node, *exts) -> str:
        # png > jpg > webp preference; jo format maujood ho wahi lo
        for e in exts or ("png", "jpg", "webp"):
            v = node.get(e)
            if isinstance(v, str) and v.startswith("http"):
                return v
        return ""

    out["profile_card"] = _imgurl(pc)
    out["outfit_image"] = _imgurl(cl)
    out["character_image"] = _imgurl(inv, "characterImage") or (
        inv.get("characterImage") if isinstance(inv.get("characterImage"), str) else "")
    out["character_name"] = _txt(inv.get("characterName")) or ""
    return out


@_tracked("ffuid")
def ff_player_info(target: str, region: str = "", use_cache: bool = True) -> Dict[str, Any]:
    """Free Fire public player info by UID.

    Args:
      target : UID (ya "UID REGION" jaisa message)
      region : explicit region code (khaali = auto-scan)

    Returns dict with `ok`. Jab `ok=False`, `service_busy=True` ho to matlab
    **service-side problem** hai (user ki galti nahi) — bot ko credit NAHI katna chahiye.
    """
    raw = str(target or "").strip()
    # region message ke andar bhi ho sakta hai ("1633864660 BR")
    if not region:
        region = parse_region(raw) or ""
        raw = strip_region(raw)
    uid = _clean_uid(raw)

    if len(uid) < 6:
        return {"ok": False, "error": _UID_ERR_HELP}

    reg = str(region or "").strip().upper()
    reg = REGION_ALIASES.get(reg, reg)
    valid_regions = ff_regions()

    # galat region code → turant saaf message (network waste nahi)
    if reg and reg not in valid_regions:
        return {"ok": False, "error": (
            f"❌ Region code <b>{reg}</b> valid nahi hai.\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Valid regions: <code>{' '.join(valid_regions)}</code>\n\n"
            "💡 Region na pata ho to <b>sirf UID bhejo</b> — bot khud "
            "saare regions me dhoondh dega.\n"
            f"📌 Jaise: <code>{uid}</code>")}

    def _work():
        st = ff_service_status()

        # --- Service hi zinda nahi? ---
        if not st.get("ok"):
            return {"ok": False, "service_busy": True, "uid": uid,
                    "error": ("⏳ <b>Free Fire info service abhi pahunch se bahar hai.</b>\n"
                              "━━━━━━━━━━━━━━━━━━━━━━\n"
                              "Ye ek free third-party service hai — kabhi-kabhi down hoti hai.\n"
                              f"🔧 Problem: <code>{str(st.get('error'))[:70]}</code>\n\n"
                              "🕐 <b>5-10 minute baad dobara try karo.</b>\n"
                              "<i>❌ Aapka credit NAHI kata (service ki galti, aapki nahi).</i>")}
        if str(st.get("status") or "").lower() not in ("online", "up", "ok", ""):
            return {"ok": False, "service_busy": True, "uid": uid,
                    "error": ("⚠️ <b>Free Fire service abhi degraded hai</b> "
                              f"(status: <code>{st.get('status')}</code>).\n"
                              "Thodi der baad try karo.\n"
                              "<i>❌ Credit nahi kata.</i>")}

        # --- Region-specific: accounts khatam? ---
        regions_to_try = [reg] if reg else list(_SCAN_ORDER)
        # sirf zinda (available accounts wale) regions try karo
        live_regions = st.get("regions") or {}
        if live_regions:
            healthy = [r for r in regions_to_try
                       if r not in live_regions or live_regions[r]["available"] > 0]
            exhausted = [r for r in regions_to_try
                         if r in live_regions and live_regions[r]["available"] <= 0]
        else:
            healthy, exhausted = list(regions_to_try), []

        if not healthy:
            return {"ok": False, "service_busy": True, "uid": uid,
                    "dead_regions": exhausted,
                    "error": ("⚠️ <b>Free Fire service ke saare query-accounts abhi khatam hain.</b>\n"
                              "━━━━━━━━━━━━━━━━━━━━━━\n"
                              "Ye free API region ke hisaab se limited accounts rakhti hai —\n"
                              "abhi " + (f"<b>{reg}</b>" if reg else "kisi bhi region") +
                              " me ek bhi available nahi hai.\n\n"
                              "🕐 <b>1-2 ghante baad try karo</b> (accounts replenish hote hain).\n"
                              "<i>❌ Aapka credit NAHI kata.</i>")}

        # --- parallel region scan ---
        # ⚠️ Speed: v53.0 audit me auto-scan **10.4 second** le raha tha
        # (6 workers x 15 regions x ~750ms upstream). Ab 12 workers — IO-bound
        # hai isliye zyada threads safe hain, aur scan ~2s me ho jata hai.
        # Jaise hi pehla "found" milta hai, baaki futures ko cancel kar dete hain
        # (warna user ko poore scan ka wait karna padta).
        found: Optional[Dict[str, Any]] = None
        states: Dict[str, str] = {}
        # ⚠️ Deadline-based scan: poore scan par ek wall-clock budget hai
        # (_SCAN_DEADLINE, default 6s). Isse ek slow region (audit me TH = 11s)
        # baaki 14 regions ke jawaab ko rok nahi sakta — budget khatam hote hi
        # jitne jawab aaye unhi se faisla hota hai, aur bache hue regions
        # "timeout" mark ho jate hain.
        max_workers = min(15, len(healthy))
        ex = ThreadPoolExecutor(max_workers=max(1, max_workers))
        try:
            futs = {ex.submit(_ff_query_one, uid, r): r for r in healthy}
            try:
                for f in as_completed(futs, timeout=_SCAN_DEADLINE):
                    r = futs[f]
                    try:
                        res = f.result()
                    except Exception:                               # noqa: BLE001
                        states[r] = "exc"
                        continue
                    states[r] = res.get("state", "?")
                    if res.get("state") == "found":
                        if found is None:
                            found = _ff_build_card(uid, r, res.get("data") or {})
                        break       # mil gaya — baaki kaam bekaar
            except FuturesTimeout:
                # deadline paar — jo nahi aaye unhe timeout mark karo
                for f, r in futs.items():
                    if not f.done():
                        states[r] = "timeout"
        finally:
            ex.shutdown(wait=False, cancel_futures=True)
        if found:
            return found

        # --- koi nahi mila: ab sach batao (guess nahi) ---
        n_empty = sum(1 for v in states.values() if v == "accounts_empty")
        n_net = sum(1 for v in states.values() if v in ("neterror", "servererror"))
        n_rl = sum(1 for v in states.values() if v == "ratelimit")
        n_nf = sum(1 for v in states.values() if v == "notfound")
        n_to = sum(1 for v in states.values() if v == "timeout")
        n_blk = sum(1 for v in states.values() if v == "blocked")
        tried = len(states)
        # kitne regions ka jawab aaya hi nahi (timeout/straggler) — ye "not found"
        # ke barabar NAHI hai, isliye message me alag batate hain.
        # ⚠️ v55: `answered` variable pehle yahan compute hota tha par use nahi
        # hota tha (dead code) — counts seedhe message me inline hote hain.

        if n_blk and n_blk >= max(1, tried - n_nf - n_empty):
            return {"ok": False, "service_busy": True, "uid": uid,
                    "blocked": True, "blocked_regions": n_blk,
                    "error": ("🚫 <b>Free Fire API ne abhi humare server ko block kar rakha hai</b> "
                              f"(HTTP 403 — {n_blk}/{tried} region).\n"
                              "━━━━━━━━━━━━━━━━━━━━━━\n"
                              "Ye <b>service-side</b> problem hai, aapki UID ki nahi.\n"
                              "Free API datacenter IP ko kabhi-kabhi temporarily rok deti hai.\n\n"
                              "🕐 <b>15-30 minute baad dobara try karo.</b>\n"
                              "<i>❌ Aapka credit NAHI kata.</i>")}
        if n_rl and n_rl == tried:
            return {"ok": False, "service_busy": True, "uid": uid,
                    "error": ("⏳ Service ne abhi <b>rate-limit</b> laga rakha hai "
                              "(bahut saari queries ja rahi hain).\n"
                              "🕐 2-3 minute baad dobara bhejo.\n<i>❌ Credit nahi kata.</i>")}
        if n_net and n_net >= max(1, tried - n_empty):
            return {"ok": False, "service_busy": True, "uid": uid,
                    "error": ("⏳ Free Fire service abhi jawab nahi de payi "
                              f"({n_net}/{tried} region me network/server error).\n"
                              "🕐 Thodi der baad dobara try karo.\n<i>❌ Credit nahi kata.</i>")}
        if n_empty and n_empty == tried:
            return {"ok": False, "service_busy": True, "uid": uid,
                    "dead_regions": sorted(states),
                    "error": ("⚠️ <b>Service ke query-accounts abhi khatam hain</b> "
                              f"(saare {tried} region me `ACCOUNTS_EMPTY`).\n"
                              "Iska matlab UID galat nahi hai — API khud busy hai.\n"
                              "🕐 1-2 ghante baad try karo.\n<i>❌ Credit nahi kata.</i>")}

        # genuinely not found
        scope = (f"region <b>{reg}</b>" if reg else
                 f"<b>{n_nf}</b> region" + ("s" if n_nf != 1 else ""))
        hint = ""
        if n_to and not reg:
            hint += (f"\n\n⏳ <b>{n_to}</b> region(s) ne time limit me jawab nahi diya "
                     "(API ka ek region slow tha) — ho sakta hai player wahin ho.\n"
                     "🔁 <b>Dobara bhejo</b> ya region specify karo, jaise "
                     f"<code>{uid} TH</code>.")
        if not reg:
            hint = ("\n\n💡 Aapka region alag ho sakta hai — UID ke saath region bhi bhejo:\n"
                    f"<code>{uid} BR</code> ya <code>{uid} SG</code>\n"
                    f"Regions: <code>{' '.join(valid_regions)}</code>")
        return {"ok": False, "uid": uid, "notfound": True,
                "regions_tried": tried, "region_states": states,
                "error": (f"🔍 UID <code>{uid}</code> {scope} me nahi mila.\n"
                          "━━━━━━━━━━━━━━━━━━━━━━\n"
                          "Ye ho sakta hai agar:\n"
                          "• UID galat type ho gaya ho (ek digit idhar-udhar)\n"
                          "• Account delete/ban ho gaya ho\n"
                          "• Region alag ho"
                          f"{hint}")}

    if not use_cache:
        return _work()
    key = f"ff:{uid}:{reg or 'auto'}"
    val, _hit = cached_call(_cache, key, _work, ttl=_CACHE_TTL, fail_ttl=_FAIL_TTL,
                            is_failure=lambda v: not v.get("ok"))
    return val


# =====================================================================================
# BGMI / PUBG Mobile — provider chain + honest availability gate
# =====================================================================================
# v52.3 sirf `kronos-api.pubg.com` try karta tha — wo host DNS me hai hi nahi
# (live test: "Max retries exceeded"). Neeche ek chhoti provider chain hai;
# jo zinda na ho usse chheda hi nahi jata.

_BGMI_PROVIDERS: List[Dict[str, str]] = [
    # ⚠️ Live audit (2026-10-05): DONO dead hain.
    #   kronos-api.pubg.com   → DNS resolve hi nahi hota (ConnectionError)
    #   pubg-shazam.herokuapp → HTTP 404 + text/html (Heroku free dynes band ho chuke)
    # Isliye availability probe sirf "koi HTTP jawab" par nahi, **JSON content-type**
    # par decide karti hai — warna dead provider "alive" lagta aur user ko
    # "server tak pahunch hui" wala jhootha message milta.
    {"id": "kronos", "base": "https://kronos-api.pubg.com"},
    {"id": "pubg-shaz", "base": "https://pubg-shazam.herokuapp.com"},
]
_BGMI_SHARDS = ["asia", "in", "global"]
_avail_lock = threading.Lock()

# Probe ke liye ek well-known dummy UID (kisi real player ka nahi).
_PROBE_UID = "510069453"


def _probe_provider(base: str) -> bool:
    """Provider sach me zinda API hai?

    Sirf tab True jab:
      • connection ban jaye, aur
      • HTTP < 500 ho, aur
      • content-type JSON ho  (HTML 404 page = dead Heroku app)
    """
    url = f"{base}/shards/asia/players/{_PROBE_UID}/stats"
    host = base.split("//")[-1].split("/")[0]
    try:
        r = http_get(url, headers={"User-Agent": _UA, "Accept": "application/json"},
                     timeout=10, retries=0)
    except Exception as e:                                          # noqa: BLE001
        note_upstream(host, False, f"connect fail: {str(e)[:80]}")
        return False
    if r.status_code >= 500:
        note_upstream(host, False, f"HTTP {r.status_code}")
        return False
    ctype = (r.headers.get("content-type") or "").lower()
    if "json" in ctype:
        note_upstream(host, True, "")
        return True
    # JSON nahi — par body JSON jaisi ho to bhi maan lo (kuch API ctype galat bhejti hain)
    body = (r.text or "")[:200].lstrip()
    alive = body.startswith("{") or body.startswith("[")
    note_upstream(host, alive,
                  "" if alive else f"HTTP {r.status_code} + {ctype[:24]} (HTML, API nahi)")
    return alive


def bgmi_availability(force: bool = False) -> Dict[str, Any]:
    """Kaunsa BGMI provider abhi sach me zinda hai? (5 min cache)

    Returns {"ok":bool,"alive":[provider_ids],"dead":[..],"checked":n}
    """
    def _work():
        alive: List[str] = []
        dead: List[str] = []
        # parallel probe — dono ek saath, warna 2x timeout wait
        with ThreadPoolExecutor(max_workers=max(1, len(_BGMI_PROVIDERS))) as ex:
            futs = {ex.submit(_probe_provider, p["base"]): p["id"] for p in _BGMI_PROVIDERS}
            for f in as_completed(futs):
                pid = futs[f]
                try:
                    ok = bool(f.result())
                except Exception:                                   # noqa: BLE001
                    ok = False
                (alive if ok else dead).append(pid)
        return {"ok": bool(alive), "alive": sorted(alive), "dead": sorted(dead),
                "checked": len(_BGMI_PROVIDERS)}

    with _avail_lock:
        val, _hit = cached_call(_cache, "bgmi:avail", _work, ttl=300, fail_ttl=120,
                                is_failure=lambda v: not v.get("ok"))
    return val


_OFFICIAL_GUIDE = (
    "✅ <b>Official tarika (100% sahi, 30 second):</b>\n"
    "1. BGMI kholo → <b>Profile</b> dabao (upar-left photo)\n"
    "2. Naam ke neeche <b>UID</b> dikhega\n"
    "3. <b>Friends → Search</b> me UID dalo → poora profile + stats\n\n"
    "⚠️ Jo bhi site 'BGMI private stats / owner name' ka dawa kare — wo risky hai "
    "(data chori ho sakti hai). Is bot me sirf public/official data aata hai."
)


@_tracked("bgmi")
def bgmi_player_info(target: str, use_cache: bool = True) -> Dict[str, Any]:
    """BGMI/PUBG-M UID → public stats (best-effort, kabhi fake data nahi).

    Returns `available=False` + `service_busy=True` jab koi provider zinda na ho —
    us case me bot ko credit NAHI katna chahiye.
    """
    uid = _clean_uid(target)
    if len(uid) < 6:
        return {"ok": False, "error": (
            "Valid BGMI UID bhejo (8-10 digit number).\n"
            "📌 Game me: <b>Profile</b> → UID (📋 copy icon).\n"
            f"📌 Jaise: <code>1067824210</code>")}

    def _work():
        av = bgmi_availability()
        alive = av.get("alive") or []
        if not alive:
            # `fallback: True` v52.3 ka contract tha (tests isi par assert karte
            # hain) — backward-compat ke liye rakha. Naye flags `available` /
            # `service_busy` zyada precise hain: service_busy=True matlab
            # "service ki galti, user ki nahi" → credit nahi katna chahiye.
            return {"ok": False, "fallback": True, "available": False,
                    "service_busy": True, "uid": uid,
                    "dead_providers": av.get("dead") or [],
                    "error": ("🎮 <b>BGMI public stats abhi available nahi hai.</b>\n"
                              "━━━━━━━━━━━━━━━━━━━━━━\n"
                              "BGMI (India) ke liye officially koi free public stats API "
                              "nahi hai — jo third-party servers the wo ab band ho gaye hain.\n\n"
                              + _OFFICIAL_GUIDE +
                              "\n<i>❌ Aapka credit NAHI kata.</i>")}

        last_err = ""
        for p in _BGMI_PROVIDERS:
            if p["id"] not in alive:
                continue
            for shard in _BGMI_SHARDS:
                try:
                    d = http_get_json(f"{p['base']}/shards/{shard}/players/{uid}/stats",
                                      params={"season": "ALL"},
                                      headers={"User-Agent": _UA, "Accept": "application/json"},
                                      timeout=12, retries=0)
                except NetError as e:
                    last_err = e.message[:60]
                    continue
                except Exception as e:                               # noqa: BLE001
                    last_err = str(e)[:60]
                    continue
                data = (d or {}).get("data") or {}
                if isinstance(data, dict) and (data.get("totalKills") is not None
                                               or data.get("rankPoints") is not None):
                    prof = _kronos_profile(p["base"], uid, shard)
                    return {"ok": True, "uid": uid, "available": True,
                            "source": f"{p['id']}:{shard}",
                            "profile": prof, "stats": data}
        return {"ok": False, "fallback": True, "available": bool(alive),
                "service_busy": True, "uid": uid,
                "error": ("🎮 <b>BGMI stats is UID ke liye nahi mile.</b>\n"
                          "━━━━━━━━━━━━━━━━━━━━━━\n"
                          f"Server tak pahunch hue ({', '.join(alive)}) par is UID ka "
                          f"public record nahi aaya.\n🔧 <code>{last_err[:60]}</code>\n\n"
                          + _OFFICIAL_GUIDE + "\n<i>❌ Credit nahi kata.</i>")}

    if not use_cache:
        return _work()
    val, _hit = cached_call(_cache, f"bgmi:{uid}", _work, ttl=_CACHE_TTL,
                            fail_ttl=_FAIL_TTL, is_failure=lambda v: not v.get("ok"))
    return val


def _kronos_profile(base: str, uid: str, shard: str) -> Dict[str, Any]:
    """Player ka naam/level (stats ke saath)."""
    try:
        d = http_get_json(f"{base}/shards/{shard}/players/{uid}",
                          headers={"User-Agent": _UA, "Accept": "application/json"},
                          timeout=10, retries=0)
        data = (d or {}).get("data") or {}
        if isinstance(data, dict):
            return {"name": str(data.get("actorName") or "—"),
                    "level": data.get("level") or "—",
                    "rankPoints": data.get("rankPoints") or "—",
                    "title": str(data.get("title") or "")}
    except Exception:                                                # noqa: BLE001
        pass
    return {"name": "—", "level": "—", "rankPoints": "—", "title": ""}
