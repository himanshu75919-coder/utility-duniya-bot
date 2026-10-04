# -*- coding: utf-8 -*-
"""
Gaming Player Info — v52.3
===========================
🔥 FREE FIRE: public player info (Garena ke public profile data se, free API).
🎮 BGMI: best-effort public stats (Kronos public API) + official in-game guide fallback.

Sirf PUBLIC in-game data (gamertag, level, rank, stats) — koi real identity /
personal info nahi dikhti. "Private leaderboard" wala data yahin NAHI aayega.
"""

import re
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

_FF_REGIONS = ["IND", "BR", "SG", "US", "VN", "ID", "TH", "PK", "RU", "ME", "TW", "CIS", "BD"]
_FF_DEFAULT_REGION = "IND"


def _clean_uid(target: str) -> str:
    return re.sub(r"[^0-9]", "", (target or "").strip())[:15]


def ff_player_info(target: str, region: str = "") -> dict:
    """Free Fire public player info by UID.
    region: '' = default IND; ya explicit 'BR'/'SG' jaisa code (user ne UID ke saath bheja)."""
    uid = _clean_uid(target)
    if len(uid) < 6:
        return {"ok": False,
                "error": ("Valid Free Fire UID bhejo (8-10 digit number).\n"
                          "📌 Game me: Profile → UID (copy icon) se milta hai. Jaise: "
                          "<code>1633864660</code>\n"
                          "🌍 Region alag ho to aise bhejo: <code>UID BR</code> "
                          "(IND/BR/SG/US/VN/ID/TH/PK/RU/ME/TW/CIS/BD)")}
    reg = (region or "").strip().upper()
    if reg not in _FF_REGIONS:
        reg = _FF_DEFAULT_REGION
    url = "https://freefireapis.lat/info-player"
    try:
        r = requests.get(url, params={"uid": uid, "region": reg}, headers=UA, timeout=25)
        d = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if not d.get("success"):
            err = str(d.get("error") or "")
            if "NOT_FOUND" in err.upper():
                return {"ok": False,
                        "error": (f"Region <b>{reg}</b> me UID <code>{uid}</code> nahi mila.\n"
                                  "🌍 Region galat ho sakta hai — dobara bhejo apne region ke saath, jaise:\n"
                                  "<code>" + uid + " BR</code> ya <code>" + uid + " SG</code>\n"
                                  "Codes: IND BR SG US VN ID TH PK RU ME TW CIS BD")}
            return {"ok": False, "error": "FF info service abhi jawab nahi de payi. 1 minute baad try karo."}
        bi = (d.get("result") or {}).get("basicInfo") or {}
        si = (d.get("result") or {}).get("socialInfo") or {}
        out = {
            "ok": True,
            "uid": str(bi.get("accountId") or uid),
            "nickname": bi.get("nickname") or "—",
            "level": bi.get("level"),
            "exp": bi.get("exp"),
            "region": bi.get("region") or reg,
            "rank_br": bi.get("rank") or "—",
            "rp_br": bi.get("rankingPoints") or "—",
            "rank_cs": bi.get("csRank") or "—",
            "rp_cs": bi.get("csRankingPoints") or "—",
            "max_rank": bi.get("maxRank") or "—",
            "prime": bi.get("primeLevel"),
            "liked": bi.get("liked"),
            "last_login": bi.get("lastLoginAt") or "—",
            "created": bi.get("createAt") or "—",
            "bio": (si.get("signature") or "").strip(),
            "version": bi.get("releaseVersion") or "",
        }
        return out
    except requests.Timeout:
        return {"ok": False, "error": "FF server ne time limit ke andar jawab nahi diya. Dobara try karo."}
    except Exception:
        return {"ok": False, "error": "FF info service abhi unavailable hai. Thodi der baad try karo."}


# =====================================================================================
# BGMI — best-effort public stats (Kronos public API) + official guide fallback
# =====================================================================================
_BGMI_SHARDS = ["in", "india", "global"]


def bgmi_player_info(target: str) -> dict:
    """BGMI/PUBG-M UID se public stats — best effort.
    India se BGMI ke liye koi free public API officially nahi hai, isliye ye attempt
    + fallback dono return kar sakta hai. Kabhi bhi fake data NAHI."""
    uid = _clean_uid(target)
    if len(uid) < 6:
        return {"ok": False,
                "error": ("Valid BGMI UID bhejo (8-10 digit number).\n"
                          "📌 Game me: Profile → UID se milta hai. Jaise: <code>1067824210</code>")
                }
    last_err = ""
    for shard in _BGMI_SHARDS:
        try:
            r = requests.get(
                f"https://kronos-api.pubg.com/shards/{shard}/players/{uid}/stats",
                params={"season": "ALL"}, headers=UA, timeout=10)
            if r.status_code == 200:
                d = r.json()
                data = d.get("data") or {}
                if data.get("totalKills") is not None or data.get("rankPoints") is not None:
                    prof = _kronos_profile(uid, shard)
                    return {"ok": True, "uid": uid, "source": "kronos:" + shard,
                            "profile": prof, "stats": data}
            last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)[:60]
    return {"ok": False, "fallback": True, "uid": uid,
            "error": (f"⏳ BGMI ka public stats server abhi jawab nahi diya ({last_err}).\n"
                      "BGMI (India) ke liye officially koi free public API nahi hai — isliye "
                      "yaar ka UID se stats abhi nahi mil paya.\n\n"
                      "✅ <b>Official tarika (100% sahi):</b>\n"
                      "1. BGMI game kholo\n"
                      "2. <b>Profile</b> dabao → wahan UID dikhta hai\n"
                      "3. Ya <b>Friends → Search</b> me UID dalo → poora profile + stats dikhega\n\n"
                      "⚠️ Jo bhi third-party site 'private stats' ka dawa karti hai — wo risky "
                      "hoti hai (data chori ho sakta hai). Is bot me sirf public/official data aayega.")
            }


def _kronos_profile(uid: str, shard: str) -> dict:
    try:
        r = requests.get(f"https://kronos-api.pubg.com/shards/{shard}/players/{uid}",
                         headers=UA, timeout=10)
        if r.status_code == 200:
            d = r.json().get("data") or {}
            return {"name": d.get("actorName") or "—",
                    "level": d.get("level") or "—",
                    "rankPoints": d.get("rankPoints") or "—"}
    except Exception:
        pass
    return {"name": "—", "level": "—", "rankPoints": "—"}
