# -*- coding: utf-8 -*-
"""
bulk_mode.py — 📤 BULK MODE (v75.1): ek file me 500 entries → poora Excel
========================================================================
YE AAPKA EARNING TOOL HAI.

Kyun ye paisa banata hai:
    Ek CA / bank agent / insurance agent / transport wala **APNE 500 kaam**
    ek-ek karke nahi karega. Wo ek hi baar me file daal ke Excel maangta hai.
    Ek aisa banda = 500 normal users ke barabar revenue. Aur wo **har mahine**
    wapas aata hai.

Kya karta hai:
    1. User lines paste karta hai (Excel se copy-paste bhi chalega)
    2. Bot KHUD pahchan leta hai ki kaunse type ki list hai
       (IFSC / pincode / mobile / gaadi number / link)
    3. Bounded parallel engine se saare check hote hain (4-6 workers)
    4. **Excel (.xlsx)** file banti hai + summary card

FREE vs VIP (yahi earning model hai):
    • FREE: ek baar me 15 entries
    • VIP : ek baar me 500 entries + Excel + "(purani file bhi)"

SAFETY (bot ke rules yaad rakhe hue):
    • RULE #1 NO-LINK  -> is file me kahin bahar ka link nahi
    • NO-GYAAN         -> sirf outcome, koi lecture nahi
    • ZERO CRASH       -> har public function try/except me bandha
    • Rate-limit safe  -> bounded workers (upstream ko maar nahi dalte)
"""
from __future__ import annotations

import io
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

log = logging.getLogger("ud.bulk")

__all__ = [
    "KINDS", "detect_kind", "extract_entries", "filter_valid", "run_bulk", "to_xlsx", "to_csv",
    "bulk_intro_text", "bulk_result_text", "limits_for", "FREE_LIMIT", "VIP_LIMIT",
    "MAX_WORKERS", "valid_entry",
]

# ------------------------------------------------------------------ limits
FREE_LIMIT = 15        # free user: ek run me
VIP_LIMIT = 500        # VIP/owner: ek run me
MAX_WORKERS = 5        # ek saath kitne checks (upstream ko maar nahi dalte)
PER_ENTRY_TIMEOUT = 25  # ek entry ka max time (second)

# ------------------------------------------------------------------- kinds
#  kind_key -> (label, emoji, column_headers)
KINDS: Dict[str, Dict[str, Any]] = {
    "ifsc": {
        "label": "IFSC Bank Branch", "emoji": "🏦",
        "cols": ["IFSC", "Bank", "Branch", "Address", "City", "State",
                 "MICR", "Contact", "UPI", "NEFT", "RTGS", "IMPS", "Status", "Detail"],
    },
    "pincode": {
        "label": "Pincode / Area", "emoji": "📮",
        "cols": ["Pincode", "Main Area", "District", "State", "Taluk", "Division",
                 "Total Offices", "Status", "Detail"],
    },
    "vehicle": {
        "label": "Gaadi Number (RC)", "emoji": "🚗",
        "cols": ["Number Plate", "Owner", "Maker/Model", "Fuel", "Reg Date",
                 "Insurance", "PUC", "RTO", "Status", "Detail"],
    },
    "mobile": {
        "label": "Mobile Number", "emoji": "📱",
        "cols": ["Number", "Operator", "Circle", "Type", "Status", "Detail"],
    },
    "url": {
        "label": "Link (safe ya nahi)", "emoji": "🔍",
        "cols": ["Link", "Risk Score", "Verdict", "Reasons", "Status", "Detail"],
    },
}

# --------------------------------------------------------------- validators
_RE_IFSC = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
_RE_PIN = re.compile(r"^[1-8][0-9]{5}$")
_RE_MOBILE = re.compile(r"^[6-9][0-9]{9}$")
_RE_VEH = re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{3,4}$")
_RE_URL = re.compile(r"^(https?://|www\.)\S+$", re.IGNORECASE)


def valid_entry(kind: str, val: str) -> bool:
    """Ek entry us kind ke liye valid hai? (junk hataane ke liye)"""
    v = str(val or "").strip()
    if not v:
        return False
    if kind == "ifsc":
        return bool(_RE_IFSC.match(v.upper()))
    if kind == "pincode":
        return bool(_RE_PIN.match(v))
    if kind == "mobile":
        return bool(_RE_MOBILE.match(v))
    if kind == "vehicle":
        return bool(_RE_VEH.match(v.upper())) and 8 <= len(v) <= 12
    if kind == "url":
        return bool(_RE_URL.match(v))
    return False


def _norm_line(line: str) -> str:
    """Excel/CSV se aayi line ko saaf karo.

    Excel se copy karne par line me tab/multiple columns hote hain —
    pehla 'kaam ka' token le lete hain."""
    s = str(line or "").replace("\u00a0", " ").strip()
    s = s.strip('"\'').strip()
    if not s:
        return ""
    # Excel paste: "SBIN0001234\tState Bank\tPatna" -> pehla column
    if "\t" in s:
        s = s.split("\t")[0].strip()
    # CSV paste: "SBIN0001234,State Bank" -> pehla column (agar comma+space)
    if "," in s and len(s.split(",")) > 1:
        _first = s.split(",")[0].strip()
        if _first:
            s = _first
    # ginti/numbering hata do: "1. SBIN0001234" / "1) SBIN..." / "- SBIN..."
    s = re.sub(r"^\s*\d{1,4}\s*[.)\-:]\s*", "", s).strip()
    s = re.sub(r"^\s*[-*•]\s*", "", s).strip()
    return s


def extract_entries(text: str, limit: int = VIP_LIMIT) -> Tuple[List[str], int]:
    """Text se entries nikalo.

    Return: (clean_entries, total_lines_seen)
    -- duplicate hata diye jaate hain (upstream par dobara call nahi).
    """
    try:
        lines = str(text or "").replace("\r", "\n").split("\n")
        seen, out = set(), []
        for ln in lines:
            v = _norm_line(ln)
            if not v or len(v) > 220:
                continue
            # Ek line me kai entries? (jaise "9876543210 8765432109")
            #  ⚠️ Ye splitting SAVDHANI se: sirf tabhi jab line ke SAARE tokens
            #  "identifier jaise" hon (>=6 char, sirf alnum/._:@/-).
            #  Isse "bank list (heading)" jaise junk toot kar entry nahi bante.
            _toks = v.split()
            if (2 <= len(_toks) <= 6
                    and all(re.match(r"^[A-Za-z0-9._:/@\-]{6,}$", t) for t in _toks)):
                _parts = _toks
            else:
                _parts = [v]
            for tok in _parts:
                t = tok.strip().strip(",;")
                if not t:
                    continue
                k = t.upper()
                if k in seen:
                    continue
                seen.add(k)
                out.append(t)
        return out[:max(1, int(limit))], len(lines)
    except Exception as e:                                       # noqa: BLE001
        log.debug("extract_entries skip: %s", str(e)[:100])
        return [], 0


def detect_kind(entries: Sequence[str]) -> Tuple[str, int, List[str]]:
    """List kaunsa type hai — majority vote se.

    Return: (kind, matched_count, sample_entries)   kind "" = pahchana nahi.
    """
    try:
        counts: Dict[str, int] = {}
        samples: Dict[str, List[str]] = {}
        for v in list(entries)[:200]:
            for k in KINDS:
                if valid_entry(k, v):
                    counts[k] = counts.get(k, 0) + 1
                    samples.setdefault(k, [])
                    if len(samples[k]) < 3:
                        samples[k].append(v)
                    break
        if not counts:
            return "", 0, []
        best = max(counts.items(), key=lambda kv: kv[1])[0]
        return best, int(counts.get(best, 0)), samples.get(best, [])
    except Exception:                                            # noqa: BLE001
        return "", 0, []


def filter_valid(kind: str, entries: Sequence[str]) -> Tuple[List[str], int]:
    """Detect hone ke BAAD junk hatao (headings, khaali, galat format).

    Return: (valid_entries, skipped_count)
    """
    try:
        good, skipped = [], 0
        for v in entries or []:
            if valid_entry(kind, v):
                good.append(str(v).strip())
            else:
                skipped += 1
        return good, skipped
    except Exception:                                            # noqa: BLE001
        return list(entries or []), 0


# ------------------------------------------------------------------ runners
def _one(kind: str, val: str) -> Dict[str, Any]:
    """Ek entry check karo — kabhi raise nahi karta."""
    t0 = time.perf_counter()
    try:
        if kind == "ifsc":
            from modules.osint_tools import lookup_ifsc
            r = lookup_ifsc(val)
        elif kind == "pincode":
            from modules.osint_tools import lookup_pincode
            r = lookup_pincode(re.sub(r"[^\d]", "", val))
        elif kind == "vehicle":
            from modules.vehicle_tool import vehicle_lookup
            r = vehicle_lookup(val)
        elif kind == "mobile":
            from modules import numinfo_provider as np
            r = np.lookup(val)
        elif kind == "url":
            from modules.toolkit_extras import analyze_link
            r = analyze_link(val)
        else:
            r = {"ok": False, "error": "unknown kind"}
        r = dict(r or {})
        r["_ms"] = int((time.perf_counter() - t0) * 1000)
        r["_value"] = val
        return r
    except Exception as e:                                       # noqa: BLE001
        return {"ok": False, "_value": val, "_ms": int((time.perf_counter() - t0) * 1000),
                "error": f"{type(e).__name__}: {str(e)[:90]}"}


def _row_of(kind: str, val: str, r: Dict[str, Any]) -> List[Any]:
    """Ek result -> Excel ki row (KINDS ke cols ke hisaab se)."""
    ok = bool(r.get("ok")) or bool(r.get("risk") is not None and kind == "url")
    status = "OK" if ok else "FAIL"
    detail = "" if ok else str(r.get("error") or "")[:180]
    try:
        if kind == "ifsc":
            return [val, r.get("bank", ""), r.get("branch", ""), r.get("address", ""),
                    r.get("city", ""), r.get("state", ""), r.get("micr", ""),
                    r.get("contact", ""),
                    "YES" if r.get("upi") else "NO", "YES" if r.get("neft") else "NO",
                    "YES" if r.get("rtgs") else "NO", "YES" if r.get("imps") else "NO",
                    status, detail]
        if kind == "pincode":
            _pos = list(r.get("post_offices") or [])
            _main = _pos[0] if _pos else ""
            _cnt = r.get("total_offices") or len(_pos) or ""
            return [r.get("pincode") or val, _main, r.get("district", ""),
                    r.get("state", ""), r.get("taluk", "") or r.get("block", ""),
                    r.get("division", ""), _cnt, status, detail]
        if kind == "vehicle":
            return [val, r.get("owner", ""), r.get("maker_model", "") or r.get("model", ""),
                    r.get("fuel", ""), r.get("reg_date", "") or r.get("registration_date", ""),
                    r.get("insurance", "") or r.get("insurance_upto", ""),
                    r.get("puc", "") or r.get("puc_upto", ""),
                    r.get("rto", "") or r.get("rto_code", ""), status, detail]
        if kind == "mobile":
            return [val, r.get("operator", ""), r.get("circle", ""), r.get("type", ""),
                    status, detail]
        if kind == "url":
            _risk = r.get("risk")
            _verdict = (r.get("verdict") or r.get("level") or "")
            _reasons = " | ".join(str(x) for x in (r.get("reasons") or [])[:4])
            return [val, _risk if _risk is not None else "",
                    _verdict, _reasons[:300], status, detail]
    except Exception:                                            # noqa: BLE001
        pass
    return [val, "", "", "", "", "", "", "", "", "", "", "", "FAIL", detail or "row build fail"]


def run_bulk(kind: str, entries: Sequence[str],
             on_progress: Optional[Callable[[int, int], None]] = None,
             workers: int = MAX_WORKERS) -> Dict[str, Any]:
    """Saari entries parallel check karo.

    Return: {ok, kind, rows(list of lists), headers, total, passed, failed, seconds}
    -- kabhi raise nahi karta. Progress callback har entry par (i, total) deta hai.
    """
    t0 = time.perf_counter()
    vals = [str(v) for v in (entries or [])]
    kd = KINDS.get(kind) or {}
    res: Dict[str, Any] = {
        "ok": True, "kind": kind, "headers": ["Input"] + list(kd.get("cols") or []),
        "rows": [], "total": len(vals), "passed": 0, "failed": 0, "seconds": 0.0,
    }
    if not vals or not kd:
        res["ok"] = False
        return res

    done = 0
    lock = threading.Lock()
    try:
        with ThreadPoolExecutor(max_workers=max(1, min(int(workers), 8)),
                                thread_name_prefix="bulk") as ex:
            fut = {ex.submit(_one, kind, v): v for v in vals}
            for f in as_completed(fut, timeout=None):
                v = fut[f]
                try:
                    r = f.result(timeout=PER_ENTRY_TIMEOUT) or {}
                except Exception as e:                           # noqa: BLE001
                    r = {"ok": False, "error": f"timeout/{type(e).__name__}"}
                row = _row_of(kind, v, r)
                res["rows"].append(row)
                if str(row[-2]).upper() == "OK":
                    res["passed"] += 1
                else:
                    res["failed"] += 1
                with lock:
                    done += 1
                    if on_progress:
                        try:
                            on_progress(done, len(vals))
                        except Exception:                        # noqa: BLE001
                            pass
    except Exception as e:                                       # noqa: BLE001
        log.warning("bulk run partial: %s", str(e)[:150])
        res["ok"] = bool(res["rows"])

    # input order me wapas (Excel me order saaf rahe)
    try:
        order = {v: i for i, v in enumerate(vals)}
        res["rows"].sort(key=lambda r: order.get(str(r[0]), 99999))
    except Exception:                                            # noqa: BLE001
        pass
    res["seconds"] = round(time.perf_counter() - t0, 1)
    return res


# ------------------------------------------------------------------ writers
def to_xlsx(res: Dict[str, Any], title: str = "") -> bytes:
    """Excel file banao (openpyxl). Na ho to csv fallback (bytes)."""
    headers = list(res.get("headers") or [])
    rows = list(res.get("rows") or [])
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter

        wb = Workbook()
        ws = wb.active
        # Excel sheet title me ye characters allowed NAHI hain (warna file hi nahi banti)
        _raw_title = (KINDS.get(res.get("kind"), {}).get("label") or "Report")
        _safe_title = "".join(ch for ch in _raw_title if ch not in ':\\/?*[]')
        ws.title = (_safe_title.strip()[:28] or "Report")

        head_fill = PatternFill("solid", fgColor="1F4E78")
        head_font = Font(bold=True, color="FFFFFF", size=11)
        fail_fill = PatternFill("solid", fgColor="FDE9E9")
        ok_fill = PatternFill("solid", fgColor="EAF7EE")

        ws.append(headers)
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=c)
            cell.fill = head_fill
            cell.font = head_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        for r in rows:
            ws.append(list(r))
        # rang: OK = halka hara, FAIL = halka laal (status column ke aadhar par)
        st_idx = None
        for i, h in enumerate(headers):
            if str(h).strip().lower() == "status":
                st_idx = i + 1
                break
        if st_idx:
            for ri in range(2, ws.max_row + 1):
                c = ws.cell(row=ri, column=st_idx)
                _ok = str(c.value or "").upper() == "OK"
                for ci in range(1, len(headers) + 1):
                    ws.cell(row=ri, column=ci).fill = ok_fill if _ok else fail_fill
        # column width (lambe text ke liye)
        for ci in range(1, len(headers) + 1):
            _want = max(12, min(46, len(str(headers[ci - 1])) + 6))
            for ri in range(2, min(ws.max_row, 60) + 1):
                _want = max(_want, min(46, len(str(ws.cell(row=ri, column=ci).value or "")) + 2))
            ws.column_dimensions[get_column_letter(ci)].width = _want
        ws.freeze_panes = "A2"
        bio = io.BytesIO()
        wb.save(bio)
        return bio.getvalue()
    except Exception as e:                                       # noqa: BLE001
        log.warning("xlsx fail (%s) — csv fallback", str(e)[:110])
        return to_csv(res)


def to_csv(res: Dict[str, Any]) -> bytes:
    """CSV fallback (Excel me seedha khulta hai)."""
    try:
        import csv
        sio = io.StringIO()
        w = csv.writer(sio)
        w.writerow(list(res.get("headers") or []))
        for r in (res.get("rows") or []):
            w.writerow(list(r))
        # Excel ko UTF-8 samajhne ke liye BOM
        return ("\ufeff" + sio.getvalue()).encode("utf-8", "ignore")
    except Exception:                                            # noqa: BLE001
        return b""


# -------------------------------------------------------------------- cards
def limits_for(uid: int) -> Tuple[int, bool]:
    """(kitne entries allowed, VIP hai kya)"""
    try:
        from bot import has_unlimited
        if has_unlimited(uid):
            return VIP_LIMIT, True
    except Exception:                                            # noqa: BLE001
        pass
    return FREE_LIMIT, False


def bulk_intro_text(vip: bool = False) -> str:
    """Bulk mode ka intro card (naya tool hai — isliye naya text)."""
    _lim = VIP_LIMIT if vip else FREE_LIMIT
    lines = [
        "📤 <b>BULK MODE — ek saath poora Excel</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "<b>Kaam kaise karta hai:</b>",
        "1️⃣ Neeche apni list <b>paste</b> kar do (Excel ya CSV se copy karke bhi chalega)",
        "2️⃣ Bot khud pahchan lega ki kaunsi list hai",
        "3️⃣ Confirm karo → <b>Excel file</b> mil jayegi",
        "",
        "<b>Kya-kya chalta hai:</b>",
        "🏦 IFSC bank codes · 📮 Pincodes · 📱 Mobile numbers",
        "🚗 Gaadi number (RC) · 🔍 Links (safe ya nahi)",
        "━━━━━━━━━━━━━━━━━━━━━━",
        (f"• Ek baar me <b>{_lim}</b> entries"
         + ("" if vip else f" (VIP me {VIP_LIMIT})")),
        "• Duplicate apne aap hat jaate hain",
        "• Junk lines (khaali/heading) chhoot jaati hain",
        "",
        "👇 <b>Apni list bhejo</b> — bas paste kar do.",
    ]
    return "\n".join(lines)


def preview_text(kind: str, count: int, matched: int, samples: Sequence[str],
                 total_lines: int, vip: bool, limit: int) -> str:
    """List pahchanne ke baad confirm card."""
    kd = KINDS.get(kind) or {}
    over = count >= limit
    lines = [
        f"{kd.get('emoji', '📤')} <b>{kd.get('label', kind)} — list pahchan li</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📄 Lines mili: <b>{total_lines}</b>",
        f"✅ Valid entries: <b>{count}</b>",
    ]
    if count != matched:
        lines.append(f"⚠️ Format match: <b>{matched}</b> (baaki line skip hongi)")
    lines += [
        "🔎 <b>Sample:</b> " + ", ".join(f"<code>{s}</code>" for s in list(samples)[:3]),
    ]
    if over:
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━",
            f"⚡ Is baar <b>{limit}</b> entries check hongi"
            + ("" if vip else f" — VIP me <b>{VIP_LIMIT}</b> tak ek saath"),
        ]
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "👇 Chalu karne ke liye neeche dabao:",
    ]
    return "\n".join(lines)


def bulk_result_text(res: Dict[str, Any], kind: str, vip: bool) -> str:
    """Result summary card (Excel ke saath jaata hai)."""
    kd = KINDS.get(kind) or {}
    total = int(res.get("total") or 0)
    ok = int(res.get("passed") or 0)
    bad = int(res.get("failed") or 0)
    secs = res.get("seconds") or 0
    pct = int(round(100.0 * ok / total)) if total else 0
    bar_len = 10
    filled = max(0, min(bar_len, int(round(pct / 100.0 * bar_len))))
    bar = "█" * filled + "░" * (bar_len - filled)
    lines = [
        f"{kd.get('emoji', '📤')} <b>BULK REPORT TAYYAR</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 <b>Total:</b> {total} entries",
        f"✅ <b>Mil gaye:</b> {ok}",
        f"❌ <b>Nahi mile:</b> {bad}",
        f"{bar} <b>{pct}%</b>",
        f"⚡ <b>Time:</b> {secs}s",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "📎 Excel file neeche hai — <b>upar wali row par filter</b> laga ke "
        "sirf FAIL wale dekh sakte ho.",
    ]
    if not vip:
        lines.append(f"\n⚡ <i>Aagli baar {VIP_LIMIT} entries ek saath karne ke liye VIP me le lo.</i>")
    return "\n".join(lines)


def file_name(kind: str, count: int) -> str:
    """Excel file ka naam (user ko seedha samajh aaye, koi link nahi)."""
    slug = {"ifsc": "IFSC", "pincode": "Pincode", "vehicle": "Gaadi",
            "mobile": "Mobile", "url": "Link"}.get(kind, "Report")
    return f"{slug}_Bulk_Report_{count}.xlsx"
