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

TUTORIAL_TITLE = "Utility Duniya Bot — Full Tutorial"
TUTORIAL_AUTHOR = "Utility Duniya Bot"

# Agar env TUTORIAL_URL set ho to wahi chalega (bot.py dekh leta hai).
DEFAULT_PAGE_NAME = "utility-duniya-bot-tutorial"

# ======================================================================
# 1. POORA TUTORIAL TEXT  (yahi page par embed hota hai)
# ======================================================================
TUTORIAL_INTRO = """
## 1. Ye bot kaise chalta hai (3 basic baatein)

Ye bot 30+ kaam karta hai — download, auto-forward, photo/document, information, QR, media.

> 1. Neeche KEYBOARD se koi tool chuno (ya /menu bhejo).
> 2. Tool ek-ek cheez maangta hai — bas wahi bhej do (link / number / photo).
> 3. Kabhi bhi /cancel bhejo — tool band ho jayega aur menu wapas aa jayega.

Naye ho? Premium tools ke liye free credits milte hain. VIP = unlimited, koi limit nahi.

## 2. Channel Cloner / Auto-Forward (3 step)

Isse ek channel ke posts doosre channel me automatic copy hote hain.

> Step 1 — SOURCE: jis channel se copy karna hai. Public channel ke liye link/username bhejo (@mychannel). Private channel ke liye us channel ki koi ek post bot ko forward karo — bot ID khud padh lega.
> Step 2 — TARGET: jis channel me posts bhejne hain (wahan bot admin hona chahiye).
> Step 3 — FULL AUTO CHALU karo.

Uske baad source ka har naya post automatic target par chala jayega. Tag, caption, watermark, words replace aur thumbnail — sab settings me set kar sakte ho.
Private channel ke liye bot ko admin banana zaroori hai — "🔒 PRIVATE CHANNEL SETUP" button me poora tarika likha hai.

## 3. Video aur file downloader

> • 📥 VIDEO DOWNLOADER — Instagram / YouTube / Facebook / X / TikTok / Pinterest / Reddit / Vimeo ka public post link bhejo. 48MB tak ki video seedha bot me aa jati hai; badi file ke liye direct download link milta hai.
> • ⚡ TERABOX & CLOUD — Terabox, Mediafire, Google Drive ya Mega link paste karo → bina ads, bina speed limit direct link.
> • Link kaise copy karein: app me Share → Copy Link → bot me paste karo.

Private ya age-restricted posts kaam nahi karte. Kuch sites rate-limit karti hain — 30-60 second baad dobara try karo.

## 4. Photo aur document tools

> • 📸 PASSPORT PHOTO — photo bhejo → naam likho → date likho → official 3.5 × 4.5 cm photo with naam/date stamp (SSC/Railway/BPSC forms ke liye).
> • 🖨️ 8-IN-1 SHEET — ek photo → 4×6 inch sheet par 8 copies. Kisi bhi studio se ₹10-20 me print karwa lo.
> • 📄 DOCUMENT PDF COMPRESS — marksheet/certificate ki photo bhejo → sharp PDF, size aap chuno (100KB se 500KB).
> • 🖼️ IMAGE→PDF — 10 photo tak → ek PDF. "A4 PDF" printing ke liye sahi size deta hai.
> • 🏦 BANK STATEMENT PDF → EXCEL — statement PDF bhejo → totals ke saath Excel/CSV table.
> • 📜 DOCUMENT SUITE — kirayanama, affidavit, legal notice 138, bayana receipt, loan paper, registry total cost, bigha/kattha converter.
> • 🖼️ SITE SCREENSHOT — website ka URL bhejo → HD screenshot (full page bhi).

## 5. Information tools

> • 🚗 VEHICLE INFO + CHALLAN — number plate (BR30AR0802) → poora RC report (maker, fuel, insurance, PUC, finance) + saare challans (pending / paid) amount aur offence ke saath. VAHAN/e-Challan API se live. VIP feature.
> • 📲 IMEI / PHONE DETAILS — 15 digit IMEI (*#06# dial karo) → brand, model, phone ki photo + poori spec sheet (display, chipset, RAM/storage, camera, battery, network) + .json copy file. VIP feature.
> • 📱 NUMBER INFO — 10 digit number → operator, circle (region), number type + WhatsApp/Telegram/Truecaller/cyber-helpline links.
> • 🏦 IFSC INFO — IFSC → bank, branch, address, MICR + UPI/NEFT/RTGS support. Paise bhejne se pehle zaroor check karo.
> • 📮 PINCODE INFO — 6 digit pincode ya area ka naam → district/state + saare post offices.
> • 🌐 IP / DOMAIN INFO — IP ya website → location, ISP, VPN/proxy check.
> • 🆔 ID & USERNAME FINDER — "me" bhejo (apni ID), ya koi message forward karo (unki ID), ya @username bhejo (GitHub/Telegram/YouTube/TikTok/Steam check).
> • 🏛️ SARKARI SEVA PORTALS — official government portals ke direct links (caste/income certificate, land records, e-Challan, EPFO).

## 6. Media Studio

> • 🎵 YouTube → MP3 — gaane ka link → MP3 file.
> • 🎬 Status Video — photo + gaana + apna text → 9:16 status video.
> • 🎧 Ringtone cutter — kisi bhi gaane ya video se 30 second ka ringtone.
> • 🎤 Karaoke — vocals hata deta hai, music rehta hai.
> • 🔊 8D / Bass boost — awaaz zyada deep aur mazedaar.
> • 🗣️ Voice change — kid / heavy / robot / ghost / gadget / echo.
> • ✂️ Video trim • 🗜️ Video compress (WhatsApp size) • 🎼 Video → MP3.

## 7. Chhote daily tools

> • 📷 QR CODE — link/text, WiFi share, contact card.
> • 📦 APP FINDER — app ka naam → 8 bharosemand stores se direct links (random site se APK download mat karo).
> • 🔗 URL SHORT — lamba link chhota karo. 🔍 LINK CHECK — link nakli hai ya safe.
> • 🧮 REGISTRY TOTAL COST (Document Suite ke andar) — stamp duty + registration + MVR.

## 8. VIP / Premium — kya milta hai

> • ♾️ Unlimited use (koi credit limit nahi).
> • 🚀 Video downloader, Number info, Channel cloner, Private channel setup.
> • 🏦 Bank PDF → Excel, 📜 Document Suite, ⚡ Media Studio.
> • 📸 Saare photo aur document tools (ye sabke liye free hain).

Plan lene ke liye: /premium bhejo → plan chuno → QR se payment karo → bot 3 step me proof maangta hai:

> 1. UTR number — payment ke baad PhonePe/GPay/Paytm ke History ya Passbook me "UTR / Ref No" dikhta hai (12 digit, jaise 448612394857). Wahi bot ko bhejo.
> 2. Screenshot — usi payment ka screenshot bhejo (amount aur UTR saaf dikhna chahiye).
> 3. Bas itna hi — admin verify karke VIP chalu kar deta hai, aapko message aa jata hai. Status /mypay se dekh lo.

⚠️ Ye nahi chalega: apni photo/selfie, meme, purana screenshot, kisi aur ka UTR, ya sirf "maine paise bheje" likhna. Bot aisa proof reject kar deta hai.

## 9. Refer & Earn

Apna referral link dost ko bhejo → wo join kare to aapko bonus days milte hain. "🎁 REFER & EARN" button par aapka link aur count dikhta hai.

## 10. Kuch galat ho jaye to

> • Tool atak gaya? → /cancel bhejo.
> • "Credits khatam" dikha? → /premium se VIP lo.
> • Account ban ho gaya? → admin se baat karo.
> • Kabhi bhi madad chahiye → keyboard ke neeche "❓ HELP / TUTORIAL" button dabao.

## 11. Har tool ek line me

Iske neeche har tool poori detail me likha hai — scroll karte raho.

Koi sawal? /support par message karo ya @Supermannn_x.
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
    "qr_wifi": "qr",
    "qr_vcard": "qr",
    "short": "short",
    "linkcheck": "linkcheck",
    "appfind": "appfind",
    "sarkari": "sarkari",
    "premium": "premium",
    "vip": "premium",
    "refer": "refer",
    "account": "account",
    "vnum": "vnum",
    "tutorial": "tutorial",
    "help": "tutorial",
    "video_dl": "video_dl",
    # ---- v38 naye tools (abhi closest video; apne video v39 me banenge) ----
    "bankpdf": "doc_compress",
    "kagaz": "pdf",
    "mediastudio": "video_dl",
    # ---- v40/v41 live API tools (closest video; apna video banega) ----
    "imei": "numinfo",
}

# video ke caption me tool ki jhalak (video title)
VIDEO_TITLES = {
    "video_dl": "📥 VIDEO DOWNLOADER", "terabox": "⚡ TERABOX DOWNLOADER", "cloner": "🔄 CHANNEL CLONER",
    "pp_stamp": "📸 PASSPORT PHOTO", "print_sheet": "🖨️ 8-IN-1 PRINT SHEET",
    "doc_compress": "📄 DOCUMENT PDF COMPRESS", "pdf": "🖼️ IMAGE TO PDF", "shot": "🖼️ SITE SCREENSHOT",
    "rto": "🚗 VEHICLE INFO + CHALLAN", "numinfo": "📱 NUMBER INFO", "ifsc": "🏦 IFSC INFO", "pin": "📮 PINCODE INFO",
    "idfind": "🆔 ID FINDER", "ip": "🌐 IP / DOMAIN INFO", "qr": "📷 QR CODE",
    "short": "🔗 URL SHORT",
    "linkcheck": "🔍 LINK CHECK", "appfind": "📦 APP FINDER",
    "sarkari": "🏛️ SARKARI PORTALS", "premium": "💎 VIP PREMIUM",
    "refer": "🎁 REFER & EARN", "account": "👤 MY ACCOUNT", "vnum": "🌐 VIRTUAL NUMBERS",
    "tutorial": "❓ HOW TO USE BOT",
    "bankpdf": "🏦 BANK PDF → EXCEL", "kagaz": "📜 DOCUMENT SUITE (+ GST/PAN check)", "mediastudio": "⚡ MEDIA STUDIO",
    "imei": "📲 IMEI / PHONE DETAILS",
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
    title = VIDEO_TITLES.get(action) or VIDEO_TITLES.get(key, "🎬 TUTORIAL")
    return (
        f"🎬 <b>{title}</b> — TUTORIAL\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "30 second video — poore steps ek-ek karke 🔥\n\n"
        "👤 <b>By:</b> HIMANSHU • @Supermannn_x\n"
        "▶️ Watch it, then open the same tool from the menu below."
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
      3) full details of every tool (from bot prompts)
    """
    nodes = []
    nodes += text_to_nodes(TUTORIAL_INTRO)
    if short_list:
        nodes.append({"tag": "hr"})
        nodes.append({"tag": "h3", "children": ["Har tool ek line me"]})
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
def _api(method: str, **data):
    """method = telegra.ph API ka naam (createPage/editPage...).
    NOTE: param ka naam 'method' hai — 'path' nahi, warna editPage ke path= se clash ho jata hai."""
    if requests is None:
        return {}
    r = requests.post("https://api.telegra.ph/" + method, data=data, timeout=25)
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
