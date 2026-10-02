"""
tutorial_hub.py — v34
=====================
Bot ke andar se "kaise use karein" wale tutorial text HATA diye gaye hain.
Ab poora tutorial ek hi page par rehta hai (telegra.ph), aur bot me sirf
neeche ek LINK dikhta hai.

Is module me:
  1. TUTORIAL_INTRO      — poori Hinglish tutorial (saare tools ka tareeka)
  2. strip_tutorial_lines() — tool ke prompt se "💡 Kaise use karein / Kaam" lines hatata hai
  3. build_page_content()  — tutorial + saare tools ke text ko telegra.ph nodes me badalta hai
  4. publish_tutorial()    — telegra.ph par page banata/update karta hai (link wapas deta hai)

Bina internet ho ya telegra.ph block ho to bot fallback link (GitHub) use karta hai.
"""

import hashlib
import json
import os
import re

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

TUTORIAL_TITLE = "Utility Duniya Bot — Poora Tutorial (Hinglish)"
TUTORIAL_AUTHOR = "Utility Duniya Bot"

# Agar env TUTORIAL_URL set ho to wahi chalega (bot.py dekh leta hai).
DEFAULT_PAGE_NAME = "utility-duniya-bot-tutorial"

# ======================================================================
# 1. POORA TUTORIAL TEXT  (yahi page par embed hota hai)
# ======================================================================
TUTORIAL_INTRO = """
## 1. Bot kaise chalta hai (3 basic baatein)

Ye bot 30+ kaam karta hai — download, cloner, photo/document, info, QR, hisaab, voice — sab kuch.

> 1. Neeche wale KEYBOARD se tool chuno (ya /menu bhejo).
> 2. Tool apna sawaal poochhega — bas wahi cheez bhej do (link / number / photo).
> 3. Kabhi bhi /cancel bhejo → tool band, wapas menu.

Pehli baar aa rahe ho? Free me roz kuch tools chal sukte hain (free limit khatam ho jaye to bot VIP ka option dikhayega). VIP = unlimited, bina koi limit.

## 2. Channel Cloner / Auto-Forward (3 step)

Apne ek channel ki posts doosre channel me khud-ba-khud bhejni ho to ye tool.

> Step 1 — SOURCE: jahan se posts leni hain. Public channel ho to link/username bhej do (@mychannel). Private channel ho to us channel ki koi ek post bot ko forward karo — bot ID pakad lega.
> Step 2 — TARGET: jahan posts bhejni hain (bot wahan admin hona chahiye).
> Step 3 — FULL AUTO ON kar do.

Uske baad jo bhi post source channel me aayegi, bot target me bhej dega. Tag, caption, watermark, replace-words, thumbnail sab settings me set kar sakte ho.
Private channel me bot ko admin banana zaroori hai — "🔒 PRIVATE CHANNEL SETUP" button wahi batata hai.

## 3. Actors Voice Studio (text se awaaz)

Text likho → asli awaaz (voiceover) ban jayegi.

> • Actor/Character Voices: 24 alag awaazein (Don, South mass hero, Shayar, Robot, Anime girl, News anchor...).
> • Voice Lab: 30 awaazein + speed control (Hindi, English, Tamil, Telugu, Bengali, Marathi, Urdu, Arabic, French...).
> • Hindi me likhoge to Hindi awaaz, English me likhoge to English awaaz — bot khud set kar leta hai.

## 4. Video aur File Downloader

> • 📥 VIDEO DOWNLOADER — Instagram / YouTube / Facebook / X / TikTok / Pinterest / Reddit / Vimeo ke public post ka link bhejo. 48MB tak video seedha bot me, bada file ho to direct download link.
> • ⚡ TERABOX & CLOUD — Terabox, Mediafire, Google Drive, Mega ka link paste karo → bina ad, bina speed-limit direct link + browser player.
> • Link kaise copy karein: app me Share → Copy Link → bot me paste.

Private/age-restricted account ki post nahi chalti. Kuch site rate-limit lagati hai — 30-60 second baad dobara try karo.

## 5. Photo aur Document ke tools (cyber cafe wala kaam)

> • 📸 PASSPORT PHOTO — photo bhejo → naam likho → date likho → official 3.5 × 4.5 cm photo with naam/date stamp (SSC/Railway/BPSC form ke liye).
> • 🖨️ 8-IN-1 SHEET — ek photo se 8 copies ek 4×6 inch sheet par. Kisi studio se ₹10-20 me print karwa lo.
> • 📄 DOCUMENT PDF COMPRESS — marksheet/certificate ki photo bhejo → sharp PDF, size 100KB se 500KB tak aap chuno.
> • 🖼️ IMAGE→PDF — 10 photo tak → ek PDF. "A4 PDF" printer ke liye sahi size.
> • 🖼️ SITE SCREENSHOT — website ka URL → HD screenshot (full page bhi).

## 6. Information tools

> • 🚗 RTO VEHICLE INFO — number plate (BR01AB1234) → state, RTO office, district + VAHAN/e-Challan/insurance/DL ke official links.
> • 📱 NUMBER INFO — 10 digit number → operator, circle (region), number type + WhatsApp/Telegram/Truecaller/cyber-helpline links.
> • 🏦 IFSC INFO — IFSC → bank, branch, address, MICR + UPI/NEFT/RTGS support. Paisa bhejne se pehle check karo.
> • 📮 PINCODE INFO — 6-digit pincode ya area ka naam → district/state + saare post offices.
> • 🌐 IP / DOMAIN INFO — IP ya website → location, ISP, VPN/proxy check.
> • 🆔 ID & USERNAME FINDER — "me" bhejo (apni ID), ya kisi ka message forward karo (uski ID), ya @username bhejo (GitHub/Telegram/YouTube/TikTok/Steam par account hai ya nahi).
> • 🏛️ SARKARI SEVA / 🎓 STUDENT EXAM HUB — official sarkari portal aur exam ke direct links.

## 7. Roz ke chhote tools

> • 📷 QR CODE — link, UPI, WiFi, contact card ka QR (dukaan/auto ke liye payment QR bhi).
> • 🔐 PASSWORD GENERATOR — naam wala, easy-words, random, PIN.
> • 🧮 EMI CALC — "500000 9% 24m" → EMI + loan kitne mahine/din me poora.
> • 📈 VYAAJ (INTEREST) — 50000 → 5 (₹100 par ₹5) → 12 mahine → chakravriddhi hisaab.
> • 🎂 AGE CALC — DOB (DD-MM-YYYY) → exact umar, agla birthday, rashi.
> • 🧑‍🤝‍🧑 FAMILY TREE — naam → relationship calculator.
> • 🔎 WEB SEARCH — Google jaisa search, ek saath DuckDuckGo + Bing ke results.
> • 📦 APP FINDER — app ka naam → 8 trusted store ke direct links (random site se APK mat lo, virus ka khatra).
> • 🔗 URL SHORT — lamba link chhota. 🔓 LINK BYPASS — ad-wale short link ka asli link. 🔍 LINK CHECK — link fake/scam hai ya asli.

## 8. VIP / Premium — kya milta hai

> • ♾️ Unlimited daily usage (free limit khatam).
> • 🚀 Terabox/cloud ki high-speed download.
> • 🔄 Cloner + Auto-Forward with custom branding.
> • 🎙️ Poora Actors Voice Studio.
> • 📸 Saare photo/document tools.

Plan: /premium bhejo → plan chuno → QR se paisa → phir bot 3 step me proof maangta hai:

> 1. UTR number — payment ke baad PhonePe/GPay/Paytm ki History ya Passbook me "UTR / Ref No" likha hota hai (12 digit, jaise 448612394857). Wahi bot ko bhejo.
> 2. Screenshot — usi payment ki History/Passbook ka screenshot bhejo (poora screen, jisme amount aur UTR dikhe).
> 3. Bas itna — admin verify karke VIP on kar dega, aapko message aa jayega. /mypay se status dekh sakte ho.

⚠️ Kya nahi chalega: apni photo/selfie, meme, dusri purani screenshot, kisi aur ka UTR, ya sirf text "paisa bhej diya". Aisa bhejne par bot mana kar dega.

## 9. Refer & Earn

Apna referral link dost ko bhejo → wo join kare to aapko bonus din milte hain. "🎁 REFER & EARN" button me link aur count dikhta hai.

## 10. Problem aaye to?

> • Tool chal raha hai nahi ruk raha? → /cancel bhejo.
> • "Daily limit khatam" dikha? → /premium se VIP lo, ya kal dobara free use karo.
> • Account ban? → admin se contact karo.
> • Kabhi bhi madad chahiye → bot me keyboard ke neeche "❓ MADAD / TUTORIAL" button dabao, yahi page khul jayega.

## 11. Neeche har tool ka short tareeka (1-1 line)

Uske baad har tool ki poori detail bhi isi page par di gayi hai — scroll karte jao.

Sawaal ho to bot me /support ya @Supermannn_x par message kar do.
""".strip()


# ======================================================================
# 1b. HAR TOOL KA TUTORIAL VIDEO (30-40 sec, Hindi voice, HIMANSHU)
# ======================================================================
REPO_SLUG = os.getenv("TUTORIAL_REPO", "himanshu75919-coder/utility-duniya-bot")
# jsDelivr CDN (fast + Telegram ko pasand) — fallback: GitHub raw
VIDEO_BASE = os.getenv(
    "TUTORIAL_VIDEO_BASE",
    f"https://cdn.jsdelivr.net/gh/{REPO_SLUG}@main/tutorial_videos",
).rstrip("/")
VIDEO_BASE_FALLBACK = os.getenv(
    "TUTORIAL_VIDEO_BASE_FALLBACK",
    f"https://raw.githubusercontent.com/{REPO_SLUG}/main/tutorial_videos",
).rstrip("/")

# bot ke tool/action → video file ka naam
TUTORIAL_VIDEO_KEYS = {
    "terabox": "terabox",
    "insta_dl": "video_dl",
    "cloner": "cloner",
    "cloner_private_help": "cloner",
    "voice": "voice",
    "pp_stamp": "pp_stamp",
    "print_sheet": "print_sheet",
    "doc_compress": "doc_compress",
    "pdf": "pdf",
    "shot": "shot",
    "shot_full": "shot",
    "rto": "rto",
    "numinfo": "numinfo",
    "ifsc": "ifsc",
    "pin": "pin",
    "idfind": "idfind",
    "ip": "ip",
    "qr": "qr",
    "qr_upi": "upi",
    "qr_wifi": "qr",
    "qr_vcard": "qr",
    "upi": "upi",
    "pwd": "pwd",
    "pwd_name": "pwd",
    "pwd_rand": "pwd",
    "pwd_pin": "pwd",
    "pwd_phrase": "pwd",
    "short": "short",
    "linkbypass": "linkbypass",
    "linkcheck": "linkcheck",
    "emi": "emi",
    "interest": "interest",
    "age": "age",
    "search": "search",
    "appfind": "appfind",
    "sarkari": "sarkari",
    "exam": "exam",
    "premium": "premium",
    "vip": "premium",
    "refer": "refer",
    "account": "account",
    "vnum": "vnum",
    "tutorial": "tutorial",
    "help": "tutorial",
    "video_dl": "video_dl",
}

# video ke caption me tool ki jhalak (video title)
VIDEO_TITLES = {
    "video_dl": "📥 VIDEO DOWNLOADER", "terabox": "⚡ TERABOX DOWNLOADER", "cloner": "🔄 CHANNEL CLONER",
    "voice": "🎙️ ACTORS VOICE STUDIO", "pp_stamp": "📸 PASSPORT PHOTO", "print_sheet": "🖨️ 8-IN-1 PRINT SHEET",
    "doc_compress": "📄 DOCUMENT PDF COMPRESS", "pdf": "🖼️ IMAGE TO PDF", "shot": "🖼️ SITE SCREENSHOT",
    "rto": "🚗 RTO VEHICLE INFO", "numinfo": "📱 NUMBER INFO", "ifsc": "🏦 IFSC INFO", "pin": "📮 PINCODE INFO",
    "idfind": "🆔 ID FINDER", "ip": "🌐 IP / DOMAIN INFO", "qr": "📷 QR CODE", "upi": "💰 UPI QR GENERATOR",
    "pwd": "🔐 PASSWORD GENERATOR", "short": "🔗 URL SHORT", "linkbypass": "🔓 LINK BYPASS",
    "linkcheck": "🔍 LINK CHECK", "emi": "🧮 EMI CALCULATOR", "interest": "📈 INTEREST CALCULATOR",
    "age": "🎂 AGE CALCULATOR", "search": "🔎 WEB SEARCH", "appfind": "📦 APP FINDER",
    "sarkari": "🏛️ SARKARI PORTALS", "exam": "🎓 STUDENT EXAM HUB", "premium": "💎 VIP PREMIUM",
    "refer": "🎁 REFER & EARN", "account": "👤 MY ACCOUNT", "vnum": "🌐 VIRTUAL NUMBERS",
    "tutorial": "❓ HOW TO USE BOT",
}


def video_key(action: str) -> str:
    return TUTORIAL_VIDEO_KEYS.get(action, action)


def tutorial_video_url(action: str) -> str:
    return f"{VIDEO_BASE}/{video_key(action)}.mp4"


def tutorial_video_url_fallback(action: str) -> str:
    return f"{VIDEO_BASE_FALLBACK}/{video_key(action)}.mp4"


def video_urls(action: str) -> list:
    """[primary CDN, fallback raw] — pehla jo chale wahi bhejenge."""
    p, fb = tutorial_video_url(action), tutorial_video_url_fallback(action)
    return [p] if p == fb else [p, fb]


def has_video(action: str) -> bool:
    return action in TUTORIAL_VIDEO_KEYS


def video_caption(action: str) -> str:
    key = video_key(action)
    title = VIDEO_TITLES.get(key, "🎬 TUTORIAL")
    return (
        f"🎬 <b>{title}</b> — TUTORIAL\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "30 second ka video — poora tareeka step by step 🔥\n\n"
        "👤 <b>By:</b> HIMANSHU • @Supermannn_x\n"
        "▶️ Dekho, samjho, aur neeche menu se wahi tool kholo."
    )


# ======================================================================
# 2. TOOL PROMPT SE TUTORIAL LINES HATANA
# ======================================================================
def _is_block_start(line: str) -> bool:
    """Nayi line apna naya block shuru kar rahi hai? (emoji / <tag> / ━)"""
    if not line:
        return False
    if line.startswith("━") or line.startswith("<") or line.startswith(">"):
        return True
    return ord(line[0]) >= 0x2300  # emoji range


def strip_tutorial_lines(text: str) -> str:
    """
    "💡 Kaise use karein: ..." / "💡 Kaam: ..." wali tutorial lines (aur unki
    agli continuation lines) hata deta hai. Baaki content jaisa hai waisa rehta hai.
    """
    if not text:
        return ""
    out = []
    skipping = False
    for line in text.split("\n"):
        ls = line.strip()
        if ls.startswith("💡"):
            skipping = True
            continue
        if skipping:
            if _is_block_start(ls):
                skipping = False
            else:
                continue
        out.append(line)

    # extra blank lines collapse + aakhir ke separators saaf karo
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    while cleaned.endswith("━"):
        cleaned = cleaned[:-1].rstrip()
    return cleaned


# ======================================================================
# 3. TELEGRAPH PAGE KE NODES
# ======================================================================
_INLINE_TAGS = {"b", "strong", "i", "em", "u", "s", "code", "a"}


def _inline(html: str) -> list:
    """Chhota HTML (<b>, <i>, <code>, <a href>) → telegra.ph inline nodes."""
    s = (html or "").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = re.sub(r"<br\s*/?>", "\n", s)
    nodes, pos = [], 0
    pattern = re.compile(r"<(/?)([a-zA-Z0-9]+)((?:\s+[^>]*)?)>")
    for m in pattern.finditer(s):
        if m.start() > pos:
            nodes.append(s[pos:m.start()])
        closing, tag = m.group(1) == "/", m.group(2).lower()
        if tag not in _INLINE_TAGS:
            pos = m.end()
            continue
        if closing:
            pos = m.end()
            continue
        end = s.find(f"</{tag}>", m.end())
        inner = s[m.end():end] if end != -1 else s[m.end():]
        node = {"tag": tag, "children": _inline(inner)}
        if tag == "a":
            href = re.search(r'href="([^"]+)"', m.group(3) or "")
            if href:
                node["attrs"] = {"href": href.group(1)}
            else:
                node = {"tag": "b", "children": _inline(inner)}
        nodes.append(node)
        pos = (end + len(tag) + 3) if end != -1 else len(s)
    if pos < len(s):
        nodes.append(s[pos:])
    return [n for n in nodes if n != ""] or [""]


def text_to_nodes(text: str) -> list:
    nodes = []
    for raw in (text or "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        if set(line) <= {"━", "-", "—"} and len(line) > 4:
            nodes.append({"tag": "hr"})
            continue
        if line.startswith("### "):
            nodes.append({"tag": "h4", "children": _inline(line[4:])})
            continue
        if line.startswith("## "):
            nodes.append({"tag": "h3", "children": _inline(line[3:])})
            continue
        if line.startswith("> "):
            nodes.append({"tag": "blockquote", "children": _inline(line[2:])})
            continue
        if line.startswith("<blockquote>"):
            inner = re.sub(r"</?blockquote>", "", line)
            nodes.append({"tag": "blockquote", "children": _inline(inner)})
            continue
        nodes.append({"tag": "p", "children": _inline(line)})
    return nodes


def build_page_content(prompts_map: dict = None, short_list: str = "") -> list:
    """
    Page ka poora content:
      1) intro (poora tutorial)
      2) har tool ka short 1-line list
      3) har tool ki poori detail (bot ke prompts se — jo text bot se hata tha)
    """
    nodes = []
    nodes += text_to_nodes(TUTORIAL_INTRO)
    if short_list:
        nodes.append({"tag": "hr"})
        nodes.append({"tag": "h3", "children": ["Har tool — ek line me"]})
        nodes += text_to_nodes(short_list)
    if prompts_map:
        nodes.append({"tag": "hr"})
        nodes.append({"tag": "h3", "children": ["Video tutorial (har tool ka 30 second video)"]})
        for key in prompts_map:
            if not has_video(key):
                continue
            title = VIDEO_TITLES.get(video_key(key), key)
            nodes.append({"tag": "p", "children": [
                {"tag": "a", "attrs": {"href": tutorial_video_url(key)}, "children": [f"🎬 {title} — video dekho"]}]})
        nodes.append({"tag": "hr"})
        nodes.append({"tag": "h3", "children": ["Har tool ki poori detail"]})
        for key, text in prompts_map.items():
            title = ""
            for ln in (text or "").split("\n"):
                if ln.strip():
                    title = re.sub(r"<[^>]+>", "", ln).strip()
                    break
            if title:
                nodes.append({"tag": "h4", "children": _inline(title)})
            body = "\n".join((text or "").split("\n")[1:])
            nodes += text_to_nodes(body)
    return nodes


# ======================================================================
# 4. PAGE PUBLISH / UPDATE
# ======================================================================
def _api(path: str, **data):
    if requests is None:
        return {}
    r = requests.post("https://api.telegra.ph/" + path, data=data, timeout=25)
    try:
        return r.json()
    except Exception:
        return {}


def publish_tutorial(meta_get, meta_set, prompts_map: dict = None, short_list: str = "", force: bool = False) -> str:
    """
    telegra.ph par tutorial page banao/update karo. URL wapas deta hai (fail = "").
    meta_get/meta_set = database.py ke chhote helper (token/url yaad rakhne ke liye).
    """
    if requests is None:
        return ""
    try:
        content = json.dumps(build_page_content(prompts_map, short_list), ensure_ascii=False)
        digest = hashlib.sha1(content.encode("utf-8")).hexdigest()
        saved_url = meta_get("tutorial_url", "")
        if not force and saved_url and meta_get("tutorial_hash", "") == digest:
            return saved_url  # pehle se updated hai

        token = meta_get("telegraph_token", "")
        if not token:
            acc = _api("createAccount", short_name="UtilityDuniya", author_name=TUTORIAL_AUTHOR)
            token = (acc.get("result") or {}).get("access_token", "")
            if not token:
                return ""
            meta_set("telegraph_token", token)

        path = meta_get("telegraph_path", "")
        payload = dict(access_token=token, title=TUTORIAL_TITLE, author_name=TUTORIAL_AUTHOR,
                       content=content, return_content="false")
        if path:
            payload["path"] = path
            res = _api("editPage", **payload)
            if not res.get("ok") and res.get("error") == "PATH_NOT_FOUND":
                path = ""
        if not path:
            res = _api("createPage", **payload)
        result = res.get("result") or {}
        url = result.get("url", "")
        if not res.get("ok") or not url:
            return ""
        meta_set("telegraph_token", token)
        meta_set("telegraph_path", result.get("path", ""))
        meta_set("tutorial_url", url)
        meta_set("tutorial_hash", digest)
        return url
    except Exception:
        return ""
