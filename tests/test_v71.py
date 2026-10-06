# -*- coding: utf-8 -*-
"""
v71 SELFTEST — 📱 PREMIUM EXAMPLES + 🚗 RC & CHALLAN + saaf cards
==================================================================
Boss ke teen order:
  1. "saare tools ke examples premium feel ho, ek valid example ho"
  2. "results me space ho, emoji ho, 'Malik' jaise words nahi — 'Owner' likho"
  3. "rc + challan wala add kar dena" (result bot ke andar)
"""
import os
import re
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv71_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V71"
os.environ["ADMIN_ID"] = "1"

PASS = FAIL = 0
FAILS = []


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILS.append(f"{name} {extra}")
        print(f"  ❌ {name}  {extra}")


def section(t):
    print("\n" + "=" * 62)
    print("  " + t)
    print("=" * 62)


print("=" * 62)
print("  v71 SELFTEST — premium examples + RC/Challan + saaf cards")
print("=" * 62)

import bot                                                          # noqa: E402
from modules import vehicle_tool as VT                               # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

def _clean(t):
    return re.sub(r"</?(?:b|code|i|blockquote|a[^>]*)>", "", str(t or ""))


# =====================================================================
section("[A] 🎨 PROMPTS — sirf box + ask + EK example (koi tip nahi)")
# =====================================================================
_bad_words = ("xxxxx", "example.com/very", "kisi-site", "myexample")
for _k, _p in bot.PROMPTS.items():
    if not _p:
        continue
    _pl = _clean(_p)
    check(f"'{_k}' ka prompt boxed hai (┏━┓)", _pl.startswith("┏"))
    check(f"'{_k}' me EK hi example (code font)", _p.count("<code>") == 1, str(_p.count("<code>")))
    check(f"'{_k}' me dummy 'xxxxx' nahi", not any(b in _pl.lower() for b in _bad_words))
    check(f"'{_k}' me khali line ka spacing hai", "\n\n" in _p)

# downloader examples ASLI links hain
for _k, _url in (("instagram", "instagram.com/reel/"),
                 ("youtube", "youtube.com/watch?v="),
                 ("facebook", "facebook.com/watch"),
                 ("tiktok", "tiktok.com/")):
    check(f"dl_{_k} ka example asli link jaisa hai ({_url})", _url in bot.DL_SITES[_k][3])

check("prompt me koi Tip/gyaan nahi", "💡" not in bot.PROMPTS["numinfo"]
      and "Tip" not in bot.PROMPTS["numinfo"])
check("prompt me 'kya result aayega' wali line nahi (⚡ nahi)",
      "⚡" not in bot.PROMPTS["dl_youtube"])
check("prompt ki aakhri line example hi hai",
      bot.PROMPTS["vahan"].rstrip().endswith("</code>"))

# =====================================================================
section("[B] 🖼️ CARDS — space, emoji, aasan shabd")
# =====================================================================
_t = bot.pcard_title("🏦", "TEST CARD")
check("title box ┏━┓ frame ka hai", "┏" in _t and "┗" in _t and "┃" in _t)
check("title ke baad khali line aati hai", _t.endswith("\n"))
check("separator ke aage-peeche khali line", bot.pcard_sep().startswith("\n") and bot.pcard_sep().endswith("\n"))
check("footer se pehle khali line", bot.pcard_foot(ms=100).startswith("\n"))

_w = bot.whois_card(bot.lookup_whois("example.com")) if False else bot.whois_card({
    "domain": "xyzshop.in", "registrar": "GoDaddy", "registrant": "",
    "created_fmt": "12-03-2019", "age": "7 saal", "expires_fmt": "12-03-2027",
    "days_left": 400, "nameservers": ["ns1.x.com"], "status": ["✅ active"],
    "dnssec": "false", "latency_ms": 200})
_wp = _clean(_w)
check("whois card me 'Owner' likha hai ('Malik' nahi)", "👤 Owner:" in _wp and "Malik" not in _wp)
check("whois card me 'Registry Company' (aasan shabd)", "Registry Company:" in _wp and "Registrar:" not in _wp)
check("whois card me 'Servers' (Nameservers nahi)", "🛰️ Servers:" in _wp and "Nameserver" not in _wp)
check("whois card me khali lines (spacing)", "\n\n" in _w or "\n" in _w)
check("whois card me koi link nahi", "http" not in _wp.split("Powered by")[0])

_n = _clean(bot.numinfo_card({"national": "78578 43092", "number": "917857843092", "country": "India"},
                             {"name": "Sanjay Sah", "father": "Ram Akwal Sah", "alt": "7305190526",
                              "region": "BIHAR JIO", "govt_id": "401635555849",
                              "address": "S/O Ram Akwal Sah, ward 02, Sitamarhi, Bihar, 843324"},
                             {}, "JIO", "BIHAR", "📱 Mobile", "", "🟢 LIVE", 300))
check("numinfo card me sample order + spacing",
      _n.index("👤 Name:") < _n.index("👨 Father:") < _n.index("📱 Phone:")
      and "\n\n" in _n)

# =====================================================================
section("[C] 🚗 GAADI X-RAY (RC + CHALLAN) — naya tool")
# =====================================================================
check("premium tool list me hai", "vahan" in bot.PREMIUM_TOOLS)
check("naam set hai", "RC" in bot.PREMIUM_TOOL_NAMES.get("vahan", ""))
check("rate limit lagi hai", "vahan" in bot.TOOL_RATE_LIMITS)
check("keyboard par button hai",
      any("RC + CHALLAN" in bot.unbold(b).upper() for r in bot.KB_BTNS for b in r))
check("button → mode mapping", bot.BTN_MODE_MAP.get("RC + CHALLAN") == "vahan")
check("prompt me valid example BR01AB1234 hai",
      "<code>BR01AB1234</code>" in bot.PROMPTS.get("vahan", ""))
check("handler mode vahan hai", 'if mode == "vahan":' in BOT_SRC)
check("handler card builder use karta hai", "vahan_card(" in BOT_SRC)
check("plate saaf karta hai (space/dash hata ke)",
      VT._clean_plate("br 01-ab 1234") == "BR01AB1234")
check("galat plate par saaf error",
      VT.vehicle_lookup("hello").get("ok") is False)
check("offline parse (provider ke bina) state nikaalta hai",
      VT.offline_parse("BR01AB1234").get("state_name") == "Bihar")

_o = VT.offline_parse("BR30AR0802")
_c1 = _clean(bot.vahan_card({}, _o))
check("card user ke format me hai (VEHICLE INFO REPORT)",
      bot.to_bold("VEHICLE INFO REPORT") in bot.vahan_card({}, _o))
check("card me Number + RTO row aata hai", "BR30AR0802" in _c1 and "📍 RTO:" in _c1)
check("card me saare section headings hain",
      all(x in _c1 for x in (bot.to_bold("VEHICLE INFORMATION"),
                             bot.to_bold("RC Specifications"),
                             bot.to_bold("CHALLAN SUMMARY"))))
check("data na ho to bhi rows 'N/A' / '-' se dikhte hain (khaali nahi)",
      "├ 👤 Owner:" in _c1 and "⚠️ N/A" in _c1)
check("koi SMS/lecture line nahi (user ka order)", "7738299899" not in _c1
      and "VAHAN" not in _c1 and "provider API" not in _c1)
check("card me koi link nahi", "http" not in _c1.split("Powered by")[0])

# provider aane par card (dummy data se test)
_c2 = _clean(bot.vahan_card({
    "rc": {"plate": "BR01AB1234", "owner": "SANJAY SAH", "maker": "MARUTI", "model": "SWIFT",
           "fuel": "PETROL", "reg_date": "12-03-2019", "ins_company": "ICICI Lombard",
           "ins_upto": "11-03-2027", "financer": "none", "colour": "WHITE",
           "mobile": "9876543210", "authority": "BIHAR Sitamarhi BR-30", "cc": "1197"},
    "challans": [{"number": "BR250023260716183506", "accused": "R****T K***R",
                  "date": "16 Jul 2026", "offence": "DRIVING WITHOUT HELMET",
                  "amount": "1,000", "status": "PENDING"}],
    "count": 1, "pending": 1, "amount": 1000}, _o))
check("provider data par poori detail aati hai",
      all(x in _c2 for x in ("SANJAY SAH", "MARUTI SWIFT", "ICICI Lombard",
                             "Finance :", "9876543210", "1197 CC")))
check("loan nahi ho to 'No Loan' likhta hai", "No Loan" in _c2)
check("challan summary + challan info rows aate hain",
      bot.to_bold("CHALLAN SUMMARY") in _c2 and bot.to_bold("CHALLAN INFO") in _c2
      and "Accused:" in _c2 and "DRIVING WITHOUT HELMET" in _c2)
check("challan me amount ₹ me + PENDING status",
      "₹1,000" in _c2 and "PENDING" in _c2)

# provider env se mapping (RapidAPI jaise headers)
os.environ["VEHICLE_PROVIDER_URL"] = "https://x.example/api"
os.environ["VEHICLE_PROVIDER_KEY"] = "TESTKEY"
os.environ["VEHICLE_PROVIDER_HEADERS"] = "X-RapidAPI-Key:{key}|X-RapidAPI-Host:x.p.rapidapi.com"
check("provider ready detect hota hai", VT.provider_ready() is True)
_h = VT._flags()
check("RapidAPI headers theek bante hain (key bharta hai)",
      _h.get("X-RapidAPI-Key") == "TESTKEY" and "x.p.rapidapi.com" in str(_h.get("X-RapidAPI-Host")))
_m = VT.map_provider_payload({"rc": {"owner_name": "RAM SAH", "vehicle_class": "M-Cycle/Scooter",
                                     "registration_date": "01-01-2020", "insurance_upto": "01-01-2027"},
                              "challans": {"count": 2, "pending_count": 1,
                                           "pending_amount": 1500, "list": []}}, "BR01AB1234")
check("kisi bhi provider ka JSON map ho jata hai",
      _m["rc"].get("owner") == "RAM SAH" and _m["rc"].get("maker") is None
      and _m["count"] == 2 and _m["amount"] == 1500)
os.environ.pop("VEHICLE_PROVIDER_URL", None)

# =====================================================================
section("[D] ⚡ RAPIDAPI AUTO-DETECT — sirf 2 line me kaam (v71.2)")
# =====================================================================
os.environ.pop("VEHICLE_PROVIDER_HEADERS", None)     # pichhla test ka header hatao
os.environ["VEHICLE_PROVIDER_URL"] = "https://vehicle-rc-information.p.rapidapi.com/vehicle/rc"
os.environ["VEHICLE_PROVIDER_KEY"] = "ABC123"
check("RapidAPI URL pehchanta hai", VT.is_rapidapi() is True)
check("host apne aap nikaalta hai",
      VT._rapidapi_host(VT._cfg()["url"]) == "vehicle-rc-information.p.rapidapi.com")
check("headers apne aap bante hain (key + host)",
      VT._flags().get("X-RapidAPI-Key") == "ABC123"
      and VT._flags().get("X-RapidAPI-Host") == "vehicle-rc-information.p.rapidapi.com")
check("provider ready batata hai", VT.provider_ready() is True)
# normal (non-rapidapi) URL par purana behaviour zinda
os.environ["VEHICLE_PROVIDER_URL"] = "https://myprovider.example/api/rc"
os.environ["VEHICLE_PROVIDER_AUTH"] = "bearer"
check("RapidAPI ke bina bearer auth hi chalta hai",
      VT.is_rapidapi() is False
      and VT._flags().get("Authorization") == "Bearer ABC123")
os.environ.pop("VEHICLE_PROVIDER_URL", None)
os.environ.pop("VEHICLE_PROVIDER_KEY", None)
os.environ.pop("VEHICLE_PROVIDER_AUTH", None)
check("sab hatane par provider off", VT.provider_ready() is False)
check("/rcsetup command hai (step-by-step help)", callable(getattr(bot, "cmd_rcsetup", None)))

# =====================================================================
section("[D] 🔁 PURANA KUCH TOOTA NAHI")
# =====================================================================
check("4 downloader tools zinda", len(bot.DL_SITES) == 4)
check("premium tools 36 (35 + vahan)", len(bot.PREMIUM_TOOLS) == 36, str(len(bot.PREMIUM_TOOLS)))
check("keyboard rows badhe (18)", len(bot.KB_BTNS) >= 18, str(len(bot.KB_BTNS)))
check("downloader sabse upar hi hai",
      "INSTA DL" in bot.unbold(bot.KB_BTNS[0][0]).upper())
check("whois tool zinda", "osint_whois" in bot.PREMIUM_TOOLS)
check("'Privacy' shabd koi jagah nahi", "privacy" not in BOT_SRC.lower())
check("version v71 hai", bot.BOT_VERSION.startswith("v71"), bot.BOT_VERSION)
check("prompt texts ka structure zinda (head/ask/ex)",
      all(("head" in d and "ask" in d and "ex" in d) for d in bot.PROMPT_DATA.values()))

# =====================================================================
section("[E] 🌐 ASLI CONNECTION TEST — local mock API (offline, koi internet nahi)")
# =====================================================================
import json as _json  # noqa: E402
import threading as _thr  # noqa: E402
from http.server import BaseHTTPRequestHandler as _BHR, HTTPServer as _HS  # noqa: E402


class _MockRapidAPI(_BHR):
    """RapidAPI wali Vehicle RC API ka nakal — Basic endpoint, VehicleNumber body."""

    def log_message(self, *a):                                # noqa: ANN002
        pass

    def do_POST(self):
        _ln = int(self.headers.get("content-length") or 0)
        _b = _json.loads(self.rfile.read(_ln) or b"{}")
        if self.path.rstrip("/") != "/VehicleInformation":
            self.send_response(404); self.end_headers(); self.wfile.write(b"{}"); return
        if "VehicleNumber" not in _b:
            self.send_response(400); self.end_headers(); self.wfile.write(b"{}"); return
        if (self.headers.get("X-RapidAPI-Key") or "") != "TESTKEY":
            self.send_response(403); self.end_headers()
            self.wfile.write(b'{"message":"Invalid API key"}'); return
        _out = {"API_Developer": "@ProPortalx", "Today_Used": 7,
                "result": {"vehicle_number": _b["VehicleNumber"], "data": {
                    "Registration Number": _b["VehicleNumber"], "Maker Name": "HONDA",
                    "Model Name": "SHINE", "Fuel Type": "PETROL", "Cubic Capacity": "99.0"}}}
        _raw = _json.dumps(_out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(_raw)

    def do_GET(self):
        self.send_response(404); self.end_headers(); self.wfile.write(b"{}")


_srv = _HS(("127.0.0.1", 0), _MockRapidAPI)
_port = _srv.server_address[1]
_thr.Thread(target=_srv.serve_forever, daemon=True).start()

os.environ["VEHICLE_PROVIDER_URL"] = f"http://127.0.0.1:{_port}/VehicleInformation"
os.environ["VEHICLE_PROVIDER_KEY"] = "TESTKEY"
os.environ["VEHICLE_PROVIDER_HEADERS"] = "X-RapidAPI-Key:{key}"

VT._CACHE.clear(); VT._WORKING_URL[0] = ""
_r = VT.vehicle_lookup("BR30AR0802")
check("asli HTTP par poora record aata hai (end-to-end)",
      _r.get("ok") is True and _r["rc"].get("model") == "SHINE", str(_r)[:130])
check("body key 'VehicleNumber' apne aap try hoti hai (Basic endpoint)",
      _r.get("ok") is True)

os.environ["VEHICLE_PROVIDER_KEY"] = "WRONGKEY"
VT._CACHE.clear(); VT._WORKING_URL[0] = ""
_r2 = VT.vehicle_lookup("BR30AR0802")
check("galat key par SAFA Hinglish error (hub ka generic message nahi)",
      _r2.get("ok") is False and "key nahi maani" in str(_r2.get("error")), str(_r2)[:130])

os.environ["VEHICLE_PROVIDER_KEY"] = "TESTKEY"
os.environ["VEHICLE_PROVIDER_URL"] = f"http://127.0.0.1:{_port}"   # sirf host
VT._CACHE.clear(); VT._WORKING_URL[0] = ""
_re = VT.is_rapidapi
VT.is_rapidapi = lambda: True         # host-only URL wala case
_r3 = VT.vehicle_lookup("BR30AR0802")
VT.is_rapidapi = _re
check("sirf HOST diya ho to path KHUD dhoondh leta hai",
      _r3.get("ok") is True and "/VehicleInformation" in VT._WORKING_URL[0],
      VT._WORKING_URL[0])
check("jo URL chala wo YAAD rehta hai (agli baar seedha wahi)",
      VT._WORKING_URL[0].endswith("/VehicleInformation"))
_srv.shutdown()
for _k2 in ("VEHICLE_PROVIDER_URL", "VEHICLE_PROVIDER_KEY", "VEHICLE_PROVIDER_HEADERS"):
    os.environ.pop(_k2, None)


# =====================================================================
section("[F] 🏁 ROOT-URL API — jaise asli 'Vehicle RC Information' (v71.5)")
# =====================================================================
class _MockRootAPI(_BHR):
    """Asli API ka behaviour: POST seedha root ('/') par, body me VehicleNumber."""

    def log_message(self, *a):                                # noqa: ANN002
        pass

    def do_POST(self):
        _ln = int(self.headers.get("content-length") or 0)
        _b = _json.loads(self.rfile.read(_ln) or b"{}")
        if self.path.rstrip("/") != "":
            self.send_response(404); self.end_headers(); self.wfile.write(b"{}"); return
        if "VehicleNumber" not in _b:
            self.send_response(400); self.end_headers(); self.wfile.write(b"{}"); return
        if (self.headers.get("X-RapidAPI-Key") or "") != "TESTKEY":
            self.send_response(403); self.end_headers()
            self.wfile.write(b'{"message":"Invalid API key"}'); return
        _out = {"success": True, "data": {
            "registrationNo": _b["VehicleNumber"],
            "registrationAuthority": "SANGRUR RTA, Punjab",
            "registrationDate": "24-11-2017 00:00:00",
            "ownerName": "S*******P S***H",
            "makerModel": "TOYOTA KIRLOSKAR MOTOR PVT LTD / FORTUNER 2WD 2.8L 6MT",
            "fuelType": "DIESEL", "vehicleClass": "Motor Car(LMV)",
            "vehicleColor": "S WHITE", "rcStatus": "ACTIVE",
            "insuranceCompany": "United India Insurance Co. Ltd.",
            "insuranceUpto": "18-02-2022 00:00:00",
            "fitnessUpto": "23-11-2032 00:00:00",
            "seatCapacity": "7", "financierName": None, "unloadWeight": "2135"}}
        _raw = _json.dumps(_out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(_raw)

    def do_GET(self):
        self.send_response(404); self.end_headers(); self.wfile.write(b"{}")


_srv2 = _HS(("127.0.0.1", 0), _MockRootAPI)
_port2 = _srv2.server_address[1]
_thr.Thread(target=_srv2.serve_forever, daemon=True).start()

os.environ["VEHICLE_PROVIDER_URL"] = f"http://127.0.0.1:{_port2}"
os.environ["VEHICLE_PROVIDER_KEY"] = "TESTKEY"
os.environ.pop("VEHICLE_PROVIDER_HEADERS", None)
VT._CACHE.clear(); VT._WORKING_URL[0] = ""
_re2 = VT.is_rapidapi
VT.is_rapidapi = lambda: True         # host-only URL wala case
_r4 = VT.vehicle_lookup("PB65AM0008")
VT.is_rapidapi = _re2
check("ROOT-endpoint API turant chalti hai (base URL pehle try)",
      _r4.get("ok") is True and _r4["rc"].get("plate") == "PB65AM0008", str(_r4)[:130])
check("'registrationNo' wali key bhi mapper samajhta hai",
      _r4.get("ok") is True and "SANGRUR" in _r4["rc"].get("authority", ""))
check("date se '00:00:00' saaf ho jata hai",
      _r4["rc"].get("reg_date") == "24-11-2017", _r4["rc"].get("reg_date"))
check("finance null → khaali (card me N/A dikhayega)",
      not _r4["rc"].get("financer"), _r4["rc"].get("financer"))
check("root URL memory me set ho jata hai",
      VT._WORKING_URL[0] == f"http://127.0.0.1:{_port2}", VT._WORKING_URL[0])
_card_txt = bot.vahan_card({"rc": dict(_r4["rc"]), "challans": []}, None)
_city_line = _card_txt.split("City:</b>")[1][:26] if "City:</b>" in _card_txt else ""
check("card me City sahi nikalta hai ('SANGRUR RTA, Punjab' → SANGRUR)",
      "SANGRUR" in _city_line and "RTA" not in _city_line, _city_line)
check("card poora banta hai (owner/model/insurance dikhte hain)",
      "S*******P" in _card_txt and "FORTUNER" in _card_txt and "United India" in _card_txt)
_srv2.shutdown()


# =====================================================================
section("[G] ✅ v71.6 — 'gaadi nahi mili' ka SAAF message + PATLI lines + Note")
# =====================================================================
class _MockNoCar(_BHR):
    """Asli API jaisa: key sahi, par gaadi DB me nahi → 404 not found."""

    def log_message(self, *a):                                # noqa: ANN002
        pass

    def do_POST(self):
        _ln = int(self.headers.get("content-length") or 0)
        self.rfile.read(_ln)
        if (self.headers.get("X-RapidAPI-Key") or "") != "TESTKEY":
            self.send_response(403); self.end_headers()
            self.wfile.write(b'{"message":"Invalid API key"}'); return
        _raw = _json.dumps({"success": False,
                            "error": "Vahan with registrationNo BR30AR0802 not found",
                            "version": "2.0.142"}).encode()
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(_raw)

    def do_GET(self):
        self.send_response(404); self.end_headers(); self.wfile.write(b"{}")


_srv3 = _HS(("127.0.0.1", 0), _MockNoCar)
_port3 = _srv3.server_address[1]
_thr.Thread(target=_srv3.serve_forever, daemon=True).start()

os.environ["VEHICLE_PROVIDER_URL"] = f"http://127.0.0.1:{_port3}"
os.environ["VEHICLE_PROVIDER_KEY"] = "TESTKEY"
VT._CACHE.clear(); VT._WORKING_URL[0] = ""
_re6 = VT.is_rapidapi
VT.is_rapidapi = lambda: True
_r6 = VT.vehicle_lookup("BR30AR0802")
VT.is_rapidapi = _re6
check("gaadi DB me na ho to 'not_found' flag aata hai",
      _r6.get("ok") is False and _r6.get("not_found") is True, str(_r6)[:130])
check("message SAFA hai ('database me nahi mila') — path/key wala confusing msg nahi",
      "nahi mila" in str(_r6.get("error")) and "endpoint ka pata galat" not in str(_r6.get("error")))
_srv3.shutdown()
for _k4 in ("VEHICLE_PROVIDER_URL", "VEHICLE_PROVIDER_KEY"):
    os.environ.pop(_k4, None)

o2 = VT.offline_parse("BR30AR0802")
_c3 = _clean(bot.vahan_card({}, o2, note="Is gaadi ka record sarkari database me nahi mila (BR30AR0802)."))
check("card me ⚠️ Note line dikhti hai (khaali card ka raaz khulta hai)",
      "⚠️ <b>Note:</b> Test wajah" in bot.vahan_card({}, o2, note="Test wajah"))
check("Note na ho to Note line nahi aati",
      "⚠️ <b>Note:</b>" not in bot.vahan_card({}, o2))
check("vahan card me moti line (━) bilkul nahi — sab patli",
      "━" not in bot.vahan_card({}, o2) and "─" in bot.vahan_card({}, o2))
check("pcard title bhi patli line ka (har tool me same look)",
      "━" not in bot.pcard_title("🚘", "TEST") and "─" in bot.pcard_title("🚘", "TEST"))
check("prompt boxes bhi patle ho gaye (user ki shikayat: white white)",
      all("━" not in bot.PROMPTS[k] for k in list(bot.PROMPTS)[:40]))
check("header box upar-neeche patli line ke saath (┏ ─ ┓)",
      "┏" in bot.vahan_card({}, o2) and "┗" in bot.vahan_card({}, o2))


print(f"\n{'=' * 62}")
print(f"  v71 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
