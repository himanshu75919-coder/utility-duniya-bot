"""v41 TEST — VEHICLE INFO + CHALLAN (hub ke 3 API se, mock server par end-to-end).

Mock server = user ke asli hub ka response shape (vehicle-rc / vehicle-challan / vehicle-challan-v4).
Chalane ke liye net ki zarurat nahi (sab kuch 127.0.0.1 par).
"""
import asyncio
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DB_PATH", "/tmp/_veh41_test.db")

# ---------------------------------------------------------------- mock data (asli hub jaisa)
HUB_RC = {
    "data": {
        "vehicle_info": {
            "address": "Mini Secretariat, Gurugram, Haryana 120001",
            "city_name": "North Gurgaon",
            "code": "HR-26",
            "model_name": "FORTUNER LEGENDER (AT)",
            "owner_name": "ELVISH YADAV",
            "phone": "(+91)12423 21808",
            "vehicle_number": "HR26EV0001",
            "website": "https://haryanatransport.gov.in/",
        },
        "sections": {
            "important_dates": {
                "Fitness Upto": "26-May-2041", "Insurance Expiry In": "2 years , 6 months & 29 days",
                "Insurance Upto": "01-May-2029", "PUC Expiry In": "0 years , 8 months & 5 days",
                "PUC No": "DL009009800XXXXX", "PUC Upto": "07-Jun-2027",
                "Registration Date": "10-Jun-2022", "Tax Upto": "LTT",
                "Vehicle Age": "4 years , 3 months & 22 days",
            },
            "insurance_information": {
                "Insurance Company": "CHOLAMANDALAM GENERAL INSURANCE CO. LTD.",
                "Insurance Expiry": "01-May-2029", "Insurance No": "TCH/975XXXXX",
                "Insurance Status": "You Are Insured",
                "Insurance Validity": "Insurance Valid Upto 2 years , 6 months & 29 days",
            },
            "other_information": {"Blacklist Status": "NA", "Cubic Capacity": "124.6 CC",
                                  "Financer Name": "NA", "NOC Details": "NA", "Permit Type": "NA",
                                  "Seating Capacity": "2"},
            "ownership_details": {"Owner Name": "ELVISH YADAV", "Owner Serial No": "First Owner",
                                  "Registered RTO": "HARYANA HEAD OFFICE CHD, HARYANA",
                                  "Registration Number": "HR26EV0001"},
            "vehicle_details": {"Chassis Number": "MBJAA3GS600560639XXXXX", "Engine Number": "1GDA5XXXXX",
                                "Fuel Norms": "BHARAT STAGE VI", "Fuel Type": "DIESEL",
                                "Maker Model": "FORTUNER LEGENDER (AT)",
                                "Model Name": "TOYOTA KIRLOSKAR MOTOR PVT LTD",
                                "Vehicle Class": "MOTOR CAR(LMV)"},
        },
    },
    "fetch_time_seconds": 1.4,
    "success": True,
    "vehicle_number": "HR26EV0001",
}

HUB_CHALLANS = {
    "data": {
        "challan_details": [
            {"accused_name": "E****H Y***V", "amount": "0", "challan_date": "01-07-2023",
             "challan_date_time": "01-07-2023 02:27:09", "challan_number": "CH46894230719122563",
             "challan_place": "HOUSING BOARD FROM KALAGRAM LIGHT", "challan_status": "Pending",
             "court_challan": True, "court_name": "Chief Judicial Magistrate UT Chandigarh",
             "offense_details": "27-DANGEROUS DRIVING-JUMPING RED LIGHT",
             "offense_details_list": [{"offense_name": "27-DANGEROUS DRIVING-JUMPING RED LIGHT"}],
             "rto": "Chandigarh", "state": "CH", "upstream_code": ""},
            {"accused_name": "E****H Y***V", "amount": "2000", "challan_date": "22-06-2025",
             "challan_number": "CH46894250622075568",
             "challan_place": "Z4  Vikash Marg SVD", "challan_status": "Pending",
             "court_challan": False, "court_name": "Chief Judicial Magistrate UT Chandigarh",
             "offense_details": "28-DRIVING AT FASTER/EXCESSIVE SPEED THEN SPEED LIMITS BY LMV/OTHER",
             "offense_details_list": [{"offense_name": "28-SPEED"}], "rto": "Chandigarh", "state": "CH"},
            {"accused_name": "E****H Y***V", "amount": "1000", "challan_date": "28-07-2025",
             "challan_number": "RJ4164865250812122824",
             "challan_place": "express, express way ps  NOGAWA", "challan_status": "Disposed",
             "court_challan": False, "court_name": "AMJM N0 3 ALWAR",
             "offense_details": "Driving at excess speed (LMV) 183(1)(i)", "rto": "Alwar", "state": "RJ"},
        ],
        "rc_number": "HR26EV0001",
    },
    "success": True,
}

HUB_V4 = {
    "data": {
        "challan_summary": {"total_amount": 45500, "total_challans": 20},
        "type_a": {"amount": 45500, "count": 20, "description": "Pending Challans"},
        "type_b": {"amount": 0, "count": 0, "description": "Disposed Challans"},
    },
    "success": True,
}

HUB_NO_CHALLAN = {"data": {"challan_details": [], "rc_number": "HR26EV0001"}, "success": True}
HUB_V4_ZERO = {"data": {"challan_summary": {"total_amount": 0, "total_challans": 0},
                        "type_a": {"amount": 0, "count": 0, "description": "Pending Challans"},
                        "type_b": {"amount": 0, "count": 0, "description": "Disposed Challans"}},
               "success": True}
UNAUTH = {"errorMsg": "Unauthorized"}

# hub khaali / unknown plate par sirf RTO office info deta hai (asli behaviour)
RTO_ONLY = {
    "data": {
        "sections": {"other_information": {"Blacklist Status": "NA", "Cubic Capacity": "124.6 CC",
                                           "Financer Name": "NA", "NOC Details": "NA",
                                           "Permit Type": "NA", "Seating Capacity": "2"}},
        "vehicle_info": {"address": "Bank Rd, West Gandhi Maidan, Raja Ji Salai, Patna, Bihar 800001",
                         "city_name": "Patna", "code": "BR-01", "model_name": "BR-01",
                         "owner_name": "Patna", "phone": "(+91)61222 37131",
                         "vehicle_number": "BR01AB1234",
                         "website": "https://state.bihar.gov.in/transport/CitizenHome.html"},
    },
    "fetch_time_seconds": 0.2, "success": True, "vehicle_number": "BR01AB1234",
}


class Handler(BaseHTTPRequestHandler):
    mode = "full"

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if Handler.mode == "err":
            self._send(UNAUTH, 200)
            return
        if Handler.mode == "rto_only":
            self._send(RTO_ONLY if path.endswith("/vehicle-rc") else HUB_V4_ZERO)
            return
        no_ch = Handler.mode == "no_challan"
        if path.endswith("/vehicle-rc"):
            self._send(HUB_RC)
        elif path.endswith("/vehicle-challan-v4"):
            self._send(HUB_V4_ZERO if no_ch else HUB_V4)
        elif path.endswith("/vehicle-challan"):
            self._send(HUB_NO_CHALLAN if no_ch else HUB_CHALLANS)
        else:
            self._send({"errorMsg": "not found"}, 404)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 8791), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["VEHICLE_API_BASE"] = "http://127.0.0.1:8791/api"
os.environ["VEHICLE_API_KEY"] = "testkey"
os.environ.pop("VEHICLE_API_URL", None)
os.environ["BOT_TOKEN"] = "123456789:AAHtesttoken_testtoken_testtoken_testtok"
os.environ["ADMIN_ID"] = "8607774564"

import bot  # noqa: E402
import database as dbm  # noqa: E402
from modules import vehicle_challan as vc  # noqa: E402

PASS, FAIL = [], []


def ok(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("✅ " if cond else "❌ ") + name + ("" if cond else f"  — {str(extra)[:240]}"))


# --------------------------------------------------------- 1) ENGINE
print("\n--- 1) ENGINE (hub ke 3 endpoint, mock) ---")
vc._CACHE.clear()
res = vc.fetch_vehicle_report("HR26EV0001")
ok("3 endpoint se report aayi (ok=True)", res.get("ok") is True, res)
ok("sources me teeno engine", set(res.get("sources") or []) >= {"vehicle-rc", "vehicle-challan",
                                                               "vehicle-challan-v4"}, res.get("sources"))
rc = res.get("rc") or {}
ok("Maker = Model Name se (TOYOTA KIRLOSKAR)", rc.get("maker") == "TOYOTA KIRLOSKAR MOTOR PVT LTD", rc.get("maker"))
ok("Model = Maker Model se (FORTUNER LEGENDER AT)", rc.get("model") == "FORTUNER LEGENDER (AT)", rc.get("model"))
ok("Fuel / Class / Emission", rc.get("fuel") == "DIESEL" and rc.get("vehicle_class") == "MOTOR CAR(LMV)"
   and rc.get("emission") == "BHARAT STAGE VI", rc)
ok("Cubic capacity 124.6 CC", vc._cc_txt(rc.get("cc")) == "124.6", rc.get("cc"))
ok("Owner ka naam aaya (ELVISH YADAV)", rc.get("owner") == "ELVISH YADAV", rc.get("owner"))
ok("RTO + city + phone + site", "HARYANA" in rc.get("rto", "") and rc.get("city") == "North Gurgaon"
   and "12423" in rc.get("rto_phone", "") and "haryana" in rc.get("rto_website", ""), rc)
ok("Registration + fitness + tax", rc.get("reg_date") == "10-Jun-2022" and rc.get("fitness_upto") == "26-May-2041"
   and rc.get("tax_upto") == "LTT", rc)
ok("Insurance company + no + status", "CHOLAMANDALAM" in rc.get("ins_company", "") and rc.get("ins_upto") == "01-May-2029"
   and "Insured" in rc.get("ins_status", ""), rc)
ok("PUC upto + no", rc.get("puc_upto") == "07-Jun-2027" and rc.get("puc_no") == "DL009009800XXXXX", rc)
ok("Finance NA (hypothecation nahi)", rc.get("financer") == "", rc.get("financer"))

chs = res.get("challans") or []
ok("Challan list mili (3)", len(chs) == 3, chs)
ok("Challan number sahi", vc._challan_from_dict(chs[0], "number") == "CH46894230719122563", chs[0])
ok("Challan status + offence sahi", "Pending" == vc._challan_from_dict(chs[0], "status")
   and "DANGEROUS DRIVING" in str(vc._challan_from_dict(chs[0], "offence")), chs[0])
ok("Court ka naam aaya", "Chandigarh" in str(vc._challan_from_dict(chs[0], "court")), chs[0])
sm = res.get("summary") or {}
ok("Summary v4 se (20 pending, ₹45,500)", sm.get("count") == 20 and sm.get("pending") == 20
   and sm.get("pending_amount") == 45500 and sm.get("from_summary_api") is True, sm)
ok("v1 se summary na ho to fallback hisaab", not (vc.challan_summary(chs).get("from_summary_api")),
   vc.challan_summary(chs))

# RC ko galti se challan na samjhe (purana pitfall: "Registration Number"/"Engine Number")
ok("RC dict challan nahi samjha jaata (guard)", vc.find_challans(HUB_RC) == [], vc.find_challans(HUB_RC))
ok("sirf RC ka jawab bhi report banti hai", vc.fetch_vehicle_report("HR26EV0001").get("ok") is True)

# masking
ok("Mobile masked (8422 tak hi)", vc.mask_mobile("9199038422").endswith("8422")
   and "9199038422" not in vc.mask_mobile("9199038422"), vc.mask_mobile("9199038422"))
ok("Owner naam masked", vc.mask_name("ELVISH YADAV") == "E****H Y***V", vc.mask_name("ELVISH YADAV"))
ok("Chassis masked (XXXXX waisa hi rehta)", vc.mask_id("MBJAA3GS600560639XXXXX").startswith("MBJAA3")
   and "MBJAA3GS600560639XXXXX" != vc.mask_id("MBJAA3GS600560639XXXXX"), vc.mask_id("MBJAA3GS600560639XXXXX"))
ok("PUC no masked", "*" in vc.mask_id("DL009009800XXXXX") and "09800" not in vc.mask_id("DL009009800XXXXX"),
   vc.mask_id("DL009009800XXXXX"))
ok("Plate format check", vc.valid_plate("HR26EV0001") and not vc.valid_plate("XX1"))

Handler.mode = "rto_only"
vc._CACHE.clear()
rto_only = vc.fetch_vehicle_report("BR01AB1234")
ok("RTO-only jawab bhi parse hota hai (Patna)", rto_only.get("ok") is True
   and "Patna" in str(rto_only.get("rc", {}).get("city")), rto_only.get("rc"))
ok("bot ka guard samajhta hai ki RC data nahi hai", bot._veh_has_rc_data(rto_only) is False,
   bot._veh_has_rc_data(rto_only))
ok("guard: asli RC par True", bot._veh_has_rc_data(res) is True)
Handler.mode = "full"
vc._CACHE.clear()

# --------------------------------------------------------- 2) CARD TEXT
print("\n--- 2) CARD TEXT (jo user ko dikhta hai) ---")
card = vc.render_vehicle_report(res)
for want in ("VEHICLE REPORT — HR26EV0001", "TOYOTA KIRLOSKAR MOTOR PVT LTD", "FORTUNER LEGENDER (AT)",
             "MOTOR CAR(LMV)", "DIESEL", "124.6 cc", "BHARAT STAGE VI", "E****H Y***V",
             "HARYANA HEAD OFFICE CHD", "North Gurgaon", "10-Jun-2022", "26-May-2041", "LTT",
             "CHOLAMANDALAM", "01-May-2029", "07-Jun-2027", "CHALLANS — 20 found",
             "⏳ Pending: <b>20</b> — ₹45,500", "₹45,500", "CH46894230719122563", "⏳ PENDING",
             "27-DANGEROUS DRIVING", "Chief Judicial Magistrate UT Chandigarh"):
    ok(f"card me '{want}'", want in card, card[:400])
ok("card me asli naam poora NAHI dikhta", "ELVISH YADAV" not in card, card)
ok("card me chassis poora NAHI dikhta", "MBJAA3GS600560639XXXXX" not in card, card)
ok("card me engine no poora NAHI dikhta", "1GDA5XXXXX" not in card, card)
ok("card par '&' safe (HTML escape)", "&amp;" in card and "& " not in card.replace("&amp;", ""), card[:200])

# no challan
Handler.mode = "no_challan"
vc._CACHE.clear()
res2 = vc.fetch_vehicle_report("DL8CAF5031")
ok("challan nahi → 'No challan found'", "No challan found" in vc.render_vehicle_report(res2),
   vc.render_vehicle_report(res2)[-400:])
Handler.mode = "full"

# API fail (Unauthorized)
Handler.mode = "err"
vc._CACHE.clear()
bad = vc.fetch_vehicle_report("MP09AB1234")
ok("API fail par saaf error + fallback=True", bad.get("ok") is False and bad.get("fallback") is True
   and "Unauthorized" in str(bad.get("error")), bad)
Handler.mode = "full"

# cache (paisa/API call bachta hai)
vc._CACHE.clear()
r1 = vc.fetch_vehicle_report("HR26EV0001")
r2 = vc.fetch_vehicle_report("HR26EV0001")
ok("dobara check = cache se (cached=True)", r2.get("cached") is True and r2.get("ok") is True, r2.get("cached"))

# --------------------------------------------------------- 3) BOT FLOW
print("\n--- 3) BOT FLOW (Telegram) ---")
_PRE_PASS, _PRE_FAIL = list(PASS), list(FAIL)   # exec naye lists banata hai — purane bacha lo
PASS, FAIL = [], []
sys.argv = ["x"]
exec(open("_selftest_v38_desi.py", encoding="utf-8").read().split(
    "# ======================================================================\nasync def t1_menu()")[0])

USER = 8607774565


async def run_cmd(coro, ctx, uid=OWNER, args=None):
    ctx.args = list(args or [])
    m = FakeMsg("", uid=uid)
    upd = Update(update_id=5, message=m)
    upd.message.from_user = User(id=uid, first_name="Test", is_bot=False)
    await coro(upd, ctx)
    return m


def _urls(m):
    out = []
    for _k, _t, kw, _ in m.replies:
        kb = (kw or {}).get("reply_markup")
        if kb is not None and getattr(kb, "inline_keyboard", None):
            out += [b.url for row in kb.inline_keyboard for b in row]
    return [u for u in out if u]


async def flows():
    fresh(USER, 5)
    ctx = Ctx()
    m = await send_text(kb_label("rto"), ctx, uid=USER)
    t = m.all_text()
    ok("prompt khulta hai (English)", "Now send the number plate" in t and "CHALLAN" in t.upper(), t[:200])

    before = dbm.get_credits(USER)
    m2 = await send_text("HR26EV0001", ctx, uid=USER)
    t2 = m2.all_text()
    ok("live report aaya (maker/model)", "TOYOTA KIRLOSKAR" in t2 and "FORTUNER LEGENDER" in t2, t2[:250])
    ok("challan list aayi", "CH46894230719122563" in t2 and "PENDING" in t2, t2[-400:])
    ok("1 credit kata", dbm.get_credits(USER) == before - 1, (before, dbm.get_credits(USER)))
    ok("'credit used' line aayi", "credit used" in t2.lower(), t2[-200:])
    ok("official buttons aaye", any("echallan" in str(u or "") for u in _urls(m2)), _urls(m2))

    q = await click(f"vehagain:HR26EV0001", ctx, uid=USER)
    ok("'Check again' callback chala", "FORTUNER LEGENDER" in q.message.all_text(), q.message.all_text()[:200])

    # galat plate → saaf error (free card)
    ctx2 = Ctx(); fresh(USER, 5)
    await send_text(kb_label("rto"), ctx2, uid=USER)
    m3 = await send_text("XX99", ctx2, uid=USER)
    ok("galat plate par saaf error", "FAILED" in m3.all_text().upper() or "format" in m3.all_text().lower(),
       m3.all_text()[:200])
    ok("galat plate par credit nahi kata", dbm.get_credits(USER) == 5, dbm.get_credits(USER))

    # 0 credits → block + free links
    fresh(USER, 0)
    ctx3 = Ctx()
    await send_text(kb_label("rto"), ctx3, uid=USER)
    m4 = await send_text("BR30AR0802", ctx3, uid=USER)
    ok("0 credits par premium block", "ALL CREDITS USED" in m4.all_text().upper(), m4.all_text()[:200])
    ok("0 credits par free RC card bhi mila", "RTO" in m4.all_text().upper(), m4.all_text()[:220])

    # VIP → unlimited, credit nahi katta
    fresh(USER, 0, vip=True)
    ctx4 = Ctx()
    await send_text(kb_label("rto"), ctx4, uid=USER)
    m5 = await send_text("BR30AR0802", ctx4, uid=USER)
    ok("VIP ko report mili (0 credits par bhi)", "FORTUNER LEGENDER" in m5.all_text(), m5.all_text()[:200])
    ok("VIP ke credits nahi kate", dbm.get_credits(USER) == 0, dbm.get_credits(USER))

    # API down → purana free card (koi crash nahi, credit nahi kata)
    os.environ["VEHICLE_API_BASE"] = "http://127.0.0.1:8799/api"     # kuch sun nahi raha
    vc._CACHE.clear()
    fresh(USER, 5)
    ctx5 = Ctx()
    await send_text(kb_label("rto"), ctx5, uid=USER)
    m6 = await send_text("DL01AB1234", ctx5, uid=USER)
    ok("API down par free card + reason", "RTO Office" in m6.all_text() or "RTO" in m6.all_text(),
       m6.all_text()[:250])
    ok("API down par credit nahi kata", dbm.get_credits(USER) == 5, dbm.get_credits(USER))
    os.environ["VEHICLE_API_BASE"] = "http://127.0.0.1:8791/api"
    vc._CACHE.clear()

    # hub se sirf RTO info aaya (koi RC/challan nahi) → free card + credit nahi kata
    Handler.mode = "rto_only"
    vc._CACHE.clear()
    fresh(USER, 5)
    ctx6 = Ctx()
    await send_text(kb_label("rto"), ctx6, uid=USER)
    m7 = await send_text("BR01AB1234", ctx6, uid=USER)
    t7 = m7.all_text()
    ok("RC data na hone par free card (Bihar/Patna)", "Bihar" in t7 or "Patna" in t7, t7[:250])
    ok("RC data na hone par saaf note", "No RC / challan record" in t7 or "No credit was cut" in t7, t7[:250])
    ok("RC data na hone par credit nahi kata", dbm.get_credits(USER) == 5, dbm.get_credits(USER))
    Handler.mode = "full"
    vc._CACHE.clear()

    # admin status command
    ctxa = Ctx()
    ma = await run_cmd(bot.cmd_vehstatus, ctxa, uid=OWNER, args=["HR26EV0001"])
    ok("/vehstatus admin ko test dikhata hai", "API is working" in ma.all_text(), ma.all_text()[:200])

    # non-admin ko kuch nahi
    ctxb = Ctx()
    mb = await run_cmd(bot.cmd_vehstatus, ctxb, uid=123456789, args=["HR26EV0001"])
    ok("/vehstatus non-admin ko kuch nahi bhejta", not mb.all_text().strip(), mb.all_text()[:120])


asyncio.run(flows())

ALL_PASS, ALL_FAIL = _PRE_PASS + PASS, _PRE_FAIL + FAIL
print("\n" + "=" * 70)
print(f"V41 VEHICLE + CHALLAN (HUB) — PASS: {len(ALL_PASS)} | FAIL: {len(ALL_FAIL)}")
for f in ALL_FAIL:
    print("  ❌", f)
print("=" * 70)
sys.exit(1 if ALL_FAIL else 0)
