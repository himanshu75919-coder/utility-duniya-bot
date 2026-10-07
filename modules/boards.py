# -*- coding: utf-8 -*-
"""
🇮🇳 INDIA BOARD REGISTRY (v74.1)
================================
User ka order (8 Oct 2026): "Result Check tool me India ke SAARE official
state boards ke alag-alag service banao — CBSE, BSEB, UP, Telangana...
aur har board ka OFFICIAL LOGO dikhe taaki users apna board pehchaan sake.
Bilkul advanced, koi galti nahi, 100% trusted."

Har board ka alag entry:
  • naam (English + short) + state
  • OFFICIAL result portal ka link
  • exam types (10th/12th/other)
  • kya chahiye (roll no / roll code / DOB / captcha)
  • status:
      "live"   → bot OFFICIAL server se seedha result laata hai (abhi BSEB)
      "portal" → official portal ka link + poore steps (login/captcha wahan)
  • logo: assets/logos/norm_*.jpg (official, unki hi website se) — jahan
    nahi mila wahan bot khud ka COLOR BADGE (initials) banata hai.

⚠️ Emaandari (user ka "life ka sawaal hai"):
  Jis board ka result bot seedha NAHI laa sakta, wahan hum JHOOTHA result
  kabhi nahi dikhayenge — sirf official portal ka link + sahi steps denge.
"""

import os
import re

_LOGO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "assets", "logos")

# ─────────────────────────────────────────────────────── board registry
# status:  live = bot khud laata hai | portal = official portal link + steps
# v74.5: ab SIRF 2 boards (user ka order) — BSEB (LIVE ✅) + CBSE.
# Baaki saare boards hata diye. Naya board chahiye to yahan ek entry +
# ORDER me naam — picker/hub/tests sab automatic kaam karte hain.
BOARDS = {
    # ---------------------------------------------------------- BIHAR (LIVE)
"bseb": {
        "name": "Bihar School Examination Board",
        "short": "BSEB (Bihar Board)",
        "hi": "बिहार विद्यालय परीक्षा समिति",
        "state": "Bihar", "flag": "🟢",
        "portal": "https://result.biharboardonline.org/",
        "portal2": "https://biharboardonline.bihar.gov.in/",
        "exams": ["Matric (10th)", "Inter (12th)", "Inter Spl/Compartmental"],
        "need": ["Roll Code", "Roll Number"],
        "status": "live",
        "logo": "norm_bseb_live.jpg",
        "color": (139, 26, 26),
        "note": "LIVE ✅",
    },

    # ---------------------------------------------------------- CBSE (All India)
"cbse": {
        "name": "Central Board of Secondary Education",
        "short": "CBSE",
        "hi": "केंद्रीय माध्यमिक शिक्षा बोर्ड",
        "state": "All India", "flag": "🔵",
        "portal": "https://results.digilocker.gov.in/",
        "portal2": "https://cbse.gov.in/",
        "exams": ["Class 10", "Class 12"],
        "need": ["Mobile OTP", "Roll Number", "DOB"],
        "status": "portal",
        "logo": None, "color": (16, 88, 200),
        "note": "",
    },
}

# pagination order — sabse kaam ke board pehle
# ⚠️ RULE #1: portal/portal2 sirf INTERNAL reference hai — user ko kabhi nahi
# dikhaya jaata (na button me, na text me). User ko sirf bot ke andar ke cards.
ORDER = ["bseb", "cbse"]   # v74.5: sirf 2 boards (BSEB LIVE ✅ + CBSE)

PAGE_SIZE = 6


def total_pages() -> int:
    return (len(ORDER) + PAGE_SIZE - 1) // PAGE_SIZE


def page_boards(page: int):
    """(boards list, page, total_pages) — page 0-based."""
    try:
        page = max(0, min(int(page or 0), total_pages() - 1))
    except Exception:                                            # noqa: BLE001
        page = 0
    start = page * PAGE_SIZE
    keys = ORDER[start:start + PAGE_SIZE]
    return [(k, BOARDS[k]) for k in keys if k in BOARDS], page, total_pages()


def find(query: str):
    """Naam/short/state se board dhoondo (search)."""
    q = re.sub(r"[^a-z0-9]+", " ", str(query or "").lower()).strip()
    if not q:
        return []
    out = []
    for k in ORDER:
        b = BOARDS.get(k) or {}
        hay = " ".join([k, str(b.get("name", "")), str(b.get("short", "")),
                        str(b.get("state", "")), str(b.get("hi", ""))]).lower()
        hay = re.sub(r"[^a-z0-9\u0900-\u097F]+", " ", hay)
        if all(tok in hay for tok in q.split()):
            out.append((k, b))
    return out[:6]


# ─────────────────────────────────────────────────────── logos / badges
def logo_path(key: str):
    """Official logo ka path (mila ho to)."""
    b = BOARDS.get(str(key)) or {}
    lp = b.get("logo")
    if lp:
        full = os.path.join(_LOGO_DIR, lp)
        if os.path.isfile(full):
            return full
    return None


def badge_png(key: str):
    """Jo board ka official logo nahi mila — uske liye color badge banao
    (initials + state). Text hamesha circle ke andar fit hota hai. Fail par None."""
    b = BOARDS.get(str(key)) or {}
    try:
        from PIL import Image, ImageDraw
        from modules.business_tools import _font_obj
    except Exception:                                            # noqa: BLE001
        return None
    try:
        W = H = 512
        col = tuple(b.get("color") or (30, 64, 175))
        img = Image.new("RGB", (W, H), (255, 255, 255))
        dr = ImageDraw.Draw(img)
        dr.ellipse((18, 18, W - 18, H - 18), fill=col)
        dr.ellipse((46, 46, W - 46, H - 46), outline=(255, 255, 255), width=5)

        _short = str(b.get("short") or "")
        _acr = re.match(r"^([A-Z]{3,8})\b", _short.strip())           # JKBOSE / CBSE
        _par = re.search(r"\(([A-Za-z][A-Za-z&./ ]{1,14})\)", _short)  # (DGE) / (SEBA / AHSEC)
        if _acr:
            initials = _acr.group(1)
        elif _par:
            _tok = re.split(r"[^A-Za-z]+", _par.group(1))[0]
            initials = (_tok[:6] if len(_tok) >= 3 else _tok).upper()
        else:
            words = [w for w in re.split(r"[^A-Za-z]+", _short) if w]
            if len(words) >= 2:
                initials = "".join(w[0] for w in words[:4]).upper()
            elif words:
                initials = words[0][:4].upper()
            else:
                initials = "IND"
        if not initials:
            initials = "IND"
        inner = W - 150                                  # safe text area
        f_big = None
        for _sz in (150, 136, 122, 108, 96, 84, 72, 62):
            try:
                f = _font_obj("latin_b", _sz)
            except Exception:                                # noqa: BLE001
                f = None
            if not f:
                break
            try:
                _bb = dr.textbbox((0, 0), initials, font=f)
                if (_bb[2] - _bb[0]) <= inner:
                    f_big = f
                    break
            except Exception:                                # noqa: BLE001
                break
        if f_big:
            try:
                bb = dr.textbbox((0, 0), initials, font=f_big)
                dr.text(((W - (bb[2] - bb[0])) / 2 - bb[0],
                         (H - (bb[3] - bb[1])) / 2 - bb[1] - 46), initials,
                        font=f_big, fill=(255, 255, 255))
            except Exception:                                # noqa: BLE001
                pass
        st = str(b.get("state") or "").strip()[:22]
        if st:
            for _sz2 in (46, 40, 34, 30, 26, 22):
                try:
                    f2 = _font_obj("latin", _sz2)
                except Exception:                            # noqa: BLE001
                    f2 = None
                if not f2:
                    break
                try:
                    _bb2 = dr.textbbox((0, 0), st, font=f2)
                    if (_bb2[2] - _bb2[0]) <= inner:
                        bb2 = _bb2
                        dr.text(((W - (bb2[2] - bb2[0])) / 2 - bb2[0], H - 150),
                                st, font=f2, fill=(255, 255, 255))
                        break
                except Exception:                            # noqa: BLE001
                    break
        import io as _io
        out = _io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception:                                            # noqa: BLE001
        return None


def photo_bytes(key: str):
    """Board card ke liye photo bytes — official logo > badge. (None = text only)"""
    lp = logo_path(key)
    if lp:
        try:
            with open(lp, "rb") as f:
                return f.read()
        except Exception:                                        # noqa: BLE001
            pass
    return badge_png(key)
