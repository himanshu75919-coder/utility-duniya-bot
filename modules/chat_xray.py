# -*- coding: utf-8 -*-
"""
💬 WHATSAPP CHAT X-RAY (v73.0)
==============================
User ka chuna hua tool: **"apni exported chat ki poori fun-report"**.

Kaam kaise karta hai (100% OFFLINE — koi API nahi, kabhi fail nahi):
  1. User WhatsApp se apni chat export karta hai (.txt — "Without media")
     ya media-wali export (.zip).
  2. Ye module file padhta hai (Android / iOS / 24-hour / am-pm — sab format).
  3. Fun report nikalta hai: total messages, top chatters, top words,
     emoji king, hasi king, raat ka jagaadu, busiest din/ghanta, media count...
  4. Ek sundar image report (WhatsApp dark theme) banata hai.

IMPORTANT (privacy): file sirf memory me padhi jati hai — kahin save/upload
nahi hoti. Report user ko hi wapas jati hai.
"""

import io
import re
import zipfile
from collections import Counter, defaultdict

# ---------------------------------------------------------------- limits
MAX_LINES = 300_000            # itne line se zyada = itna hi padhenge (speed)
MAX_BYTES = 12 * 1024 * 1024   # 12 MB se badi file = saaf error

# ---------------------------------------------------------------- regexes
# Android: "12/10/25, 9:41 pm - Rahul: Hi bhai"
# Android 24h: "12.10.2025, 21:41 - Rahul: Hi"
# iOS: "[12/10/25, 9:41:05 PM] Rahul: Hi"
_LRM = "\u200e\u200f\u202a\u202b\u202c\u2066\u2067\u2068\u2069\u00a0"
_RX_ANDROID = re.compile(
    r"^(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}),?\s+"
    r"(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[apAP]\.?\s?[mM]\.?)?)\s*[-\u2013\u2014]\s*"
    r"([^:]{1,80}?):\s?(.*)$")
_RX_IOS = re.compile(
    r"^\[(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}),?\s+"
    r"(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[apAP]\.?\s?[mM]\.?)?)\]\s*"
    r"([^:]{1,80}?):\s?(.*)$")
# Sirf timestamp wali line (system message) — user ka naam nahi
_RX_SYS = re.compile(
    r"^[\[\(]?(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}),?\s+"
    r"\d{1,2}:\d{2}(?::\d{2})?(?:\s*[apAP]\.?\s?[mM]\.?)?[\]\)]?\s*[-\u2013\u2014]?\s*(.*)$")

_RX_WORD = re.compile(r"[a-zA-Z\u0900-\u097F]{3,}")
_RX_MEDIA = re.compile(r"<\s*media omitted\s*>", re.I)
_RX_HAHA = re.compile(r"\b(?:ha(?:ha)+|he(?:he)+|hi(?:hi)+|lol|lmao)\b|[\U0001F602\U0001F923\U0001F606\U0001F605]",
                      re.I)
_RX_OK = re.compile(r"\b(?:ok+|okay|hmm+|haan+|han+|hmmm+)\b", re.I)
_RX_GM = re.compile(r"\b(?:good\s*morning|gm|suprabhat|सुप्रभात)\b", re.I)

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Hinglish + English stopwords (top-words list saaf rakhne ke liye)
_STOP = set("""
hai hain hoga hogi honge kya kyu kyun ye yeh wo woh vo kar karna karo kare
nahi nahin bhi aur par pr tha thi the theek ho raha rahi rahe rahata mera meri
mere tera teri tere aap tum hum main mein mai toh to se ka ki ke ko ek sab kuch
ab kal aaj bahut bohot accha acha ok okay haan han ha hua hui gaya gayi gaye
liye wala wali wale chalo chal hello hi hey good morning night bhai bro didi
bhaiya sir madam please plz god thanks thank thik aata aati aata jata jati
karne karte karta karti kaise kaisa kaisi konsa bata batao dekho dekh liya
bhej bhejo bhejna mila mil milta mile samajh pata nahin kar sakta sakti sakte
bas phir abhi warna jaisa waise kaun kab kitna kitne koi kuchh aapka apna
and the you for this that with from your have are was were will would can
could not but what when where who how why all any out get got one two now
than than very just know also only over some such into more most
end messages calls encrypted read listen outside photo video image sticker
document audio gif contact card joined left changed subject deleted message
was this you your omitted media file files sent received missed group added
removed created changed icon we're they're don't didn't cant can't
will be if or an so no yes see seen look looking going gone come
aayega aayegi ayega ayegi karega karegi hoga hogi honge dena denge diya
diye liye hua hue mat karo karna karke bola boli kaha kahi yehi wahi
other been call come came make made like time day today tomorrow yesterday
because about after before again still even much many little well does did
done doing say said says something anything nothing everything ok
""".split())

_EMOJI_NAMES = {
    "\U0001F602": "Laugh", "\U0001F923": "ROFL", "\U0001F606": "LOL", "\U0001F605": "Hehe",
    "\u2764": "Love", "\U0001F60D": "Heart Eyes", "\U0001F618": "Kiss", "\U0001F60A": "Smile",
    "\U0001F44D": "Thumbs Up", "\U0001F44C": "OK Hand", "\U0001F64F": "Please", "\U0001F64C": "Party",
    "\U0001F525": "Fire", "\U0001F4AF": "100", "\U0001F389": "Party Pop", "\U0001F382": "Cake",
    "\U0001F60E": "Cool", "\U0001F60B": "Yum", "\U0001F609": "Wink", "\U0001F62D": "Cry Loud",
    "\U0001F62E": "Shock", "\U0001F621": "Angry", "\U0001F624": "Huff", "\U0001F914": "Thinking",
    "\U0001F644": "Roll Eyes", "\U0001F60F": "Smirk", "\U0001F970": "Love Face", "\U0001F929": "Star Eyes",
    "\U0001F44F": "Clap", "\U0001F64B": "Raised Hand", "\U0001F642": "Slight Smile",
    "\U0001F643": "Upside Smile", "\U0001F63B": "Cat Love", "\U0001F496": "Sparkle Heart",
    "\U0001F494": "Broken Heart", "\U0001F612": "Unamused", "\U0001F610": "Neutral",
    "\U0001F615": "Confused", "\U0001F61C": "Tongue", "\U0001F601": "Grin", "\U0001F603": "Big Smile",
    "\U0001F604": "Big Smile", "\U0001F600": "Grin", "\U0001F440": "Eyes", "\U0001F4AA": "Muscle",
    "\U0001F4A5": "Boom", "\u2728": "Sparkles", "\u2705": "Check", "\u274C": "Cross",
    "\u2b50": "Star", "\U0001F31F": "Glow Star", "\U0001F4F7": "Camera", "\U0001F3B5": "Music",
    "\U0001F3B6": "Notes", "\U0001F44B": "Wave", "\U0001F91D": "Handshake", "\U0001F4F1": "Phone",
    "\U0001F4B0": "Money", "\U0001F48B": "Kiss Mark", "\U0001F495": "Hearts", "\U0001F49B": "Yellow Heart",
    "\U0001F499": "Blue Heart", "\U0001F49A": "Green Heart", "\U0001F49C": "Purple Heart",
    "\U0001F5A4": "Black Heart", "\U0001F90D": "White Heart", "\U0001F90E": "Brown Heart",
    "\U0001F9E1": "Orange Heart", "\U0001F497": "Growing Heart", "\U0001F49D": "Heart Gift",
    "\U0001F49E": "Revolving Hearts", "\U0001F498": "Cupid", "\U0001F493": "Beating Heart",
    "\U0001F607": "Halo", "\U0001F608": "Devil", "\U0001F47B": "Ghost", "\U0001F480": "Skull",
    "\U0001F921": "Clown", "\U0001F92A": "Zany", "\U0001F92C": "Swear", "\U0001F631": "Scream",
    "\U0001F628": "Fear", "\U0001F630": "Cold Sweat", "\U0001F622": "Sad", "\U0001F62A": "Sleepy",
    "\U0001F634": "Sleeping", "\U0001F971": "Yawn", "\U0001F973": "Party Face", "\U0001F60C": "Relieved",
    "\U0001F917": "Hug", "\U0001F92D": "Shush", "\U0001F928": "Raised Brow",
    "\U0001F611": "Expressionless", "\U0001F636": "No Mouth",
}

_EMOJI_EXTRA = {0x2764, 0x2665, 0x2666, 0x2660, 0x2663, 0x203C, 0x2049, 0x00A9, 0x00AE,
                0x2B50, 0x2B55, 0x2728, 0x2705, 0x274C, 0x2757, 0x2753, 0x2755}


def _is_emoji(ch: str) -> bool:
    o = ord(ch)
    if o in (0xFE0F, 0xFE0E, 0x200D, 0x20E3):
        return False
    return (0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF
            or 0x2B00 <= o <= 0x2BFF or 0x1F1E6 <= o <= 0x1F1FF
            or o in _EMOJI_EXTRA)


def _emojis(text: str):
    return [c for c in text if _is_emoji(c)]


def _parse_date(ds: str):
    """'12/10/25' / '12.10.2025' / '5-1-26' → (y, m, d) ya None. India = din pehle."""
    try:
        parts = re.split(r"[/.\-]", ds)
        if len(parts) != 3:
            return None
        a, b, y = (int(x) for x in parts)
        d, m = (a, b) if a > 12 or b <= 12 else (b, a)
        if y < 100:
            y += 2000
        if not (1 <= m <= 12 and 1 <= d <= 31 and 2000 <= y <= 2100):
            return None
        return (y, m, d)
    except Exception:                                            # noqa: BLE001
        return None


def _parse_hour(ts: str):
    """'9:41 pm' / '21:41' / '9:41:05 PM' → 0-23 ya None."""
    try:
        t = ts.strip().lower().replace(".", "").replace("\u202f", " ")
        pm = "pm" in t or "p m" in t
        am = "am" in t
        t = re.sub(r"[ap]\s?m", "", t).strip()
        hh = int(t.split(":")[0]) % 24
        if pm and hh < 12:
            hh += 12
        if am and hh == 12:
            hh = 0
        return hh
    except Exception:                                            # noqa: BLE001
        return None


def _iso(dt_tuple) -> str:
    return "%04d-%02d-%02d" % dt_tuple if dt_tuple else ""


def _pretty(iso: str) -> str:
    try:
        y, m, d = iso.split("-")
        return f"{int(d)} {_MONTHS[int(m) - 1]} {y}"
    except Exception:                                            # noqa: BLE001
        return iso or "-"


# ======================================================================
#  FILE → TEXT
# ======================================================================

def extract_text(data: bytes, filename: str = "") -> tuple:
    """(.txt ya .zip se chat text nikalo). Returns (text, error)."""
    fn = (filename or "").lower()
    if len(data or b"") > MAX_BYTES:
        return "", "File bahut badi hai (12 MB se kam bhejein) — media ke bina export karein."
    raw = data or b""
    if fn.endswith(".zip") or raw[:2] == b"PK":
        try:
            zf = zipfile.ZipFile(io.BytesIO(raw))
            cands = [n for n in zf.namelist()
                     if n.lower().endswith(".txt") and not n.startswith("__MACOSX")]
            if not cands:
                return "", "Is .zip me koi chat .txt nahi mili — 'Without media' wala export bhejein."
            cands.sort(key=lambda n: zf.getinfo(n).file_size, reverse=True)
            raw = zf.read(cands[0])
        except Exception:                                        # noqa: BLE001
            return "", "Ye .zip file kharab lagti hai — dobara export karke bhejein."
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc), ""
        except Exception:                                        # noqa: BLE001
            continue
    return raw.decode("utf-8", "ignore"), ""


# ======================================================================
#  PARSE
# ======================================================================

def _txt_in(v):
    """Kachra input (None/bool/dict) -> str. v78: `(x or '')` True/5 jaisa
    truthy non-str pass kar deta tha -> re.compile TypeError = tool crash."""
    if isinstance(v, str):
        return v
    if v is None:
        return ""
    try:
        return v.decode("utf-8", "ignore") if isinstance(v, (bytes, bytearray)) else str(v)
    except Exception:                                       # noqa: BLE001
        return ""


def parse_chat(text: str) -> dict:
    """Chat text → messages list + counters (system msgs alag)."""
    msgs = []                      # (user, raw_text, hour, iso_date)
    sys_n = 0
    cur = None                     # [user, text, hour, iso]
    lines = _txt_in(text).splitlines()
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
    for ln in lines:
        line = ln.lstrip(_LRM).rstrip()
        if not line:
            if cur:
                cur[1] += "\n"
            continue
        m = _RX_IOS.match(line) or _RX_ANDROID.match(line)
        if m:
            ds, ts, user, body = m.group(1), m.group(2), m.group(3).strip(), m.group(4)
            user = user.strip().strip(_LRM)
            dt = _parse_date(ds)
            hr = _parse_hour(ts)
            if cur:
                msgs.append(tuple(cur))
            cur = [user, body, hr, _iso(dt)]
            continue
        if re.search(r"end-to-end encrypted|Messages and calls are", line, re.I):
            if cur:
                msgs.append(tuple(cur))
                cur = None
            sys_n += 1
            continue
        if _RX_SYS.match(line):
            # system line — user ka message nahi
            if cur:
                msgs.append(tuple(cur))
                cur = None
            sys_n += 1
            continue
        # multi-line message ka agla hissa
        if cur:
            cur[1] += "\n" + line
        else:
            sys_n += 1
    if cur:
        msgs.append(tuple(cur))
    return {"msgs": msgs, "sys": sys_n}


def analyze_text(text: str) -> dict:
    """Poori fun-report (stats dict)."""
    try:
        p = parse_chat(text)
        msgs, sys_n = p["msgs"], p["sys"]
        if not msgs:
            return {"ok": False,
                    "error": "Is file me WhatsApp chat jaisa kuch nahi mila. "
                             "WhatsApp → chat → ⋮ → More → Export chat → "
                             "<b>Without media</b> karke aayi .txt file bhejein."}
        if len(msgs) < 3:
            return {"ok": False, "error": "Is chat me sirf 2-3 message hain — "
                                          "thodi badi chat export karein."}

        per_user = Counter()
        emoji_user = Counter()
        haha_user = Counter()
        ok_user = Counter()
        gm_user = Counter()
        night_user = Counter()
        emojis_all = Counter()
        words = Counter()
        hours = Counter()
        dates = Counter()
        media_n = 0
        longest = {"user": "", "chars": 0}

        for user, body, hr, iso in msgs:
            per_user[user] += 1
            if iso:
                dates[iso] += 1
            if hr is not None:
                hours[hr] += 1
                if 0 <= hr <= 4:
                    night_user[user] += 1
            media_n += len(_RX_MEDIA.findall(body))
            ems = _emojis(body)
            if ems:
                emoji_user[user] += len(ems)
                emojis_all.update(ems)
            hh = len(_RX_HAHA.findall(body))
            if hh:
                haha_user[user] += hh
            oo = len(_RX_OK.findall(body))
            if oo:
                ok_user[user] += oo
            gg = len(_RX_GM.findall(body))
            if gg:
                gm_user[user] += gg
            for w in _RX_WORD.findall(body.lower()):
                if w not in _STOP:
                    words[w] += 1
            ln_len = len(body)
            if ln_len > longest["chars"]:
                longest = {"user": user, "chars": ln_len,
                           "preview": body[:70].replace("\n", " ")}

        total = len(msgs)
        top = per_user.most_common(5)
        users = [{"name": u, "n": n, "share": round(n * 100.0 / total, 1)}
                 for u, n in top]
        d_list = sorted(dates)
        days = len(d_list) or 1
        busy_day = (dates.most_common(1)[0] if dates else ("", 0))
        busy_hr = (hours.most_common(1)[0] if hours else (None, 0))

        def _king(cnt):
            return cnt.most_common(1)[0] if cnt else ("", 0)

        st = {
            "ok": True,
            "total": total,
            "sys": sys_n,
            "users": users,
            "users_all": len(per_user),
            "d1": d_list[0] if d_list else "",
            "d2": d_list[-1] if d_list else "",
            "days": days,
            "per_day": round(total / days, 1),
            "busy_day": busy_day,
            "busy_hour": busy_hr,
            "words": words.most_common(10),
            "emojis": emojis_all.most_common(5),
            "emoji_king": _king(emoji_user),
            "haha_king": _king(haha_user),
            "ok_king": _king(ok_user),
            "gm_king": _king(gm_user),
            "night": {"n": sum(night_user.values()), "top": _king(night_user)},
            "longest": longest,
            "media": media_n,
        }
        return st
    except Exception as e:                                       # noqa: BLE001
        return {"ok": False, "error": f"Report banate waqt dikkat aayi: {str(e)[:120]}"}


def analyze_file(data: bytes, filename: str = "") -> dict:
    """File bytes → report. {'ok': True, 'stats': {...}} ya {'ok': False, 'error': ...}"""
    text, err = extract_text(data, filename)
    if err:
        return {"ok": False, "error": err}
    st = analyze_text(text)
    if not st.get("ok"):
        return st
    return {"ok": True, "stats": st}


# ======================================================================
#  IMAGE REPORT (WhatsApp dark theme — 1080 px wide)
# ======================================================================

def report_image(st: dict):
    """Stats → PNG bytes. Fail ho to None (bot text card bhej dega)."""
    try:
        from PIL import Image, ImageDraw
    except Exception:                                            # noqa: BLE001
        return None
    try:
        from modules.business_tools import _font_obj, _clean, has_devanagari
    except Exception:                                            # noqa: BLE001
        return None

    BG, PANEL, TRACK = (11, 20, 26), (17, 27, 33), (31, 44, 52)
    ACC, TXT, DIM, WHITE = (37, 211, 102), (233, 237, 239), (134, 150, 160), (255, 255, 255)
    W, M = 1080, 60

    def F(size, bold=False):
        try:
            return _font_obj("latin_b" if bold else "latin", size)
        except Exception:                                        # noqa: BLE001
            return None

    def Fn(name, size, bold=False):
        try:
            return _font_obj("deva", size) if has_devanagari(name) else F(size, bold)
        except Exception:                                        # noqa: BLE001
            return F(size, bold)

    def cl(s):
        try:
            return _clean(s)
        except Exception:                                        # noqa: BLE001
            return str(s or "")

    users = st.get("users") or []
    scratch = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    f_word = F(34)
    maxw_words = W - 2 * M - 60

    def wrap_words(pairs):
        lines, cur = [], ""
        for w, n in pairs[:10]:
            piece = f"{cl(w)} ({n})"
            cand = (cur + "  ·  " + piece) if cur else piece
            try:
                wid = scratch.textlength(cand, font=f_word)
            except Exception:                                    # noqa: BLE001
                wid = len(cand) * 18
            if wid <= maxw_words:
                cur = cand
            else:
                if cur:
                    lines.append(cur)
                cur = piece
        if cur:
            lines.append(cur)
        return lines or ["—"]

    wlines = wrap_words(st.get("words") or [])

    def _kv(name):
        u, n = name if isinstance(name, tuple) else (name, 0)
        return (u or "").strip(), int(n or 0)

    stat_rows = []
    u, n = _kv(st.get("emoji_king") or ("", 0))
    if n:
        stat_rows.append(("Emoji King", f"{u}  ({n} emoji)"))
    u, n = _kv(st.get("haha_king") or ("", 0))
    if n:
        stat_rows.append(("Hasi King (haha/lol)", f"{u}  ({n}x)"))
    u, n = _kv(st.get("ok_king") or ("", 0))
    if n:
        stat_rows.append(("OK / Hmm King", f"{u}  ({n}x)"))
    u, n = _kv(st.get("gm_king") or ("", 0))
    if n:
        stat_rows.append(("Good Morning Champ", f"{u}  ({n}x)"))
    nt = st.get("night") or {}
    u, n = _kv(nt.get("top") or ("", 0))
    if n:
        stat_rows.append(("Raat Ka Jagaadu (12-5 baje)",
                          f"{u}  ({nt.get('n', n)} msg)"))
    lg = st.get("longest") or {}
    if lg.get("chars"):
        stat_rows.append(("Sabse Lamba Message", f"{lg.get('user','')}  ({lg['chars']} chars)"))
    bd, bn = (st.get("busy_day") or ("", 0))
    if bn:
        stat_rows.append(("Sabse Busy Din", f"{_pretty(bd)}  ({bn} msg)"))
    bh, bhn = (st.get("busy_hour") or (None, 0))
    if bhn:
        hh = f"{bh:02d}:00"
        stat_rows.append(("Sabse Busy Ghanta", f"{hh}  ({bhn} msg)"))
    if st.get("media"):
        stat_rows.append(("Media Files Bheje", str(st["media"])))
    if st.get("sys"):
        stat_rows.append(("System Messages", f"{st['sys']} (skip kiye)"))
    ems = st.get("emojis") or []
    if ems:
        _named = []
        for e, c in ems[:3]:
            _nm = _EMOJI_NAMES.get(e) or _EMOJI_NAMES.get(e.rstrip("\ufe0f"))
            if _nm:
                _named.append(f"{_nm} x{c}")
        if _named:
            stat_rows.append(("Top 3 Emoji", "  ·  ".join(_named)))

    H = (300 + 250 + 120 + max(1, len(users)) * 116 + 130 + len(wlines) * 70 + 70
         + 130 + len(stat_rows) * 74 + 300)
    img = Image.new("RGB", (W, int(H)), BG)
    dr = ImageDraw.Draw(img)

    def rr(box, r, fill):
        try:
            dr.rounded_rectangle(box, radius=r, fill=fill)
        except Exception:                                        # noqa: BLE001
            dr.rectangle(box, fill=fill)

    def center(y, s, font, fill, cx=None):
        try:
            dr.text((cx if cx else W // 2, y), cl(s), font=font, fill=fill, anchor="mm")
        except Exception:                                        # noqa: BLE001
            pass

    # ---------- header ----------
    rr((M, 46, W - M, 262), 28, PANEL)
    dr.rectangle((M, 46, M + 12, 262), fill=ACC)
    center(112, "WHATSAPP CHAT X-RAY", F(62, True), WHITE)
    center(186, "Aapki chat ki poori report — 100% offline", F(31), DIM)
    center(230, "Kahin upload nahi hui — sirf aapke liye", F(26), ACC)

    # ---------- 3 big numbers ----------
    bw, gap = 300, 30
    bx = M + (W - 2 * M - (bw * 3 + gap * 2)) // 2
    for i, (lab, val) in enumerate([
            ("MESSAGES", f"{st.get('total', 0):,}"),
            ("DIN CHALI", f"{st.get('days', 0):,}"),
            ("PER DAY", f"{st.get('per_day', 0):g}")]):
        x = bx + i * (bw + gap)
        cx = x + bw // 2
        rr((x, 300, x + bw, 456), 24, PANEL)
        center(348, lab, F(26, True), DIM, cx=cx)
        center(408, val, F(58, True), ACC, cx=cx)

    y = 520

    # ---------- top chatters ----------
    dr.rectangle((M, y + 8, M + 10, y + 40), fill=ACC)
    dr.text((M + 26, y), "TOP CHATTERS", font=F(38, True), fill=WHITE)
    y += 74
    maxn = max([u2["n"] for u2 in users] or [1])
    for u2 in users:
        nm, nn, sh = u2["name"], u2["n"], u2.get("share", 0)
        try:
            dr.text((M + 26, y), cl(nm)[:24], font=Fn(nm, 42), fill=TXT)
        except Exception:                                        # noqa: BLE001
            pass
        try:
            dr.text((W - M - 26, y + 6), f"{nn} msg  ({sh}%)",
                    font=F(30, True), fill=ACC, anchor="ra")
        except Exception:                                        # noqa: BLE001
            pass
        rr((M + 26, y + 62, W - M - 26, y + 80), 9, TRACK)
        wfill = int((W - 2 * M - 52) * (nn / maxn)) if maxn else 0
        if wfill > 8:
            rr((M + 26, y + 62, M + 26 + wfill, y + 80), 9, ACC)
        y += 116

    # ---------- top words ----------
    y += 26
    dr.rectangle((M, y + 8, M + 10, y + 40), fill=ACC)
    dr.text((M + 26, y), "TOP WORDS (jo sabse zyada likhe)", font=F(36, True), fill=WHITE)
    y += 76
    for wl in wlines:
        dr.text((M + 26, y), wl, font=f_word, fill=TXT)
        y += 70

    # ---------- masala stats ----------
    y += 40
    dr.rectangle((M, y + 8, M + 10, y + 40), fill=ACC)
    dr.text((M + 26, y), "MAZEDAAR STATS", font=F(38, True), fill=WHITE)
    y += 78
    f_lab, f_val = F(31), F(31, True)
    for lab, val in stat_rows:
        dr.text((M + 26, y), cl(lab), font=f_lab, fill=DIM)
        try:
            dr.text((W - M - 26, y), cl(val)[:44], font=Fn(val, 31, True),
                    fill=WHITE, anchor="ra")
        except Exception:                                        # noqa: BLE001
            pass
        dr.line((M + 26, y + 52, W - M - 26, y + 52), fill=(24, 36, 44), width=2)
        y += 74

    # ---------- footer ----------
    y += 30
    center(y + 30, "@Supermannn_x", F(40, True), ACC)
    center(y + 92, "100% offline — koi data kahin nahi gaya", F(28), DIM)
    center(y + 138, "WHATSAPP CHAT X-RAY", F(24), (70, 88, 96))

    try:
        img = img.crop((0, 0, W, min(img.height, y + 186)))
    except Exception:                                            # noqa: BLE001
        pass
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()
