# -*- coding: utf-8 -*-
"""
earn_studio.py — 💰 EARN STUDIO (v76) — 5 NAYE PREMIUM KAMAAI WALE TOOLS
=====================================================================
Ye 5 tools isliye chune gaye hain kyunki India me inki maang ROZ / MAHINE ki
hoti hai — matlab user baar-baar aayega ( subscriptions / VIP bechne ke liye
sabse best). Aur ye sab 100% OFFLINE hain (koi API kharidni nahi padti):

  1. 🧾 RENT RECEIPT      — kiraya rasid (HRA tax claim ke liye). Har mahine
                            chahiye -> sabse zyada baar chalta hai.
                            Ek A4 page par 3 receipt (receipt-book jaisa).
  2. 📒 UDHAAR KHATA      — dukaan ka ledger (kaun kitna dena hai).
                            Har kirana/dukaandaar ki roz ki zaroorat.
  3. 🎨 OFFER POSTER      — tyohar/sale ka poster (Diwali, Holi, 50% OFF).
                            WhatsApp status + dukaan ke bahar lagane layak.
  4. 💼 QUOTATION         — professional estimate/rate-quote (GST ke saath).
                            Contractor, electrician, designer sabko chahiye.
  5. 📈 PROFIT CARD       — business ka munafa/nuksan + margin + health.
                            Dukaandaar ko "hamara business kaisa chal raha hai".

Har tool:
  • A4 @ 200 DPI ya HD poster — seedha print/WhatsApp ke liye
  • Hindi + English DONO (ScriptFont se mixed text perfect)
  • PNG + PDF dono banta hai (bot.py dono bhejta hai)
  • KABHI CRASH NAHI — har function try/except me, hamesha dict return

----------------------------------------------------------------------
USE:
    from modules.earn_studio import rent_receipt_image, khata_image, ...
    res = rent_receipt_image({...})      # {"ok":True,"png":bytes,...}
----------------------------------------------------------------------
"""
from __future__ import annotations

import io
import logging
from datetime import datetime

from modules.business_tools import (
    INK,
    LINE,
    MUTED,
    WHITE,
    FAINT,
    ScriptFont,
    _blank,
    _brand,
    _hex,
    _num,
    _save_png,
    _today,
    amount_words,
    money,
    to_pdf,
)

log = logging.getLogger("utility-super-bot.earn-studio")

__all__ = [
    "rent_receipt_image", "khata_image", "poster_image",
    "quotation_image", "profit_card_image",
    "EARN_MENU", "EARN_ORDER",
]

# =====================================================================
#  TOOL LIST (bot.py isi se menu banata hai)
# =====================================================================
EARN_ORDER = [
    "biz_rent", "biz_khata", "biz_poster", "biz_quote", "biz_profit",
]

EARN_MENU = {
    "biz_rent":   ("🧾", "Rent Receipt",      "kiraya rasid · HRA claim · 3 page me"),
    "biz_khata":  ("📒", "Udhaar Khata",      "dukaan ka ledger · kaun kitna dena hai"),
    "biz_poster": ("🎨", "Offer Poster",      "Diwali · sale · 50% OFF · HD status"),
    "biz_quote":  ("💼", "Quotation",         "professional estimate · GST ke saath"),
    "biz_profit": ("📈", "Profit Card",       "munafa · margin · business health"),
}


def _err(where: str, e: BaseException) -> dict:
    return {"ok": False, "error": f"{where}: {type(e).__name__}: {str(e)[:160]}"}


def _A4():
    """A4 @ 200 DPI (print quality)."""
    return int(8.27 * 200), int(11.69 * 200)


def _split_money(v: str):
    """'Sugar:48:55' -> (name, qty, rate) — business_tools ka hi tareeka."""
    import re as _re
    t = str(v or "").strip()
    if not t:
        return None
    parts = [p.strip() for p in _re.split(r"[:|]", t) if p.strip() != ""]
    if len(parts) >= 3:
        return (parts[0], _num(parts[1], 1), _num(parts[2], 0))
    if len(parts) == 2:
        return (parts[0], 1.0, _num(parts[1], 0))
    return None


# =====================================================================
#  1. 🧾 RENT RECEIPT — 3 receipt ek A4 page par (receipt-book style)
# =====================================================================
def rent_receipt_image(d: dict) -> dict:
    """Kiraya ki rasid — HRA tax claim ke liye. Ek page par 3 receipt.

    d = {owner, tenant, address, amount, month, from_month, to_month,
         mode, note, accent, pan}
    """
    try:
        from PIL import ImageDraw
        W, H = _A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)

        amount = _num(d.get("amount"), 0)
        if amount <= 0:
            return {"ok": False,
                    "error": "kiraye ki rakam (amount) 0 hai — sahi number likhiye"}
        owner = str(d.get("owner") or "MAKAN MALIK KA NAAM")[:44]
        tenant = str(d.get("tenant") or "KIRAYEDAAR KA NAAM")[:44]
        addr = str(d.get("address") or "Makan / flat ka poora pata")[:70]
        month = str(d.get("month") or datetime.now().strftime("%B %Y"))[:26]
        mode = str(d.get("mode") or "Cash")[:22]
        pan = str(d.get("pan") or "")[:14]
        acc = _hex(d.get("accent"), (30, 64, 124))
        M = 60
        gap = 24
        rh = (H - 2 * M - 2 * gap) // 3          # ek receipt ki height

        for i in range(3):
            y0 = M + i * (rh + gap)
            # ---------- outer border (kati hui receipt jaisi dashed) ----------
            dr.rectangle([M, y0, W - M, y0 + rh], outline=LINE, width=2)
            # ---------- header ----------
            dr.rectangle([M, y0, W - M, y0 + 92], fill=acc)
            ScriptFont(38, True).draw(dr, (M + 24, y0 + 22), "RENT RECEIPT", WHITE)
            ScriptFont(30, True).draw_right(dr, W - M - 24,
                                            f"No. {int(_num(d.get('start_no'), 1)) + i}",
                                            WHITE, y0 + 28)
            # ---------- body ----------
            by = y0 + 92
            # Received from
            ScriptFont(23).draw(dr, (M + 28, by + 26), "RECEIVED FROM (प्राप्त किया)", MUTED)
            ScriptFont(33, True).draw(dr, (M + 28, by + 56), tenant, INK)
            dr.line([M + 28, by + 104, W - M - 28, by + 104], fill=LINE, width=2)

            # Amount (bada)
            ScriptFont(23).draw(dr, (M + 28, by + 122), "AMOUNT (राशि)", MUTED)
            ScriptFont(52, True).draw(dr, (M + 28, by + 150),
                                      f"Rs. {money(amount)}", acc)
            # stamp box (right side) — asli rasid jaisa
            bx1 = W - M - 300
            dr.rectangle([bx1, by + 122, W - M - 28, by + 232],
                         outline=acc, width=3)
            ScriptFont(20).draw_center(dr, (bx1, W - M - 28),
                                       "REVENUE STAMP", MUTED, by + 132)
            ScriptFont(20).draw_center(dr, (bx1, W - M - 28),
                                       "(₹1 स्टाम्प लगायें)", FAINT, by + 180)

            # month / mode — do column
            colw = (W - 2 * M - 56) // 2
            rows = [("FOR THE MONTH OF (महीना)", month),
                    ("PAYMENT MODE (भुगतान)", mode)]
            for j, (lab, val) in enumerate(rows):
                cx = M + 28 + j * (colw + 20)
                ScriptFont(22).draw(dr, (cx, by + 250), lab, MUTED)
                ScriptFont(30, True).draw(dr, (cx, by + 280), val[:24], INK)

            # property address
            ScriptFont(22).draw(dr, (M + 28, by + 326),
                                "PROPERTY ADDRESS (संपत्ति का पता)", MUTED)
            _ay = by + 352
            for ln in ScriptFont(26).wrap(addr, W - 2 * M - 56, 2):
                ScriptFont(26).draw(dr, (M + 28, _ay), ln, INK)
                _ay += 34

            # words
            ScriptFont(22).draw(dr, (M + 28, by + 424),
                                "AMOUNT IN WORDS (शब्दों में)", MUTED)
            _wy = by + 450
            for ln in ScriptFont(26).wrap(amount_words(amount) + " Only",
                                          W - 2 * M - 56, 2):
                ScriptFont(26, True).draw(dr, (M + 28, _wy), ln, INK)
                _wy += 34

            # landlord line + signature
            sy = y0 + rh - 132
            dr.line([M + 28, sy, M + 28 + 520, sy], fill=LINE, width=2)
            ScriptFont(21).draw(dr, (M + 28, sy + 12),
                                "Landlord / मकान मालिक", MUTED)
            ScriptFont(28, True).draw(dr, (M + 28, sy - 40), owner[:34], INK)
            if pan:
                ScriptFont(23).draw_right(dr, W - M - 28, f"PAN: {pan}", MUTED,
                                          sy + 10)
            ScriptFont(20).draw_right(dr, W - M - 28,
                                      f"{_brand()} · {_today()}", FAINT, sy + 46)
            # katne wali line (dotted)
            for xx in range(M, W - M, 18):
                dr.line([xx, y0 + rh + gap // 2, xx + 8, y0 + rh + gap // 2],
                        fill=LINE, width=2)

        return {"ok": True, "png": _save_png(img), "amount": amount,
                "count": 3, "size": img.size,
                "notice": "₹1 ka revenue stamp laga kar sign karein"}
    except Exception as e:                                       # noqa: BLE001
        return _err("rent_receipt", e)


# =====================================================================
#  2. 📒 UDHAAR KHATA — dukaan ka ledger
# =====================================================================
def khata_image(d: dict) -> dict:
    """Customer ka udhaar khata — kitna liya, kitna diya, kitna baaki.

    d = {shop, customer, phone, entries:[(date, item, udhaar, jama)], note, accent}
    entries simple text se bhi ban jaate hain: "01-09 aata 500, 05-09 jama 300"
    """
    try:
        from PIL import ImageDraw
        import re as _re
        W, H = _A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        acc = _hex(d.get("accent"), (120, 44, 20))
        M = 60
        shop = str(d.get("shop") or "DUKAAN KA NAAM")[:46]
        cust = str(d.get("customer") or "Customer ka naam")[:40]
        phone = str(d.get("phone") or "")[:16]

        entries = []
        raw = d.get("entries")
        if isinstance(raw, str):
            # "01-09 aata 500 | 05-09 jama 300" ya "01-09, aata, 500, 0"
            for chunk in _re.split(r"[|\n;]+", raw):
                chunk = chunk.strip()
                if not chunk:
                    continue
                bits = [b.strip() for b in _re.split(r"[,]+", chunk) if b.strip()]
                if len(bits) >= 4:
                    entries.append((bits[0][:12], bits[1][:26],
                                    _num(bits[2], 0), _num(bits[3], 0)))
                elif len(bits) == 3:
                    low = bits[1].lower()
                    if "jama" in low or "paid" in low or "diya" in low:
                        entries.append((bits[0][:12], bits[1][:26], 0.0,
                                        _num(bits[2], 0)))
                    else:
                        entries.append((bits[0][:12], bits[1][:26],
                                        _num(bits[2], 0), 0.0))
                elif len(bits) == 2:
                    entries.append((bits[0][:12], "udhaar", _num(bits[1], 0), 0.0))
        elif isinstance(raw, (list, tuple)):
            for it in raw:
                try:
                    if isinstance(it, dict):
                        entries.append((str(it.get("date") or "")[:12],
                                        str(it.get("item") or "")[:26],
                                        _num(it.get("udhaar"), 0),
                                        _num(it.get("jama"), 0)))
                    else:
                        a, b, c, e2 = (list(it) + ["", "", 0, 0])[:4]
                        entries.append((str(a)[:12], str(b)[:26],
                                        _num(c, 0), _num(e2, 0)))
                except Exception:                                # noqa: BLE001
                    continue
        if not entries:
            return {"ok": False,
                    "error": ("khata khali hai — kam se kam ek entry likhiye "
                              "(jaise: 01-09, aata, 500, 0)")}

        # ---------- header ----------
        dr.rectangle([0, 0, W, 132], fill=acc)
        ScriptFont(42, True).draw(dr, (M, 30), shop, WHITE)
        ScriptFont(30, True).draw_right(dr, W - M, "UDHAAR KHATA", WHITE, 36)
        ScriptFont(24).draw_right(dr, W - M, "बाकी हिसाब", WHITE, 82)

        # ---------- customer box ----------
        cy = 172
        dr.rectangle([M, cy, W - M, cy + 118], fill=(252, 248, 244), outline=LINE,
                     width=2)
        ScriptFont(23).draw(dr, (M + 26, cy + 18), "CUSTOMER (ग्राहक)", MUTED)
        ScriptFont(34, True).draw(dr, (M + 26, cy + 48), cust, INK)
        if phone:
            ScriptFont(28).draw_right(dr, W - M - 26, f"Ph: {phone}", INK, cy + 52)
        ScriptFont(22).draw(dr, (M + 26, cy + 88), f"Statement date: {_today()}",
                            MUTED)

        # ---------- table ----------
        ty = 330
        row_h = 62
        colx = [M + 26, M + 250, M + 780, M + 1080, M + 1340]
        hdr = ["DATE", "PARTICULARS (ब्यौरा)", "UDHAAR (उधार)", "JAMA (जमा)",
               "BALANCE"]
        dr.rectangle([M, ty, W - M, ty + row_h], fill=acc)
        for j, h in enumerate(hdr):
            x = colx[j]
            if j >= 2:
                ScriptFont(24, True).draw_right(dr, (W - M - 26 if j == 4
                                                     else colx[j] + 240), h, WHITE,
                                                ty + 17)
            else:
                ScriptFont(24, True).draw(dr, (x, ty + 17), h, WHITE)

        tot_u = tot_j = 0.0
        bal = 0.0
        ry = ty + row_h
        shown = 0
        for (dt, item, u, j) in entries:
            if ry + row_h > H - 320:
                break
            bal = round(bal + _num(u, 0) - _num(j, 0), 2)
            tot_u += _num(u, 0)
            tot_j += _num(j, 0)
            if shown % 2 == 1:
                dr.rectangle([M, ry, W - M, ry + row_h], fill=(252, 250, 247))
            ScriptFont(25).draw(dr, (colx[0], ry + 16), str(dt)[:12], INK)
            ScriptFont(25).draw(dr, (colx[1], ry + 16), str(item)[:26], INK)
            ScriptFont(25).draw_right(dr, colx[2] + 240,
                                      money(u) if u else "—", (170, 60, 30), ry + 16)
            ScriptFont(25).draw_right(dr, colx[3] + 240,
                                      money(j) if j else "—", (20, 110, 60), ry + 16)
            ScriptFont(26, True).draw_right(dr, W - M - 26, money(bal), INK, ry + 14)
            dr.line([M, ry, W - M, ry], fill=LINE, width=1)
            ry += row_h
            shown += 1

        # ---------- total ----------
        dr.rectangle([M, ry, W - M, ry + row_h + 14], fill=(244, 232, 220))
        ScriptFont(27, True).draw(dr, (colx[0], ry + 18), "TOTAL", INK)
        ScriptFont(26, True).draw_right(dr, colx[2] + 240, money(tot_u),
                                        (170, 60, 30), ry + 18)
        ScriptFont(26, True).draw_right(dr, colx[3] + 240, money(tot_j),
                                        (20, 110, 60), ry + 18)
        ny = ry + row_h + 14

        # ---------- NET DUE (sabse bada) ----------
        due = round(tot_u - tot_j, 2)
        dy = ny + 46
        good = due <= 0
        bar = (20, 110, 60) if good else (150, 40, 30)
        dr.rectangle([M, dy, W - M, dy + 150], fill=bar)
        ScriptFont(34, True).draw(dr, (M + 30, dy + 26),
                                  "NET BAaki (कुल बाकी)" if not good
                                  else "ADVANCE / EXTRA JAMA", WHITE)
        ScriptFont(58, True).draw_right(dr, W - M - 30,
                                        f"Rs. {money(abs(due))}", WHITE, dy + 20)
        ScriptFont(24).draw(dr, (M + 30, dy + 100),
                            "Amount in words: " + amount_words(abs(due)), WHITE)

        # ---------- note ----------
        note = str(d.get("note") or "").strip() or (
            "Ye khata dukaan ke record se banaya gaya hai. Koi bhi gadbad "
            "7 din ke andar batayein.")
        nty = dy + 200
        dr.rectangle([M, nty, W - M, nty + 190], fill=(250, 250, 250),
                     outline=LINE, width=2)
        ScriptFont(24, True).draw(dr, (M + 26, nty + 18), "NOTE / शर्तें", MUTED)
        _ny2 = nty + 62
        for ln in ScriptFont(25).wrap(note, W - 2 * M - 52, 4):
            ScriptFont(25).draw(dr, (M + 26, _ny2), ln, MUTED)
            _ny2 += 34

        ScriptFont(23).draw(dr, (M, H - 150), "Customer signature", MUTED)
        dr.line([M, H - 180, M + 420, H - 180], fill=INK, width=2)
        ScriptFont(23).draw_right(dr, W - M, "Shopkeeper sign", MUTED, H - 150)
        dr.line([W - M - 420, H - 180, W - M, H - 180], fill=INK, width=2)
        ScriptFont(21).draw(dr, (M, H - 96),
                            f"Computer generated · {_brand()} · {_today()}", FAINT)

        return {"ok": True, "png": _save_png(img), "amount": due,
                "count": shown, "size": img.size,
                "notice": (" Yeh khata sirf dukaan ke record ke liye hai.")}
    except Exception as e:                                       # noqa: BLE001
        return _err("khata", e)


# =====================================================================
#  3. 🎨 OFFER POSTER — tyohar / sale (HD, WhatsApp status ready)
# =====================================================================
_POSTER_THEMES = {
    "diwali":  ((28, 20, 60), (255, 176, 59), "✨ शुभ दीपावली ✨"),
    "holi":    ((70, 16, 80), (255, 120, 180), "🎨 होली की हार्दिक शुभकामनाएँ"),
    "sale":    ((150, 20, 30), (255, 214, 102), "🔥 MEGA SALE 🔥"),
    "newyear": ((10, 40, 70), (120, 220, 255), "🎊 नव वर्ष की शुभकामनाएँ 🎊"),
    "eid":     ((8, 70, 55), (240, 220, 130), "🌙 ईद मुबारक 🌙"),
    "republic":((12, 40, 90), (255, 153, 51), "🇮🇳 गणतंत्र दिवस 🇮🇳"),
    "independence": ((12, 60, 40), (255, 255, 255), "🇮🇳 स्वतंत्रता दिवस 🇮🇳"),
    "opening": ((110, 30, 20), (255, 205, 120), "🎉 GRAND OPENING 🎉"),
    "custom":  ((20, 24, 40), (255, 200, 90), "⭐ SPECIAL OFFER ⭐"),
}


def poster_image(d: dict) -> dict:
    """Dukaan ka offer/festival poster — HD (1080x1920), status + print dono.

    d = {shop, offer, headline, theme, phone, address, dates, items, accent}
    """
    try:
        from PIL import ImageDraw
        W, H = 1080, 1920                      # HD vertical (WhatsApp status)
        theme = str(d.get("theme") or "sale").lower().strip()
        bg, gold, festival = _POSTER_THEMES.get(theme, _POSTER_THEMES["sale"])
        bg = _hex(d.get("accent"), bg)
        img = _blank(W, H, bg)
        dr = ImageDraw.Draw(img)

        shop = str(d.get("shop") or "आपकी दुकान")[:30]
        offer = str(d.get("offer") or "50% OFF")[:22]
        headline = str(d.get("headline") or festival)[:34]
        phone = str(d.get("phone") or "")[:16]
        addr = str(d.get("address") or "")[:52]
        dates = str(d.get("dates") or "")[:40]

        # ---------- decorative border ----------
        for k, (x1, y1, x2, y2) in enumerate((
                (34, 34, W - 34, H - 34), (48, 48, W - 48, H - 48))):
            dr.rectangle([x1, y1, x2, y2], outline=gold, width=3 if k == 0 else 1)

        # ---------- corner decoration ----------
        for (cx, cy) in ((34, 34), (W - 34, 34), (34, H - 34), (W - 34, H - 34)):
            r = 46
            dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=gold)

        # ---------- festival line ----------
        ScriptFont(52, True).draw_center(dr, (0, W), headline, gold, 170)

        # ---------- OFFER (sabse bada) ----------
        oy = 300
        # ribbon
        dr.rectangle([90, oy, W - 90, oy + 300], fill=gold)
        ScriptFont(150, True).draw_center(dr, (0, W), offer, bg, oy + 46)

        # ---------- shop name ----------
        ScriptFont(74, True).draw_center(dr, (0, W), shop, WHITE, 690)

        # ---------- items / details ----------
        items_txt = str(d.get("items") or "").strip()
        iy = 830
        if items_txt:
            dr.rectangle([140, iy - 30, W - 140, iy + 30 +
                          70 * min(5, len(items_txt.split(",")))],
                         fill=(255, 255, 255, 0))
            _iy = iy
            for chunk in items_txt.split(","):
                chunk = chunk.strip()
                if not chunk or _iy > iy + 340:
                    break
                ScriptFont(42).draw_center(dr, (0, W), "• " + chunk[:40],
                                           (235, 240, 250), _iy)
                _iy += 66
            iy = _iy + 40

        # ---------- dates ----------
        if dates:
            ScriptFont(46, True).draw_center(dr, (0, W), dates, gold, iy + 30)
            iy += 110

        # ---------- address ----------
        if addr:
            _ay = iy + 40
            for ln in ScriptFont(38).wrap(addr, W - 260, 2):
                ScriptFont(38).draw_center(dr, (0, W), ln, (220, 226, 240), _ay)
                _ay += 50
            iy = _ay

        # ---------- phone (nyauta) ----------
        py = H - 300
        dr.rounded_rectangle([190, py, W - 190, py + 116], radius=58, fill=gold)
        label = ("📞 " + phone) if phone else "📞 आज ही आएं"
        ScriptFont(58, True).draw_center(dr, (0, W), label, bg, py + 24)

        ScriptFont(28).draw_center(dr, (0, W),
                                   f"{_brand()} · {_today()}",
                                   (180, 190, 210), H - 120)

        return {"ok": True, "png": _save_png(img), "size": img.size,
                "notice": None}
    except Exception as e:                                       # noqa: BLE001
        return _err("poster", e)


# =====================================================================
#  4. 💼 QUOTATION — professional estimate (GST ke saath)
# =====================================================================
def quotation_image(d: dict) -> dict:
    """Professional quotation / estimate — contractor · designer · dukaan.

    d = {shop, tagline, address, phone, email, gstin, upi, to, to_addr,
         items:[{name,qty,rate}], gst, valid, terms, note, accent}
    """
    try:
        from PIL import ImageDraw
        W, H = _A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        M = 64
        acc = _hex(d.get("accent"), (24, 58, 110))

        items = d.get("items") or []
        if isinstance(items, str):
            parsed = []
            for chunk in items.replace("|", ",").split(","):
                got = _split_money(chunk)
                if got:
                    parsed.append({"name": got[0], "qty": got[1], "rate": got[2]})
            items = parsed
        if not items:
            return {"ok": False,
                    "error": ("quotation me koi item nahi mila — "
                              "aise likhein: LED 4x120, Wire 1x450")}

        shop = str(d.get("shop") or "YOUR COMPANY")[:44]
        to = str(d.get("to") or "Client ka naam")[:40]
        gst_rate = _num(d.get("gst"), 18.0)
        valid = str(d.get("valid") or "15 din")[:24]

        # ---------- header ----------
        dr.rectangle([0, 0, W, 168], fill=acc)
        ScriptFont(46, True).draw(dr, (M, 26), shop, WHITE)
        tagline = str(d.get("tagline") or "")[:50]
        if tagline:
            ScriptFont(26).draw(dr, (M, 86), tagline, (200, 218, 240))
        ScriptFont(56, True).draw_right(dr, W - M, "QUOTATION", WHITE, 34)
        ScriptFont(26).draw_right(dr, W - M,
                                  f"No. QT-{datetime.now().strftime('%y%m%d%H%M')}",
                                  (200, 218, 240), 106)

        # ---------- from / to ----------
        y = 212
        bh = 190
        half = (W - 2 * M - 30) // 2
        boxes = (
            ("FROM (हम)", [shop,
                           str(d.get("address") or "—")[:40],
                           ("Ph: " + str(d.get("phone") or "—"))[:40],
                           ("GSTIN: " + str(d.get("gstin") or "—"))[:40]]),
            ("TO (ग्राहक)", [to,
                             str(d.get("to_addr") or "—")[:40],
                             ("Ph: " + str(d.get("to_phone") or "—"))[:40],
                             f"Date: {_today()}"]),
        )
        for i, (title, lines) in enumerate(boxes):
            x0 = M + i * (half + 30)
            dr.rectangle([x0, y, x0 + half, y + bh], fill=(247, 250, 253),
                         outline=LINE, width=2)
            ScriptFont(24, True).draw(dr, (x0 + 22, y + 14), title, acc)
            _ly = y + 52
            for ln in lines:
                ScriptFont(26).draw(dr, (x0 + 22, _ly), str(ln)[:38], INK)
                _ly += 34

        # ---------- items table ----------
        ty = y + bh + 46
        row_h = 64
        cols = [M + 24, M + 640, M + 820, M + 1030, W - M - 24]
        dr.rectangle([M, ty, W - M, ty + row_h], fill=acc)
        for lbl, x, right in (("DESCRIPTION (विवरण)", cols[0], False),
                              ("QTY", cols[1] + 60, True),
                              ("RATE", cols[2] + 60, True),
                              ("AMOUNT", cols[4], True)):
            if right:
                ScriptFont(25, True).draw_right(dr, x, lbl, WHITE, ty + 17)
            else:
                ScriptFont(25, True).draw(dr, (x, ty + 17), lbl, WHITE)

        subtotal = 0.0
        ry = ty + row_h
        for i, it in enumerate(items[:16]):
            qty = _num(it.get("qty"), 1)
            rate = _num(it.get("rate"), 0)
            amt = round(qty * rate, 2)
            subtotal += amt
            if i % 2 == 1:
                dr.rectangle([M, ry, W - M, ry + row_h], fill=(249, 251, 254))
            ScriptFont(26).draw(dr, (cols[0], ry + 16),
                                str(it.get("name") or "Item")[:40], INK)
            ScriptFont(26).draw_right(dr, cols[1] + 60, f"{qty:g}", INK, ry + 16)
            ScriptFont(26).draw_right(dr, cols[2] + 60, money(rate), INK, ry + 16)
            ScriptFont(26, True).draw_right(dr, cols[4], money(amt), INK, ry + 16)
            dr.line([M, ry, W - M, ry], fill=LINE, width=1)
            ry += row_h

        subtotal = round(subtotal, 2)
        gst_amt = round(subtotal * gst_rate / 100.0, 2)
        total = round(subtotal + gst_amt, 2)

        # ---------- totals ----------
        trow = 62
        summary = [("SUBTOTAL (कुल)", money(subtotal), False),
                   (f"GST @ {gst_rate:g}%", money(gst_amt), False),
                   ("TOTAL (कुल देय)", f"Rs. {money(total)}", True)]
        for lab, val, big in summary:
            if big:
                dr.rectangle([M + 700, ry, W - M, ry + trow + 18], fill=acc)
                ScriptFont(30, True).draw(dr, (M + 726, ry + 22), lab, WHITE)
                ScriptFont(38, True).draw_right(dr, W - M - 24, val, WHITE, ry + 16)
                ry += trow + 18
            else:
                ScriptFont(27).draw_right(dr, W - M - 240, lab, MUTED, ry + 14)
                ScriptFont(27, True).draw_right(dr, W - M - 24, val, INK, ry + 14)
                ry += trow

        # ---------- words ----------
        ScriptFont(24).draw(dr, (M, ry + 16), "AMOUNT IN WORDS", MUTED)
        _wy = ry + 46
        for ln in ScriptFont(26, True).wrap(amount_words(total) + " Only",
                                            W - 2 * M, 2):
            ScriptFont(26, True).draw(dr, (M, _wy), ln, INK)
            _wy += 34

        # ---------- validity + terms ----------
        vy = _wy + 40
        dr.rectangle([M, vy, W - M, vy + 84], fill=(255, 247, 230),
                     outline=(240, 200, 120), width=2)
        ScriptFont(27, True).draw(dr, (M + 22, vy + 24),
                                  f"⏳ Ye quotation {valid} tak maany hai.",
                                  (150, 100, 20))

        terms = str(d.get("terms") or "").strip() or (
            "1) Rate upar likhe gaye kaam/saaman ke liye hain. "
            "2) Kaam shuru karne se pehle 50% advance lagega. "
            "3) GST actual ke hisaab se lagega.")
        tty = vy + 124
        dr.rectangle([M, tty, W - M, tty + 210], fill=(248, 250, 252),
                     outline=LINE, width=2)
        ScriptFont(25, True).draw(dr, (M + 22, tty + 16),
                                  "TERMS & CONDITIONS (शर्तें)", MUTED)
        _ty2 = tty + 58
        for ln in ScriptFont(25).wrap(terms, W - 2 * M - 44, 4):
            ScriptFont(25).draw(dr, (M + 22, _ty2), ln, INK)
            _ty2 += 34

        # ---------- footer ----------
        upi = str(d.get("upi") or "").strip()
        fy = H - 260
        dr.line([M, fy, W - M, fy], fill=LINE, width=2)
        if upi:
            ScriptFont(26).draw(dr, (M, fy + 20), f"UPI: {upi[:40]}", INK)
        ScriptFont(24).draw(dr, (M, fy + 62),
                            "Thank you for your business!", MUTED)
        ScriptFont(26, True).draw_right(dr, W - M, f"For {shop[:26]}", INK, fy + 70)
        dr.line([W - M - 400, fy + 130, W - M, fy + 130], fill=INK, width=2)
        ScriptFont(23).draw_right(dr, W - M, "Authorised Signatory", MUTED,
                                  fy + 140)
        ScriptFont(21).draw(dr, (M, H - 74),
                            f"Computer generated · {_brand()} · {_today()}", FAINT)

        return {"ok": True, "png": _save_png(img), "amount": total,
                "count": len(items[:16]), "size": img.size}
    except Exception as e:                                       # noqa: BLE001
        return _err("quotation", e)


# =====================================================================
#  5. 📈 PROFIT CARD — business health (munafa / margin)
# =====================================================================
def profit_card_image(d: dict) -> dict:
    """Business ka profit & loss card — margin, health, breakdown.

    d = {shop, month, sale, cost, expense, expense_items, note, accent}
    expense_items: "kiraya 8000, bijli 2500, staff 15000" (optional)
    """
    try:
        from PIL import ImageDraw
        W, H = _A4()
        img = _blank(W, H, WHITE)
        dr = ImageDraw.Draw(img)
        M = 64
        shop = str(d.get("shop") or "AAPKA BUSINESS")[:40]
        month = str(d.get("month") or datetime.now().strftime("%B %Y"))[:24]
        sale = _num(d.get("sale"), 0)
        cost = _num(d.get("cost"), 0)
        expense = _num(d.get("expense"), 0)

        if sale <= 0:
            return {"ok": False,
                    "error": ("bikri (sale) 0 hai — is mahine ki total bikri "
                              "likhiye, jaise: 250000")}

        gross = round(sale - cost, 2)
        net = round(gross - expense, 2)
        gm = round(100.0 * gross / sale, 1) if sale else 0.0
        nm = round(100.0 * net / sale, 1) if sale else 0.0

        if nm >= 20:
            verdict, vcol = ("🟢 BAHUT ACCHA — business strong hai", (20, 110, 60))
        elif nm >= 10:
            verdict, vcol = ("🟡 THEEK HAI — sudhaar ki gunjayish hai", (170, 120, 20))
        elif nm >= 0:
            verdict, vcol = ("🟠 KAM MOBILE — kharcha kam karein", (190, 100, 20))
        else:
            verdict, vcol = ("🔴 GHATA HO RAHA HAI — turant dhyaan dein", (160, 35, 30))

        acc = _hex(d.get("accent"), (18, 70, 120))

        # ---------- header ----------
        dr.rectangle([0, 0, W, 150], fill=acc)
        ScriptFont(44, True).draw(dr, (M, 28), shop, WHITE)
        ScriptFont(26).draw(dr, (M, 88), f"Business Health Card · {month}",
                            (200, 220, 245))
        ScriptFont(38, True).draw_right(dr, W - M, "P & L", WHITE, 40)

        # ---------- 3 big numbers ----------
        by = 196
        bh = 210
        cw = (W - 2 * M - 2 * 26) // 3
        cards = (("TOTAL BIKRI (SALE)", money(sale), acc),
                 ("LAGAAT (COST)", money(cost), (140, 70, 30)),
                 ("SAFA MUNFAFA (GROSS)", money(gross),
                  (20, 110, 60) if gross >= 0 else (170, 40, 30)))
        for i, (lab, val, col) in enumerate(cards):
            x0 = M + i * (cw + 26)
            dr.rectangle([x0, by, x0 + cw, by + bh], fill=(247, 250, 253),
                         outline=LINE, width=2)
            dr.rectangle([x0, by, x0 + 8, by + bh], fill=col)
            ScriptFont(24).draw(dr, (x0 + 28, by + 22), lab, MUTED)
            ScriptFont(46, True).draw(dr, (x0 + 28, by + 60), f"Rs. {val}", col)
            pct = round(100.0 * (sale if i == 0 else cost if i == 1 else gross)
                        / sale, 1) if sale else 0.0
            ScriptFont(24).draw(dr, (x0 + 28, by + 140), f"{pct:g}% of bikri", FAINT)

        # ---------- NET PROFIT (hero) ----------
        ny = by + bh + 46
        dr.rectangle([M, ny, W - M, ny + 200], fill=vcol)
        ScriptFont(34, True).draw(dr, (M + 30, ny + 26), "NET MUNFAFA (शुद्ध लाभ)",
                                  WHITE)
        ScriptFont(78, True).draw_right(dr, W - M - 30, f"Rs. {money(net)}",
                                        WHITE, ny + 14)
        ScriptFont(27).draw(dr, (M + 30, ny + 90), f"Margin: {nm:g}% of bikri",
                            WHITE)
        ScriptFont(24).draw(dr, (M + 30, ny + 132),
                            "Amount in words: " + amount_words(abs(net)),
                            (240, 245, 255))
        ScriptFont(30, True).draw_right(dr, W - M - 30, verdict, WHITE, ny + 130)

        # ---------- breakdown bar ----------
        bry = ny + 250
        dr.rectangle([M, bry, W - M, bry + 70], fill=(235, 238, 244))
        total_bar = max(1.0, sale)
        w_cost = int((W - 2 * M) * min(1.0, cost / total_bar))
        w_exp = int((W - 2 * M) * min(1.0, expense / total_bar))
        w_net = max(0, (W - 2 * M) - w_cost - w_exp)
        x = M
        for w, col in ((w_cost, (190, 90, 40)), (w_exp, (120, 130, 150)),
                       (w_net, (30, 150, 90))):
            if w > 0:
                dr.rectangle([x, bry, x + w, bry + 70], fill=col)
                x += w
        ly = bry + 92
        legend = (("■ Lagaat (cost)", (190, 90, 40)),
                  ("■ Kharcha (expense)", (120, 130, 150)),
                  ("■ Munafa (profit)", (30, 150, 90)))
        lx = M
        for txt, col in legend:
            ScriptFont(26).draw(dr, (lx, ly), txt, col)
            lx += int(ScriptFont(26).width(txt)) + 46

        # ---------- expense list ----------
        exy = ly + 80
        raw_exp = str(d.get("expense_items") or "").strip()
        exp_list = []
        if raw_exp:
            for chunk in raw_exp.split(","):
                got = _split_money(chunk)
                if got:
                    exp_list.append((got[0], got[2]))
        if not exp_list and expense > 0:
            exp_list = [("Total kharcha (विवरण नहीं दिया)", expense)]
        if exp_list:
            dr.rectangle([M, exy, W - M, exy + 70 + 62 * min(8, len(exp_list))],
                         fill=(250, 251, 253), outline=LINE, width=2)
            ScriptFont(26, True).draw(dr, (M + 24, exy + 18),
                                      "KHARCHE (EXPENSES)", MUTED)
            _ey = exy + 66
            for nm_i, amt_i in exp_list[:8]:
                ScriptFont(26).draw(dr, (M + 24, _ey), str(nm_i)[:34], INK)
                ScriptFont(26, True).draw_right(dr, W - M - 24, money(amt_i),
                                                (150, 60, 40), _ey)
                _ey += 62
            exy = _ey + 20

        # ---------- suggestions ----------
        sug = str(d.get("note") or "").strip()
        if not sug:
            if net < 0:
                sug = ("Bikri se zyada kharcha ho raha hai. Sabse pehle "
                       "kam-munafe wala saaman band karein aur kiraya/staff "
                       "ka kharcha ghataayein.")
            elif nm < 10:
                sug = ("Munafa kam hai. Rate thoda badhaayein ya lagaat "
                       "(purchase) kam karne ki koshish karein — 5% sudhaar "
                       "se hi farq padega.")
            else:
                sug = ("Business accha chal raha hai. Ab jo saaman sabse "
                       "zyada munafa de raha hai, usi par dhyaan dein aur "
                       "stock badhaayein.")
        sy = min(exy, H - 420)
        dr.rectangle([M, sy, W - M, sy + 230], fill=(246, 250, 246),
                     outline=(200, 225, 205), width=2)
        ScriptFont(26, True).draw(dr, (M + 24, sy + 18), "💡 SALAH (SUGGESTION)",
                                  (30, 110, 70))
        _sy = sy + 62
        for ln in ScriptFont(26).wrap(sug, W - 2 * M - 48, 5):
            ScriptFont(26).draw(dr, (M + 24, _sy), ln, INK)
            _sy += 36

        ScriptFont(21).draw(dr, (M, H - 74),
                            f"Computer generated · {_brand()} · {_today()}", FAINT)

        return {"ok": True, "png": _save_png(img), "amount": net,
                "size": img.size,
                "notice": f"Gross margin {gm:g}% · Net margin {nm:g}%"}
    except Exception as e:                                       # noqa: BLE001
        return _err("profit_card", e)


# =====================================================================
#  DISPATCHER (bot.py isi se sahi function chunta hai)
# =====================================================================
_IMAGE_FN = {
    "biz_rent": rent_receipt_image,
    "biz_khata": khata_image,
    "biz_poster": poster_image,
    "biz_quote": quotation_image,
    "biz_profit": profit_card_image,
}


def earn_build(key: str, d: dict) -> dict:
    """Tool key -> image function. Kabhi crash nahi."""
    try:
        fn = _IMAGE_FN.get(str(key or "").strip())
        if fn is None:
            return {"ok": False, "error": "tool nahi mila"}
        return fn(d or {})
    except Exception as e:                                       # noqa: BLE001
        return _err("earn_build", e)


def earn_pdf(res: dict):
    """PNG -> PDF (print ke liye)."""
    try:
        return to_pdf([res["png"]])
    except Exception:                                            # noqa: BLE001
        return None
