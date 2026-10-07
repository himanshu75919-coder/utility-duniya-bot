# -*- coding: utf-8 -*-
"""
PAYGUARD — VIP Payment ko STRICTLY verify karne wala module (v33)
=================================================================
Kaam: payment proof me "kuch bhi" na aaye. 4 layer ka check:

  1) UTR / Transaction ID ka FORMAT check      (12-digit UPI UTR ya 16-22 char bank ref)
  2) UTR DUPLICATE check                        (ek UTR sirf ek hi payment me chalega)
  3) SCREENSHOT check                           (asli app/UI screenshot hai ya photo)
  4) SCREENSHOT DUPLICATE check                (same image dobara use nahi ho sakti)

Screenshot check kaise hota hai (bina internet, bina OCR — fast):
  • App/UI screenshots me bade-flat colour blocks hote hain + seedhi horizontal/vertical lines
    (buttons, cards, separators) + text edges.
  • Camera se khinchi hui photo (selfie/kagaz) me gradient smooth hota hai, seedhi lines nahi hoti.
  In 4 naap se ek score banta hai (0-100) -> 🟢 screenshot / 🟡 shaq / 🔴 photo.

Agar Render par pytesseract (OCR) available ho to extra keyword check bhi hota hai
(payed, success, UTR, ₹ amount, phonepe/gpay/paytm...) — na ho to chup-chaap skip.
"""

import io
import re

try:
    import numpy as np
    from PIL import Image
    _PIL_OK = True
except Exception:
    _PIL_OK = False

# ---------------------------------------------------------------------------
# LIMITS (yahan se tune kar sakte ho)
# ---------------------------------------------------------------------------
MIN_WIDTH = 400          # screenshot kam se kam itna bada ho
MIN_HEIGHT = 400
MIN_KB = 8               # itni chhoti file screenshot nahi hoti
MAX_MB = 8               # isse badi file (mila hua kachra) reject
SHOT_GOOD = 70           # score >= 70 → 🟢 pakka screenshot
SHOT_MAYBE = 40          # 40-69 → 🟡 shaq  |  < 40 → 🔴 photo
MAX_BAD_TRIES = 3        # 3 baar photo bhejne par bhi admin ko chala jayega (flag ke saath)

# OCR keywords (agar tesseract available ho)
PAY_KEYWORDS = [
    "utr", "transaction", "txn", "paid", "success", "successful", "payment",
    "debited", "credited", "amount", "₹", "rs.", "inr", "phonepe", "gpay",
    "google pay", "paytm", "bhim", "upi", "ref no", "reference", "receipt",
    "sent to", "transfer", "completed", "bank",
]


# ===========================================================================
# 1) UTR VALIDATION
# ===========================================================================
_UTR_LABELS = re.compile(r"(utr|ref(erence)?(\s*(no|number|id))?|txn|transaction(\s*id)?|rrn)\s*[:#\-]?\s*", re.I)


def validate_utr(raw: str) -> dict:
    """
    UTR / Transaction ID ko check karta hai.
    Return: {ok, utr, kind, reason}
      ok=True  → sahi format (kind: 'UPI/Bank UTR (12 digit)' ya 'Bank Reference (16-22 char)')
      ok=False → reason me saaf wajah
    """
    raw = raw if isinstance(raw, str) else ("" if raw is None else str(raw))   # v78: bool/int par crash
    text = raw.strip()
    if not text:
        return {"ok": False, "utr": "", "reason": "Khaali hai — UTR number type karke bhejo."}

    cleaned = _UTR_LABELS.sub(" ", text)                    # "UTR: 123456789012" → "123456789012"
    cleaned = re.sub(r"[\s\-\.,#/:]+", "", cleaned).strip()
    up = cleaned.upper()

    if not cleaned:
        return {"ok": False, "utr": "", "reason": "Sirf 'UTR' likha hai — uske baad ka number bhi bhejo."}

    digits_only = re.sub(r"\D", "", cleaned)

    # --- 12 digit = UPI / NEFT / IMPS UTR (sabse common) ---
    if re.fullmatch(r"\d{12}", cleaned):
        if cleaned[0] == "0":
            return {"ok": False, "utr": cleaned, "reason": "A UTR never starts with 0 — please check again."}
        return {"ok": True, "utr": cleaned, "kind": "UPI / Bank UTR (12 digit)"}

    # --- 16-22 char alphanumeric = bank reference ---
    if re.fullmatch(r"[A-Za-z0-9]{16,22}", cleaned) and len(re.findall(r"\d", cleaned)) >= 4:
        return {"ok": True, "utr": up, "kind": "Bank Reference (16-22 char)"}

    # --- common galtiyan, saaf-saaf batao ---
    if re.fullmatch(r"[6-9]\d{9}", digits_only) and len(cleaned) <= 12:
        return {"ok": False, "utr": cleaned,
                "reason": "Ye <b>mobile number</b> lag raha hai (10 digit). UTR aam taur par 12 digit ka hota hai."}
    if len(digits_only) == 10:
        return {"ok": False, "utr": cleaned,
                "reason": "10 digit number UTR nahi hota. UPI app me <b>UTR / Transaction ID</b> 12 digit ka hota hai."}
    if len(cleaned) < 10:
        return {"ok": False, "utr": cleaned, "reason": f"Too short ({len(cleaned)} char) — a UTR is at least 12 digits."}
    if len(cleaned) > 25:
        return {"ok": False, "utr": cleaned, "reason": f"Too long ({len(cleaned)} char) — a UTR is 12-22 characters."}
    if not any(c.isdigit() for c in cleaned):
        return {"ok": False, "utr": cleaned, "reason": "A UTR must contain numbers — not only letters."}
    if re.fullmatch(r"\d{11}|\d{13,15}", cleaned):
        return {"ok": False, "utr": cleaned,
                "reason": f"{len(cleaned)} digit ka number valid UTR nahi hai. UPI app se <b>poora 12 digit UTR</b> copy karo "
                          "(ya bank app se 16-22 character ka reference)."}
    return {"ok": False, "utr": cleaned,
            "reason": "Ye UTR nahi lag raha. Payment app kholo → transaction details → wahan se <b>UTR / Ref No</b> copy karo."}


# ===========================================================================
# 2) SCREENSHOT ANALYSIS
# ===========================================================================
def _ui_metrics(img) -> dict:
    """App/UI jaisi image ke 5 naap (flat blocks, seedhi lines, text edges, dominant colour, text density)."""
    w, h = img.size
    # native resolution par text sharpness (photo blurry hoti hai, screenshot me text sharp hota hai)
    a_full = np.asarray(img.convert("L"), dtype=np.int16)
    fgx = np.abs(np.diff(a_full, axis=1))
    fgy = np.abs(np.diff(a_full, axis=0))
    sharp_full = float(((fgx > 25).mean() + (fgy > 25).mean()) / 2 * 100)
    if w >= h:
        small = img.resize((320, max(1, int(320 * h / w))))
    else:
        small = img.resize((max(1, int(320 * w / h)), 320))
    a = np.asarray(small.convert("L"), dtype=np.int16)

    gx = np.abs(np.diff(a, axis=1))
    gy = np.abs(np.diff(a, axis=0))
    flat = ((gx < 3).mean() + (gy < 3).mean()) / 2 * 100          # bade flat areas
    strong = ((gx > 35).mean() + (gy > 35).mean()) / 2 * 100      # text / sharp edges
    rowlines = (np.abs(np.diff(a.mean(axis=1))) > 6).mean() * 100 # lambi horizontal lines (UI)
    collines = (np.abs(np.diff(a.mean(axis=0))) > 6).mean() * 100 # lambi vertical lines

    q = (a // 16)
    uniq, counts = np.unique(q, return_counts=True)
    dominant = counts.max() / counts.sum() * 100                  # ek hi colour ka hissa (app background)

    return {"flat": float(flat), "strong": float(strong), "rowlines": float(rowlines),
            "collines": float(collines), "dominant": float(dominant), "sharp_full": sharp_full}


def _ocr_keywords(img_bytes: bytes) -> tuple:
    """Agar tesseract ho to screenshot me payment keywords dhoondta hai. (na ho to None)"""
    try:
        import pytesseract  # type: ignore
        txt = pytesseract.image_to_string(Image.open(io.BytesIO(img_bytes))).lower()
    except Exception:
        return None, []
    found = [k for k in PAY_KEYWORDS if k in txt]
    return bool(txt.strip()), found


def analyze_screenshot(img_bytes: bytes, expected_amount=None) -> dict:
    """
    Screenshot asli app/UI ka hai ya camera photo? Score 0-100.
    Return: {ok, score, verdict, label, flags, notes, size, kb}
    """
    size_kb = len(img_bytes) / 1024.0
    if size_kb < MIN_KB:
        return {"ok": False, "score": 0, "verdict": "bad", "label": "🔴 Not a photo — send a screenshot",
                "flags": [f"File is too small ({size_kb:.0f} KB)"], "notes": "", "kb": round(size_kb),
                "size": (0, 0)}
    if size_kb > MAX_MB * 1024:
        return {"ok": False, "score": 0, "verdict": "bad", "label": "🔴 File is too big",
                "flags": [f"{size_kb/1024:.1f} MB — a screenshot is never that big"], "notes": "",
                "kb": round(size_kb), "size": (0, 0)}

    if not _PIL_OK:
        return {"ok": True, "score": 50, "verdict": "maybe", "label": "🟡 Could not check (admin will look)",
                "flags": ["Image engine not available"], "notes": "", "kb": round(size_kb), "size": (0, 0)}

    try:
        img = Image.open(io.BytesIO(img_bytes))
        img = img.convert("RGB")
    except Exception as e:
        return {"ok": False, "score": 0, "verdict": "bad", "label": "🔴 Could not open this image",
                "flags": [str(e)[:80]], "notes": "", "kb": round(size_kb), "size": (0, 0)}

    w, h = img.size
    m = _ui_metrics(img)
    score, flags = 0, []

    # --- a) bada flat/ek-rang area (app background ya card) ---
    if m["dominant"] >= 30:
        score += 25
    elif m["dominant"] >= 20:
        score += 12
    else:
        flags.append("No big plain background block found (photos usually have one)")

    # --- b) seedhi UI lines (button border / separator / card edges) ---
    lines = m["rowlines"] + m["collines"]
    if lines >= 15:
        score += 25
    elif lines >= 6:
        score += 12
    else:
        flags.append("No straight UI lines found")

    # --- c) text ki sharpness (screenshot me text tez hota hai; photo blurry/smooth hoti hai) ---
    if m["sharp_full"] >= 1.5:
        score += 25
    elif m["sharp_full"] >= 0.4:
        score += 12
    else:
        flags.append("No sharp text/number content found (looks like a photo)")

    # --- d) text / sharp edges ---
    if m["strong"] >= 3:
        score += 15
    elif m["strong"] >= 1:
        score += 8
    else:
        flags.append("No screenshot-like detail found")

    # --- e) resolution ---
    if w >= 500 and h >= 500:
        score += 10
    elif w < MIN_WIDTH or h < MIN_HEIGHT:
        flags.append(f"Resolution is too low ({w}×{h})")

    # --- f) OCR (agar available) ---
    ocr_ran, ocr_found = _ocr_keywords(img_bytes)
    if ocr_ran:
        if ocr_found:
            score = min(100, score + 15)
        else:
            score = max(0, score - 20)
            flags.append("No payment words (paid/UTR/₹) found in the screenshot")

    # --- g) amount check (agar amount pata ho) ---
    if expected_amount and ocr_ran:
        # (poora OCR text yahan available nahi rakhte — keyword level par hi rehte hain)
        pass

    score = int(max(0, min(100, score)))
    if score >= SHOT_GOOD:
        verdict, label = "good", "🟢 Looks like a screenshot"
    elif score >= SHOT_MAYBE:
        verdict, label = "maybe", "🟡 Suspicious — the admin should look carefully"
    else:
        verdict, label = "bad", "🔴 This looks like a photo, not a screenshot"

    return {"ok": verdict != "bad", "score": score, "verdict": verdict, "label": label,
            "flags": flags, "notes": f"UI-match {score}%", "kb": round(size_kb), "size": (w, h),
            "ocr_ran": bool(ocr_ran), "ocr_found": ocr_found or []}


# ===========================================================================
# 3) ADMIN CARD (panel me kya dikhega)
# ===========================================================================
def shot_verdict_line(analysis: dict) -> str:
    if not analysis:
        return "❔ Could not check"
    icon = {"good": "🟢", "maybe": "🟡", "bad": "🔴"}.get(analysis.get("verdict"), "❔")
    fl = analysis.get("flags") or []
    txt = f"{icon} <b>Screenshot check:</b> {analysis.get('label', '-')} (score {analysis.get('score', 0)}/100)"
    if fl:
        txt += "\n      • " + "\n      • ".join(str(f)[:70] for f in fl[:3])
    if analysis.get("ocr_ran"):
        found = analysis.get("ocr_found") or []
        txt += f"\n      • OCR: {'✅ payment words found: ' + ', '.join(found[:4]) if found else '❌ no payment words found'}"
    return txt


def admin_payment_card(pay: dict, user_row: dict = None, history: dict = None) -> str:
    """Admin ko dikhne wala strict verification card."""
    import json as _json
    try:
        flags = _json.loads(pay.get("flags") or "{}")
    except Exception:
        flags = {}

    utr_v = validate_utr(pay.get("utr_ref") or "")
    lines = [
        f"🔔 <b>VERIFY THIS PAYMENT — #{pay['id']}</b>",
        "──────────────────────",
        f"👤 <b>User ID:</b> <code>{pay['user_id']}</code>",
        f"🏷️ <b>Username:</b> @{flags.get('username') or 'NoUser'}",
        f"👋 <b>Name:</b> {flags.get('name') or '-'}",
        "──────────────────────",
        f"💎 <b>Plan:</b> {pay.get('plan_name') or pay.get('plan_key')}",
        f"💰 <b>Amount:</b> ₹{pay.get('amount')}",
        f"📅 <b>Days:</b> {pay.get('plan_days')}",
        "──────────────────────",
        f"🧾 <b>UTR:</b> <code>{pay.get('utr_ref')}</code>",
        f"      • Format: {'✅ correct — ' + utr_v['kind'] if utr_v['ok'] else '❌ WRONG: ' + utr_v.get('reason', '')[:90]}",
        f"      • Used before?: {'⚠️ YES (duplicate!)' if flags.get('utr_dup') else '✅ No — it is new'}",
        "──────────────────────",
        f"🖼️ <b>Screenshot:</b> {'✅ Received' if pay.get('shot_file_id') else '❌ Not found'}",
        shot_verdict_line(flags.get("shot") or {}),
        f"      • Same image again?: {'⚠️ YES (duplicate!)' if flags.get('shot_dup') else '✅ No'}",
        "──────────────────────",
        f"🕒 <b>Sent:</b> {pay.get('created_at', '-')}",
    ]
    if isinstance(user_row, dict) and user_row:
        prem = user_row.get("premium_until") or ""
        lines.append(f"👑 <b>User VIP:</b> {'👑 LIFETIME' if prem == 'lifetime' else (str(prem)[:10] if prem else '❌ No')}")
        lines.append(f"⚡ <b>Uses today:</b> {user_row.get('uses_today', 0) if isinstance(user_row, dict) else 0}")
    if history:
        lines.append(f"📜 <b>This user's history:</b> ✅ {history.get('approved', 0)} approved · "
                     f"❌ {history.get('rejected', 0)} rejected · ⏳ {history.get('pending', 0)} pending")
    lines.append("──────────────────────")
    lines.append("🤔 <b>Decision:</b> tap a button below" if not (flags.get("utr_dup") or flags.get("shot_dup"))
                 else "🚨 <b>Careful:</b> a duplicate signal was found — think before approving!")
    return "\n".join(lines)


def user_payment_reply(pay_id: int, plan_name: str, amount: int, analysis: dict) -> str:
    return (
        f"✅ <b>Payment proof submitted!</b>\\n"
        "──────────────────────\\n"
        f"🧾 <b>Payment ID:</b> <code>#{pay_id}</code>\\n"
        f"💎 <b>Plan:</b> {plan_name}\\n"
        f"💰 <b>Amount:</b> ₹{amount}\\n"
        f"{shot_verdict_line(analysis)}\\n"
        "──────────────────────\\n"
        "⏳ Admin check karke VIP chalu kar dega (aam taur par 5-30 minute).\\n"
        f"📌 To check status send <code>/mypay</code>.\\n\\n"
        "<i>UTR aur screenshot sahi ho to jaldi approve hota hai.</i>"
    )


def utr_help_text() -> str:
    """UTR kahan milega — chhota Hinglish card."""
    return (
        "🧾 <b>UTR / Transaction ID kahan milega?</b>\n"
        "──────────────────────\n"
        "📱 <b>PhonePe:</b> History → us payment par tap → <b>UTR</b> (12 digit)\n"
        "📱 <b>GPay:</b> Transaction → <b>UPI transaction ID</b>\n"
        "📱 <b>Paytm:</b> Passbook → payment → <b>Order / Txn ID</b>\n"
        "🏦 <b>Bank app / SMS:</b> SMS me <b>Ref No / UTR</b> likha hota hai (12 digit ya 16-22 character)\n\n"
        "⚠️ <b>Dhyan rakho:</b> mobile number ya koi random number UTR nahi hota — "
        "payment ke baad mila <b>asli</b> number hi bhejo. Galat UTR par VIP nahi milta."
    )

