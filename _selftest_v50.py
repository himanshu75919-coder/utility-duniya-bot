# -*- coding: utf-8 -*-
"""
v50 Self-Test — saare naye/changed tools ka OFFLINE + LIVE check
Chalao:  python _selftest_v50.py
"""
import io
import os
import sys

os.environ.setdefault("BOT_TOKEN", "123:test")  # imports ke liye dummy
os.environ.setdefault("ADMIN_ID", "1")

PASS = 0
FAIL = 0
FAILS = []


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILS.append(name)
        print(f"  ❌ {name}  {extra}")


def section(t):
    print(f"\n=== {t} ===")


# =====================================================================
section("1) ️ WEATHER ENGINE (Open-Meteo, free, no key)")
from modules.general_tools import weather_report, domain_age_days

r = weather_report("")
check("khaali input → saaf error", (not r["ok"]) and "shehar" in r["error"].lower())

r = weather_report("Gaya")
check("Gaya resolve hua", r.get("ok") is True, str(r)[:120])
if r.get("ok"):
    check("Gaya state = Bihar", "bihar" in r["place"].lower(), r["place"])
    check("temperature mila", isinstance(r.get("temp"), (int, float)))
    check("feels-like mila", isinstance(r.get("feels"), (int, float)))
    check("3 din forecast", len(r.get("forecast") or []) == 3, str(len(r.get("forecast") or [])))
    check("sunrise/sunset hh:mm", len(r.get("sunrise", "")) == 5 and len(r.get("sunset", "")) == 5,
          f"{r.get('sunrise')}/{r.get('sunset')}")

r2 = weather_report("Pune")
check("Pune bhi resolve", r2.get("ok") is True, str(r2)[:120])
if r2.get("ok"):
    check("Pune India me sorted", "india" in r2["place"].lower() or "maharashtra" in r2["place"].lower(),
          r2["place"])

r3 = weather_report("XYZNONEXISTCITY999")
check("galat city → saaf error", (not r3["ok"]))

# =====================================================================
section("2) 🔍 DOMAIN AGE (free RDAP)")
a = domain_age_days("github.com")
check("github.com ki age mili (>1000 din)", isinstance(a, int) and a > 1000, str(a))
a2 = domain_age_days("google.com")
check("google.com ki age mili", isinstance(a2, int) and a2 > 1000, str(a2))
a3 = domain_age_days("8.8.8.8")
check("IP par age = None (skip)", a3 is None, str(a3))

# =====================================================================
section("3) 🖨️ PRINT SHEET — exact 3.5×4.5cm (413×532 px @300DPI)")
from PIL import Image as _PILImage
from modules.cyber_studio import make_printable_sheet, make_stamped_passport, compress_document_pdf

# ek dummy 1000x1000 photo banao
_src = _PILImage.new("RGB", (1000, 1200), (120, 160, 200))
_pb = io.BytesIO(); _src.save(_pb, "JPEG"); photo_bytes = _pb.getvalue()

sheet = make_printable_sheet(photo_bytes)
sh = _PILImage.open(sheet)
check("sheet 1800×1200 (6×4 inch @300DPI)", sh.size == (1800, 1200), str(sh.size))
# photo 413×532 hai — spacing 29/45 px; pehli photo (29,45) par hai (JPEG ±8 tolerance)
px_center = sh.getpixel((29 + 413 // 2, 45 + 532 // 2))
check("photo sheet par paste hai (center pixel ≈ source colour)",
      all(abs(px_center[i] - (120, 160, 200)[i]) <= 8 for i in range(3)), str(px_center))
px_margin = sh.getpixel((5, 600))
check("sheet ka margin safed hai", px_margin[0] > 240, str(px_margin))

# =====================================================================
section("4) 📸 PASSPORT PHOTO — 20-50KB window")
import numpy as _np
from PIL import ImageFilter as _IF, ImageDraw as _D
# realistic "photo jaisi" image: smooth gradient + blobs + halka sensor noise
_h, _w = 1000, 1200
_arr = _np.zeros((_h, _w, 3), dtype=_np.float32)
_yy, _xx = _np.mgrid[0:_h, 0:_w]
_arr[..., 0] = 150 + 60 * _xx / _w
_arr[..., 1] = 120 + 80 * _yy / _h
_arr[..., 2] = 100 + 50 * (_xx + _yy) / (_w + _h)
_noise_img = _PILImage.fromarray(_np.clip(_arr, 0, 255).astype(_np.uint8))
_d2 = _D.Draw(_noise_img)
_rng = _np.random.default_rng(7)
for _ in range(14):
    _x, _y = _rng.integers(0, _w - 200), _rng.integers(0, _h - 200)
    _r = int(_rng.integers(40, 160))
    _col = tuple(int(c) for c in _rng.integers(40, 220, 3))
    _d2.ellipse([(_x, _y), (_x + _r, _y + _r)], fill=_col)
_noise_img = _noise_img.filter(_IF.GaussianBlur(6))
_a = _np.asarray(_noise_img).astype(_np.float32) + _rng.normal(0, 6, (_h, _w, 3))
_noise_img = _PILImage.fromarray(_np.clip(_a, 0, 255).astype(_np.uint8))
_pb2 = io.BytesIO(); _noise_img.save(_pb2, "JPEG"); noisy = _pb2.getvalue()

out, kb = make_stamped_passport(noisy, "RAHUL KUMAR", "01-01-2026")
img_out = _PILImage.open(out)
check("passport 700×900", img_out.size == (700, 900), str(img_out.size))
check("size 20-50KB window me", 20 <= kb <= 50, f"{kb}KB")

out2, kb2 = make_stamped_passport(photo_bytes, "RAMESH", "15-05-2026")
check("simple photo bhi bina crash (window ke paas)", 0 < kb2 <= 60, f"{kb2}KB")

# extreme case: pure random noise (JPG ke liye worst case) → bhi reasonable size
_pure = _np.random.default_rng(1).integers(0, 255, (800, 800, 3), dtype=_np.uint8)
_pure_b = io.BytesIO(); _PILImage.fromarray(_pure).save(_pure_b, "JPEG")
out3, kb3 = make_stamped_passport(_pure_b.getvalue(), "NOISE TEST", "01-01-2026")
check("extreme noise → window ke paas (150KB se chhota)", 0 < kb3 <= 150, f"{kb3}KB")

# =====================================================================
section("5) 📄 IMAGE→PDF (A4 + normal)")
from modules.general_tools import pages_to_pdf, make_qr_bytes, wifi_qr_data, vcard_data

pages = [photo_bytes, noisy]
pdf_n = pages_to_pdf(pages)
check("normal PDF bana", len(pdf_n) > 1000 and pdf_n[:4] == b"%PDF", str(len(pdf_n)))
pdf_a4 = pages_to_pdf(pages, a4=True)
check("A4 PDF bana", len(pdf_a4) > 1000 and pdf_a4[:4] == b"%PDF", str(len(pdf_a4)))

q = make_qr_bytes("https://t.me/test")
check("QR bytes", len(q.getvalue()) > 500)
check("WiFi QR data", wifi_qr_data("HomeWiFi", "1234").startswith("WIFI:T:WPA"))
check("vCard data", "BEGIN:VCARD" in vcard_data("Test", "9876543210"))

# =====================================================================
section("6)  EMI CALCULATOR ENGINE")
from modules.toolkit_extras import emi_calculator, village_compound_interest

# known value: P=500000, 12%/yr, 60 mo → EMI ≈ 11,120.5
r = emi_calculator(500000, 12, 60)
check("EMI ok", r["ok"] is True)
check("EMI ≈ 11120", abs(r["emi"] - 11120.5) < 2, str(r["emi"]))
check("total interest = emi*60 - P", abs(r["total_interest"] - (r["emi"] * 60 - 500000)) < 2)
check("schedule me milestones", len(r["schedule"]) == 10, str(len(r["schedule"])))  # 6,12,...,60
check("aakhri balance ~0", r["schedule"][-1]["balance"] < 5, str(r["schedule"][-1]))

r0 = emi_calculator(120000, 0, 12)
check("0% rate → EMI = P/12", abs(r0["emi"] - 10000) < 0.01, str(r0["emi"]))
rb = emi_calculator("abc", 12, 12)
check("garbage input → saaf error", rb["ok"] is False)
rb2 = emi_calculator(100, 12, -5)
check("negative months → error", rb2["ok"] is False)

# =====================================================================
section("7) 🪔 GAON-WALA CHAKRAVRIDDHI VYAAJ")
# P=1000, 5%/mo, 12 mo → 1000*1.05^12 = 1795.86
r = village_compound_interest(1000, 5, 12)
check("ok", r["ok"] is True)
check("12 mahine balance ≈ 1795.86", abs(r["total_payable"] - 1795.86) < 0.5, str(r["total_payable"]))
check("total interest ≈ 795.86", abs(r["total_interest"] - 795.86) < 0.5, str(r["total_interest"]))
check("milestones 6+12", ("6 months" in r["milestones"]) and ("12 months" in r["milestones"]),
      str(r["milestones"]))
check("double = 2000", r["double_amount"] == 2000)

# =====================================================================
section("8) 📱 PHONE NUMBER — toll-free fix")
from modules.osint_tools import lookup_phone_info

m = lookup_phone_info("9876543210")
check("10-digit mobile ok", m["ok"] is True, str(m)[:100])
check("mobile +91 format", m["international"].startswith("+91"), m["international"])

t = lookup_phone_info("18001020005")  # Indian toll-free (11 digit, '1' se)
check("1800 toll-free ok", t["ok"] is True, str(t)[:120])
if t["ok"]:
    check("toll-free +91 country", t["country_code"] == "IN", t.get("country_code", ""))

bad = lookup_phone_info("123")
check("galat number → error", not bad["ok"])

# =====================================================================
section("9) 🏦 BANK STATEMENT → CSV (fake PDF se)")
from modules.desi_tools import parse_bank_statement, statement_summary_text
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as _canvas

def _make_fake_statement_pdf() -> bytes:
    buf = io.BytesIO()
    c = _canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica", 10)
    c.drawString(60, 780, "STATE BANK OF INDIA — CUSTOMER STATEMENT")
    c.drawString(60, 760, "Account: 30011234567  Branch: Patna")
    rows = [
        ("01/04/2026", "SALARY CREDIT LTD", "", "50000.00", "55000.00"),
        ("05/04/2026", "UPI/DR/1234567890/STORE", "2500.00", "", "52500.00"),
        ("10/04/2026", "ATM WDL 4567", "10000.00", "", "42500.00"),
        ("15/04/2026", "NEFT/CR/999888/RENT", "", "20000.00", "62500.00"),
        ("20/04/2026", "UPI/DR/112233/FOOD", "1200.00", "", "61300.00"),
    ]
    y = 720
    for dt, det, dr, cr, bal in rows:
        c.drawString(60, y, dt)
        c.drawString(160, y, det)
        if dr:
            c.drawString(430, y, dr)
        if cr:
            c.drawString(500, y, cr)
        c.drawString(570, y, bal)
        y -= 20
    c.save()
    buf.seek(0)
    return buf.getvalue()

res = parse_bank_statement(_make_fake_statement_pdf())
check("PDF parse ok", res["ok"] is True, str(res)[:150])
if res["ok"]:
    check("bank detect = SBI", res["bank"] == "SBI", res["bank"])
    check("5 transactions", res["summary"]["count"] == 5, str(res["summary"]))
    check("total credit 70000", abs(res["summary"]["total_credit"] - 70000) < 1, str(res["summary"]))
    check("total debit 13700", abs(res["summary"]["total_debit"] - 13700) < 1, str(res["summary"]))
    check("closing balance 61300", abs(res["summary"]["closing"] - 61300) < 1, str(res["summary"]))
    csv_txt = res["csv"].decode("utf-8-sig")
    check("CSV header sahi", csv_txt.startswith("Date,Detail,Debit (out),Credit (in),Balance"))
    check("summary text banata hai", "BANK STATEMENT READY" in statement_summary_text(res))

# =====================================================================
section("10) 🧾 KAGAZ + LAND + REGISTRY")
from modules.desi_tools import convert_land, registry_cost, registry_text, land_text

c = convert_land(2, "katha")
check("2 katha → 2722.5 sqft", abs(c["sqft"] - 2722.5) < 1, str(c["sqft"]))
c2 = convert_land(1, "bigha")
check("1 bigha → 27225 sqft", abs(c2["sqft"] - 27225) < 1, str(c2["sqft"]))

r = registry_cost("bihar", 2722.5, 3000, "female")
check("registry ok", r["ok"] is True)
check("value = 8167500", abs(r["value"] - 2722.5 * 3000) < 1, str(r["value"]))
check("female → 5.5% stamp (6.5-1)", abs(r["stamp_pct"] - 5.5) < 0.01, str(r["stamp_pct"]))
check("total = stamp+reg+panch", abs(r["total"] - (r["stamp"] + r["reg"] + r["panchayat"])) < 0.05)
check("registry text", "REGISTRY TOTAL COST" in registry_text(r))
check("land text", "SQR" in land_text(c).upper() or "Sq Feet" in land_text(c))

# =====================================================================
section("11) 🛡️ PAYGUARD — UTR + screenshot")
from modules.payguard import validate_utr, analyze_screenshot

u1 = validate_utr("UTR: 123456789012")
check("12-digit UTR ok", u1["ok"] is True and u1["utr"] == "123456789012", str(u1))
u2 = validate_utr("9876543210")
check("mobile number UTR nahi", u2["ok"] is False)
u3 = validate_utr("AB12CD34EF56GH78IJ")
check("16-22 char bank ref ok", u3["ok"] is True, str(u3))
u4 = validate_utr("12345678901")
check("11 digit → saaf reason", u4["ok"] is False and "11" in u4["reason"], str(u4)[:80])

shot = analyze_screenshot(b"tiny")
check("chhoti file → reject", shot["verdict"] == "bad")

# =====================================================================
section("12) 🔗 SHORTENER PARALLEL (live)")
from modules.toolkit_extras import shorten_url, clean_tracking, expand_url

ct = clean_tracking("https://x.com/y?utm_source=a&fbclid=b&id=7")
check("tracking params gayab", "utm_source" not in ct and "fbclid" not in ct and "id=7" in ct, ct)

import time
_t0 = time.time()
links = shorten_url("https://www.example.com/very/long/path?x=1", want=3)
_dt = time.time() - _t0
check("kam se kam 1 short link", len(links) >= 1, str(links))
check("parallel = fast (<12s)", _dt < 12, f"{_dt:.1f}s")
print(f"   ⏱️ parallel shortener: {len(links)} links me {_dt:.1f}s")

# =====================================================================
section("13) 📲 USERNAME FINDER PARALLEL (live)")
from modules.osint_tools import check_username_platforms

_t0 = time.time()
p = check_username_platforms("torvalds")  # exists on GitHub
_dt = time.time() - _t0
check("result ok", p["ok"] is True)
gh = [r for r in p["results"] if r["key"] == "github"]
check("github = torvalds FOUND", gh and gh[0]["exists"] is True, str(gh)[:100])
check("5 platform check hue", len(p["results"]) == 5, str(len(p["results"])))
check("parallel = fast (<20s)", _dt < 20, f"{_dt:.1f}s")
print(f"   ⏱️ parallel username check: {_dt:.1f}s")

# =====================================================================
section("14) 🛡️ LINK CHECK + DOMAIN AGE SIGNAL (live)")
from modules.toolkit_extras import analyze_link

chk = analyze_link("https://github.com/")
check("link check ok", chk["ok"] is True)
check("github = low risk", chk["risk"] < 40, f"risk={chk['risk']}")
check("domain age signal present", "domain_age_days" in chk["signals"], str(chk["signals"].get("domain_age_days")))
print(f"    github risk={chk['risk']} · age={chk['signals'].get('domain_age_days')} din")

# =====================================================================
section("15) 🔌 DATABASE (busy_timeout + credits + vip)")
os.environ["DB_PATH"] = "/tmp/v50_test_botdata.db"
if os.path.exists("/tmp/v50_test_botdata.db"):
    os.remove("/tmp/v50_test_botdata.db")
import importlib
import database
importlib.reload(database)
import inspect
src_db = inspect.getsource(database.db)
check("busy_timeout set hota hai", "busy_timeout" in src_db)

d = database.get_user(777, "Test User")
check("naya user + credits", d.get("credits", 0) == database.CREDITS_START, str(d))
left = database.spend_credits(777, 1)
check("credit spend", left == database.CREDITS_START - 1, str(left))
database.grant_premium(777, 30)
d2 = database.get_user(777)
check("vip grant", database.is_premium(d2), str(d2.get("premium_until")))
check("stats ban rahe hain", database.stats()["total_users"] >= 1)
os.remove("/tmp/v50_test_botdata.db")

# =====================================================================
section("16) 🤖 BOT.PY WIRING CHECKS (static)")
bot_src = open("bot.py").read()
checks = [
    ("v50 version", any(f"v50.{i}" in bot_src for i in range(0, 9))),
    ("weather button menu me", "WEATHER / MAUSAM" in bot_src),
    ("emi button menu me", "EMI / INTEREST CALC" in bot_src),
    ("weather prompt", '"weather": (' in bot_src),
    ("weather handler", 'if mode == "weather":' in bot_src),
    ("emi_calc callback", 'data in ("emi_calc", "emi_vyaaj")' in bot_src),
    ("emi ask modes", 'if mode == "emi_ask_amt":' in bot_src and 'if mode == "emi_ask_rate":' in bot_src),
    ("vyaaj ask modes", 'if mode == "vyaaj_ask_amt":' in bot_src and 'if mode == "vyaaj_ask_months":' in bot_src),
    ("idfind forward fix", "forwarded message PEHLE check karo" in bot_src),
    ("pdf 10 limit", "Max 10 photos" in bot_src),
    ("pdf_clear handler", 'if q.data == "pdf_clear":' in bot_src),
    ("bankpdf auto-pass", "statement_passwords()" in bot_src),
    ("admtut fix", "Current link:</i>" not in bot_src),
    ("broadcast fallback", "parse fail ho to plain text me bhejo" in bot_src),
    ("on_error user msg", "Chhota sa ghatna ho gaya" in bot_src),
    ("weather import", "weather_report" in bot_src),
    ("emi import", "emi_calculator" in bot_src),
    ("vyaaj import", "village_compound_interest" in bot_src),
    ("dead admin block delete", "row[1] if row else" not in bot_src),
    ("interest calc removed-list se bahar", '"INTEREST CALC", "INTEREST CALCULATOR", "INTEREST", "VYAAJ CALC"' not in bot_src),
]
for nm, ok in checks:
    check(nm, ok)

# =====================================================================
print(f"\n{'=' * 55}")
print(f"RESULT: {PASS} PASSED · {FAIL} FAILED")
if FAILS:
    print("Failed:", ", ".join(FAILS))
print(f"{'=' * 55}")
sys.exit(1 if FAIL else 0)
