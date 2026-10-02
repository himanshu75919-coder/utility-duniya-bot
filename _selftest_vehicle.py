"""v40 TEST — VEHICLE INFO + CHALLAN (mock API se end-to-end).
Asli API ka response format = jo user ne diya (ProPortalx style: result.data + challan block).
"""
import asyncio
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DB_PATH", "/tmp/_veh_test.db")

# ---- mock API server (user ke sample JSON jaisa) ----
SAMPLE_FULL = {
    "API_Developer": "@ProPortalx",
    "Today_Used": 7,
    "result": {
        "vehicle_number": "BR30AR0802",
        "data": {
            "Office Code": "BR",
            "Registration Authority": "BIHAR Sitamrahi BR-30",
            "Registration Number": "BR30AR0802",
            "Manufacture Year": "2025",
            "Registration Date": "29-08-2025",
            "Registration Validity": "28-08-2040",
            "Chassis Number": "ME4HC154DSG053849",
            "Engine Number": "HC15EG2054174",
            "Maker Name": "HONDA",
            "Model Name": "SHINE",
            "Body Type": "FULL BODY",
            "Vehicle Class": "M-CYCLE/SCOOTER",
            "Vehicle Category": "Private",
            "Fuel Type": "PETROL",
            "Color": "BLACK+GREY STRIPES",
            "Emission Norms": "BHARAT STAGE VI",
            "Cubic Capacity": "99.0",
            "Unladen Weight": "99",
            "Seating Capacity": "2",
            "Hypothecation Bank": "CREDIT WISE CAPITAL PVT LTD",
            "Insurance Company": "GO DIGIT GENERAL INSURANCE LTD",
            "Insurance Validity": "27-07-2030",
            "Tax Upto": "LTT",
            "PUCC Upto": "28-08-2026",
            "Owner Mobile": "9199038422",
        },
        "challan": {
            "challan_details": [
                {"challan_number": "BR250023260716183506", "accused_name": "R****T K***R",
                 "amount": "1000", "challan_date": "16 Jul 2026", "status": "PENDING",
                 "offence": "DRIVING WITHOUT HELMET", "place": "Sitamarhi"},
                {"challan_number": "BR250023260716183507", "accused_name": "R****T K***R",
                 "amount": "500", "challan_date": "02 Jun 2026", "status": "PAID",
                 "offence": "OVER SPEEDING", "place": "Muzaffarpur"},
            ]
        },
    },
}

SAMPLE_NO_CHALLAN = json.loads(json.dumps(SAMPLE_FULL))
SAMPLE_NO_CHALLAN["result"]["challan"] = {"challan_details": []}


class Handler(BaseHTTPRequestHandler):
    mode = "full"

    def do_GET(self):
        if "fail" in self.path:
            self.send_response(500); self.end_headers(); self.wfile.write(b"boom"); return
        body = json.dumps(SAMPLE_FULL if Handler.mode == "full" else SAMPLE_NO_CHALLAN).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 8791), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
os.environ["VEHICLE_API_URL"] = "http://127.0.0.1:8791/rc"
os.environ["VEHICLE_API_KEY"] = "testkey"
os.environ["BOT_TOKEN"] = "123456789:AAHtesttoken_testtoken_testtoken_testtok"
os.environ["ADMIN_ID"] = "8607774564"

import bot  # noqa: E402
import database as dbm  # noqa: E402
from modules import vehicle_challan as vc  # noqa: E402

PASS, FAIL = [], []


def ok(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("✅ " if cond else "❌ ") + name + ("" if cond else f"  — {str(extra)[:220]}"))


# --------------------------------------------------------- 1) ENGINE
print("\n--- 1) ENGINE (mock API) ---")
res = vc.fetch_vehicle_report("BR30AR0802")
ok("API call hui (ok=True)", res.get("ok") is True, res)
rc = res.get("rc") or {}
ok("Maker/Model mile (HONDA SHINE)", vc._g(rc, "maker name") == "HONDA" and vc._g(rc, "model name") == "SHINE", rc)
ok("Insurance mili (GO DIGIT)", "GO DIGIT" in vc._g(rc, "insurance company"), rc)
ok("PUC validity mili", vc._g(rc, "pucc upto") == "28-08-2026", rc)
ok("Challan 2 mile", len(res.get("challans") or []) == 2, res.get("challans"))
ok("Challan number + offence sahi", vc._challan_from_dict(res["challans"][0], "number") == "BR250023260716183506"
   and "HELMET" in str(vc._challan_from_dict(res["challans"][0], "offence")), res["challans"][0])
sm = vc.challan_summary(res["challans"])
ok("Summary: 1 pending, 1 paid, ₹1000 pending", sm["pending"] == 1 and sm["paid"] == 1 and sm["pending_amount"] == 1000, sm)
ok("Mobile masked", "9199038422" not in vc.mask_mobile("9199038422") and vc.mask_mobile("9199038422").endswith("8422"),
   vc.mask_mobile("9199038422"))
ok("Chassis masked", "ME4HC154DSG053849" != vc.mask_id("ME4HC154DSG053849"), vc.mask_id("ME4HC154DSG053849"))
ok("Name masked (R****T style)", "*" in vc.mask_name("RAMESH KUMAR"), vc.mask_name("RAMESH KUMAR"))
ok("Plate format check", vc.valid_plate("BR30AR0802") and not vc.valid_plate("XX1"))

# --------------------------------------------------------- 2) CARD TEXT
print("\n--- 2) CARD TEXT (jo user ko dikhta hai) ---")
card = vc.render_vehicle_report(res)
for want in ("VEHICLE REPORT — BR30AR0802", "HONDA SHINE", "M-CYCLE/SCOOTER", "PETROL", "99 cc",
             "28-08-2040", "GO DIGIT GENERAL INSURANCE LTD", "till 27-07-2030", "28-08-2026", "LTT",
             "CREDIT WISE CAPITAL PVT LTD", "CHALLANS — 2 found", "BR250023260716183506", "PENDING",
             "₹1,000", "DRIVING WITHOUT HELMET"):
    ok(f"card me '{want}'", want in card, card[:300])
ok("card me mobile poora NAHI dikhta", "9199038422" not in card, card)
ok("card me chassis poora NAHI dikhta", "ME4HC154DSG053849" not in card, card)

# no challan case
Handler.mode = "no_challan"
res2 = vc.fetch_vehicle_report("BR30AR0802")
ok("challan nahi → 'No challan found'", "No challan found" in vc.render_vehicle_report(res2), res2.get("challans"))
Handler.mode = "full"

# fail case
bad = vc.fetch_vehicle_report("BR30AR0802")  # ok
os.environ["VEHICLE_API_URL"] = "http://127.0.0.1:8791/fail-path"
b2 = vc.fetch_vehicle_report("BR30AR0802")
ok("API fail par saaf error + fallback=True", b2.get("ok") is False and b2.get("fallback") is True, b2)
os.environ["VEHICLE_API_URL"] = "http://127.0.0.1:8791/rc"

# --------------------------------------------------------- 3) BOT FLOW
print("\n--- 3) BOT FLOW (Telegram) ---")
sys.path.insert(0, "/home/user/fix")
import importlib
td = importlib.import_module("_selftest_v34") if False else None

# bot ke test helpers reuse karo (v38 ke Ctx pattern)
sys.argv = ["x"]
exec(open("_selftest_v38_desi.py", encoding="utf-8").read().split("# ======================================================================\nasync def t1_menu()")[0])
# ^ isse Ctx / fresh / send_text / click helpers mil jaate hain (aur bot import bhi)

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
    ok("prompt me challan ka zikr", "Challan" in t, t[:200])

    before = dbm.get_credits(USER)
    m2 = await send_text("BR30AR0802", ctx, uid=USER)
    t2 = m2.all_text()
    ok("live report aaya (maker/model)", "HONDA SHINE" in t2, t2[:250])
    ok("challan list aayi", "BR250023260716183506" in t2 and "PENDING" in t2, t2[-400:])
    ok("1 credit kata", dbm.get_credits(USER) == before - 1, (before, dbm.get_credits(USER)))
    ok("'credit used' line aayi", "credit used" in t2.lower(), t2[-200:])
    ok("official buttons aaye", any("echallan" in str(u or "") for u in _urls(m2)), _urls(m2))

    # dobara check (callback)
    q = await click(f"vehagain:BR30AR0802", ctx, uid=USER)
    ok("'Check again' callback chala", "HONDA SHINE" in q.message.all_text(), q.message.all_text()[:200])

    # galat plate → saaf error
    ctx2 = Ctx(); fresh(USER, 5)
    await send_text(kb_label("rto"), ctx2, uid=USER)
    m3 = await send_text("XX99", ctx2, uid=USER)
    ok("galat plate par saaf error", "FAILED" in m3.all_text().upper() or "format" in m3.all_text().lower(), m3.all_text()[:200])

    # 0 credits → block + free links
    fresh(USER, 0)
    ctx3 = Ctx()
    await send_text(kb_label("rto"), ctx3, uid=USER)
    m4 = await send_text("BR30AR0802", ctx3, uid=USER)
    ok("0 credits par premium block", "ALL CREDITS USED" in m4.all_text().upper(), m4.all_text()[:200])

    # VIP → unlimited, credit nahi katta
    fresh(USER, 0, vip=True)
    ctx4 = Ctx()
    await send_text(kb_label("rto"), ctx4, uid=USER)
    m5 = await send_text("BR30AR0802", ctx4, uid=USER)
    ok("VIP ko report mili (0 credits par bhi)", "HONDA SHINE" in m5.all_text(), m5.all_text()[:200])
    ok("VIP ke credits nahi kate", dbm.get_credits(USER) == 0, dbm.get_credits(USER))

    # API config hi nahi → purana free card (koi crash nahi)
    os.environ.pop("VEHICLE_API_URL", None)
    fresh(USER, 5)
    ctx5 = Ctx()
    await send_text(kb_label("rto"), ctx5, uid=USER)
    m6 = await send_text("BR30AR0802", ctx5, uid=USER)
    ok("API ke bina purana free card (district + links)", "RTO Office" in m6.all_text() or "RTO" in m6.all_text(), m6.all_text()[:220])
    ok("API ke bina credit nahi kata", dbm.get_credits(USER) == 5, dbm.get_credits(USER))
    os.environ["VEHICLE_API_URL"] = "http://127.0.0.1:8791/rc"

    # admin status command
    ctxa = Ctx()
    ma = await run_cmd(bot.cmd_vehstatus, ctxa, uid=OWNER, args=["BR30AR0802"])
    ok("/vehstatus admin ko test dikhata hai", "API is working" in ma.all_text(), ma.all_text()[:200])


asyncio.run(flows())

print("\n" + "=" * 70)
print(f"V40 VEHICLE + CHALLAN — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
for f in FAIL:
    print("  ❌", f)
print("=" * 70)
sys.exit(1 if FAIL else 0)
