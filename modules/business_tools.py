# -*- coding: utf-8 -*-
"""
business_tools.py — 💼 BUSINESS / EARNING STUDIO (v60)
======================================================
Ye tools seedha PAISA kamane wale hain. Har file aisi cheez banati hai jo
aam aadmi ko bahar ₹50-500 me milti hai:

  1. 🧾 INVOICE / BILL        — dukaan ka GST bill, estimate, quotation
  2. 💼 RESUME / CV           — job ke liye professional resume
  3. 💍 MARRIAGE BIO-DATA     — shaadi ka biodata (Bihar/UP me bahut demand)
  4. 🎓 CERTIFICATE           — achievement / bonafide / experience letter
  5. 🪪 ID CARD               — school/coaching/office ka ID card (10 copies)
  6. 📇 VISITING CARD         — dukaan/office ka card (100 pcs print sheet)
  7. 📄 APPLICATION LETTER    — leave, NOC, complaint, character certificate
  8. 💳 UPI PAYMENT POSTER    — dukaan ka "scan & pay" board
  9. 🏷️ PRICE LABEL SHEET     — dukaan ke rate tag (print + cut)
 10. 🧮 EMI / LOAN CARD       — EMI ka poora hisaab + month-wise schedule

----------------------------------------------------------------------
ANDAR KI TECHNICAL BAAT (kyun aisa banaya):
----------------------------------------------------------------------
Sab kuch Pillow se HIGH-RES (200 DPI, A4 = 1654x2339 px) image banta hai,
phir img2pdf se PDF. Aisa kyun, reportlab ke bajaye?

  • HINDI SUPPORT: Pillow me Raqm (HarfBuzz) hota hai — "हिन्दी", "क्या",
    "श्री" bilkul sahi chhapta hai (conjuncts + matras). reportlab Indic
    shaping nahi karta.
  • DESIGN CONTROL: border, colour, logo, layout — poori azaadi.

⚠️ EK KHAS PROBLEM jo solve karna pada:
  Noto Sans Devanagari font me **Latin letters (A-Z, a-z) hote hi nahi hain**
  (sirf Devanagari + digits + punctuation). Isliye agar poore document ke liye
  ek hi font use karo to ya Hindi toota dikhta hai ya English ▯▯▯ ban jata hai.

  ISKA HAL — `ScriptFont` engine (neeche): har text ko SCRIPT ke hisaab se
  tukdon me todta hai aur Devanagari tukda Devanagari font se, Latin tukda
  Latin font se likhta hai. Dono ek saath, ek hi line me, bilkul sahi.

Har function bytes leta hai, bytes deta hai, aur **kabhi exception nahi**
karta — error ho to {"ok": False, "error": "..."}.
"""
from __future__ import annotations

import io
import os
import re
from datetime import datetime
from typing import Any, Optional

__all__ = [
    "invoice_image", "resume_image", "biodata_image", "certificate_image",
    "idcard_image", "visiting_card_image", "letter_image", "upi_qr_image",
    "label_sheet_image", "emi_card_image", "to_pdf", "money", "ScriptFont",
    "has_devanagari", "load_font", "BRAND", "set_brand", "emi_breakup",
    "amount_words", "FONT_INFO",
]

# =====================================================================
#  FONT DISCOVERY
# =====================================================================
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_FONT_DIRS = [
    os.path.join(_ROOT, "assets", "fonts"),
    os.path.join(_HERE, "assets", "fonts"),
    "/usr/share/fonts/truetype/noto",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    "/System/Library/Fonts",
    "C:\\Windows\\Fonts",
]

_PATTERNS = {
    # Devanagari (Hindi) — Latin letters in nahi hote (isliye mixed engine)
    "deva": ["NotoSansDevanagari-Regular.ttf", "NotoSansDevanagari.ttf",
             "NotoSansDevanagari*", "NotoSerifDevanagari-Regular.ttf",
             "Noto*Devanagari*.ttf", "Noto*Devanagari*.otf", "Mangal.ttf",
             "Nirmala.ttf", "NirmalaUI.ttf"],
    # Latin regular
    "latin": ["DejaVuSans.ttf", "NotoSans-Regular.ttf", "FreeSans.ttf",
              "LiberationSans-Regular.ttf", "Arial.ttf", "Vera.ttf",
              "DejaVuSans*", "NotoSans-*.ttf"],
    # Latin bold
    "latin_b": ["DejaVuSans-Bold.ttf", "NotoSans-Bold.ttf", "FreeSansBold.ttf",
                "LiberationSans-Bold.ttf", "Arial_Bold.ttf", "VeraBd.ttf",
                "DejaVuSans-Bold*", "NotoSans-Bold*"],
}
_resolved: dict = {}
FONT_INFO: dict = {}


def _find_font(patterns) -> Optional[str]:
    import glob as _glob
    for pat in patterns:
        for d in _FONT_DIRS:
            if not d or not os.path.isdir(d):
                continue
            cand = os.path.join(d, pat)
            try:
                if os.path.isfile(cand):
                    return cand
                for h in _glob.glob(cand):
                    if os.path.isfile(h) and h.lower().endswith((".ttf", ".otf", ".ttc")):
                        return h
            except Exception:                                    # noqa: BLE001
                continue
    return None


def _resolve() -> None:
    if _resolved.get("done"):
        return
    _resolved["done"] = True
    for k in ("deva", "latin", "latin_b"):
        _resolved[k] = _find_font(_PATTERNS[k])
    # DejaVu etc. Latin font me Devanagari nahi hota — dono alag hone chahiye.
    # Agar Devanagari font hi na mile to Hindi ke liye Latin font hi use karenge
    # (toota dikhega par crash nahi hoga).
    if not _resolved["deva"]:
        _resolved["deva"] = _resolved["latin"]
    if not _resolved["latin"]:
        _resolved["latin"] = _resolved["deva"]
    if not _resolved["latin_b"]:
        _resolved["latin_b"] = _resolved["latin"]
    FONT_INFO.update({
        "deva": os.path.basename(_resolved["deva"] or "?"),
        "latin": os.path.basename(_resolved["latin"] or "?"),
        "bold": os.path.basename(_resolved["latin_b"] or "?"),
        "hindi_ok": bool(_resolved["deva"] and "deva" in
                         os.path.basename(_resolved["deva"] or "").lower()),
    })


FONT_REG: Optional[str] = None
FONT_BOLD: Optional[str] = None
_FONT_CACHE: dict = {}


def _font_obj(kind: str, size: int):
    """Pillow font object (cached) — kabhi crash nahi."""
    _resolve()
    key = (kind, max(6, int(size)))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    from PIL import ImageFont
    path = _resolved.get(kind) or _resolved.get("latin")
    obj = None
    for p in (path, _resolved.get("latin"), _resolved.get("deva")):
        if not p:
            continue
        try:
            obj = ImageFont.truetype(p, max(6, int(size)))
            break
        except Exception:                                        # noqa: BLE001
            continue
    if obj is None:
        try:
            obj = ImageFont.load_default()
        except Exception:                                        # noqa: BLE001
            obj = None
    _FONT_CACHE[key] = obj
    return obj


def load_font(size: int, bold: bool = False):
    """Purana API — Pillow font object (sirf Latin). Naye code me ScriptFont use karein."""
    return _font_obj("latin_b" if bold else "latin", size)


# =====================================================================
#  TEXT SANITIZER — emoji font me nahi hote -> ▯ aate hain, isliye hata do
# =====================================================================
_EMOJI_MAP = {
    "📞": "Ph:", "☎": "Ph:", "✉": "Email:", "📧": "Email:", "📍": "Add:",
    "💳": "Pay:", "🏦": "Bank:", "🕒": "Time:", "📅": "Date:", "👤": "",
    "🏠": "", "🔗": "", "✅": "", "⭐": "", "💰": "Rs.", "₹": "Rs.",
    "（": "(", "）": ")", "：": ":", "，": ",", "。": ".",
}
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U0000FE00-\U0000FE0F\U00002B00-\U00002BFF\U00002300-\U000023FF"
    "\U000024C2\U0000FE0F\U0000200D]"
)


def _clean(text) -> str:
    """Emoji + missing glyphs hata do (warna ▯▯▯ boxes aate hain)."""
    t = "" if text is None else str(text)
    for k, v in _EMOJI_MAP.items():
        if k in t:
            t = t.replace(k, v)
    try:
        t = _EMOJI_RE.sub("", t)
    except Exception:                                            # noqa: BLE001
        pass
    return t


def has_devanagari(text) -> bool:
    try:
        for ch in str(text or ""):
            if "\u0900" <= ch <= "\u097F":
                return True
    except Exception:                                            # noqa: BLE001
        pass
    return False


# =====================================================================
#  🧠 ScriptFont — Devanagari + Latin EK HI line me (yahi asli jugaad hai)
# =====================================================================
class ScriptFont:
    """Ek size ka "font", jo Hindi aur English dono likh sakta hai.

    Andar ye text ko script-wise tukdon me todta hai:
        "बिल / Bill"  ->  [("बिल ", deva), ("/ Bill", latin)]
    aur har tukda apne font se draw karta hai, x ko aage badhata jaata hai.

    Isi wajah se mixed Hindi-English documents PERFECT aate hain.
    """

    __slots__ = ("size", "bold", "_l", "_d")

    def __init__(self, size: int, bold: bool = False):
        self.size = max(6, int(size))
        self.bold = bool(bold)
        self._l = _font_obj("latin_b" if bold else "latin", self.size)
        self._d = _font_obj("deva", self.size)

    # ---------------------------------------------------------------- runs
    @staticmethod
    def runs(text) -> list:
        """Text ko script-wise tukdon me baanto: [("नाम ", deva), ("Name", latin)].

        ⚠️ Yahan ek asli bug tha aur isko theek karna zaroori hai:
        pehle hum ne ASCII ke saare characters ko "neutral" maan liya tha —
        matlab "नाम / Name" me "Name" bhi Devanagari tukde me chala jata tha,
        aur Noto Sans Devanagari me Latin letters NA hone ki wajah se wahan
        ▯▯▯▯ (khali dabbe) chhapte the.

        AB sahi tarika:
          • Devanagari letters (U+0900-U+097F) -> deva run
          • Latin letters (A-Z, a-z, à-ÿ, Greek etc.) -> latin run
          • digits / punctuation / space -> NEUTRAL (jo chal raha ho usme chalo,
            aur script badalte waqt aage wale run me chale jao taaki spacing sahi rahe)
        """
        t = str(text or "")
        out: list = []
        cur = ""
        cur_kind: Optional[str] = None          # "d" = deva, "l" = latin

        def _kind(ch: str) -> Optional[str]:
            o = ord(ch)
            if 0x0900 <= o <= 0x097F:           # Devanagari block
                return "d"
            if 0x0980 <= o <= 0x0DFF:           # baaki Indic (Bengali..Sinhala)
                return "d"
            if ch.isalpha():
                return "l"
            # Bullet / dash / middle-dot — ye DejaVu me hote hain, Noto
            # Devanagari me nahi. Agar inhe "neutral" chhod do to ye Hindi ke
            # saath Devanagari font me chale jaate hain aur ▯ (khali dabba)
            # ban jaate hain. Isliye inhe Latin maan lo — dikhne me sahi.
            if ch in "·•‣∙‒–—―′″«»":
                return "l"
            if o >= 0x2000 and ch not in "’‘“”…":     # symbols/emoji etc.
                return "l"
            return None                          # digit/punct/space -> neutral

        for ch in t:
            k = _kind(ch)
            if k is None:
                cur += ch                        # neutral — chalti script me
                continue
            if cur_kind is None:
                cur_kind = k
                cur += ch
            elif k == cur_kind:
                cur += ch
            else:
                # script badli — trailing neutrals naye run me bhej do
                stripped = cur.rstrip()
                tail = cur[len(stripped):]
                if stripped:
                    out.append((stripped, cur_kind == "d"))
                cur = tail + ch
                cur_kind = k
        if cur:
            out.append((cur, cur_kind == "d"))
        return out

    def _f(self, is_deva: bool):
        return self._d if is_deva else self._l

    # --------------------------------------------------------------- width
    def width(self, text) -> float:
        w = 0.0
        for seg, is_deva in self.runs(_clean(text)):
            f = self._f(is_deva)
            if f is None:
                w += len(seg) * self.size * 0.55
                continue
            try:
                w += f.getlength(seg)
            except Exception:                                    # noqa: BLE001
                try:
                    w += f.getsize(seg)[0]
                except Exception:                                # noqa: BLE001
                    w += len(seg) * self.size * 0.55
        return w

    # ---------------------------------------------------------------- draw
    def draw(self, dr, xy, text, fill=(0, 0, 0), anchor_v: str = "la") -> float:
        """Text draw karo (script-wise). Return: kitni width use hui."""
        x, y = xy
        total = 0.0
        for seg, is_deva in self.runs(_clean(text)):
            f = self._f(is_deva)
            if f is None:
                continue
            try:
                dr.text((x, y), seg, font=f, fill=fill)
            except Exception:                                    # noqa: BLE001
                try:
                    dr.text((x, y), seg, font=f, fill=fill, anchor=anchor_v)
                except Exception:                                # noqa: BLE001
                    continue
            try:
                adv = f.getlength(seg)
            except Exception:                                    # noqa: BLE001
                adv = len(seg) * self.size * 0.55
            x += adv
            total += adv
        return total

    def draw_center(self, dr, box, text, fill=(0, 0, 0), y: float = 0) -> None:
        """box = (x1, x2) — text ko beech me likho."""
        w = self.width(text)
        self.draw(dr, ((box[0] + box[1] - w) / 2.0, y), text, fill)

    def draw_right(self, dr, x_right, text, fill=(0, 0, 0), y: float = 0) -> None:
        w = self.width(text)
        self.draw(dr, (x_right - w, y), text, fill)

    # ---------------------------------------------------------------- wrap
    def wrap(self, text, max_w: float, max_lines: int = 99) -> list:
        """Word-boundary wrap — script-aware width ke saath."""
        words = _clean(text).split()
        lines: list = []
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if self.width(trial) <= max_w or not cur:
                if self.width(trial) > max_w and not cur:
                    # ek hi word bahut lamba — character se todo
                    piece = ""
                    for ch in w:
                        if self.width(piece + ch) <= max_w:
                            piece += ch
                        else:
                            lines.append(piece)
                            piece = ch
                            if len(lines) >= max_lines:
                                break
                    cur = piece
                    continue
                cur = trial
            else:
                lines.append(cur)
                cur = w
            if len(lines) >= max_lines:
                break
        if cur and len(lines) < max_lines:
            lines.append(cur)
        return lines or [""]

    def paragraph(self, dr, xy, text, max_w, fill, line_gap: int = 38,
                  max_lines: int = 40, prefix: str = "") -> float:
        """Poora paragraph likho (wrap karke). Return: neeche ki y position."""
        x, y = xy
        for i, ln in enumerate(self.wrap(text, max_w - (0 if not prefix else 0),
                                        max_lines)):
            self.draw(dr, (x + (0 if i == 0 else 0), y),
                      (prefix + ln) if i == 0 and prefix else ("" if i == 0 else "") + ln,
                      fill)
            y += line_gap
        return y


# =====================================================================
#  HELPERS
# =====================================================================
def _blank(w: int, h: int, bg=(255, 255, 255)):
    from PIL import Image
    return Image.new("RGB", (int(w), int(h)), bg)


def _save_png(img) -> bytes:
    bio = io.BytesIO()
    img.save(bio, format="PNG", optimize=True)
    return bio.getvalue()


def A4(dpi: int = 200):
    """A4 ka pixel size (200 DPI = print quality)."""
    return int(8.27 * dpi), int(11.69 * dpi)


def to_pdf(png_list) -> Optional[bytes]:
    """PNG(s) -> PDF. img2pdf, warna Pillow. Kabhi crash nahi."""
    if isinstance(png_list, (bytes, bytearray)):
        png_list = [bytes(png_list)]
    items = [bytes(x) for x in (png_list or []) if x]
    if not items:
        return None
    try:
        import img2pdf
        return img2pdf.convert(items)
    except Exception:                                            # noqa: BLE001
        pass
    try:
        from PIL import Image
        imgs = [Image.open(io.BytesIO(b)).convert("RGB") for b in items]
        bio = io.BytesIO()
        imgs[0].save(bio, format="PDF", save_all=True, append_images=imgs[1:],
                     resolution=200.0)
        return bio.getvalue()
    except Exception:                                            # noqa: BLE001
        return None


def _err(where: str, e: BaseException) -> dict:
    return {"ok": False, "error": f"{where}: {type(e).__name__}: {str(e)[:160]}"}


def _hex(v, default=(16, 88, 200)):
    try:
        h = str(v or "").strip().lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) == 6:
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:                                            # noqa: BLE001
        pass
    return default


def _mx(a, b):
    return a if a > b else b


def money(v) -> str:
    """Indian format: 1234567 -> 12,34,567"""
    try:
        n = float(str(v).replace(",", "").replace("₹", "").replace("Rs.", "").strip() or 0)
    except Exception:                                            # noqa: BLE001
        return str(v)
    neg = n < 0
    n = abs(n)
    whole = int(n)
    frac = int(round((n - whole) * 100))
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + s + (f".{frac:02d}" if frac else "")


def _num(v, default=0.0) -> float:
    try:
        return float(str(v).replace(",", "").replace("₹", "").strip() or default)
    except Exception:                                            # noqa: BLE001
        return float(default)


_ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
         "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
         "Seventeen", "Eighteen", "Nineteen"]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty",
         "Ninety"]


def amount_words(n) -> str:
    """Rupees in words (Indian system: lakh/crore) — bill me likhne ke liye."""
    try:
        num = int(round(float(str(n).replace(",", "") or 0)))
    except Exception:                                            # noqa: BLE001
        return ""
    if num == 0:
        return "Zero Rupees Only"

    def two(x):
        if x < 20:
            return _ONES[x]
        return (_TENS[x // 10] + ((" " + _ONES[x % 10]) if x % 10 else "")).strip()

    def three(x):
        if x >= 100:
            return (_ONES[x // 100] + " Hundred" +
                    ((" " + two(x % 100)) if x % 100 else "")).strip()
        return two(x)

    parts = []
    crore, num = divmod(num, 10000000)
    lakh, num = divmod(num, 100000)
    thousand, num = divmod(num, 1000)
    if crore:
        parts.append(three(crore) + " Crore")
    if lakh:
        parts.append(three(lakh) + " Lakh")
    if thousand:
        parts.append(three(thousand) + " Thousand")
    if num:
        parts.append(three(num))
    return " ".join(parts).strip() + " Rupees Only"


def _make_qr_png(data: str, box: int = 360) -> Optional[bytes]:
    try:
        import qrcode
        q = qrcode.QRCode(version=None, box_size=10, border=2,
                          error_correction=qrcode.constants.ERROR_CORRECT_M)
        q.add_data(str(data))
        q.make(fit=True)
        im = q.make_image(fill_color="black", back_color="white").convert("RGB")
        return _save_png(im.resize((box, box)))
    except Exception:                                            # noqa: BLE001
        return None


def _paste_photo(img, photo_bytes, box, radius: int = 0, border=None, bw: int = 4):
    """Photo ko box (x, y, size) par chipkao — crop-to-square, corner round."""
    try:
        from PIL import Image, ImageDraw
        ph = Image.open(io.BytesIO(bytes(photo_bytes))).convert("RGB")
        s = min(ph.size)
        ph = ph.crop(((ph.width - s) // 2, (ph.height - s) // 2,
                      (ph.width + s) // 2, (ph.height + s) // 2)).resize((box[2], box[2]))
        if radius:
            m = Image.new("L", ph.size, 0)
            ImageDraw.Draw(m).rounded_rectangle([0, 0, ph.size[0] - 1, ph.size[1] - 1],
                                                radius=radius, fill=255)
            base = Image.new("RGB", ph.size, (255, 255, 255))
            base.paste(ph, (0, 0), m)
            ph = base
        img.paste(ph, (box[0], box[1]))
        if border:
            # v63 FIX: pehle yahan box[3] likha tha — wo hota hi nahi (box = x,y,size).
            # Is liye border kabhi lagta hi nahi tha (chup-chaap fail ho jata tha).
            ImageDraw.Draw(img).rectangle(
                [box[0] - bw // 2, box[1] - bw // 2,
                 box[0] + box[2] + bw // 2, box[1] + box[2] + bw // 2],
                outline=border, width=bw)
        return True
    except Exception:                                            # noqa: BLE001
        return False


def _paste_logo(img, logo_bytes, box, pad: int = 8, bg=(255, 255, 255)):
    """v63: Logo ko box (x, y, size) ke ANDAR fit karo — kata nahi, poora dikhe.

    Photo ke liye `_paste_photo` (square crop) hota hai, par logo chaura-patra
    hota hai — usko kaatna galat lagta hai. Is liye ye alag helper hai.
    """
    try:
        from PIL import Image
        lg = Image.open(io.BytesIO(bytes(logo_bytes))).convert("RGB")
        inner = max(8, int(box[2]) - 2 * pad)
        r = min(inner / max(1, lg.width), inner / max(1, lg.height))
        lg = lg.resize((max(1, int(lg.width * r)), max(1, int(lg.height * r))))
        canvas = Image.new("RGB", (int(box[2]), int(box[2])), bg)
        canvas.paste(lg, ((int(box[2]) - lg.width) // 2, (int(box[2]) - lg.height) // 2))
        img.paste(canvas, (int(box[0]), int(box[1])))
        return True
    except Exception:                                            # noqa: BLE001
        return False


# ---- brand footer (bot.py set kar sakta hai)
BRAND = {"txt": "Utility Duniya Bot"}


def set_brand(text: str) -> None:
    try:
        BRAND["txt"] = str(text or "").strip() or "Utility Duniya Bot"
    except Exception:                                            # noqa: BLE001
        pass


def _brand() -> str:
    return str(BRAND.get("txt") or "Utility Duniya Bot")


def _today() -> str:
    return datetime.now().strftime("%d-%m-%Y")


# Module load hote hi fonts dhoondh lo — isse FONT_INFO hamesha bhara rehta hai
# aur pehla document banate waqt koi delay nahi hota.
try:
    _resolve()
except Exception:                                                # noqa: BLE001
    pass


# =====================================================================
#  PALETTE
# =====================================================================
INK = (17, 24, 39)
MUTED = (95, 104, 120)
FAINT = (150, 158, 172)
LINE = (208, 214, 226)
BAND = (243, 246, 252)
WHITE = (255, 255, 255)


# =====================================================================
#  1. 🧾 INVOICE / BILL / ESTIMATE
# =====================================================================
def invoice_image(d: dict) -> dict:
    """GST-style invoice / bill / estimate / quotation (A4, 200 DPI).

    d = { shop, tagline, address, phone, email, gstin, upi, upi_name,
          doc_type:"TAX INVOICE", number, date, mode, buyer, buyer_phone,
          buyer_addr, buyer_gst, items:[{name,qty,rate,gst}], discount,
          advance, note, terms, logo:bytes }
    """
    try:
        from PIL import ImageDraw
        W, H = A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (16, 88, 200))

        F = ScriptFont
        f_h1, f_h2 = F(62, True), F(34, True)
        f_b, f_s, f_xs = F(30), F(26), F(23)
        M = 90

        y = M
        dr.rectangle([0, 0, W, 14], fill=acc)
        logo = d.get("logo")
        if logo and isinstance(logo, (bytes, bytearray)):
            try:
                from PIL import Image
                lg = Image.open(io.BytesIO(bytes(logo))).convert("RGB")
                s = min(lg.size)
                lg = lg.crop(((lg.width - s) // 2, (lg.height - s) // 2,
                              (lg.width + s) // 2, (lg.height + s) // 2)).resize((130, 130))
                img.paste(lg, (W - M - 130, y))
            except Exception:                                    # noqa: BLE001
                pass
        shop_w = W - 2 * M - (160 if logo else 0)
        for i, ln in enumerate(f_h1.wrap(str(d.get("shop") or d.get("name") or "MY SHOP"),
                                         shop_w, 2)):
            f_h1.draw(dr, (M, y + i * 72), ln, INK)
        y += 72 * max(1, len(f_h1.wrap(str(d.get("shop") or "MY SHOP"), shop_w, 2))) + 6
        for key, lbl, fnt, col in (("tagline", "", f_s, MUTED),
                                   ("address", "", f_xs, MUTED),
                                   ("phone", "Ph: ", f_xs, MUTED),
                                   ("email", "Email: ", f_xs, MUTED),
                                   ("gstin", "GSTIN: ", f_xs, MUTED)):
            val = str(d.get(key) or "").strip()
            if not val:
                continue
            for ln in f_xs.wrap(lbl + val, shop_w, 2):
                f_xs.draw(dr, (M, y), ln, col)
                y += 32
            if key == "tagline":
                y += 6

        y += 12
        dr.line([M, y, W - M, y], fill=LINE, width=3)
        y += 28

        dtype = _clean(str(d.get("doc_type") or "INVOICE")).upper()[:26]
        dr.rectangle([M, y, W - M, y + 66], fill=BAND, outline=LINE, width=2)
        f_h2.draw_center(dr, (M, W - M), dtype, acc, y + 15)
        y += 66 + 26

        box_h = 252
        mid = W // 2 + 70
        dr.rectangle([M, y, mid, y + box_h], outline=LINE, width=2)
        f_s.draw(dr, (M + 20, y + 14), "BILL TO", acc)
        by = y + 62
        first = True
        for key in ("buyer", "buyer_phone", "buyer_addr", "buyer_gst"):
            val = str(d.get(key) or "").strip()
            if not val:
                continue
            for ln in f_b.wrap(val, mid - M - 40, 3):
                if by > y + box_h - 34:
                    break
                f_b.draw(dr, (M + 20, by), ln, INK)
                by += 38
            first = False
        if first:
            f_b.draw(dr, (M + 20, by), "—", FAINT)

        mx = mid + 20
        dr.rectangle([mid, y, W - M, y + box_h], outline=LINE, width=2)
        f_s.draw(dr, (mx, y + 14), "DETAILS", acc)
        my = y + 62
        for lbl, val in (("No.", d.get("number")), ("Date", d.get("date") or _today()),
                         ("Time", d.get("time")), ("Mode", d.get("mode") or "Cash"),
                         ("Due", d.get("due"))):
            val = str(val or "").strip()
            if not val:
                continue
            f_xs.draw(dr, (mx, my), f"{lbl}:", MUTED)
            f_b.draw(dr, (mx + 130, my), val[:26], INK)
            my += 40
        y += box_h + 28

        c0, c1, c2, c3 = M, M + 76, M + 726, M + 966
        dr.rectangle([M, y, W - M, y + 56], fill=acc)
        for cx, h in ((c0, "#"), (c1, "ITEM / DESCRIPTION"), (c2, "QTY"),
                      (c3, "RATE")):
            f_s.draw(dr, (cx + 14, y + 14), h, WHITE)
        f_s.draw_right(dr, W - M - 20, "AMOUNT", WHITE, y + 14)
        y += 56

        items = d.get("items") if isinstance(d.get("items"), list) else []
        subtotal = tax_total = 0.0
        shown = 0
        for i, it in enumerate(items[:26]):
            if not isinstance(it, dict):
                continue
            qty = _num(it.get("qty"), 1.0)
            rate = _num(it.get("rate"))
            gstp = _num(it.get("gst"))
            amt = qty * rate
            subtotal += amt
            tax_total += amt * gstp / 100.0
            lines = f_b.wrap(str(it.get("name") or "-"), c2 - c1 - 30, 2)
            rh = max(62, 22 + 34 * len(lines))
            if y + rh > H - 700:
                break
            if i % 2 == 0:
                dr.rectangle([M, y, W - M, y + rh], fill=(250, 251, 253))
            f_s.draw(dr, (c0 + 16, y + 16), str(i + 1), MUTED)
            ly = y + 12 if len(lines) == 1 else y + 8
            for ln in lines:
                f_b.draw(dr, (c1 + 14, ly), ln, INK)
                ly += 34
            f_s.draw(dr, (c2 + 14, y + 16), f"{qty:g}", INK)
            if gstp:
                f_xs.draw(dr, (c2 + 14, y + 38), f"+{gstp:g}%", FAINT)
            f_s.draw(dr, (c3 + 14, y + 16), money(rate), INK)
            f_b.draw_right(dr, W - M - 20, money(amt), INK, y + 14)
            y += rh
            shown += 1
        if not shown:
            f_b.draw(dr, (c1 + 14, y + 18), "(koi item nahi)", FAINT)
            y += 62
        if len(items) > shown:
            f_xs.draw(dr, (c1 + 14, y + 16),
                      f"... aur {len(items) - shown} item (agli page)", MUTED)
            y += 46
        dr.line([M, y, W - M, y], fill=LINE, width=3)

        y += 38
        disc = _num(d.get("discount"))
        adv = _num(d.get("advance"))
        gst_total = _num(d.get("gst_total"), tax_total)
        grand = subtotal + gst_total - disc
        balance = grand - adv
        tx = W - M - 580
        rows = [("Sub Total", money(subtotal))]
        if gst_total:
            rows.append(("GST / Tax", money(gst_total)))
        if disc:
            rows.append(("Discount", "-" + money(disc)))
        rows.append(("GRAND TOTAL", "Rs. " + money(grand)))
        if adv:
            rows.append(("Advance Paid", "-" + money(adv)))
            rows.append(("BALANCE DUE", "Rs. " + money(balance)))
        for lbl, val in rows:
            big = lbl in ("GRAND TOTAL", "BALANCE DUE")
            rh = 62 if big else 46
            if big:
                dr.rectangle([tx, y, W - M, y + rh], fill=acc)
                f_b.draw(dr, (tx + 18, y + 15), _clean(lbl), WHITE)
                f_h2.draw_right(dr, W - M - 18, val, WHITE, y + 13)
            else:
                f_b.draw(dr, (tx + 18, y + 8), _clean(lbl), INK)
                vw = f_b.width(val)
                f_b.draw(dr, (W - M - 18 - vw, y + 8), val, INK)
            y += rh
        y += 16
        words = amount_words(grand)
        f_xs.draw(dr, (tx, y), f"In words: {words[:70]}", MUTED)
        y += 54

        upi = str(d.get("upi") or "").strip()
        if upi and y < H - 620:
            try:
                from modules.general_tools import build_upi_link
                link = build_upi_link(upi, str(d.get("upi_name") or d.get("shop") or "Shop"),
                                      grand if grand else None,
                                      note=f"Bill {d.get('number') or ''}".strip())
            except Exception:                                    # noqa: BLE001
                link = f"upi://pay?pa={upi}&am={grand:.2f}&cu=INR"
            qp = _make_qr_png(link, 330)
            if qp:
                from PIL import Image
                qr = Image.open(io.BytesIO(qp)).convert("RGB").resize((330, 330))
                img.paste(qr, (M, y))
                f_h2.draw(dr, (M + 360, y + 24), "SCAN & PAY", acc)
                f_b.draw(dr, (M + 360, y + 92), f"UPI: {upi[:34]}", INK)
                f_b.draw(dr, (M + 360, y + 138), f"Amount: Rs. {money(grand)}", INK)
                f_xs.draw(dr, (M + 360, y + 188), "GPay · PhonePe · Paytm · BHIM",
                          MUTED)
                y += 360

        fy = H - 300
        dr.line([M, fy, W - M, fy], fill=LINE, width=2)
        fy += 16
        for label, key in (("Note", "note"), ("Terms", "terms")):
            val = str(d.get(key) or "").strip()
            if not val:
                continue
            for ln in f_xs.wrap(f"{label}: {val}", W - 2 * M - 420, 3):
                f_xs.draw(dr, (M, fy), ln, MUTED)
                fy += 32
        sig = str(d.get("sign_by") or "Authorised Signatory")
        dr.line([W - M - 340, H - 150, W - M, H - 150], fill=INK, width=2)
        f_s.draw_center(dr, (W - M - 340, W - M), sig, MUTED, H - 140)
        f_xs.draw(dr, (M, H - 92), f"Computer generated · {_brand()}", FAINT)
        return {"ok": True, "png": _save_png(img), "amount": grand,
                "size": img.size, "items": shown}
    except Exception as e:                                       # noqa: BLE001
        return _err("invoice", e)


# =====================================================================
#  2. 💼 RESUME / CV
# =====================================================================
def resume_image(d: dict) -> dict:
    """Professional resume — A4, print-ready, photo optional."""
    try:
        from PIL import ImageDraw
        W, H = A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (16, 88, 200))
        F = ScriptFont
        f_nm, f_role = F(68, True), F(34)
        f_sec, f_b, f_s = F(36, True), F(29), F(26)
        M = 95
        CW = W - 2 * M

        has_photo = bool(d.get("photo"))
        dr.rectangle([0, 0, W, 400], fill=acc)
        if has_photo:
            _paste_photo(img, d.get("photo"), (W - M - 250, 75, 250), radius=16)
        tw_max = CW - (300 if has_photo else 0)
        ny = 72
        for ln in f_nm.wrap(str(d.get("name") or "YOUR NAME"), tw_max, 2):
            f_nm.draw(dr, (M, ny), ln, WHITE)
            ny += 78
        f_role.draw(dr, (M, ny + 6), str(d.get("role") or "")[:60], (222, 233, 255))
        cy = ny + 78
        cx = M
        for val in (d.get("phone"), d.get("email"), d.get("city") or d.get("address")):
            val = str(val or "").strip()
            if not val:
                continue
            label = val[:40]
            wl = f_s.width(label)
            if cx + wl > M + tw_max:
                cx = M
                cy += 40
            f_s.draw(dr, (cx, cy), label, (232, 240, 255))
            cx += wl + 44
        y = 440

        def section(title: str, y: int) -> int:
            f_sec.draw(dr, (M, y), _clean(title).upper(), acc)
            y += 52
            dr.line([M, y, M + CW, y], fill=LINE, width=3)
            return y + 22

        def para(title, text, y, gap=42, prefix="", maxl=6):
            text = str(text or "").strip()
            if not text:
                return y
            y = section(title, y)
            for ln in f_b.wrap(text, CW - 30, maxl):
                f_b.draw(dr, (M, y), (prefix + ln) if prefix else ln, INK)
                y += gap
            return y + 24

        y = para("Career Objective", d.get("objective"), y)

        if d.get("education"):
            y = section("Education", y)
            for e in (d.get("education") or [])[:6]:
                if not isinstance(e, dict):
                    continue
                f_b_bold = ScriptFont(30, True)
                f_b_bold.draw(dr, (M, y), str(e.get("course") or "")[:60], INK)
                yr = str(e.get("year") or "")
                if yr:
                    f_s.draw_right(dr, W - M, yr, acc, y)
                y += 42
                sub = " · ".join(x for x in (str(e.get("institute") or "")[:70],
                                             str(e.get("percent") or "")) if x)
                if sub:
                    f_s.draw(dr, (M + 8, y), sub, MUTED)
                    y += 38
                y += 16
            y += 16

        if d.get("experience"):
            y = section("Experience", y)
            for e in (d.get("experience") or [])[:6]:
                if not isinstance(e, dict):
                    continue
                ScriptFont(30, True).draw(dr, (M, y), str(e.get("role") or "")[:60], INK)
                yr = str(e.get("year") or "")
                if yr:
                    f_s.draw_right(dr, W - M, yr, acc, y)
                y += 42
                comp = str(e.get("company") or "")[:70]
                if comp:
                    f_s.draw(dr, (M + 8, y), comp, MUTED)
                    y += 38
                det = str(e.get("detail") or "").strip()
                if det:
                    for ln in f_s.wrap(det, CW - 40, 3):
                        f_s.draw(dr, (M + 8, y), "• " + ln, INK)
                        y += 36
                y += 18
            y += 16

        if d.get("projects"):
            y = section("Projects", y)
            for p in (d.get("projects") or [])[:5]:
                if not isinstance(p, dict):
                    continue
                ScriptFont(30, True).draw(dr, (M, y), str(p.get("name") or "")[:60], INK)
                y += 42
                for ln in f_s.wrap(str(p.get("detail") or ""), CW - 40, 3):
                    f_s.draw(dr, (M + 8, y), ln, MUTED)
                    y += 36
                y += 16

        skills = str(d.get("skills") or "").strip()
        langs = str(d.get("languages") or "").strip()
        if skills or langs:
            y = section("Skills & Languages", y)
            for label, val in (("Skills", skills), ("Languages", langs)):
                if not val:
                    continue
                lw = ScriptFont(29, True).width(label + ":")
                ScriptFont(29, True).draw(dr, (M, y), label + ":", INK)
                x = M + lw + 20
                for chunk in [c.strip() for c in val.split(",") if c.strip()][:14]:
                    cw = f_s.width(chunk) + 36
                    if x + cw > W - M:
                        x = M + lw + 20
                        y += 50
                    dr.rectangle([x, y - 4, x + cw, y + 42], fill=(238, 243, 252),
                                 outline=(203, 217, 240))
                    f_s.draw(dr, (x + 18, y + 4), chunk[:24], acc)
                    x += cw + 12
                y += 62

        y = para("Achievements", d.get("achievements"), y, prefix="• ")
        y = para("Hobbies", d.get("hobbies"), y)

        dr.line([M, H - 210, W - M, H - 210], fill=LINE, width=2)
        f_s.draw(dr, (M, H - 192),
                 "I hereby declare that the above information is true to the best of my knowledge.",
                 MUTED)
        dr.line([W - M - 330, H - 122, W - M, H - 122], fill=INK, width=2)
        f_b.draw(dr, (W - M - 330, H - 112), str(d.get("name") or "")[:40], INK)
        f_xs = ScriptFont(22)
        f_xs.draw(dr, (M, H - 78), f"Made with {_brand()}", FAINT)
        return {"ok": True, "png": _save_png(img), "size": img.size}
    except Exception as e:                                       # noqa: BLE001
        return _err("resume", e)


# =====================================================================
#  3. 💍 MARRIAGE BIO-DATA
# =====================================================================
def biodata_image(d: dict) -> dict:
    """Shaadi ka biodata — decorative border, photo, do column details."""
    try:
        from PIL import ImageDraw
        W, H = A4()
        img = _blank(W, H, (255, 253, 247))
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (150, 106, 20))
        ink = (42, 33, 20)
        F = ScriptFont
        f_t, f_sub = F(70, True), F(30)
        f_lbl, f_val = F(28, True), F(30)
        f_sec = F(36, True)
        M = 80

        dr.rectangle([0, 0, W - 1, H - 1], outline=acc, width=18)
        dr.rectangle([34, 34, W - 35, H - 35], outline=acc, width=4)
        dr.rectangle([0, 0, W, 12], fill=acc)
        dr.rectangle([0, H - 12, W, H], fill=acc)

        y = 92
        f_t.draw_center(dr, (M, W - M), str(d.get("title") or "विवाह परिचय")[:44], acc, y)
        y += 94
        f_sub.draw_center(dr, (M, W - M), str(d.get("subtitle") or "MARRIAGE BIODATA")[:48],
                          (150, 132, 100), y)
        y += 58
        dr.line([M + 60, y, W - M - 60, y], fill=acc, width=3)
        y += 34

        # photo right side
        psize = 330
        px = W - M - psize
        if d.get("photo"):
            _paste_photo(img, d.get("photo"), (px, y, psize), border=acc, bw=5)
        else:
            dr.rectangle([px, y, px + psize, y + psize], outline=acc, width=4)
            f_sub.draw_center(dr, (px, px + psize), "फोटो", (170, 155, 130), y + 145)

        left_w = px - M - 40
        ry = y
        for lbl, val in (("नाम / Name", d.get("name")), ("जन्म तिथि / DOB", d.get("dob")),
                         ("जन्म समय / Time", d.get("tob")), ("जन्म स्थान / Place", d.get("place")),
                         ("ऊँचाई / Height", d.get("height")), ("शिक्षा / Education", d.get("education")),
                         ("नौकरी / Job", d.get("job")), ("आय / Income", d.get("income")),
                         ("पिता / Father", d.get("father")), ("माता / Mother", d.get("mother"))):
            val = str(val or "").strip()
            if not val or ry > y + psize - 10:
                continue
            f_lbl.draw(dr, (M, ry), lbl + ":", acc)
            lines = f_val.wrap(val, left_w - 20, 2)
            vy = ry + 38
            for ln in lines:
                f_val.draw(dr, (M + 12, vy), ln, ink)
                vy += 36
            ry = vy + 12
        y = max(y + psize + 50, ry + 30)

        def band(title, y, pairs, cols=2):
            f_sec.draw(dr, (M, y), title, acc)
            y += 52
            dr.line([M, y, W - M, y], fill=(224, 212, 190), width=2)
            y += 18
            per = (W - 2 * M) // cols
            i = 0
            for lbl, val in pairs:
                val = str(val or "").strip()
                if not val:
                    continue
                cx = M + (i % cols) * per
                cy = y + (i // cols) * 88
                if lbl:
                    f_lbl.draw(dr, (cx, cy), lbl + ":", (120, 104, 80))
                    for j, ln in enumerate(f_val.wrap(val, per - 40, 2)):
                        f_val.draw(dr, (cx + 12, cy + 36 + j * 36), ln, ink)
                else:
                    for j, ln in enumerate(f_val.wrap(val, W - 2 * M - 20, 3)):
                        f_val.draw(dr, (cx + 12, cy + j * 38), ln, ink)
                i += 1
            rows_used = (i + cols - 1) // cols
            return y + rows_used * 88 + 30

        y = band("व्यक्तिगत जानकारी / Personal Details", y, [
            ("गोत्र / Gotra", d.get("gotra")), ("राशि / Rashi", d.get("rashi")),
            ("नक्षत्र / Nakshatra", d.get("nakshatra")), ("मांगलिक / Manglik", d.get("manglik")),
            ("गाँव / Village", d.get("village")), ("जिला / District", d.get("district")),
            ("राज्य / State", d.get("state")), ("भाई-बहन / Siblings", d.get("siblings")),
        ])
        if str(d.get("about") or "").strip() and y < H - 620:
            y = band("मेरे बारे में / About Me", y, [("", d.get("about"))], cols=1)
        if str(d.get("expect") or "").strip() and y < H - 520:
            y = band("अपेक्षा / Expectation", y, [("", d.get("expect"))], cols=1)

        phone = str(d.get("phone") or "").strip()
        if phone:
            dr.rectangle([M, H - 262, W - M, H - 152], fill=(252, 247, 233),
                         outline=acc, width=3)
            ScriptFont(38, True).draw_center(
                dr, (M, W - M), "संपर्क / Contact: " + phone, acc, H - 234)
        ScriptFont(22).draw(dr, (M, H - 92), f"Made with {_brand()}", (168, 154, 130))
        return {"ok": True, "png": _save_png(img), "size": img.size}
    except Exception as e:                                       # noqa: BLE001
        return _err("biodata", e)


# =====================================================================
#  4. 🎓 CERTIFICATE
# =====================================================================
def certificate_image(d: dict) -> dict:
    """Achievement / bonafide / experience letter style certificate (landscape)."""
    try:
        from PIL import ImageDraw
        W, H = A4()[1], A4()[0]              # landscape
        W, H = A4(200)[1], int(A4(200)[0] * 1.0)
        W, H = int(11.69 * 200), int(8.27 * 200)
        img = _blank(W, H, (255, 255, 252))
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (146, 108, 22))
        ink = (35, 32, 26)
        F = ScriptFont
        M = 70

        # ornamental frame
        dr.rectangle([0, 0, W - 1, H - 1], fill=acc)
        dr.rectangle([26, 26, W - 27, H - 27], fill=(255, 255, 252))
        dr.rectangle([26, 26, W - 27, H - 27], outline=acc, width=6)
        dr.rectangle([46, 46, W - 47, H - 47], outline=acc, width=2)
        for cx, cy in ((26, 26), (W - 27, 26), (26, H - 27), (W - 27, H - 27)):
            dr.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=acc)

        # v63: sanstha ka logo (top-right) — photo ho to wo neeche lagega
        if d.get("logo"):
            _paste_logo(img, d.get("logo"), (W - 218, 74, 148), pad=10)

        y = 120
        f_org = F(34, True)
        for ln in f_org.wrap(str(d.get("org") or "ORGANISATION NAME"), W - 400, 2):
            f_org.draw_center(dr, (M, W - M), ln, ink, y)
            y += 46
        addr = str(d.get("org_line") or d.get("address") or "").strip()
        if addr:
            f_xs = ScriptFont(24)
            f_xs.draw_center(dr, (M, W - M), addr[:120], (110, 104, 92), y)
            y += 40
        y += 20
        dr.line([W // 2 - 420, y, W // 2 + 420, y], fill=acc, width=3)
        y += 40

        f_title = F(64, True)
        f_title.draw_center(dr, (M, W - M),
                            str(d.get("title") or "CERTIFICATE OF ACHIEVEMENT")[:48],
                            acc, y)
        y += 88
        sub = str(d.get("subtitle") or "").strip()
        if sub:
            ScriptFont(30).draw_center(dr, (M, W - M), sub[:70], (120, 112, 96), y)
            y += 56
        y += 16

        body = str(d.get("body") or "").strip()
        if not body:
            nm = str(d.get("name") or "Student Name")
            body = (f"This is to certify that {nm} has successfully completed "
                    f"{d.get('course') or 'the course'} at our institute.")
        f_body = ScriptFont(36)
        for ln in f_body.wrap(body, W - 360, 8):
            f_body.draw_center(dr, (M, W - M), ln, ink, y)
            y += 54
        y += 20
        nl = str(d.get("name_line") or "").strip()
        if nl:
            for ln in ScriptFont(36, True).wrap(nl, W - 340, 2):
                ScriptFont(36, True).draw_center(dr, (M, W - M), ln, acc, y)
                y += 50
        y += 40

        # details row
        pairs = [(lbl, d.get(k)) for lbl, k in
                 (("Date", "date"), ("Roll No.", "roll"), ("Grade", "grade"),
                  ("Duration", "duration"), ("Reg. No.", "reg_no"))]
        pairs = [(a, b) for a, b in pairs if str(b or "").strip()]
        if pairs:
            per = (W - 2 * M) // max(1, len(pairs))
            for i, (lbl, val) in enumerate(pairs):
                cx = M + i * per
                ScriptFont(25).draw(dr, (cx, y), lbl, (130, 122, 108))
                ScriptFont(30, True).draw(dr, (cx, y + 34), str(val)[:26], ink)
            y += 96

        # ---------- v63: beech ka khaali hissa saaf-suthra bharo ----------
        # Poore bache hue hisse ko naapo, phir uske EXACT beech me rakho —
        # is se kuch bhi overlap nahi hota (pehle fixed y ki wajah se ho raha tha).
        _band_top = y + 10
        _band_bot = H - 250
        _band_mid = (_band_top + _band_bot) // 2

        # (a) student ka photo — baayein taraf, band ke beech
        _ph = d.get("photo")
        if _ph:
            _pbox = 230
            _px = M + 70
            _py = _band_mid - _pbox // 2 - 46
            _paste_photo(img, _ph, (_px, _py, _pbox), radius=10,
                         border=acc, bw=6)
            ScriptFont(24).draw_center(dr, (_px - 20, _px + _pbox + 20),
                                       "STUDENT PHOTO", (140, 132, 118),
                                       _py + _pbox + 16)

        # (b) gold medal — center me (asli 5-kone wala sitara, glyph par bharosa nahi)
        _mx2 = W // 2
        _r = 92
        _my2 = _band_mid - _r - 74
        dr.polygon([(_mx2 - 30, _my2 + _r - 10), (_mx2 + 30, _my2 + _r - 10),
                    (_mx2 + 16, _my2 + _r + 96), (_mx2 - 16, _my2 + _r + 96)],
                   fill=acc)
        dr.ellipse([_mx2 - _r, _my2 - _r, _mx2 + _r, _my2 + _r], fill=(247, 240, 218),
                   outline=acc, width=6)
        dr.ellipse([_mx2 - _r + 16, _my2 - _r + 16, _mx2 + _r - 16, _my2 + _r - 16],
                   outline=acc, width=2)
        _sr = 46
        _pts = []
        import math as _math
        for _i in range(10):
            _ang = -_math.pi / 2 + _i * _math.pi / 5
            _rr = _sr if _i % 2 == 0 else _sr * 0.44
            _pts.append((_mx2 + _rr * _math.cos(_ang), _my2 + _rr * _math.sin(_ang)))
        dr.polygon(_pts, fill=acc)
        _txt = str(d.get("medal_text") or "EXCELLENCE").upper()[:16]
        ScriptFont(28, True).draw_center(dr, (_mx2 - 240, _mx2 + 240), _txt,
                                         acc, _my2 + _r + 112)

        # (c) issue date — band ke neeche, center me (kisi cheez se takrata nahi)
        ScriptFont(26).draw_center(dr, (W // 2 - 260, W // 2 + 260),
                                   f"Issued on {d.get('date') or _today()}",
                                   (130, 122, 108), _band_mid + 268)

        # signatures
        by = H - 200
        dr.line([M + 90, by, M + 430, by], fill=ink, width=2)
        ScriptFont(26).draw_center(dr, (M + 90, M + 430),
                                   str(d.get("sign1") or "Class Teacher"), (110, 104, 92), by + 12)
        dr.line([W - M - 430, by, W - M - 90, by], fill=ink, width=2)
        ScriptFont(26).draw_center(dr, (W - M - 430, W - M - 90),
                                   str(d.get("sign2") or "Principal / Director"),
                                   (110, 104, 92), by + 12)
        if str(d.get("seal_text") or "").strip():
            dr.ellipse([W // 2 - 90, by - 90, W // 2 + 90, by + 90], outline=acc, width=3)
            ScriptFont(22).draw_center(dr, (W // 2 - 90, W // 2 + 90),
                                       str(d["seal_text"])[:16], acc, by - 12)
        ScriptFont(19).draw_center(dr, (M + 40, W - M - 40),
                                   f"Made with {_brand()}", (176, 170, 156), H - 78)
        return {"ok": True, "png": _save_png(img), "size": img.size}
    except Exception as e:                                       # noqa: BLE001
        return _err("certificate", e)


# =====================================================================
#  5. 🪪 ID CARD  (ek A4 par 10 cards, cut karke use karo)
# =====================================================================
def idcard_image(d: dict) -> dict:
    """School / coaching / office ID card — A4 sheet par 10 card (cut lines ke saath).

    d = { org, tagline, address, phone, session, card_title:"STUDENT ID CARD",
          students:[{name, father, class, roll, dob, blood, phone, address, photo}],
          sign1, sign2, accent, notice }
    """
    try:
        from PIL import ImageDraw
        W, H = A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (12, 74, 160))
        F = ScriptFont

        cards = [c for c in (d.get("students") or d.get("cards") or []) if isinstance(c, dict)]
        if not cards:
            cards = [{"name": d.get("name"), "father": d.get("father"),
                      "class": d.get("class"), "roll": d.get("roll"),
                      "dob": d.get("dob"), "blood": d.get("blood"),
                      "phone": d.get("phone"), "address": d.get("address"),
                      "photo": d.get("photo")}]

        # ---------- v63: ASLI layout — 2 column x 5 row = 10 cards ----------
        # Pehle 1 column x 10 row try kiya gaya tha, par 10 card page me fit hi
        # nahi hote the (2814px > 2338px) — 2 aakhri card page se bahar chale
        # jaate the. Ab asli ID card ka size (85x54 mm) use hota hai.
        per_page = 10
        pages = []
        gapx, gapy = 34, 26
        cw = (W - 44 - 2 * gapx) // 2          # = 776 px  (~85mm)
        ch = (H - 96 - 4 * gapy) // 5          # = 427 px  (~54mm)
        x_cols = [22 + i2 * (cw + gapx) for i2 in range(2)]
        y_rows = [66 + i3 * (ch + gapy) for i3 in range(5)]
        org = str(d.get("org") or "INSTITUTE NAME")[:42]
        tagline = str(d.get("tagline") or d.get("address") or "")[:58]
        session = str(d.get("session") or "")[:18]

        for pg in range((len(cards) + per_page - 1) // per_page):
            page = _blank(W, H, WHITE)
            pd = ImageDraw.Draw(page)
            pd.rectangle([0, 0, W, 44], fill=(238, 241, 246))
            ScriptFont(21).draw(pd, (20, 11),
                                "Cut along the dotted lines  ·  Print at 100% (A4, 200 DPI)",
                                (100, 106, 118))
            ScriptFont(21).draw_right(pd, W - 20, f"Page {pg + 1}", (100, 106, 118))

            for k in range(per_page):
                idx = pg * per_page + k
                if idx >= len(cards):
                    break
                st = cards[idx]
                x0 = x_cols[k % 2]
                y = y_rows[k // 2]

                # ---- cut guide (chaaron taraf dots) ----
                for xx in range(x0, x0 + cw, 16):
                    pd.line([xx, y - 11, xx + 8, y - 11], fill=(196, 202, 212), width=2)
                    pd.line([xx, y + ch + 11, xx + 8, y + ch + 11],
                            fill=(196, 202, 212), width=2)
                for yy in range(y, y + ch, 16):
                    pd.line([x0 - 11, yy, x0 - 11, yy + 8], fill=(196, 202, 212), width=2)
                    pd.line([x0 + cw + 11, yy, x0 + cw + 11, yy + 8],
                            fill=(196, 202, 212), width=2)

                # ---- card body ----
                pd.rectangle([x0, y, x0 + cw, y + ch], fill=WHITE,
                             outline=(186, 194, 206), width=2)
                HB = 74                                  # header band
                pd.rectangle([x0, y, x0 + cw, y + HB], fill=acc)

                # org + logo (logo ho to header me baayein)
                _lx = x0 + 14
                if d.get("logo"):
                    _paste_logo(page, d.get("logo"), (x0 + 10, y + 8, 58), pad=3, bg=acc)
                    _lx = x0 + 78
                f_org = ScriptFont(27, True)
                for i2, ln in enumerate(f_org.wrap(org, cw - (_lx - x0) - 130, 1)):
                    f_org.draw(pd, (_lx, y + 11 + i2 * 30), ln, WHITE)
                ScriptFont(19).draw(pd, (_lx, y + 45), tagline, (214, 228, 250))
                if session:
                    ScriptFont(19, True).draw_right(pd, x0 + cw - 14, session,
                                                    (214, 228, 250), y + 45)

                # ---- photo (daayein taraf, band ke andar) ----
                pbox = (x0 + cw - 168, y + HB + 14, 150)
                if st.get("photo"):
                    _paste_photo(page, st.get("photo"), pbox,
                                 border=(178, 188, 202), bw=4)
                else:
                    pd.rectangle([pbox[0], pbox[1], pbox[0] + pbox[2],
                                  pbox[1] + pbox[2]], fill=(246, 249, 252),
                                 outline=(196, 202, 212), width=3)
                    ScriptFont(20).draw_center(pd, (pbox[0], pbox[0] + pbox[2]),
                                               "PHOTO", (168, 176, 190),
                                               pbox[1] + pbox[2] // 2 - 12)
                ScriptFont(17).draw_center(pd, (pbox[0] - 6, pbox[0] + pbox[2] + 6),
                                           str(st.get("sign1") or ""), (150, 158, 172),
                                           pbox[1] + pbox[2] + 6)

                # ---- fields (photo ke baayein) ----
                fy = y + HB + 14
                f_lbl = ScriptFont(21)
                f_val = ScriptFont(25, True)
                lw = 124
                maxw = cw - (pbox[2] + 40) - lw - 24
                for lbl, key in (("Name", "name"), ("Father", "father"),
                                 ("Class", "class"), ("Roll No", "roll"),
                                 ("DOB", "dob"), ("Mobile", "phone"),
                                 ("Blood", "blood")):
                    val = str(st.get(key) or "").strip()
                    if not val:
                        continue
                    f_lbl.draw(pd, (x0 + 16, fy), lbl + ":", (108, 116, 130))
                    for ln in f_val.wrap(val, maxw, 1):
                        f_val.draw(pd, (x0 + 16 + lw, fy - 2), ln, INK)
                    fy += 30
                    if fy > y + ch - 74:
                        break

                # ---- halka watermark (khaali jagah bhare, asli card jaisa lage) ----
                _wm = str(d.get("watermark") or org or "").strip()[:30]
                if _wm:
                    _wf = ScriptFont(46, True)
                    _wy = y + HB + 116
                    try:
                        _ww = _wf.width(_wm)
                        if _ww > cw - 40:
                            _wf = ScriptFont(34, True)
                    except Exception:                            # noqa: BLE001
                        pass
                    _wf.draw_center(pd, (x0 + 10, x0 + cw - 10), _wm,
                                    (240, 244, 250), _wy)

                # ---- agar jagah bachi ho to kaam ki lines (real ID card jaisa) ----
                if fy < y + ch - 100:
                    # session "2026-27" se "31-03-2027" nikaalo (na mile to chhodo)
                    _valid = ""
                    _sess = str(d.get("session") or "").strip()
                    _mm = re.findall(r"(\d{4})\D+(\d{2,4})", _sess)
                    if _mm:
                        _y2 = int(_mm[0][1])
                        _y2 = _y2 + 2000 if _y2 < 100 else _y2
                        _valid = f"31-03-{_y2}"
                    if _valid:
                        ScriptFont(19).draw(pd, (x0 + 16, fy + 6),
                                            f"Valid Upto: {_valid}", (120, 128, 142))
                    # student ke signature ki line
                    _sy = y + ch - 92
                    pd.line([x0 + 16, _sy, x0 + 196, _sy], fill=(150, 158, 172), width=2)
                    ScriptFont(17).draw(pd, (x0 + 16, _sy + 4), "Student Signature",
                                        (150, 158, 172))

                # ---- footer: address + principal signature ----
                pad_line = y + ch - 66
                pd.line([x0 + 14, pad_line, x0 + cw - 14, pad_line],
                        fill=(214, 220, 230), width=2)
                _foot = str(d.get("address") or d.get("phone") or "")[:58]
                if _foot:
                    ScriptFont(19).draw(pd, (x0 + 16, pad_line + 12), _foot,
                                        (110, 118, 132))
                sig = str(d.get("sign1") or "Principal")
                f_sg = ScriptFont(19)
                sw = f_sg.width(sig)
                pd.line([x0 + cw - 34 - sw, y + ch - 44, x0 + cw - 34, y + ch - 44],
                        fill=(120, 128, 142), width=2)
                f_sg.draw(pd, (x0 + cw - 34 - sw, y + ch - 39), sig, (110, 118, 132))
                # card ke andar halka brand (chhota, cut ke baad bhi dikhe)
                ScriptFont(15).draw(pd, (x0 + 16, y + ch - 26), _brand(),
                                    (196, 202, 212))
            pages.append(_save_png(page))
        notice = str(d.get("notice") or "").strip()
        return {"ok": True, "png": pages[0], "pages": pages, "count": len(cards),
                "notice": notice}
    except Exception as e:                                       # noqa: BLE001
        return _err("idcard", e)


# =====================================================================
#  6. 📇 VISITING CARD (A4 par 10 card — 90x54mm standard)
# =====================================================================
def visiting_card_image(d: dict) -> dict:
    """Business / visiting card — A4 sheet par 10 card (2 column x 5 row).

    d = { owner, shop, tagline, phone, phone2, email, address, website, upi,
          services:"...", accent, style:"clean"|"dark"|"band" }
    """
    try:
        from PIL import ImageDraw
        W, H = A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (12, 74, 160))
        style = str(d.get("style") or "band").lower()
        F = ScriptFont

        # v63: asli visiting card = 90x54 mm -> 200 DPI par 709x425 px.
        # Pehle 900x540 tha, jisse 2 column page (1654px) me fit hi nahi hote the
        # aur pehla column page ke BAHAR chala jata tha.
        cw, ch = 776, 427
        gapx, gapy = 34, 26
        x1 = 22
        x2 = 22 + cw + gapx
        top = 66
        f_name = F(46, True)
        f_shop = F(30)
        f_sm = F(22)
        f_val = F(24)

        def one(cx, cy):
            bg = WHITE if style != "dark" else (24, 28, 38)
            txt = INK if style != "dark" else (240, 244, 250)
            sub = (110, 118, 132) if style != "dark" else (170, 180, 198)
            dr.rectangle([cx, cy, cx + cw, cy + ch], fill=bg, outline=(198, 204, 214), width=2)
            if style in ("band", "dark"):
                dr.rectangle([cx, cy, cx + cw, cy + 120], fill=acc)
            elif style == "clean":
                dr.rectangle([cx, cy, cx + 14, cy + ch], fill=acc)
            # header
            if style in ("band", "dark"):
                f_name.draw(dr, (cx + 34, cy + 18), str(d.get("owner") or "YOUR NAME")[:26], WHITE)
                f_shop.draw(dr, (cx + 34, cy + 76), str(d.get("shop") or "")[:34], (222, 233, 252))
                y = cy + 142
            else:
                f_name.draw(dr, (cx + 40, cy + 30), str(d.get("owner") or "YOUR NAME")[:26], txt)
                f_shop.draw(dr, (cx + 40, cy + 88), str(d.get("shop") or "")[:34], acc)
                y = cy + 152
            tag = str(d.get("tagline") or "").strip()
            if tag:
                f_sm.draw(dr, (cx + 40, y), tag[:60], sub)
                y += 34
            svc = str(d.get("services") or "").strip()
            if svc:
                for ln in f_sm.wrap(svc, cw - 90, 2):
                    f_sm.draw(dr, (cx + 40, y), ln, txt)
                    y += 32
                y += 8
            for val in (d.get("phone"), d.get("phone2"), d.get("email"),
                        d.get("address"), d.get("website")):
                val = str(val or "").strip()
                if not val:
                    continue
                f_val.draw(dr, (cx + 40, y), val[:56], txt if style == "dark" else INK)
                y += 34
            upi = str(d.get("upi") or "").strip()
            if upi:
                try:
                    qp = _make_qr_png(f"upi://pay?pa={upi}&cu=INR", 130)
                    if qp:
                        from PIL import Image
                        qr = Image.open(io.BytesIO(qp)).convert("RGB").resize((130, 130))
                        img.paste(qr, (cx + cw - 170, cy + ch - 160))
                        f_sm.draw(dr, (cx + cw - 174, cy + ch - 24), "Scan & Pay", sub)
                except Exception:                                # noqa: BLE001
                    pass

        coords = [(x1, top + 0 * (ch + gapy)), (x2, top + 0 * (ch + gapy)),
                  (x1, top + 1 * (ch + gapy)), (x2, top + 1 * (ch + gapy)),
                  (x1, top + 2 * (ch + gapy)), (x2, top + 2 * (ch + gapy)),
                  (x1, top + 3 * (ch + gapy)), (x2, top + 3 * (ch + gapy)),
                  (x1, top + 4 * (ch + gapy)), (x2, top + 4 * (ch + gapy))]
        for cx, cy in coords:
            one(cx, cy)
        # cut marks
        for cx, cy in coords:
            for xx in range(cx, cx + cw, 16):
                dr.line([xx, cy - 16, xx + 8, cy - 16], fill=(196, 202, 212), width=2)
                dr.line([xx, cy + ch + 16, xx + 8, cy + ch + 16], fill=(196, 202, 212), width=2)
        ScriptFont(20).draw(dr, (W // 2 - 260, H - 40),
                            "10 visiting cards · 200 DPI · cut along dotted lines",
                            (150, 158, 172))
        return {"ok": True, "png": _save_png(img), "count": 10, "size": img.size}
    except Exception as e:                                       # noqa: BLE001
        return _err("visiting_card", e)


# =====================================================================
#  7. 📄 APPLICATION LETTER (formal, Hindi ya English)
# =====================================================================
def letter_image(d: dict) -> dict:
    """Formal application / letter — leave, NOC, complaint, character, experience.

    d = { sender_name, sender_lines:[..], date, to_lines:[..],
          subject, salutation, body, closing, sign_name, sign_place, photo }
    Ya shortcuts: d = {type:"leave", name, post, org, reason, from, to}
    """
    try:
        from PIL import ImageDraw
        W, H = A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        F = ScriptFont
        acc = _hex(d.get("accent"), (12, 74, 160))
        f_b = F(29)
        M = 130
        CW = W - 2 * M

        t = str(d.get("type") or "").lower()
        if t and not d.get("body"):
            nm = str(d.get("name") or "________")
            d.setdefault("sender_name", nm)
            d.setdefault("subject", {
                "leave": "Application for Leave",
                "noc": "Application for No Objection Certificate",
                "character": "Application for Character Certificate",
                "experience": "Application for Experience Certificate",
                "transfer": "Application for Transfer Certificate",
                "complaint": "Complaint Application",
                "bonafide": "Application for Bonafide Certificate",
                "fee": "Application regarding Fee Concession",
            }.get(t, "Application"))
            d.setdefault("to_lines", ["The Principal / The Manager",
                                      str(d.get("org") or "________")])
            d.setdefault("body",
                         f"With due respect, I beg to state that I am "
                         f"{nm}, {d.get('post') or 'a member'} of your "
                         f"{d.get('org') or 'institution'}. I request you to kindly "
                         f"{d.get('request') or 'grant my application'} "
                         f"{('from ' + str(d.get('from'))) if d.get('from') else ''}"
                         f"{(' to ' + str(d.get('to'))) if d.get('to') else ''} "
                         f"due to {d.get('reason') or 'unavoidable circumstances'}. "
                         f"I shall be highly obliged for your kind consideration.")
            d.setdefault("closing", "Thanking you,")
            d.setdefault("sign_name", nm)

        y = M - 30
        f_line = F(24)
        dr.line([M, y - 20, W - M, y - 20], fill=(220, 226, 236), width=2)
        f_line.draw(dr, (M, y - 68), "APPLICATION / LETTER", (150, 158, 172))
        y = M + 40

        sn = str(d.get("sender_name") or "").strip()
        if sn:
            for ln in ScriptFont(30, True).wrap(sn, CW - 320, 2):
                ScriptFont(30, True).draw(dr, (M, y), ln, INK)
                y += 42
        for extra in (d.get("sender_lines") or []):
            if str(extra or "").strip():
                for ln in f_b.wrap(str(extra), CW - 320, 2):
                    f_b.draw(dr, (M, y), ln, MUTED)
                    y += 38
        dt = str(d.get("date") or _today())
        f_b.draw_right(dr, W - M, "Date: " + dt, INK, M + 42)
        if d.get("photo"):
            _paste_photo(img, d.get("photo"), (W - M - 180, M + 90, 170), radius=12)
        y += 60

        to_lines = [str(x) for x in (d.get("to_lines") or []) if str(x or "").strip()]
        if to_lines:
            f_b.draw(dr, (M, y), "To,", MUTED)
            y += 44
            for ln in to_lines:
                for l2 in f_b.wrap(ln, CW - 60, 2):
                    f_b.draw(dr, (M + 34, y), l2, INK)
                    y += 40
                y += 4
            y += 30

        subj = str(d.get("subject") or "").strip()
        if subj:
            ScriptFont(31, True).draw(dr, (M, y), "Subject: ", INK)
            sw = ScriptFont(31, True).width("Subject: ")
            for i2, ln in enumerate(ScriptFont(31, True).wrap(subj, CW - sw - 10, 3)):
                ScriptFont(31, True).draw(dr, (M + (sw if i2 == 0 else 0), y), ln, acc)
                y += 44
            y += 16

        sal = str(d.get("salutation") or "Respected Sir/Madam,").strip()
        f_b.draw(dr, (M, y), sal, INK)
        y += 56

        body = str(d.get("body") or "").strip()
        for ln in f_b.wrap(body, CW, 26):
            f_b.draw(dr, (M, y), ln, INK)
            y += 46
            if y > H - 340:
                break
        y += 36

        closing = str(d.get("closing") or "Thanking you,").strip()
        if closing:
            f_b.draw(dr, (M, y), closing, INK)
            y += 52
        f_b.draw(dr, (M, y), "Yours faithfully,", INK)
        y += 90
        dr.line([M, y, M + 400, y], fill=INK, width=2)
        sig = str(d.get("sign_name") or sn or "").strip()
        ScriptFont(30, True).draw(dr, (M, y + 12), sig[:44], INK)
        sp = str(d.get("sign_place") or "").strip()
        if sp:
            f_b.draw(dr, (M, y + 56), sp[:60], MUTED)
        ScriptFont(22).draw(dr, (M, H - 78), f"Drafted with {_brand()} · review before signing",
                            (155, 162, 174))
        return {"ok": True, "png": _save_png(img), "size": img.size}
    except Exception as e:                                       # noqa: BLE001
        return _err("letter", e)


# =====================================================================
#  8. 💳 UPI PAYMENT POSTER (dukaan ka "Scan & Pay" board)
# =====================================================================
def upi_qr_image(d: dict) -> dict:
    """Dukaan ke liye UPI payment board — QR + naam + dukaan details.

    d = { upi, upi_name, shop, phone, amount (0/khali = open amount),
          note, accent, show_amount:bool }
    """
    try:
        from PIL import ImageDraw
        W, H = A4()
        img = _blank(W, H, (255, 255, 255))
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (15, 66, 165))
        F = ScriptFont

        upi = str(d.get("upi") or "").strip()
        if not upi:
            return {"ok": False, "error": "UPI ID khaali hai"}
        shop = str(d.get("shop") or d.get("upi_name") or "MERCHANT")[:48]
        amt = _num(d.get("amount"))
        try:
            from modules.general_tools import build_upi_link
            link = build_upi_link(upi, str(d.get("upi_name") or shop),
                                  amt if amt else None,
                                  note=str(d.get("note") or "Payment").strip())
        except Exception:                                        # noqa: BLE001
            link = f"upi://pay?pa={upi}&pn={shop}&cu=INR" + (f"&am={amt:.2f}" if amt else "")

        # header
        dr.rectangle([0, 0, W, 300], fill=acc)
        # v63: merchant ka logo (baayein), naam uske baad center me
        _cbox = (60, W - 60)
        if d.get("logo"):
            _paste_logo(img, d.get("logo"), (58, 78, 148), pad=6, bg=acc)
            _cbox = (232, W - 60)
        ScriptFont(58, True).draw_center(dr, _cbox, shop, WHITE, 60)
        ScriptFont(32).draw_center(dr, _cbox, "SCAN & PAY · UPI Accepted",
                                   (216, 229, 252), 150)
        dr.rectangle([W // 2 - 300, 220, W // 2 + 300, 232], fill=(255, 255, 255))

        # QR
        qsize = 1000
        qp = _make_qr_png(link, qsize)
        if not qp:
            return {"ok": False, "error": "QR ban nahi paya"}
        from PIL import Image
        qr = Image.open(io.BytesIO(qp)).convert("RGB").resize((qsize, qsize))
        qx = (W - qsize) // 2
        qy = 380
        dr.rectangle([qx - 26, qy - 26, qx + qsize + 26, qy + qsize + 26],
                     outline=acc, width=12)
        img.paste(qr, (qx, qy))
        y = qy + qsize + 60

        if amt:
            dr.rectangle([qx - 26, y, qx + qsize + 26, y + 130], fill=(240, 246, 255),
                         outline=acc, width=4)
            ScriptFont(56, True).draw_center(dr, (qx, qx + qsize),
                                             "Rs. " + money(amt), acc, y + 32)
            y += 160

        ScriptFont(40, True).draw_center(dr, (80, W - 80), upi[:48], INK, y)
        y += 70
        ph = str(d.get("phone") or "").strip()
        if ph:
            ScriptFont(32).draw_center(dr, (80, W - 80), "Ph: " + ph[:40], MUTED, y)
            y += 58
        note = str(d.get("note") or "").strip()
        if note:
            for ln in ScriptFont(30).wrap(note, W - 240, 2):
                ScriptFont(30).draw_center(dr, (120, W - 120), ln, MUTED, y)
                y += 46

        # accepted apps strip
        strip_y = H - 300
        dr.rectangle([0, strip_y, W, strip_y + 120], fill=(245, 247, 251))
        ScriptFont(34, True).draw_center(dr, (60, W - 60),
                                         "GPay   ·   PhonePe   ·   Paytm   ·   BHIM   ·   Amazon Pay",
                                         acc, strip_y + 40)
        ScriptFont(26).draw_center(dr, (60, W - 60),
                                   "Payment ka screenshot zaroor lein · " + _brand(),
                                   MUTED, H - 110)
        return {"ok": True, "png": _save_png(img), "link": link, "size": img.size}
    except Exception as e:                                       # noqa: BLE001
        return _err("upi_qr", e)


# =====================================================================
#  9. 🏷️ PRICE LABEL SHEET (dukaan ke rate tag)
# =====================================================================
def label_sheet_image(d: dict) -> dict:
    """Rate tag / price label sheet — print karo aur kaat kar chipka do.

    d = { shop, labels:[{name, price, mrp, unit}], cols:3, accent,
          currency:"Rs.", footer, per_page }
    """
    try:
        from PIL import ImageDraw
        W, H = A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (200, 30, 44))
        cols = max(1, min(5, int(_num(d.get("cols"), 3))))
        labels = [x for x in (d.get("labels") or []) if isinstance(x, dict)]
        if not labels:
            return {"ok": False, "error": "koi label nahi diya"}

        M = 60
        gap = 16
        cw = (W - 2 * M - gap * (cols - 1)) // cols
        ch = 200
        rows = max(1, (H - 200) // (ch + gap))
        per_page = cols * rows
        pages = []

        for pg in range((len(labels) + per_page - 1) // per_page):
            page = _blank(W, H, WHITE)
            pd = ImageDraw.Draw(page)
            pd.rectangle([0, 0, W, 70], fill=acc)
            _shop_txt = str(d.get("shop") or "PRICE LIST")[:48]
            _pgt = f"Page {pg + 1} · {_today()}"
            if d.get("logo"):
                # v63: logo daayein, page-text neeche (band ke bahar)
                _paste_logo(pd, d.get("logo"), (W - M - 58, 6, 58), pad=2)
                ScriptFont(34, True).draw(pd, (M, 16),
                                          ScriptFont(34, True).wrap(_shop_txt, W - 2 * M - 80, 1)[0],
                                          WHITE)
                ScriptFont(20).draw(pd, (M, 76), _pgt, MUTED)
            else:
                ScriptFont(34, True).draw(pd, (M, 16), _shop_txt, WHITE)
                ScriptFont(24).draw_right(pd, W - M, _pgt, WHITE, 24)
            for k in range(per_page):
                i = pg * per_page + k
                if i >= len(labels):
                    break
                it = labels[i]
                cx = M + (k % cols) * (cw + gap)
                cy = 100 + (k // cols) * (ch + gap)
                pd.rectangle([cx, cy, cx + cw, cy + ch], fill=WHITE,
                             outline=(190, 196, 206), width=2)
                pd.rectangle([cx, cy, cx + cw, cy + 10], fill=acc)
                nm = str(it.get("name") or "-")
                ny = cy + 26
                for ln in ScriptFont(27, True).wrap(nm, cw - 30, 3):
                    ScriptFont(27, True).draw(pd, (cx + 15, ny), ln, INK)
                    ny += 34
                    if ny > cy + ch - 90:
                        break
                price = it.get("price")
                pf = ScriptFont(46, True)
                ptxt = f"{d.get('currency') or 'Rs.'} {money(price)}"
                try:
                    pw = pf.width(ptxt)
                    while pw > cw - 30 and pf.size > 16:
                        pf = ScriptFont(pf.size - 3, True)
                        pw = pf.width(ptxt)
                except Exception:                                # noqa: BLE001
                    pass
                pf.draw(pd, (cx + 15, cy + ch - 92), ptxt, acc)
                mrp = it.get("mrp")
                if _num(mrp) > _num(price):
                    mtxt = f"MRP {money(mrp)}"
                    mw = ScriptFont(23).width(mtxt)
                    ScriptFont(23).draw(pd, (cx + 15, cy + ch - 46), mtxt, FAINT)
                    pd.line([cx + 15, cy + ch - 34, cx + 15 + mw, cy + ch - 34],
                            fill=FAINT, width=2)
                unit = str(it.get("unit") or "").strip()
                if unit:
                    ScriptFont(23).draw_right(pd, cx + cw - 15, unit[:16], MUTED,
                                              cy + ch - 44)
            foot = str(d.get("footer") or "").strip()
            if foot:
                ScriptFont(24).draw_center(pd, (M, W - M), foot[:90], MUTED, H - 70)
            pages.append(_save_png(page))
        return {"ok": True, "png": pages[0], "pages": pages, "count": len(labels),
                "per_page": per_page}
    except Exception as e:                                       # noqa: BLE001
        return _err("labels", e)


# =====================================================================
#  10. 🧮 EMI / LOAN CARD (poora hisaab + month-wise schedule)
# =====================================================================
def emi_breakup(principal, annual_rate, months) -> dict:
    """EMI ka ganit — flat aur reducing dono. Kabhi crash nahi."""
    p = max(0.0, _num(principal))
    r = max(0.0, _num(annual_rate))
    n = int(max(1, min(600, _num(months, 12))))
    mr = r / 12.0 / 100.0
    if p <= 0:
        return {"error": "loan amount 0 hai"}
    if mr <= 0:
        emi = p / n
    else:
        f = (1 + mr) ** n
        emi = p * mr * f / (f - 1)
    total = emi * n
    interest = total - p
    rows = []
    bal = p
    for i in range(1, n + 1):
        intr = bal * mr
        prin = emi - intr
        if i == n:
            prin = bal
            emi_use = prin + intr
            bal = 0.0
        else:
            bal = max(0.0, bal - prin)
            emi_use = emi
        rows.append({"n": i, "emi": emi_use, "principal": prin, "interest": intr,
                     "balance": bal})
    return {"principal": p, "rate": r, "months": n, "emi": emi, "total": total,
            "interest": interest, "rows": rows,
            "interest_pct": (interest / p * 100.0) if p else 0.0}


def emi_card_image(d: dict) -> dict:
    """Loan / EMI summary card — poora hisaab + month-wise schedule.

    d = { bank, borrower, loan_amount, rate, months, start_date, processing_fee,
          accent, note }
    """
    try:
        from PIL import ImageDraw
        W, H = A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (13, 120, 88))
        F = ScriptFont

        res = emi_breakup(d.get("loan_amount"), d.get("rate"), d.get("months"))
        if res.get("error"):
            return {"ok": False, "error": res["error"]}

        M = 80
        dr.rectangle([0, 0, W, 260], fill=acc)
        ScriptFont(48, True).draw_center(dr, (M, W - M),
                                         str(d.get("bank") or "LOAN / EMI SUMMARY")[:44],
                                         WHITE, 46)
        ScriptFont(30).draw_center(dr, (M, W - M),
                                   "ब्याज और EMI का पूरा हिसाब · Full repayment schedule",
                                   (216, 240, 230), 124)
        if str(d.get("borrower") or "").strip():
            ScriptFont(28).draw_center(dr, (M, W - M),
                                       "Borrower: " + str(d["borrower"])[:40],
                                       (216, 240, 230), 180)
        y = 300

        # summary tiles
        fee = _num(d.get("processing_fee"))
        tiles = [("Loan Amount", "Rs. " + money(res["principal"])),
                 ("Interest Rate", f"{res['rate']:g}% p.a."),
                 ("Tenure", f"{res['months']} months"),
                 ("Monthly EMI", "Rs. " + money(res["emi"]))]
        tw = (W - 2 * M - 3 * 20) // 4
        for i, (lbl, val) in enumerate(tiles):
            tx = M + i * (tw + 20)
            dr.rectangle([tx, y, tx + tw, y + 170], fill=BAND, outline=LINE, width=2)
            ScriptFont(24).draw_center(dr, (tx, tx + tw), lbl, MUTED, y + 26)
            fv = ScriptFont(34, True)
            try:
                while fv.width(val) > tw - 20 and fv.size > 18:
                    fv = ScriptFont(fv.size - 3, True)
            except Exception:                                    # noqa: BLE001
                pass
            fv.draw_center(dr, (tx, tx + tw), val, acc, y + 84)
        y += 210

        rows = [("Total Payment", "Rs. " + money(res["total"])),
                ("Total Interest", "Rs. " + money(res["interest"])
                 + f"  ({res['interest_pct']:.1f}%)"),
                ("Principal", "Rs. " + money(res["principal"]))]
        if fee:
            rows.append(("Processing Fee", "Rs. " + money(fee)))
            rows.append(("Total Cost", "Rs. " + money(res["total"] + fee)))
        for lbl, val in rows:
            ScriptFont(30).draw(dr, (M, y), lbl, MUTED)
            ScriptFont(30, True).draw_right(dr, W - M, val, INK, y)
            y += 48
        y += 20
        dr.line([M, y, W - M, y], fill=LINE, width=3)
        y += 24

        # month-wise schedule (do column)
        ScriptFont(34, True).draw(dr, (M, y), "Month-wise Schedule", acc)
        y += 56
        heads = ("#", "EMI", "Principal", "Interest", "Balance")
        rows_list = res["rows"]
        half = (len(rows_list) + 1) // 2
        # ⚠️ do column: har table ko available jagah me FIT karo (pehle 800px
        # fix tha aur page se bahar nikal jata tha — Balance column kata hua)
        gap_c = 24
        tw_col = (W - 2 * M - gap_c) // 2
        # column positions table width ke hisaab se (proportional)
        col_rel = (0,
                   int(tw_col * 0.085),
                   int(tw_col * 0.290),
                   int(tw_col * 0.540),
                   int(tw_col * 0.780))
        f_hdr = ScriptFont(21)
        f_row = ScriptFont(21)
        row_h = 36
        for ci, chunk in enumerate((rows_list[:half], rows_list[half:])):
            if not chunk:
                continue
            base_x = M + ci * (tw_col + gap_c)
            cy = y
            dr.rectangle([base_x, cy, base_x + tw_col, cy + 42], fill=acc)
            for hi, h in enumerate(heads):
                f_hdr.draw(dr, (base_x + col_rel[hi] + 8, cy + 10), h, WHITE)
            cy += 42
            for j, rr in enumerate(chunk):
                if j % 2 == 0:
                    dr.rectangle([base_x, cy, base_x + tw_col, cy + row_h],
                                 fill=(249, 251, 253))
                f_row.draw(dr, (base_x + 8, cy + 7), str(rr["n"]), MUTED)
                for hi, key in ((1, "emi"), (2, "principal"), (3, "interest"),
                                (4, "balance")):
                    f_row.draw(dr, (base_x + col_rel[hi] + 8, cy + 7),
                               money(round(rr[key])), INK)
                cy += row_h
                if cy > H - 120:
                    break
        note = str(d.get("note") or "").strip()
        if note:
            ScriptFont(24).draw(dr, (M, H - 96), note[:110], MUTED)
        ScriptFont(22).draw(dr, (M, H - 62),
                            f"Indicative calculation only · confirm with bank · {_brand()}",
                            FAINT)
        return {"ok": True, "png": _save_png(img), "emi": res["emi"],
                "total": res["total"], "interest": res["interest"],
                "months": res["months"], "size": img.size}
    except Exception as e:                                       # noqa: BLE001
        return _err("emi", e)


# =====================================================================
#  11. 💰 SALARY SLIP (v62) — staff ka monthly pay slip
# =====================================================================
def salary_slip_image(d: dict) -> dict:
    """Company ka salary slip — A4 print-ready, Hindi/English dono.

    d = {company, name, code, post, month, gross, days, advance,
         pf_rate, ptax, accent, footer}
    """
    try:
        from PIL import ImageDraw
        W, H = A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (13, 96, 78))
        M = 70
        gross = _num(d.get("gross"), 0)
        if gross <= 0:
            return {"ok": False, "error": "salary (gross) 0 hai — sahi amount likhiye"}

        basic = round(gross * 0.50, 2)
        hra = round(gross * 0.20, 2)
        other = round(gross - basic - hra, 2)
        pf = round(basic * _num(d.get("pf_rate"), 12.0) / 100.0, 2)
        esi = round(gross * 0.0075, 2) if gross <= 21000 else 0.0
        ptax = _num(d.get("ptax"), 200.0)
        adv = _num(d.get("advance"), 0)
        ded_total = round(pf + esi + ptax + adv, 2)
        net = round(gross - ded_total, 2)
        company = str(d.get("company") or "COMPANY NAME")[:60]
        month = str(d.get("month") or _today())[:24]

        # ---------- header ----------
        dr.rectangle([0, 0, W, 158], fill=acc)
        ScriptFont(48, True).draw(dr, (M, 34), company, WHITE)
        ScriptFont(34, True).draw_right(dr, W - M, "SALARY SLIP", WHITE, 40)
        ScriptFont(25).draw_right(dr, W - M, f"Month: {month}", WHITE, 92)

        # ---------- employee box ----------
        by = 200
        dr.rectangle([M, by, W - M, by + 300], fill=(247, 249, 252),
                     outline=LINE, width=2)
        pairs = [("Employee Name", d.get("name") or "—"),
                 ("Employee Code", d.get("code") or f"EMP{datetime.now().strftime('%m%d')}"),
                 ("Designation", d.get("post") or "Staff"),
                 ("Month", month),
                 ("Working Days", f"{int(_num(d.get('days'), 30))}"),
                 ("Paid Days", f"{int(_num(d.get('days'), 30))}")]
        colw = (W - 2 * M - 60) // 2
        for i, (lab, val) in enumerate(pairs):
            cx = M + 30 + (i % 2) * colw
            cy = by + 34 + (i // 2) * 92
            ScriptFont(24).draw(dr, (cx, cy), lab.upper(), MUTED)
            ScriptFont(30, True).draw(dr, (cx, cy + 34), str(val)[:34], INK)

        # ---------- earnings / deductions ----------
        ty = 560
        gapx = 44
        tw = (W - 2 * M - gapx) // 2
        row_h = 62
        earn = [("Basic Salary", basic), ("H.R.A.", hra),
                ("Other Allowance", other), ("Gross Salary", gross)]
        dedu = [("Provident Fund (PF)", pf), ("E.S.I.", esi),
                ("Professional Tax", ptax), ("Advance / Loan", adv)]

        for side, (title, rows, total_lbl, total_val) in enumerate((
                ("EARNINGS", earn, "TOTAL EARNING", gross),
                ("DEDUCTIONS", dedu, "TOTAL DEDUCTION", ded_total))):
            x0 = M + side * (tw + gapx)
            dr.rectangle([x0, ty, x0 + tw, ty + row_h], fill=acc)
            ScriptFont(27, True).draw(dr, (x0 + 20, ty + 15), title, WHITE)
            ScriptFont(25).draw_right(dr, x0 + tw - 20, "Amount (Rs.)", WHITE, ty + 17)
            ry = ty + row_h
            for i2, (lab, val) in enumerate(rows):
                if i2 % 2 == 0:
                    dr.rectangle([x0, ry, x0 + tw, ry + row_h], fill=(249, 251, 253))
                ScriptFont(26).draw(dr, (x0 + 20, ry + 17), lab[:26], INK)
                ScriptFont(26).draw_right(dr, x0 + tw - 20, money(val), INK, ry + 17)
                dr.line([x0, ry, x0 + tw, ry], fill=LINE, width=1)
                ry += row_h
            dr.rectangle([x0, ry, x0 + tw, ry + row_h], fill=(236, 242, 248))
            ScriptFont(26, True).draw(dr, (x0 + 20, ry + 17), total_lbl, INK)
            ScriptFont(28, True).draw_right(dr, x0 + tw - 20, money(total_val), INK, ry + 15)

        # ---------- net pay ----------
        ny = ty + 2 * row_h + 4 * row_h + 60
        dr.rectangle([M, ny, W - M, ny + 150], fill=acc)
        ScriptFont(38, True).draw(dr, (M + 30, ny + 24), "NET PAY", WHITE)
        ScriptFont(58, True).draw_right(dr, W - M - 30, f"Rs. {money(net)}", WHITE, ny + 18)
        ScriptFont(24).draw(dr, (M + 30, ny + 96),
                            "Amount in words: " + amount_words(net), WHITE)

        # ---------- payment details (khaali jagah bhare, kaam ki baat likhe) ----------
        py = ny + 210
        dr.rectangle([M, py, W - M, py + 300], fill=WHITE, outline=LINE, width=2)
        ScriptFont(28, True).draw(dr, (M + 26, py + 18), "PAYMENT DETAILS", acc)
        dr.line([M + 26, py + 62, W - M - 26, py + 62], fill=LINE, width=2)
        pay = [("Payment Mode", d.get("mode") or "Bank Transfer"),
               ("Bank Name", d.get("bank") or "—"),
               ("Account No. (last 4)", d.get("account") or "—"),
               ("Payment Date", d.get("pay_date") or _today()),
               ("UAN / ESIC No.", d.get("uan") or "—"),
               ("Paid Days", f"{int(_num(d.get('days'), 30))} / {int(_num(d.get('days'), 30))}")]
        for i3, (lab, val) in enumerate(pay):
            cx = M + 26 + (i3 % 2) * ((W - 2 * M - 52) // 2)
            cy = py + 82 + (i3 // 2) * 72
            ScriptFont(22).draw(dr, (cx, cy), lab.upper(), MUTED)
            ScriptFont(27, True).draw(dr, (cx, cy + 30), str(val)[:26], INK)

        # ---------- declaration ----------
        dy = py + 340
        note = str(d.get("note") or "").strip() or (
            f"Ye salary slip {month} ke liye company record se generate ki gayi hai. "
            "Koi bhi gadbad 7 din me batayein.")
        dr.rectangle([M, dy, W - M, dy + 160], fill=(247, 249, 252),
                     outline=(226, 232, 240), width=1)
        ScriptFont(24, True).draw(dr, (M + 26, dy + 20), "DECLARATION", MUTED)
        _ny2 = dy + 62
        for ln in ScriptFont(25).wrap(note, W - 2 * M - 52, 4):
            ScriptFont(25).draw(dr, (M + 26, _ny2), ln, MUTED)
            _ny2 += 34

        ScriptFont(24).draw(dr, (M, H - 230),
                            "This is a computer generated salary slip and does not "
                            "require a signature.", MUTED)
        dr.line([W - M - 380, H - 150, W - M, H - 150], fill=INK, width=2)
        ScriptFont(24).draw_center(dr, (W - M - 380, W - M),
                                   "Authorised Signatory", MUTED, H - 140)
        ScriptFont(22).draw(dr, (M, H - 92), f"Computer generated · {_brand()}", FAINT)
        return {"ok": True, "png": _save_png(img), "amount": net,
                "gross": gross, "deductions": ded_total, "size": img.size}
    except Exception as e:                                       # noqa: BLE001
        return _err("salary", e)


# =====================================================================
#  12. 🍽️ MENU CARD / RATE CARD (v62) — dhaba · hotel · dukaan
# =====================================================================
def menu_card_image(d: dict) -> dict:
    """Dhaba / hotel / dukaan ka menu ya rate card — A4.

    d = {name, tagline, items:[{name, price, tag}], accent, contact, footer}
    """
    try:
        from PIL import ImageDraw
        W, H = A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (176, 46, 30))
        M = 60
        items = [x for x in (d.get("items") or []) if isinstance(x, dict)][:80]
        if not items:
            return {"ok": False, "error": "koi item nahi diya — kam se kam ek likhiye"}

        # ---------- frame ----------
        dr.rectangle([36, 36, W - 36, H - 36], outline=acc, width=8)
        dr.rectangle([56, 56, W - 56, H - 56], outline=(232, 220, 210), width=2)

        # ---------- header ----------
        name = str(d.get("name") or "MENU")[:44]
        tagline = str(d.get("tagline") or "").strip()[:70]
        hy = 76
        dr.rectangle([76, hy, W - 76, hy + 210], fill=acc)
        f_n = ScriptFont(64, True)
        while f_n.width(name) > W - 260 and f_n.size > 26:
            f_n = ScriptFont(f_n.size - 4, True)
        # v63: dukaan/hotel ka logo (header ke andar, baayein taraf)
        _nbox = (100, W - 100)
        if d.get("logo"):
            _paste_logo(img, d.get("logo"), (96, hy + 44, 122), pad=4, bg=acc)
            _nbox = (240, W - 100)
        f_n.draw_center(dr, _nbox, name, WHITE, hy + 34)
        if tagline:
            ScriptFont(30).draw_center(dr, _nbox, tagline, WHITE, hy + 130)
        ScriptFont(26, True).draw_center(dr, _nbox, "— RATE LIST / MENU —",
                                         WHITE, hy + 172)

        # ---------- items (2 columns) ----------
        cols = 2 if len(items) > 6 else 1
        colw = (W - 2 * M - (60 if cols == 2 else 0)) // cols
        per_col = (len(items) + cols - 1) // cols
        top = hy + 240
        avail = H - top - 300
        # poori jagah barabar baanto -> page bhara-bhara dikhe (khali na lage)
        row_h = max(56, avail // max(1, per_col))
        fs = 34 if row_h >= 110 else (30 if row_h >= 84 else (27 if row_h >= 66 else 23))
        ytop = top
        f_it = ScriptFont(fs, True)
        f_pr = ScriptFont(fs + 4, True)
        for idx, it in enumerate(items):
            ci = idx // per_col
            ri = idx % per_col
            x0 = M + ci * (colw + 60)
            y = ytop + ri * row_h
            nm = str(it.get("name") or "-")[:34]
            _tg = str(it.get("tag") or "").strip()[:22]
            if _tg and row_h < fs + 54:
                nm = (nm + f" ({_tg})")[:46]
            pr = f"Rs. {money(it.get('price'))}"
            tag = str(it.get("tag") or "").strip()[:22]
            f_it.draw(dr, (x0, y), nm, INK)
            pw = f_pr.width(pr)
            f_pr.draw_right(dr, x0 + colw, pr, acc, y - 2)
            nx = x0 + f_it.width(nm) + 12
            px = x0 + colw - pw - 12
            dot_y = y + fs // 2 + 8
            dx = nx
            while dx < px:
                dr.ellipse([dx, dot_y, dx + 4, dot_y + 4], fill=(198, 190, 182))
                dx += 16
            if tag and row_h >= fs + 54:             # jagah hai -> naam ke neeche
                ScriptFont(fs - 8).draw(dr, (x0 + 6, y + fs + 16), tag, MUTED)

        # ---------- footer ----------
        fy = H - 286
        dr.line([M + 16, fy, W - M - 16, fy], fill=acc, width=4)
        contact = str(d.get("contact") or "").strip()
        if contact:
            ScriptFont(30, True).draw_center(dr, (M, W - M),
                                             f"📞 {contact}"[:70], INK, fy + 26)
        ScriptFont(28, True).draw_center(dr, (M, W - M), "THANKS · VISIT AGAIN",
                                         acc, fy + 84)
        foot = str(d.get("footer") or "").strip()
        if foot:
            ScriptFont(24).draw_center(dr, (M, W - M), foot[:80], MUTED, fy + 132)
        ScriptFont(21).draw_center(dr, (M, W - M), _brand(), FAINT, H - 104)
        return {"ok": True, "png": _save_png(img), "count": len(items),
                "size": img.size}
    except Exception as e:                                       # noqa: BLE001
        return _err("menucard", e)
