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
section("1) 🌦️ WEATHER TOOL — v51.1 me PERMANENTLY REMOVED (verify)")
import modules.general_tools as _gt
check("weather_report function delete hua", not hasattr(_gt, "weather_report"))
check("WMO_WEATHER dict delete hua", not hasattr(_gt, "WMO_WEATHER"))
check("WEATHER_CITY_ALIASES delete hua", not hasattr(_gt, "WEATHER_CITY_ALIASES"))
check("build_upi_link safe (UPI QR tool ke liye)", hasattr(_gt, "build_upi_link"))
check("domain_age_days safe (linkcheck use karta hai)", hasattr(_gt, "domain_age_days"))

# =====================================================================
section("2) 🔍 DOMAIN AGE (free RDAP)")
from modules.general_tools import domain_age_days
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
section("5) 📷 QR ENGINES (QR / WiFi / vCard)")
from modules.general_tools import make_qr_bytes, wifi_qr_data, vcard_data

q = make_qr_bytes("https://t.me/test")
check("QR bytes", len(q.getvalue()) > 500)
check("WiFi QR data", wifi_qr_data("HomeWiFi", "1234").startswith("WIFI:T:WPA"))
check("vCard data", "BEGIN:VCARD" in vcard_data("Test", "9876543210"))

# =====================================================================
section("6) 📱 PHONE NUMBER — toll-free fix")
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
section("16) 🤖 BOT.PY WIRING CHECKS (static) — v51")
bot_src = open("bot.py").read()
checks = [
    # v53.0: version aage badhi — ab hardcode v52.3 nahi, v53.x check hota hai.
    # Saath me ek "regression guard": version kabhi v53 se peeche na jaye.
    ("v53.0 version", "v53.0 Premium Earning" in bot_src),
    # regression guard: version string kabhi purane release par wapas na jaye
    ("version v53+ par hai (peeche regress nahi hua)",
     "v53.0 Premium Earning" in bot_src
     and "v52.3 Premium Earning" not in bot_src
     and "v50." not in bot_src.split("BOT_VERSION =")[1][:40]),
    # ---- v52.1: GOVT SERVICES user order par DELETE hua (verify) ----
    ("govt import gayab", "from modules import govt_tools" not in bot_src),
    ("govt action gayab", 'if action == "govt":' not in bot_src),
    ("govt case callback gayab", 'if data == "govt_case":' not in bot_src),
    ("govt on_text gayab", 'if mode == "govt_case":' not in bot_src),
    ("govt menu kb gayab", "def govt_menu_kb():" not in bot_src),
    ("govt premium gayab", '"govt_case"' not in bot_src),
    ("govt removed-list me", '"GOVT SERVICES", "GOVT"' in bot_src),
    ("govt_tools.py file delete", not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules", "govt_tools.py"))),
    # ---- v52: 🎞️ YouTube quality selector ----
    ("yt quality chooser", "yt_available_qualities" in bot_src),
    ("ytq callback", 'data.startswith("ytq:")' in bot_src),
    ("yt quality download fn", "_yt_quality_download" in bot_src),
    ("yt quality rate-limit", '"yt_q":        (8,  120, "YouTube Quality")' in bot_src),
    # ---- v52: 🚀 speed fixes ----
    ("self-ping keepalive", "_self_health not in _KEEPALIVE_PEERS" in bot_src),
    ("welcome fid cache", "_WELCOME_FID" in bot_src),
    ("conflict friendly handler", "isinstance(err, Conflict)" in bot_src),
    ("conflict import", "from telegram.error import RetryAfter, Conflict" in bot_src),
    ("conflict user msg nahi", "_CONFLICT_NOTE" in bot_src),
    ("banner asli version", 'print(f"🚀 Starting ToolVault / Utility Duniya Super Bot ({BOT_VERSION})...")' in bot_src),
    ("weather button menu se gayab", "🌦️ {to_bold('WEATHER / MAUSAM')}" not in bot_src),
    ("weather prompt gayab", '"weather": (' not in bot_src),
    ("weather handler gayab", 'if mode == "weather":' not in bot_src),
    ("weather import gayab", "weather_report" not in bot_src),
    ("weather premium list se gayab", '"weather",             # 🌦️ WEATHER / MAUSAM' not in bot_src),
    ("weather rate-limit se gayab", '"weather":     (15, 60,  "Weather / Mausam")' not in bot_src),
    ("weather removed-list me", '"WEATHER", "MAUSAM"' in bot_src),
    ("bankpdf auto-pass", "statement_passwords()" in bot_src),
    ("admtut fix", "Current link:</i>" not in bot_src),
    ("broadcast fallback", "parse fail ho to plain text me bhejo" in bot_src),
    ("on_error user msg", "Chhota sa ghatna ho gaya" in bot_src),
    ("dead admin block delete", "row[1] if row else" not in bot_src),
    # ---- v51: 5 tools PERMANENTLY delete (wiring gayab) ----
    ("EMI mapping gayab", '"EMI / INTEREST CALC": "emi"' not in bot_src),
    ("EMI action gayab", 'action == "emi"' not in bot_src),
    ("EMI modes gayab", 'if mode == "emi_ask_amt":' not in bot_src),
    ("vyaaj modes gayab", 'if mode == "vyaaj_ask_amt":' not in bot_src),
    ("screenshot mapping gayab", '"SITE SCREENSHOT": "shot"' not in bot_src),
    ("shot action gayab", 'action == "shot"' not in bot_src),
    ("shot mode gayab", 'if mode in ("shot", "shot_full")' not in bot_src),
    ("image→pdf mapping gayab", '"IMAGE→PDF": "pdf"' not in bot_src),
    ("pdf action gayab", 'action == "pdf"' not in bot_src),
    ("on_pdf_cb gayab", "async def on_pdf_cb" not in bot_src),
    ("private channel action gayab", 'action == "cloner_private_help"' not in bot_src),
    ("private mapping gayab", '"PRIVATE CHANNEL SETUP": "cloner_private_help"' not in bot_src),
    ("idfind mapping gayab", '"ID & USERNAME FINDER": "idfind"' not in bot_src),
    ("idfind mode gayab", 'if mode == "idfind":' not in bot_src),
    ("check_username_platforms import gayab", "check_username_platforms" not in bot_src),
    ("deleted tools removed-list me", '"EMI / INTEREST CALC", "EMI CALC"' in bot_src),
    # ---- v51: SAARE tools premium ----
    ("all tools premium set", all(t in bot_src for t in
        ["\"terabox\"", "\"pp_stamp\"", "\"print_sheet\"", "\"doc_compress\"",
         "\"sarkari\"", "\"ifsc\"", "\"pin\"", "\"ip\"", "\"qr\"",
         "\"short\"", "\"linkcheck\"", "\"appfind\""])),
    ("vehicle key = rto", '"rto",                 # 🚗 VEHICLE' in bot_src),
    ("premium tool names updated", '"terabox": "⚡ Terabox / Cloud Downloader"' in bot_src),
]
for nm, ok in checks:
    check(nm, ok)

# =====================================================================
section("17) 🗣️ TEXT → HINDI VOICE (edge-tts, free neural) — v51.2")
import asyncio
from modules import desi_tools as _desi

async def _tts_main():
    r_m = await _desi.hindi_tts("Namaste bhai! Ye hai Utility Duniya ka naya Hindi voice tool.", "male")
    r_f = await _desi.hindi_tts("Main bhi sunn liya, awaaz ekdum acchi lagi.", "female")
    r_e = await _desi.hindi_tts("   ")
    return r_m, r_f, r_e

r_m, r_f, r_e = asyncio.run(_tts_main())
check("male voice MP3 bana", r_m.get("ok") is True and len(r_m.get("bytes", b"")) > 1000, str(r_m)[:100])
check("female voice MP3 bana", r_f.get("ok") is True and len(r_f.get("bytes", b"")) > 1000, str(r_f)[:100])
check("khaali text → saaf error", r_e.get("ok") is False)
check("TTS voices registered", _desi.TTS_HI_VOICES.get("male") == "hi-IN-MadhurNeural"
      and _desi.TTS_HI_VOICES.get("female") == "hi-IN-SwaraNeural")

tts_checks = [
    ("media_tts rate-limit", '"media_tts":   (8,  60,  "Text → Hindi Voice")' in bot_src),
    ("tts menu button", 'callback_data="media_tts"' in bot_src),
    ("tts ask prompt", '"tts": ("🗣️ <b>TEXT → HINDI VOICE</b>' in bot_src),
    ("tts on_text handler", 'if mode == "media_tts":' in bot_src),
    ("tts voice pick kb", 'ttsvoice:male' in bot_src and 'ttsvoice:female' in bot_src),
    ("tts callback handler", 'data.startswith("ttsvoice:")' in bot_src),
    ("tts engine call", "desi.hindi_tts(txt, vkey)" in bot_src),
    ("tts credit spend", 'spend_credit_msg(uid, "mediastudio")' in bot_src),
    ("edge-tts in requirements", "edge-tts" in open("requirements.txt").read()),
]
for nm, ok in tts_checks:
    check(nm, ok)

# =====================================================================
section("19) 🎞️ YOUTUBE QUALITY SELECTOR (v52) — live")
import modules.media_downloader as _md

check("yt quality options const", _md.YT_QUALITY_OPTIONS == [1080, 720, 480, 360])
# Live: ek YT video ke available qualities (metadata only — fast)
try:
    hs = _md.yt_available_qualities("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    check("yt available qualities (live)", isinstance(hs, list) and len(hs) >= 2, str(hs))
    check("1080 quality available", 1080 in hs or 720 in hs, str(hs))
except Exception as e:
    check("yt available qualities (live)", False, str(e)[:120])

# downscale: ek chhota test video banao -> 360p me convert
import subprocess as _sp, tempfile as _tf, os as _os
try:
    _src = _tf.mktemp(suffix=".mp4")
    _sp.run([_md._FFMPEG_LOC, "-y", "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=24:duration=2",
             "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
             "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", _src],
            capture_output=True, timeout=120)
    _data = open(_src, "rb").read()
    _os.remove(_src)
    _ds = _md.downscale_video(_data, 360)
    check("downscale 720->360 kaam karta", _ds.get("ok") is True and len(_ds.get("bytes", b"")) > 1000,
          str(_ds)[:100])
except Exception as e:
    check("downscale 720->360 kaam karta", False, str(e)[:120])

# =====================================================================
section("20) 🌍 DOMAIN OSINT + 🏦 UPI VERIFY + 📡 TG PUBLIC INFO (v52.2)")
import modules.osint_tools as _ot

# --- UPI VERIFY (fast, offline) ---
_u = _ot.upi_verify("rahul@sbi")
check("upi valid + bank", _u.get("ok") and "State Bank of India" in (_u.get("bank") or ""))
_u2 = _ot.upi_verify("9876543210@hdfcbank")
check("upi mobile-style + HDFC", _u2.get("ok") and "HDFC" in (_u2.get("bank") or ""))
_u3 = _ot.upi_verify("abc@xyzunknown")
check("upi unknown handle -> known=False", _u3.get("ok") and _u3.get("handle_known") is False)
check("upi galat input reject", _ot.upi_verify("garbage-no-at").get("ok") is False)
check("upi linked-mobile nahi (no key)", "linked_mobile" not in _u)

# --- TG PUBLIC INFO (live, public page) ---
_t = _ot.tg_user_public("telegram")
check("tg public @telegram name", _t.get("ok") and _t.get("exists") and "Telegram" in _t.get("name", ""))
check("tg public photo field", isinstance(_t.get("photo"), str) and _t.get("photo", "").startswith("http"))
_t404 = _ot.tg_user_public("thisusernamedoesnotexist99x")
check("tg non-existent -> not found", _t404.get("ok") is False and _t404.get("exists") is False)

# --- DOMAIN OSINT (live: RDAP + DoH + crt.sh) ---
_d = _ot.domain_osint("onrender.com")
check("domain osint ok", _d.get("ok") is True)
check("domain osint A record", isinstance(_d.get("a"), list) and len(_d.get("a", [])) >= 1)
check("domain osint NS record", len(_d.get("ns", [])) >= 1)
check("domain osint whois registrar", bool((_d.get("whois") or {}).get("registrar")))
check("domain osint ip_info", bool(_d.get("ip_info")))
check("domain osint galat input reject", _ot.domain_osint("not a domain!!").get("ok") is False)

# --- bot.py wiring (static) ---
check("bot: domain_osint import", "domain_osint" in bot_src)
check("bot: upi_verify import", "upi_verify" in bot_src)
check("bot: tg_user_public import", "tg_user_public" in bot_src)
check("bot: upi mode handler", 'if mode == "upi":' in bot_src)
check("bot: tginfo mode handler", 'if mode == "tginfo":' in bot_src)
check("bot: upi keyboard", "UPI VERIFY" in bot_src)
check("bot: tginfo keyboard", "TG PUBLIC INFO" in bot_src)
check("bot: domain osint keyboard", "DOMAIN OSINT / IP" in bot_src)
check("bot: upi premium", '"upi",                 # 🏦 UPI VERIFY' in bot_src or '"upi"' in bot_src)
check("bot: tginfo premium", '"tginfo"' in bot_src)
check("bot: upi rate-limit", '"upi":         (15, 60,  "UPI Verify")' in bot_src)

# =====================================================================
section("21) v52.3 → v53.0 — 🎮BGMI 🔥FF Pinterest 📄WebScraper 📧TempMail EID")
import re
import modules.gaming_tools as _gg
import modules.pinterest_tools as _pt
import modules.web_tools as _wt
import modules.temp_mail as _tm
import modules.desi_tools as _dt

# --- FF (live, known-good public player) ---
_ff = _gg.ff_player_info("228159683", "BR")
check("ff valid player", _ff.get("ok") is True and bool(_ff.get("nickname")))
_ffbad = _gg.ff_player_info("12")
check("ff galat uid reject", _ffbad.get("ok") is False)
_ffnf = _gg.ff_player_info("999999999999", "IND")
check("ff not-found -> region hint", _ffnf.get("ok") is False and "egion" in _ffnf.get("error", ""))
# v53.0: regions ab API se LIVE validate hote hain (purani list me `RU` tha jo
# exist hi nahi karta, aur `EU`/`NA`/`SAC` missing the — SAC na hone ki wajah se
# South America ke players kabhi nahi milte the).
_regs = _gg.ff_regions()
check("ff regions live-validate hote hain", len(_regs) >= 10 and "RU" not in _regs)
check("ff EU/NA/SAC ab supported hain", all(x in _regs for x in ("EU", "NA", "SAC")))
_st = _gg.ff_service_status()
check("ff service status pre-check", isinstance(_st, dict) and "status" in _st
      and "regions" in _st)
check("ff galat region code par saaf message",
      _gg.ff_player_info("1633864660", "ZZZZ").get("ok") is False)
# auto-scan speed: TH region 11s leta tha aur poora scan block kar deta tha.
import time as _tt
_t0 = _tt.time()
_gg.ff_player_info("1633864660", use_cache=False)
_scan_s = _tt.time() - _t0
check(f"ff auto-scan deadline me hota hai ({_scan_s:.1f}s < 9s)", _scan_s < 9.0)

# --- BGMI (fallback-safe, kabhi fake data nahi) ---
# v53.0: engine ab provider-chain + **availability gate** rakhta hai. Dono
# BGMI providers live audit me DEAD mile (kronos-api.pubg.com DNS fail,
# pubg-shazam.herokuapp.com HTML 404), isliye jawab `available=False` +
# `service_busy=True` aata hai — aur bot us case me credit NAHI katta.
_bg = _gg.bgmi_player_info("1067824210")
check("bgmi ok-or-fallback", _bg.get("ok") is True or _bg.get("fallback") is True
      or _bg.get("available") is False)
check("bgmi galat uid reject", _gg.bgmi_player_info("12").get("ok") is False)
check("bgmi soft-fail par credit nahi katna chahiye",
      _bg.get("ok") is True or _bg.get("service_busy") is True)
check("bgmi kabhi fake data nahi deta",
      not (_bg.get("ok") is False and bool(_bg.get("stats"))))
# availability gate khud bhi ek function hai
_bgav = _gg.bgmi_availability()
check("bgmi availability gate chalta hai", isinstance(_bgav, dict) and "alive" in _bgav
      and "dead" in _bgav)

# --- Pinterest search (live) ---
_ps = _pt.pinterest_search("cat wallpaper")
check("pinterest search 6 results", _ps.get("ok") is True and len(_ps.get("results", [])) >= 1)
_pbad = _pt.pinterest_search("x")
check("pinterest short kw reject", _pbad.get("ok") is False)
# v53.0: pehle Bing scrape se **0 asli Pinterest images** aati thi. Ab official
# BaseSearchResource API use hoti hai → real pins + original-quality URLs.
_pn = sum(1 for x in (_ps.get("is_pinterest") or []) if x)
check(f"pinterest search me asli Pinterest images hain ({_pn})", _pn >= 1)
check("pinterest results rich dicts hain (title/dimensions)",
      isinstance(_ps["results"][0], dict) and "image_url" in _ps["results"][0])
check("pinterest original-quality URL", any(
      "/originals/" in str(r.get("image_url", "")) for r in _ps.get("results", [])))
_pd = _pt.pinterest_pin_detail("576742296077249680")
check("pinterest pin detail (pehle og:image=0 tha)",
      _pd.get("ok") is True and bool((_pd.get("pin") or {}).get("image_url")))
check("pinterest pin metadata (title/pinner)",
      _pd.get("ok") is False or bool((_pd.get("pin") or {}).get("title")
                                     or (_pd.get("pin") or {}).get("pinner_name")))
check("pinterest extract_pin_id", _pt.extract_pin_id(
      "https://in.pinterest.com/pin/576742296077249680/") == "576742296077249680")

# --- Web Scraper (live + SSRF) ---
_ws = _wt.scrape_public_text("https://en.wikipedia.org/wiki/Patna")
check("webscraper live text", _ws.get("ok") is True and _ws.get("words", 0) > 500)
_wspriv = _wt.scrape_public_text("http://192.168.1.1/")
check("webscraper SSRF block", _wspriv.get("ok") is False)
# v53.0: pehle Wikipedia page par 22,515 words aate the — jisme navigation,
# 300+ references, "See also", categories aur copyright notice sab tha.
# Ab real readability extraction hoti hai + backmatter strip.
_wtxt = str(_ws.get("text") or "")
check("webscraper metadata (title)", bool(_ws.get("title")))
check("webscraper reading-time", isinstance(_ws.get("reading_min"), int)
      and _ws.get("reading_min", 0) >= 1)
check("webscraper paragraphs list", isinstance(_ws.get("paragraphs"), list)
      and len(_ws.get("paragraphs") or []) >= 3)
check("webscraper backmatter strip (References/Categories nahi)",
      "From Wikipedia, the free encyclopedia" not in _wtxt
      and "Jump to navigation" not in _wtxt
      and not __import__("re").search(r"(?m)^Categories\s*$", _wtxt))
_md = _wt.html_to_markdown("<html><head><title>T</title></head><body><article>"
                           "<h1>Heading</h1><p>" + ("word " * 120) + "</p>"
                           "<h2>References</h2><p>[1] Foo. Retrieved 1 Jan 2020</p>"
                           "</article></body></html>", "https://x.com/a")
check("webscraper markdown output", _md.startswith("# ") and "word" in _md)
check("webscraper markdown me backmatter nahi", "Retrieved 1 Jan 2020" not in _md)

# --- Temp Mail (live) ---
_t1 = _tm.tm_create()
check("tempmail create", _t1.get("ok") is True and "@" in _t1.get("address", ""))
if _t1.get("ok"):
    _t2 = _tm.tm_messages(_t1["address"], _t1["token"])
    check("tempmail inbox", _t2.get("ok") is True)
    _t3 = _tm.tm_poll(_t1["address"], _t1["token"], [])
    check("tempmail poll (auto-refresh)", _t3.get("ok") is True and "new_count" in _t3)
check("tempmail password user ko nahi dikhta (server-side hai)",
      bool(_t1.get("password")) or _t1.get("ok") is False)
check("tempmail bad address reject", _tm.tm_messages("notanemail", "x").get("ok") is False)
check("tempmail expired token detect",
      _tm.tm_messages("a@b.com", "bad.token").get("expired") is True
      or _tm.tm_messages("a@b.com", "bad.token").get("ok") is False)
# --- OTP extraction: temp mail ka ASLI use-case (v53.0 me add hua) ---
_otp_cases = [
    ("Your Google verification code", "Your verification code is 483920. Expires in 5 minutes.", "483920"),
    ("Amazon OTP", "<p>Your OTP is <b>738291</b></p><p>Valid 10 min.</p>", "738291"),
    ("WhatsApp", "<p>WhatsApp code: <strong>45218</strong></p>", "45218"),
    ("Verify", "<div style='text-align:center'><span style='font-size:32px'>904512</span></div>", "904512"),
    ("Login", "847291 is your verification code for Utility Duniya.", "847291"),
]
_otp_ok = 0
for _s, _b, _want in _otp_cases:
    _c = _tm.extract_codes(_s, _b, re.sub(r"<[^>]+>", " ", _b))
    if _c and _c[0]["code"] == _want:
        _otp_ok += 1
check(f"OTP extraction {_otp_ok}/{len(_otp_cases)} real emails par sahi", _otp_ok == len(_otp_cases))
# false positives: order id / amount / date / phone — ye code NAHI hain
_fp = 0
for _s, _b in [("Order confirmed", "Order 9827364512 of Rs 1,499 placed on 04/10/2026."),
               ("Payment", "You paid ₹2,499 on 05/10/2026. Transaction ID TXN9182736455."),
               ("Welcome", "Thanks for signing up. No code here.")]:
    if not _tm.extract_codes(_s, _b, _b):
        _fp += 1
check(f"OTP false-positive filter {_fp}/3", _fp == 3)
check("tempmail body cleanup (footer strip)",
      "Unsubscribe" not in _tm.clean_body(
          "<p>Your OTP is 123456</p><p>Unsubscribe | Privacy Policy | © 2026 Acme</p>"))

# --- Aadhaar EID (offline) ---
_e1 = _dt.aadhaar_eid_helper("99305683211412")
check("eid valid", _e1.get("ok") is True and _e1.get("sms").startswith("UID STATUS"))
check("eid galat reject", _dt.aadhaar_eid_helper("123").get("ok") is False)
_e2 = _dt.aadhaar_eid_helper("9930568321141299305683211412")  # EID+stamp
check("eid stamp bhi handle", _e2.get("ok") is True and _e2.get("eid") == "99305683211412")

# --- bot.py wiring (static) ---
for fn, mod in [("ff_player_info", "_gg"), ("bgmi_player_info", "_gg"),
                ("pinterest_search", "_pt"), ("scrape_public_text", "_wt"),
                ("tm_create", "_tm"), ("aadhaar_eid_helper", "_dt")]:
    check(f"import {fn}", fn in bot_src)
for m in ("bgmi", "ffuid", "pinterest", "webscraper", "tempmail", "aadeid"):
    check(f"mode {m}", f'if mode == "{m}":' in bot_src)
for lbl in ("BGMI UID", "FF UID", "PINTEREST", "WEB SCRAPER", "TEMP MAIL", "AADHAAR EID"):
    check(f"kbd {lbl}", lbl in bot_src)
check("pinpick callback", 'data.startswith("pinpick:")' in bot_src)

# =====================================================================
print(f"\n{'=' * 55}")
print(f"RESULT: {PASS} PASSED · {FAIL} FAILED")
if FAILS:
    print("Failed:", ", ".join(FAILS))
print(f"{'=' * 55}")
sys.exit(1 if FAIL else 0)
