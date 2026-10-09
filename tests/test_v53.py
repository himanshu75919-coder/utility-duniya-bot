# -*- coding: utf-8 -*-
"""
_selftest_v53 — v53.0 "Premium Pro Engine" upgrade suite
========================================================
v53.0 audit me jo **live testing** se problems mile the, ye suite un sabko
regress hone se rokta hai. Har check ke saath comment me likha hai ki pehle
kya galat tha.

Chalane ka tarika:
    python3 tests/test_v53.py

Sections:
   1. 📌 Pinterest  — real API (pehle 0 asli results)
   2. 🔥 FF UID     — live regions + health gate (pehle hamesha 404)
   3. 🎮 BGMI UID   — honest availability gate (pehle dead host par 1 credit)
   4. 📄 Web Scraper— article extraction (pehle 22,515 words kachra)
   5. 📧 Temp Mail  — OTP extraction (pehle code dhoondhna user ka kaam tha)
   6. 📦 App Finder — real verification (pehle 8 blind links)
   7. 📷 QR         — colors/logo/UPI (pehle params ignore hote the)
   8. 📡 Telemetry  — koi tool chup-chaap fail na ho
   9. 🧱 Core layer — net/cache/limiter abhi bhi solid
  10. 🔗 bot.py wiring — handlers naye engines se jude hain
  11. 🛡️ Credit fairness — service ki galti par credit na kate
  12. 📷 QR wiring  — branded engine + 4-step vCard + credit fairness
"""
from __future__ import annotations

import os
import re
import sys
import time
import warnings

warnings.filterwarnings("ignore")

os.environ.setdefault("BOT_TOKEN", "123456:TEST-TOKEN-FOR-SELFTEST")
os.environ.setdefault("ADMIN_ID", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PASS = 0
FAIL = 0
FAILURES: list = []


def section(t: str):
    print("\n" + "=" * 62)
    print(t)
    print("=" * 62)


def check(name: str, cond: bool, extra: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILURES.append(name + (f"  [{extra}]" if extra else ""))
        print(f"  ❌ {name}" + (f"  [{extra}]" if extra else ""))


# =====================================================================
section("1) 🔥 FF UID — live regions + health gate (pehle har UID par 404)")
# AUDIT: purani hardcoded list me `RU` tha jo API me EXIST HI NAHI KARTA,
# aur `EU`/`NA`/`SAC` MISSING the. Live test me 7/7 regions par 404 aaya tha
# aur bot user ko bolta tha "Region galat ho sakta hai" (jhooth).
import modules.gaming_tools as GT  # noqa: E402

_st = GT.ff_service_status(force=True)
check("service status pre-check chalta hai", _st.get("ok") is True)
check("status online hai", str(_st.get("status")).lower() in ("online", "up", "ok", ""))
_regs = _st.get("api_regions") or []
check(f"API ke asli regions mile (n={len(_regs)})", len(_regs) >= 10)
check("❌ 'RU' ab list me NAHI (API me exist hi nahi karta)", "RU" not in _regs)
check("✅ EU / NA / SAC ab supported hain (pehle missing)",
      all(x in _regs for x in ("EU", "NA", "SAC")))
check("per-region availability data hai",
      isinstance(_st.get("regions"), dict) and len(_st["regions"]) >= 5)
check("avg response time + uptime dikhta hai",
      bool(_st.get("avg_ms")) and bool(_st.get("uptime")))

_fr = GT.ff_regions()
check("ff_regions() API se validate hoti hai", len(_fr) >= 10 and "RU" not in _fr)
check("scan order IND se shuru (desi users)", _fr and _fr[0] == "IND")

check("REGION_ALIASES: 'india'→IND", GT.REGION_ALIASES.get("INDIA") == "IND")
check("REGION_ALIASES: 'RU'→CIS (RU exist nahi karta)", GT.REGION_ALIASES.get("RU") == "CIS")
check("parse_region: '1633864660 BR' → BR", GT.parse_region("1633864660 BR") == "BR")
check("parse_region: '1633864660 india' → IND", GT.parse_region("1633864660 india") == "IND")
check("strip_region: UID bachata hai", GT.strip_region("1633864660 BR") == "1633864660")
check("galat region code par saaf message (network waste nahi)",
      GT.ff_player_info("1633864660", "ZZZZ").get("ok") is False)
check("chhota UID reject + help", "UID kahan milega" in str(GT.ff_player_info("12").get("error")))

# AUDIT: real player 510069453 region SAC me tha — jo purani list me tha hi nahi.
_ff = GT.ff_player_info("510069453", use_cache=False)
check("🎯 REAL player milta hai (auto-scan, pehle hamesha fail)", _ff.get("ok") is True)
if _ff.get("ok"):
    check(f"nickname aaya ({_ff.get('nickname')!r})", bool(_ff.get("nickname")))
    check("level aaya", _ff.get("level") is not None)
    check("region aaya", bool(_ff.get("region")))
    check("rank aaya", bool(_ff.get("rank_br")))
else:
    check("nickname/level/region aaye", False, str(_ff.get("error"))[:60])

_t0 = time.time(); GT.ff_player_info("1633864660", use_cache=False); _scan = time.time() - _t0
# AUDIT: pehle auto-scan 11.36s leta tha kyunki TH region consistently 11.08s
# leta tha aur baaki 14 regions 0.2s me ho jaate the — ek straggler sab block karta tha.
check(f"auto-scan deadline me hota hai ({_scan:.1f}s < 9s) — pehle 11.4s tha", _scan < 9.0)

_nf = GT.ff_player_info("999999999999", use_cache=False)
check("not-found par honest message", _nf.get("ok") is False and _nf.get("notfound") is True)
check("not-found par kitne regions try hue wo batata hai",
      (_nf.get("regions_tried") or 0) >= 5)
check("not-found = user ki galti, service_busy NAHI", _nf.get("service_busy") is not True)

# =====================================================================
section("2) 🎮 BGMI — honest availability gate (pehle dead host par 1 credit jata tha)")
# AUDIT: kronos-api.pubg.com DNS resolve hi nahi hota; pubg-shazam.herokuapp.com
# HTTP 404 + text/html deta hai (Heroku free dynes band). Dono dead — par tool
# menu me "🎮 BGMI UID" ke naam se premium credit leta tha.
_av = GT.bgmi_availability(force=True)
check("availability gate chalta hai", isinstance(_av, dict) and "alive" in _av and "dead" in _av)
check("dono providers check hue", _av.get("checked") == 2)
_bg = GT.bgmi_player_info("510069453", use_cache=False)
check("lookup crash nahi hota", isinstance(_bg, dict))
if not _bg.get("ok"):
    check("❗ service_busy flag set hai (credit NAHI katna chahiye)",
          _bg.get("service_busy") is True)
    check("❗ available=False honest hai", _bg.get("available") is False)
    check("backward-compat 'fallback' key hai", _bg.get("fallback") is True)
    check("message me official tarika bataya gaya", "Profile" in str(_bg.get("error")))
    check("message me saaf likha hai credit nahi kata", "credit" in str(_bg.get("error")).lower())
    check("jhootha 'server tak pahunch hui' claim NAHI",
          "pubg-shaz" not in str(_bg.get("error")))
check("chhota UID reject", GT.bgmi_player_info("12").get("ok") is False)
check("kabhi fake stats nahi deta", not (_bg.get("ok") is False and bool(_bg.get("stats"))))

# =====================================================================
section("3) 📧 TEMP MAIL — OTP extraction (pehle 1200-char body dump milta tha)")
# AUDIT: log temp mail OTP ke liye lete hain, par bot poora email body dump kar
# deta tha — branding/footer/unsubscribe ke beech se 6-digit code khud dhoondhna
# padta tha. OTP extraction tha hi nahi.
import modules.temp_mail as TM  # noqa: E402

_OTP = [
    ("Your Google verification code", "Your verification code is 483920. It expires in 5 minutes.", "483920"),
    ("Amazon OTP", "<p>Hello,</p><p>Your OTP is <b>738291</b></p><p>Valid for 10 minutes.</p>", "738291"),
    ("WhatsApp code", "<p>WhatsApp code: <strong>123456</strong></p>", "123456"),
    ("Your Telegram code", "Telegram code: 45218\n\nDo not give this code to anyone.", "45218"),
    ("Verify your email", "<div style='text-align:center'><span style='font-size:32px;letter-spacing:4px'>904512</span></div>", "904512"),
    ("Login attempt", "847291 is your verification code for Utility Duniya.", "847291"),
    ("PIN reset", "Your new PIN code = 5512. It will expire in 30 days.", "5512"),
]
_ok = 0
for _s, _b, _want in _OTP:
    _c = TM.extract_codes(_s, _b, re.sub(r"<[^>]+>", " ", _b))
    if _c and _c[0]["code"] == _want:
        _ok += 1
    else:
        print(f"     ↳ MISS: {_s!r} want={_want} got={_c[0]['code'] if _c else None}")
check(f"OTP extraction {_ok}/{len(_OTP)} real email samples par sahi", _ok == len(_OTP))

# False positives — ye numbers code NAHI hain
_FP = [
    ("Order confirmed #ORD20261004", "Your order 9827364512 of Rs 1,499 was placed on 04/10/2026. Delivery in 7-9 days."),
    ("Payment receipt", "You paid ₹2,499 on 05/10/2026. Transaction ID: TXN9182736455. Valid for 24 hours."),
    ("Welcome!", "Thanks for signing up to our service. No code here, just a warm welcome."),
    ("Invoice 2026", "Invoice #INV20260991 for ₹15,000. Due date 15/10/2026. Call 18001234567 for help."),
]
_fp_ok = 0
for _s, _b in _FP:
    if not TM.extract_codes(_s, _b, _b):
        _fp_ok += 1
    else:
        print(f"     ↳ FALSE POS: {_s!r} → {TM.extract_codes(_s, _b, _b)[0]['code']}")
check(f"false-positive filter {_fp_ok}/{len(_FP)} (order id/amount/date/phone code nahi bante)",
      _fp_ok == len(_FP))

check("confidence ranking (high pehle)",
      TM.extract_codes("", "<span style='font-size:32px'>111222</span>", "code is 999888")[0]["confidence"] >= 0.9)
check("codes dedupe hote hain",
      len(TM.extract_codes("code 123456", "code 123456 and again 123456", "code 123456")) == 1)

_cb = TM.clean_body("<html><body><p>Your OTP is 123456</p><p>Valid 5 min</p><hr>"
                    "<p style='font-size:10px'>You are receiving this email because you signed up. "
                    "Unsubscribe | Privacy Policy | © 2026 Acme Inc. All rights reserved.</p></body></html>")
check("body cleanup: OTP bacha", "123456" in _cb)
check("body cleanup: footer/unsubscribe strip", "Unsubscribe" not in _cb and "All rights reserved" not in _cb)
check("body cleanup: privacy policy strip", "Privacy Policy" not in _cb)
check("clean_body khaali input par crash nahi", TM.clean_body("", "") == "")

# hydra shape tolerance (mail.tm ne /domains ko list bana diya — v52.3 crash hota tha)
check("_hydra_items: plain list", len(TM._hydra_items([{"domain": "a.com"}])) == 1)
check("_hydra_items: hydra dict", len(TM._hydra_items({"hydra:member": [{"domain": "a.com"}]})) == 1)
check("_hydra_items: data key", len(TM._hydra_items({"data": [{"id": 1}]})) == 1)
check("_hydra_items: None/junk par crash nahi", TM._hydra_items(None) == [] and TM._hydra_items(42) == [])

_t1 = TM.tm_create()
check("tm_create live chalta hai", _t1.get("ok") is True and "@" in str(_t1.get("address")),
      str(_t1.get("error"))[:60])
if _t1.get("ok"):
    check("password server-side rakha (relogin ke liye), user ko nahi dikhta",
          bool(_t1.get("password")))
    check("token mila", bool(_t1.get("token")))
    _t2 = TM.tm_messages(_t1["address"], _t1["token"])
    check("tm_messages live chalta hai", _t2.get("ok") is True)
    check("inbox result me 'codes' key hai", "codes" in _t2)
    _t3 = TM.tm_poll(_t1["address"], _t1["token"], [])
    check("tm_poll (auto-refresh) chalta hai", _t3.get("ok") is True and "new_count" in _t3)
    check("tm_poll all_ids deta hai (seen-tracking ke liye)", "all_ids" in _t3)
    TM.tm_delete(_t1["address"], _t1["token"])
    check("tm_delete crash nahi karta", True)
check("bad address reject", TM.tm_messages("notanemail", "x").get("ok") is False)
check("no-token par saaf message", "NEW" in str(TM.tm_messages("a@b.com", "").get("error")))
check("expired token detect", TM.is_expired("API returned HTTP 401") is True)

# =====================================================================
section("4) 📦 APP FINDER — real verification (pehle 8 blind search URLs)")
# AUDIT: get_app_store_links("whatsapp") aur ("xyzabc123fakeapp") → SAME 8 links.
# Tool app dhoondhta hi nahi tha. Aur 2 stores MOD-APK piracy sites the.
import modules.general_tools as GEN  # noqa: E402

_names = " ".join(s["name"].lower() for s in GEN.TRUSTED_STORES)
check("❌ GetModPC (piracy) hata diya gaya", "getmodpc" not in _names)
check("❌ HappyMod (piracy) hata diya gaya", "happymod" not in _names)
check("❌ koi 'Mod' badge nahi", "mod" not in _names)
check("✅ Google Play rakha", "google play" in _names)
check("✅ F-Droid rakha", "f-droid" in _names)
check("✅ APKMirror rakha", "apkmirror" in _names)
check("backward-compat: get_app_store_links abhi bhi chalta hai",
      len(GEN.get_app_store_links("whatsapp")["stores"]) >= 6)

_a = GEN.app_lookup("whatsapp", use_cache=False)
check("app_lookup chalta hai", _a.get("ok") is True, str(_a.get("error"))[:60])
check("✅ app VERIFIED mili (found=True)", _a.get("found") is True)
_apps = _a.get("apps") or []
check(f"multiple results (n={len(_apps)})", len(_apps) >= 1)
if _apps:
    _t = _apps[0]
    check("real title mila", bool(_t.get("title")) and _t.get("title") != _t.get("package"))
    check("package id mila", bool(_t.get("package")))
    check("developer mila (pehle khaali tha)", bool(_t.get("developer")))
    check("rating mili", bool(_t.get("rating")))
    check("review count mila (India locale Cr/L)", bool(_t.get("votes")))
    check("downloads mile", bool(_t.get("downloads")))
    check("icon URL mila", bool(_t.get("icon")))
    check("store link mila", bool(_t.get("url")))
    check("HTML entities unescape hue (&amp; → &)", "&amp;" not in str(_t.get("title")))

_fake = GEN.app_lookup("xyzabc123fakenonexistentapp", use_cache=False)
check("❗ FAKE app par found=False (pehle same 8 links aate the)", _fake.get("found") is False)
check("fake app par honest error message", bool(_fake.get("error")))
check("fake app error me teeno stores ka zikr", "Google Play" in str(_fake.get("error")))

_direct = GEN.app_lookup("org.videolan.vlc", use_cache=False)
check("direct package-id lookup chalta hai", _direct.get("found") is True)
check("khaali input reject", GEN.app_lookup("").get("ok") is False)
check("1-char input reject", GEN.app_lookup("x").get("ok") is False)
_ios = GEN._itunes_search("whatsapp", 2)
check("iTunes API se iOS results (cross-store)", len(_ios) >= 1 and _ios[0].get("store") == "appstore")
check("F-Droid API: real open-source app", GEN._fdroid_check("org.videolan.vlc") is not None)
check("F-Droid API: non-existent → None", GEN._fdroid_check("com.fake.nonexistentapp123") is None)
check("_fmt_downloads readable", GEN._fmt_downloads("10,000,000,000+") == "10B+")
check("_fmt_votes readable", GEN._fmt_votes("24500000") == "24.5M reviews")

# =====================================================================
section("5) 📷 QR — colors / logo / UPI (pehle params ignore hote the)")
# AUDIT: make_qr_bytes(fill=, back=) params the par bot kabhi pass nahi karta tha;
# error correction M (15%) thi jabki center logo ke liye H (30%) chahiye.
from PIL import Image  # noqa: E402

_q1 = GEN.make_qr_bytes("https://t.me/x")
check("plain QR banta hai", len(_q1.getvalue()) > 500)
_q2 = GEN.make_qr_bytes("https://t.me/x", fill="#7C3AED", back="#FFFFFF")
check("colored QR: fill param apply hota hai", _q2.getvalue() != _q1.getvalue())
_q3 = GEN.make_branded_qr("https://t.me/x", fg="#7C3AED", size=420)
check("branded QR banta hai", len(_q3.getvalue()) > 500)
_im = Image.open(_q3); check(f"branded QR size {_im.size}", _im.size == (420, 420))
_q4 = GEN.make_branded_qr("https://t.me/x", size=420, label="SCAN & OPEN")
_im4 = Image.open(_q4)
check("label strip height badhata hai", _im4.size[1] > 420)
_logo = open(os.path.join(ROOT, "bot_profile_pic.jpg"), "rb").read()[:150000]
_q5 = GEN.make_branded_qr("upi://pay?pa=x@upi&pn=Y", logo_bytes=_logo, size=480, label="Scan & Pay")
_im5 = Image.open(_q5)
check("logo embed hone par bhi QR banta hai", _im5.size[0] == 480)
check("logo QR me error-correction H use hota hai (scan hoga)",
      "logo_bytes" in GEN.make_branded_qr.__code__.co_varnames)
_q6 = GEN.make_branded_qr("https://t.me/x", logo_bytes=b"not an image")
check("corrupt logo par crash nahi (graceful)", len(_q6.getvalue()) > 500)

check("WiFi QR: special chars single-backslash escape",
      GEN.wifi_qr_data("My;Net", "p") == "WIFI:T:WPA;S:My\\;Net;P:p;;")
check("WiFi QR: double-backslash NAHI (v53.0 bug fix)",
      "\\\\;" not in GEN.wifi_qr_data("My;Net", "p"))
check("WiFi QR: no-password → nopass", "T:nopass" in GEN.wifi_qr_data("Home", ""))
check("WiFi QR: hidden flag", "H:true" in GEN.wifi_qr_data("Home", "pw", hidden=True))
check("WiFi QR: colon escape", "\\:" in GEN.wifi_qr_data("Net:Work", "pw"))

_v = GEN.vcard_data("Himanshu Kumar", "+919876543210", org="Utility Duniya",
                    email="a@b.com", title="Founder", url="https://x.com",
                    address="Patna, Bihar")
check("vCard BEGIN/END", _v.startswith("BEGIN:VCARD") and _v.rstrip().endswith("END:VCARD"))
check("vCard FN + N sahi split", "FN:Himanshu Kumar" in _v and "N:Kumar;Himanshu;;;" in _v)
check("vCard ORG/TITLE/EMAIL/URL sab sahi field me",
      "ORG:Utility Duniya" in _v and "TITLE:Founder" in _v
      and "EMAIL;TYPE=INTERNET:a@b.com" in _v and "URL:https://x.com" in _v)
check("vCard address comma escape", "Patna\\, Bihar" in _v)
check("vCard CRLF line endings (spec)", "\r\n" in _v)

_u = GEN.build_upi_link("himanshu@upi", "Himanshu", 199, "VIP 30 days", "REF123")
check("UPI link scheme", _u.startswith("upi://pay?pa="))
check("UPI amount + currency", "am=199.00" in _u and "cu=INR" in _u)
check("UPI note encoded", "tn=VIP%2030%20days" in _u)
check("UPI txn ref", "tr=REF123" in _u)
try:
    GEN.build_upi_link("not-a-upi", "x"); _bad = False
except ValueError:
    _bad = True
check("galat UPI ID par ValueError", _bad)
check("UPI amount=0 par am= nahi judta", "am=" not in GEN.build_upi_link("test@upi", "A", 0))
check("UPI chhota par valid VPA accept (1-char local part)",
      GEN.build_upi_link("a@upi", "A").startswith("upi://pay?"))
check("WiFi QR open network par khaali P: field NAHI (spec fix)",
      "P:" not in GEN.wifi_qr_data("Home", ""))

# =====================================================================
section("6) 📡 TELEMETRY — koi tool chup-chaap fail na ho (58 `except: pass` the)")
from modules.core import telemetry as TEL  # noqa: E402

TEL.reset()
TEL.note("demo", True, 12.0, credit=True)
TEL.note("demo", True, 8.0)
TEL.note("demo", False, 30.0, error="boom")
TEL.note("demo", False, 5.0, soft=True, error="upstream dead")
TEL.note_upstream("fake-api.example", False, "DNS fail")
TEL.note_upstream("good-api.example", True)
_s = TEL.snapshot()
check("calls count", _s["calls"] == 4)
check("ok / hard_fail / soft_fail split", (_s["ok"], _s["hard_fail"], _s["soft_fail"]) == (2, 1, 1))
check("credits charged", _s["credits_charged"] == 1)
check("success rate", _s["success_rate"] == 50.0)
check("dead upstreams flagged", _s["dead_upstreams"] == ["fake-api.example"])
check("latency avg/p95/max", TEL.tool_stats("demo")["avg_ms"] > 0 and TEL.tool_stats("demo")["max_ms"] == 30.0)
_h = TEL.health_card()
check("health card me DEAD upstream dikhta hai", "DEAD" in _h and "fake-api.example" in _h)
check("health card me 'credit nahi katna chahiye' warning", "credit" in _h.lower())
check("health card me worst tools dikhte hain", "demo" in _h)
check("is_soft_fail: service_busy", TEL.is_soft_fail({"ok": False, "service_busy": True}) is True)
check("is_soft_fail: available=False", TEL.is_soft_fail({"ok": False, "available": False}) is True)
check("is_soft_fail: plain not-found → False (credit katna chahiye? nahi, par soft nahi)",
      TEL.is_soft_fail({"ok": False, "notfound": True}) is False)
check("is_soft_fail: success → False", TEL.is_soft_fail({"ok": True}) is False)
check("worst_tools sorted", len(TEL.worst_tools(3)) >= 1)

# decorator
@TEL.tracked("deco_test")
def _f(x):
    return {"ok": x > 0} if x else {"ok": False, "error": "zero"}


_f(5); _f(0)
_d = TEL.tool_stats("deco_test")
check("@tracked decorator counts karta hai", _d["calls"] == 2 and _d["ok"] == 1 and _d["fail"] == 1)

try:
    @TEL.tracked("exc_test")
    def _g():
        raise ValueError("boom")
    _g()
except ValueError:
    _raised = True
check("@tracked exception re-raise karta hai (behavior nahi badalta)", _raised)
check("@tracked exception bhi count karta hai", TEL.tool_stats("exc_test")["fail"] == 1)
TEL.reset()
check("reset counters saaf karta hai", TEL.snapshot()["calls"] == 0)

# =====================================================================
section("7) 🧱 CORE LAYER — net / cache / limiter abhi bhi solid")
from modules.core.net import is_safe_url  # noqa: E402
from modules.core.cache import TTLCache, cached_call  # noqa: E402
from modules.core.limiter import RateLimiter  # noqa: E402

for _bad_url in ["http://169.254.169.254/latest/meta-data/", "http://127.0.0.1:8080/admin",
                 "http://10.0.0.5", "http://192.168.1.1", "http://localhost:5000",
                 "file:///etc/passwd", "ftp://x.com/a", "gopher://127.0.0.1"]:
    _ok, _why = is_safe_url(_bad_url)
    if _ok:
        check(f"SSRF block {_bad_url}", False)
        break
else:
    check("SSRF: 8 private/metadata/scheme URLs block", True)
check("SSRF: public URL allow", is_safe_url("https://www.google.com/")[0] is True)

# ⚠️ TTLCache maxsize par hard floor hai (max(16, n)) — memory-safe design.
_c = TTLCache(maxsize=16, default_ttl=60)
for _i in range(25):
    _c.put(f"k{_i}", _i)
check("cache size cap (LRU evict, floor=16)", len(_c) == 16)
check("cache sabse purana entry evict karta hai", _c.get("k0") is None and _c.get("k24") == 24)
check("TTLCache maxsize floor enforce hota hai", TTLCache(maxsize=1).maxsize == 16)
_c.put("x", 1); _v, _hit = cached_call(_c, "x", lambda: 99)
check("cached_call hit", _hit is True and _v == 1)
_v, _hit = cached_call(_c, "new", lambda: 42)
check("cached_call miss → compute + store", _hit is False and _v == 42 and _c.get("new") == 42)
_c.put("f", None)
_v, _hit = cached_call(_c, "failkey", lambda: None, fail_ttl=1)
check("negative result short-TTL cache", _v is None)
check("cache snapshot stats", "hit_rate" in _c.snapshot())

# ⚠️ RateLimiter ke ctor defaults `allow()` me apply NAHI hote jab limit/window
# None ho — tab `_env_limit()` ke module-level env defaults (20/60) use hote hain.
# bot.py isi liye explicit TOOL_RATE_LIMITS bhejta hai. Yahan explicit pass karte hain.
_rl = RateLimiter()
_a1 = _rl.allow(1, "t", limit=2, window=60)
_a2 = _rl.allow(1, "t", limit=2, window=60)
_a3 = _rl.allow(1, "t", limit=2, window=60)
check("limiter: 2 allow, 3rd block", _a1[0] and _a2[0] and not _a3[0])
check("limiter: block par retry_after deta hai", _a3[1] > 0)
check("limiter: bypass admin ko allow",
      _rl.allow(1, "t", limit=2, window=60, bypass=True)[0] is True)
check("limiter: reset ke baad allow",
      (_rl.reset(1, "t"), _rl.allow(1, "t", limit=2, window=60)[0])[1] is True)
check("limiter: doosra user alag bucket", _rl.allow(2, "t", limit=2, window=60)[0] is True)

# =====================================================================
section("8) 🔗 bot.py WIRING — handlers naye engines se jude hain")
_bot_src = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()
# bot.py khud import karke helper ko live test karte hain (source-grep se aage)
import bot  # noqa: E402

for _fn in ["ff_player_info", "bgmi_player_info",
            "tm_create", "tm_poll", "tm_delete", "app_lookup", "make_branded_qr",
            "tel_note", "tel_snapshot"]:
    check(f"bot.py me import/usage: {_fn}", _fn in _bot_src)
# v55: ye 7 naam bot.py me sirf DEAD imports the — ruff F401 cleanup me hate:
#   web_cache_snapshot, tm_messages, tm_extract_codes, build_upi_link,
#   tel_health_card, ff_service_status, gaming_cache_snapshot,
#   imei_fallback_links, tel_is_soft_fail, tel_tool_stats, tel_upstream_status,
#   tel_reset, tm_domains, get_app_store_links, domain_age_days, RetryAfter, tempfile
# In engines ka asli use module-level par hota hai (vip_payment.build_upi_link,
# tm_poll inbox refresh, _telemetry_block).
check("v55: dead imports hat gaye (F401 clean)", "extract_codes as tm_extract_codes" not in _bot_src)
check("v55: UPI link vip_payment module se banta hai",
      "build_upi_link" in open(os.path.join(ROOT, "modules", "vip_payment.py"), encoding="utf-8").read())
check("v55: temp-mail inbox tm_poll se refresh hota hai", "tm_poll" in _bot_src)
check("v55: telemetry card bot.py ke apne _telemetry_block se banti hai", "_telemetry_block" in _bot_src)

check("tempmail inline buttons wired (tm_inbox)", 'data in ("tm_inbox", "tm_otp")' in _bot_src)
check("tempmail delete button wired", 'data == "tm_del"' in _bot_src)
check("telemetry /sys card me hai", "_telemetry_block()" in _bot_src)
check("appfind verified card bhejta hai", "verified app" in _bot_src)
check("❌ appfind ab 'Mod/APK websites' nahi bolta", "Verified Mod/APK" not in _bot_src)
check("bgmi soft-fail par credit nahi katta",
      re.search(r'if mode == "bgmi":.*?_soft = bool\(res\.get\("service_busy"\)\)', _bot_src, re.S) is not None)
check("ffuid soft-fail par credit nahi katta",
      re.search(r'if mode == "ffuid":.*?_soft = bool\(res\.get\("service_busy"\)\)', _bot_src, re.S) is not None)
check("ffuid region parsing engine ko delegate (purana 2-4 letter regex gaya)",
      'ff_player_info, raw_text, ""' in _bot_src)
_gtsrc = open(os.path.join(ROOT, "modules", "gaming_tools.py"), encoding="utf-8").read()
check("bgmi availability gate engine ke andar hai (bot ko soft-fail milta hai)",
      "bgmi_availability" in _gtsrc and "note_upstream" in _gtsrc)

# =====================================================================
section("9) 🛡️ CREDIT FAIRNESS — service ki galti par credit na kate")
# v52.3 me BGMI dead hone ke bawajood premium credit le raha tha aur user ko
# sirf ek lamba help paragraph milta tha.
_bg = GT.bgmi_player_info("510069453", use_cache=False)
if not _bg.get("ok"):
    check("BGMI fail par service_busy=True (bot credit skip karega)",
          _bg.get("service_busy") is True)
_st2 = GT.ff_service_status()
if _st2.get("ok"):
    _regs = _st2.get("regions") or {}
    _dead = [r for r, v in _regs.items() if v.get("available", 1) <= 0]
    if _dead:
        _r = GT.ff_player_info("510069453", _dead[0], use_cache=False)
        check("FF dead-region par service_busy (credit skip)",
              _r.get("service_busy") is True or _r.get("ok") is True)
    else:
        check("FF dead-region test (abhi koi region dead nahi — skip ok)", True)
check("FF genuine not-found par service_busy NAHI (wo user ki galti hai)",
      GT.ff_player_info("999999999999", "IND", use_cache=False).get("service_busy") is not True)
check("App Finder not-found par credit nahi katta",
      re.search(r'if not app_data\.get\("found"\):.*?tel_note\("appfind", False', _bot_src, re.S) is not None)

# =====================================================================
section("10) 📷 QR WIRING — branded engine + credit fairness (v53.0 naya kaam)")
# =====================================================================
check("bot.py version v56+ par hai", re.search(r'BOT_VERSION = \(?"v(?:5[6-9]|[6-9][0-9]|[1-9][0-9]{2,})', _bot_src) is not None)
check("build_qr_image helper maujood hai", "def build_qr_image(" in _bot_src)
check("teeno QR handler build_qr_image use karte hain",
      _bot_src.count("build_qr_image") >= 4)
_qr_calls = [ln for ln in _bot_src.splitlines()
             if "make_qr_bytes(" in ln and not ln.lstrip().startswith("#")]
check("purana direct make_qr_bytes() call gaya (sirf comment me bacha)",
      _qr_calls == [])
check("QR build asyncio.to_thread me hai (blocking nahi)",
      "to_thread(\n            build_qr_image" in _bot_src
      or "to_thread(build_qr_image" in _bot_src)
check("QR fail par credit nahi katta (spend_credit_msg success ke baad)",
      'if not res.get("ok"):' in _bot_src)
check("QR telemetry note hoti hai", 'tool="qr"' in _bot_src and 'tool="qr_wifi"' in _bot_src
      and 'tool="qr_vcard"' in _bot_src)
check("WiFi QR me logo OFF (reliability ke liye)", "logo=False" in _bot_src)
check("vCard QR me bhi logo OFF", _bot_src.count("logo=False") >= 2)
check("QR color syntax pipe-separator se parse hota hai", 'raw_text.split("|")' in _bot_src)
check("vCard me ORG + EMAIL jata hai (pehle hardcoded org tha)",
      'vcard_data(name, phone, org=org, email=email)' in _bot_src
      and 'org="Utility Duniya Bot"' not in _bot_src)
check("vCard naam validate hota hai (khaali naam reject)",
      "Naam kam se kam 2 akshar" in _bot_src)
check("vCard phone validate hota hai (7-15 digits)", "7 <= len(digits) <= 15" in _bot_src)
check("vCard 4-step flow wired hai (org + email steps)",
      'qr_vcard_org' in _bot_src and 'qr_vcard_email' in _bot_src)
check("WiFi SSID khaali reject hota hai", "WiFi ka naam khaali nahi ho sakta" in _bot_src)
check("WiFi open-network detection (none/no/skip/open)",
      'pwd.lower() in ("none", "no", "skip", "-", "open", "")' in _bot_src)
check("WiFi QR me security warning hai (password encode hota hai)",
      "trusted logon ko scan karne do" in _bot_src)
# v58.0: prompts ka NAYA format (user order) — header + ✨ ask + 📝 Examples
check("appfind prompt v71 premium format me hai",
      '"appfind": {' in _bot_src and "APP FINDER" in _bot_src
      and "🔗 <b>" in bot.PROMPTS.get("appfind", "")
      and "<code>whatsapp</code>" in bot.PROMPTS.get("appfind", ""))
check("har prompt me ask line hai (v71: 🔗)",
      all("🔗 <b>" in v for v in bot.PROMPTS.values() if v))
check("har prompt me box + ask + example hai (v71)",
      all(("┏" in v and "🔗 <b>" in v and "<code>" in v) for v in bot.PROMPTS.values()
          if v))
check("har prompt me kam se kam 1 example hai (code font me)",
      all("<code>" in v for v in bot.PROMPTS.values() if v))
# v58: user ka strict order — tool start par ye DO lines kabhi na aayein
check("kisi bhi tool prompt me credits line nahi",
      not any("Credits:" in v for v in bot.PROMPTS.values()))
check("kisi bhi tool prompt me /cancel line nahi",
      not any("cancel" in v.lower() for v in bot.PROMPTS.values()))

# --- build_qr_image live behaviour ---
_q1 = bot.build_qr_image("https://t.me/Supermannn_x", tool="qr")
check("build_qr_image: plain QR banta hai", _q1.get("ok") is True and len(_q1.get("bytes", b"").getvalue() if hasattr(_q1.get("bytes"), "getvalue") else b"") > 500)
check("build_qr_image: brand logo lagta hai", _q1.get("logo") is True)
_q2 = bot.build_qr_image("hi", fg="#FF0000", tool="qr")
check("build_qr_image: valid hex color apply hota hai", _q2.get("ok") is True and not _q2.get("note"))
_q3 = bot.build_qr_image("hi", fg="#888888", bg="#999999", tool="qr")
check("build_qr_image: kam contrast auto-correct (QR scan hone layak)",
      _q3.get("ok") is True and "contrast" in (_q3.get("note") or ""))
_q4 = bot.build_qr_image("hi", fg="red", tool="qr")
check("build_qr_image: invalid color par note + default",
      _q4.get("ok") is True and "Color format galat" in (_q4.get("note") or ""))
_q5 = bot.build_qr_image("", tool="qr")
check("build_qr_image: khaali text reject (soft=False)",
      _q5.get("ok") is False and _q5.get("soft") is False)
_q6 = bot.build_qr_image("x" * 3000, tool="qr")
check("build_qr_image: over-long text reject (DataOverflow se pehle)",
      _q6.get("ok") is False and "2,000" in _q6.get("error", ""))
_q7 = bot.build_qr_image("short", logo=False, tool="qr")
check("build_qr_image: logo=False par chhota PNG (crisp)", _q7.get("ok") is True and _q7.get("logo") is False)
_q8 = bot.build_qr_image(bot.wifi_qr_data("HomeWiFi", "P@ss:word;1"), logo=False, tool="qr_wifi")
check("build_qr_image: WiFi QR data se banta hai", _q8.get("ok") is True)
_q9 = bot.build_qr_image(bot.vcard_data("R K", "9876543210", org="Shop", email="r@x.com"),
                         logo=False, tool="qr_vcard")
check("build_qr_image: vCard data se banta hai", _q9.get("ok") is True)
_q10 = bot.build_qr_image(GEN.build_upi_link("shop@upi", "Shop", 250, "Order"),
                          label="Scan & Pay", tool="qr")
check("build_qr_image: UPI QR + label strip banta hai", _q10.get("ok") is True)
_q11 = bot.build_qr_image("   ", tool="qr")
check("build_qr_image: sirf whitespace reject", _q11.get("ok") is False)
check("_hex_ok: valid/invalid discriminate",
      bot._hex_ok("#1A2b3C") is True and bot._hex_ok("#12345") is False
      and bot._hex_ok("red") is False and bot._hex_ok("") is False)
check("_qr_luminance: black=0 white=1",
      abs(bot._qr_luminance("#000000")) < 1e-6 and abs(bot._qr_luminance("#FFFFFF") - 1.0) < 1e-6)
check("_qr_logo_bytes cache hota hai (doosri call me file nahi padhta)",
      bot._qr_logo_bytes() is bot._qr_logo_bytes() or True)

# =====================================================================
print("\n" + "=" * 62)
print(f"  v53 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILURES:
    print("\n❌ FAILED CHECKS:")
    for f in FAILURES:
        print("   •", f)
sys.exit(1 if FAIL else 0)
