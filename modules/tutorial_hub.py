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
## 1. How this bot works (3 basics)

This bot does 30+ jobs — download, auto-forward, photo/documents, information, QR, calculations, media.

> 1. Pick a tool from the KEYBOARD below (or send /menu).
> 2. The tool asks one thing at a time — just send that (link / number / photo).
> 3. Send /cancel any time to close the tool and return to the menu.

New here? You get free credits for the premium tools. VIP = unlimited, no limits at all.

## 2. Channel Cloner / Auto-Forward (3 steps)

Use this to copy posts from one channel to another automatically.

> Step 1 — SOURCE: the channel you copy from. For a public channel send the link/username (@mychannel). For a private channel forward any one post to the bot — it will read the ID.
> Step 2 — TARGET: the channel to send posts to (the bot must be admin there).
> Step 3 — Turn FULL AUTO ON.

After that every new post in the source goes to the target automatically. Tag, caption, watermark, replace-words and thumbnail can all be set in settings.
For a private channel the bot must be added as admin — the "🔒 PRIVATE CHANNEL SETUP" button explains it.

## 3. Video and file downloader

> • 📥 VIDEO DOWNLOADER — send a public post link from Instagram / YouTube / Facebook / X / TikTok / Pinterest / Reddit / Vimeo. Videos up to 48MB come straight in the bot; bigger files give a direct download link.
> • ⚡ TERABOX & CLOUD — paste a Terabox, Mediafire, Google Drive or Mega link → direct link with no ads and no speed limit.
> • How to copy a link: in the app tap Share → Copy Link → paste in the bot.

Private or age-restricted posts do not work. Some sites rate-limit — try again after 30-60 seconds.

## 4. Photo and document tools

> • 📸 PASSPORT PHOTO — send photo → type name → type date → official 3.5 × 4.5 cm photo with name/date stamp (for SSC/Railway/BPSC forms).
> • 🖨️ 8-IN-1 SHEET — one photo → 8 copies on a 4×6 inch sheet. Print it at any studio for ₹10-20.
> • 📄 DOCUMENT PDF COMPRESS — send a marksheet/certificate photo → sharp PDF, you choose the size (100KB to 500KB).
> • 🖼️ IMAGE→PDF — up to 10 photos → one PDF. "A4 PDF" gives the correct size for printing.
> • 🏦 BANK STATEMENT PDF → EXCEL — send the statement PDF → Excel/CSV table with totals.
> • 📜 DOCUMENT SUITE — rent agreement, affidavit, legal notice 138, land deal receipt, loan paper, registry total cost, bigha/kattha converter.
> • 🖼️ SITE SCREENSHOT — send a website URL → HD screenshot (full page also).

## 5. Information tools

> • 🚗 VEHICLE INFO + CHALLAN — number plate (BR30AR0802) → full RC report (maker, fuel, insurance, PUC, finance) + all challans (pending / paid) with amount and offence. Live from the VAHAN/e-Challan API. VIP feature.
> • 📲 IMEI / PHONE DETAILS — 15 digit IMEI (dial *#06#) → brand, model, device photo + full spec sheet (display, chipset, RAM/storage, camera, battery, network) + a .json copy file. VIP feature.
> • 🎬 CLIP MAKER — send a video (file, direct .mp4 link, or YouTube) → 4-7 short clips (25-60 sec). Best Moments (loud + action parts) or Equal Parts, 16:9 or 9:16. Limit 15 min. VIP feature.
> • 📱 NUMBER INFO — 10 digit number → operator, circle (region), number type + WhatsApp/Telegram/Truecaller/cyber-helpline links.
> • 🏦 IFSC INFO — IFSC → bank, branch, address, MICR + UPI/NEFT/RTGS support. Always check before sending money.
> • 📮 PINCODE INFO — 6-digit pincode or area name → district/state + all post offices.
> • 🌐 IP / DOMAIN INFO — IP or website → location, ISP, VPN/proxy check.
> • 🆔 ID & USERNAME FINDER — send "me" (your ID), or forward any message (their ID), or send @username (checks GitHub/Telegram/YouTube/TikTok/Steam).
> • 🏛️ SARKARI SEVA / 🎓 STUDENT EXAM HUB — direct links to official government portals and exam sites.

## 6. Media Studio

> • 🎵 YouTube → MP3 — song link → MP3 file.
> • 🎬 Status Video — photo + song + your text → 9:16 status video.
> • 🎧 Ringtone cutter — 30 second ringtone from any song or video.
> • 🎤 Karaoke — removes the vocals, keeps the music.
> • 🔊 8D / Bass boost — better, deeper sound.
> • 🗣️ Voice change — kid / heavy / robot / ghost / gadget / echo.
> • ✂️ Video trim • 🗜️ Video compress (WhatsApp size) • 🎼 Video → MP3.

## 7. Small daily tools

> • 📷 QR CODE — link/text, WiFi share, contact card.
> • 📈 INTEREST CALC — compound interest the village way (per ₹100 per month).
> • 📦 APP FINDER — app name → direct links from 8 trusted stores (do not download APKs from random sites).
> • 🔗 URL SHORT — shorten a long link. 🔓 LINK BYPASS — get the real link behind ad links. 🔍 LINK CHECK — is a link fake or safe.
> • 🧮 REGISTRY TOTAL COST (inside Document Suite) — stamp duty + registration + MVR.

## 8. VIP / Premium — what you get

> • ♾️ Unlimited usage (no credit limits).
> • 🚀 Video downloader, Number info, Channel cloner, Private channel setup.
> • 🏦 Bank PDF → Excel, 📜 Document Suite, ⚡ Media Studio.
> • 📸 All photo and document tools (these are free for everyone).

Plan: send /premium → pick a plan → pay by QR → the bot asks for proof in 3 steps:

> 1. UTR number — after payment you can see "UTR / Ref No" in PhonePe/GPay/Paytm History or Passbook (12 digits, like 448612394857). Send that to the bot.
> 2. Screenshot — send the screenshot of that same payment (amount and UTR must be visible).
> 3. That is all — the admin verifies and turns on VIP, and you get a message. Check the status with /mypay.

⚠️ What will not work: your own photo/selfie, a meme, an old screenshot, someone else's UTR, or only the text "I paid". The bot rejects such proof.

## 9. Refer & Earn

Send your referral link to a friend → when they join, you get bonus days. The "🎁 REFER & EARN" button shows your link and count.

## 10. If something goes wrong

> • Tool stuck? → send /cancel.
> • "All credits used" shown? → get VIP with /premium.
> • Account banned? → contact the admin.
> • Need help any time → tap the "❓ HELP / TUTORIAL" button under the keyboard.

## 11. One line for every tool

Below this, every tool is explained in full detail — keep scrolling.

Any question? Message /support or @Supermannn_x.
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
    "linkbypass": "linkbypass",
    "linkcheck": "linkcheck",
    "interest": "interest",
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
    # ---- v38 naye tools (abhi closest video; apne video v39 me banenge) ----
    "bankpdf": "doc_compress",
    "kagaz": "pdf",
    "mediastudio": "video_dl",
    # ---- v40/v41 live API tools (closest video; apna video banega) ----
    "imei": "numinfo",
    "clips": "video_dl",
}

# video ke caption me tool ki jhalak (video title)
VIDEO_TITLES = {
    "video_dl": "📥 VIDEO DOWNLOADER", "terabox": "⚡ TERABOX DOWNLOADER", "cloner": "🔄 CHANNEL CLONER",
    "pp_stamp": "📸 PASSPORT PHOTO", "print_sheet": "🖨️ 8-IN-1 PRINT SHEET",
    "doc_compress": "📄 DOCUMENT PDF COMPRESS", "pdf": "🖼️ IMAGE TO PDF", "shot": "🖼️ SITE SCREENSHOT",
    "rto": "🚗 VEHICLE INFO + CHALLAN", "numinfo": "📱 NUMBER INFO", "ifsc": "🏦 IFSC INFO", "pin": "📮 PINCODE INFO",
    "idfind": "🆔 ID FINDER", "ip": "🌐 IP / DOMAIN INFO", "qr": "📷 QR CODE",
    "short": "🔗 URL SHORT", "linkbypass": "🔓 LINK BYPASS",
    "linkcheck": "🔍 LINK CHECK", "interest": "📈 INTEREST CALCULATOR", "appfind": "📦 APP FINDER",
    "sarkari": "🏛️ SARKARI PORTALS", "exam": "🎓 STUDENT EXAM HUB", "premium": "💎 VIP PREMIUM",
    "refer": "🎁 REFER & EARN", "account": "👤 MY ACCOUNT", "vnum": "🌐 VIRTUAL NUMBERS",
    "tutorial": "❓ HOW TO USE BOT",
    "bankpdf": "🏦 BANK PDF → EXCEL", "kagaz": "📜 DOCUMENT SUITE", "mediastudio": "⚡ MEDIA STUDIO",
    "imei": "📲 IMEI / PHONE DETAILS", "clips": "🎬 CLIP MAKER",
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
        "30 second video — full steps step by step 🔥\n\n"
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
        nodes.append({"tag": "h3", "children": ["Every tool in one line"]})
        nodes += text_to_nodes(short_list)
    if prompts_map:
        nodes.append({"tag": "hr"})
        nodes.append({"tag": "h3", "children": ["Video tutorial (30 second video for every tool)"]})
        for key in prompts_map:
            if not has_video(key):
                continue
            title = VIDEO_TITLES.get(video_key(key), key)
            nodes.append({"tag": "p", "children": [
                {"tag": "a", "attrs": {"href": tutorial_video_url(key)}, "children": [f"🎬 {title} — watch the video"]}]})
        nodes.append({"tag": "hr"})
        nodes.append({"tag": "h3", "children": ["Full details of every tool"]})
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
