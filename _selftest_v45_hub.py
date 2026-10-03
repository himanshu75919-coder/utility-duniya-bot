# -*- coding: utf-8 -*-
"""
v45 TEST — OSINT HUB & Privacy-Safe Guardrails
==============================================
Offline chalne wale tests:
  1) modules/osint_hub.py — privacy-safe disabled lookups, vehicle_report_v2, error, cache (hub_get mock)
  2) bot.py wiring — menu button, premium set, prompt, handler, /hubstatus
  3) bot ke asli handlers (fake Telegram objects se) — numinfo / vehicle
  4) live smoke test — agar internet hai to asli hub se (nahi to SKIP)

Chalao:  python3 _selftest_v45_hub.py
"""
import asyncio
import io
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ["DB_PATH"] = "/tmp/_v45_hub.db"
os.environ["BOT_TOKEN"] = "123456789:AAHtesttoken_testtoken_testtoken_testtok"
os.environ["ADMIN_ID"] = "8607774564"
os.environ["OSINT_API_KEY"] = "Demo"
sys.path.insert(0, ROOT)

for f in ("/tmp/_v45_hub.db",):
    if os.path.exists(f):
        os.remove(f)

from telegram import Chat, Update, User                       # noqa: E402
from telegram.constants import ChatType                        # noqa: E402

import bot                                                     # noqa: E402
import database as dbm                                         # noqa: E402
from modules import api_hub                                    # noqa: E402
from modules import osint_hub as hub                           # noqa: E402
from modules import vehicle_challan as vc                      # noqa: E402

REAL_HUB_GET = hub.hub_get

PASS, FAIL = [], []
OWNER = 8607774564
USER = 880000444


def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'✅' if cond else '❌'} {name}" + (f"  — {str(detail)[:200]}" if detail and not cond else ""))


def norm(t):
    import unicodedata
    return unicodedata.normalize("NFKC", t or "")


VEH_PAYLOAD = {
    "success": True, "number": "BR30AR0802",
    "vehicle": {"maker": "HONDA", "model": "SHINE", "maker_model": "HONDA SHINE",
                "vehicle_class": "M-CYCLE/SCOOTER", "fuel": "PETROL",
                "cubic_capacity": "124.6 CC", "seating_capacity": "2",
                "fuel_norms": "BHARAT STAGE VI"},
    "owner": {"owner_name": "S*****U S*H", "financer": "NA", "blacklist_status": "NA"},
    "rto": {"registered_rto": "SITAMARHI, BIHAR", "code": "BR-30", "city_name": "Sitamarhi",
            "address": "Dumra Road, Sitamarhi", "phone": "NA", "state": "Bihar"},
    "rc": {"registration_number": "BR30AR0802", "registration_date": "29-Aug-2025",
           "fitness_upto": "28-Aug-2040", "insurance_upto": "27-Jul-2030"},
    "insurance": {"company": "GO DIGIT GENERAL INSURANCE LTD", "expiry": "27-Jul-2030",
                  "status": "You Are Insured"},
    "puc": {"upto": "28-Aug-2026", "status": "PUC Already Expired"},
    "challans": {"count": 1, "pending_count": 1, "pending_amount": 1000,
                 "total_amount": 1000, "disposed_count": 0,
                 "list": [{"accused_name": "R****T K***R", "amount": "1000",
                           "challan_date": "16-07-2026", "challan_number": "BR250023260716183506",
                           "challan_place": "Sitamarhi", "challan_status": "Pending",
                           "court_name": "", "offense_details": "Driving without helmet"}]},
    "sources_used": ["vehicle-rc", "vehicle-challan"],
}


class _MockHub:
    def __init__(self, mapping):
        self.mapping = mapping
        self.calls = []

    def __call__(self, path, params=None, tmo=None, tries=1,
                 base_override=None, key_override=None):
        self.calls.append((path, dict(params or {})))
        for key, val in self.mapping.items():
            if key in path:
                if isinstance(val, Exception):
                    raise val
                if val is None:
                    return None, "The API did not answer."
                return val, None
        return None, "The API did not answer."


def _patch(payload_map):
    hub.cache_clear()
    m = _MockHub(payload_map)
    hub.hub_get = m
    return m


# ======================================================================
#  1) OSINT HUB MODULE
# ======================================================================
def test_hub_module():
    print("\n--- 1) 📡 modules/osint_hub.py (offline, mocked) ---")

    ok("default base aapka hub hai", "osint-api-hub.onrender.com" in hub.DEFAULT_BASE, hub.DEFAULT_BASE)
    ok("default key Demo", hub.api_key() == "Demo", hub.api_key())

    # ---- privacy-safe disabled num-info & aadhaar ----
    m = _patch({})
    r = hub.num_info_report("9058390341")
    ok("num-info privacy disabled (ok=False)", r.get("ok") is False and r.get("disabled") is True, r)
    ok("num-info has_data False", r.get("has_data") is False)
    ok("num-info koi network call nahi karta", len(m.calls) == 0, m.calls)

    a = hub.aadhaar_family_report("861313813129")
    ok("aadhaar privacy disabled (ok=False)", a.get("ok") is False and a.get("disabled") is True, a)
    ok("aadhaar has_data False", a.get("has_data") is False)
    ok("aadhaar koi network call nahi karta", len(m.calls) == 0, m.calls)

    # ---- asli hub_get (requests layer) ----
    captured = {}

    class _Resp:
        status_code = 200

        def json(self):
            return {"success": True}

    def _fake_get(url, params=None, headers=None, timeout=None):
        captured["url"], captured["params"] = url, dict(params or {})
        return _Resp()

    real_get = hub.requests.get
    real_hub_get = hub.hub_get
    hub.requests.get = _fake_get
    hub.hub_get = REAL_HUB_GET
    try:
        hub.cache_clear()
        hub.hub_get("health", {"format": "json"})
    finally:
        hub.requests.get = real_get
        hub.hub_get = real_hub_get
    ok("hub_get URL sahi", str(captured.get("url", "")).endswith("/api/health"), captured.get("url"))
    ok("hub_get me key jata hai", captured.get("params", {}).get("key") == "Demo", captured.get("params"))
    ok("format=json bheja", captured.get("params", {}).get("format") == "json")

    # ---- vehicle (default unauthorized vs authorized) ----
    os.environ.pop("VEHICLE_PROVIDER_AUTHORIZED", None)
    os.environ.pop("VEHICLE_API_BASE", None)
    v_unauth = hub.vehicle_report_v2("BR30AR0802")
    ok("vehicle bina authorization fallback deta hai", v_unauth.get("ok") is False and v_unauth.get("fallback") is True)

    os.environ["VEHICLE_PROVIDER_AUTHORIZED"] = "1"
    os.environ["VEHICLE_API_BASE"] = "https://osint-api-hub.onrender.com/api"
    try:
        m = _patch({"vehicle-report": VEH_PAYLOAD})
        v = hub.vehicle_report_v2("br30ar0802")
        ok("vehicle ok", v.get("ok") is True, v)
        ok("plate upper + clean", v["plate"] == "BR30AR0802", v.get("plate"))
        ok("maker map hua", v["rc"]["maker"] == "HONDA")
        ok("model map hua", v["rc"]["model"] == "SHINE")
        ok("insurance map hua", "GO DIGIT" in (v["rc"]["ins_company"] or ""), v["rc"]["ins_company"])
        ok("PUC map hua", v["rc"]["puc_upto"] == "28-Aug-2026")
        ok("challan count", v["summary"]["count"] == 1, v.get("summary"))
        ok("pending amount", v["summary"]["pending_amount"] == 1000.0, v["summary"])
        ok("challan list me 1 row", len(v["challans"]) == 1)
        ok("challan number asli", v["challans"][0]["challan_number"] == "BR250023260716183506")
        ok("has_data True", v.get("has_data") is True)
        ok("cache dobara call nahi karta", len(m.calls) == 1, m.calls)
        hub.vehicle_report_v2("BR30AR0802")
        ok("dusri call cache se (network call nahi hua)", len(m.calls) == 1, len(m.calls))
    finally:
        os.environ.pop("VEHICLE_PROVIDER_AUTHORIZED", None)
        os.environ.pop("VEHICLE_API_BASE", None)


# ======================================================================
#  2) BOT WIRING
# ======================================================================
def test_wiring():
    print("\n--- 2) 🔌 bot.py wiring ---")
    src = io.open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()

    kb_txt = norm(str(bot.KB_BTNS)).upper()
    ok("menu me NUMBER INFO button", "NUMBER INFO" in kb_txt)
    ok("menu me VEHICLE + CHALLAN button", "VEHICLE" in kb_txt)
    ok("menu me IMEI / PHONE DETAILS button", "IMEI" in kb_txt)
    ok("api_hub wired in bot.py", "from modules import api_hub" in src)
    ok("/hubstatus registered", 'CommandHandler(["hubstatus"' in src)
    ok("SUPPORT_USERNAME defined", "SUPPORT_USERNAME" in src and "@Supermannn_x" in src)
    ok("sancharsaathi safety link", "sancharsaathi.gov.in" in src)
    ok("env example me HUB_API_BASE",
       "HUB_API_BASE" in io.open(os.path.join(ROOT, ".env.example"), encoding="utf-8").read())


# ======================================================================
#  3) BOT HANDLERS (fake Telegram)
# ======================================================================
class FakeSent:
    def __init__(self, owner=None, bucket=None):
        self.owner = owner
        self.bucket = bucket if bucket is not None else []

    async def edit_text(self, text, **kw):
        if self.owner is not None:
            self.bucket.append(text)
        return self

    async def delete(self):
        return True


class FakeMsg:
    def __init__(self, text="", uid=USER):
        self.text = text
        self.caption = None
        self.uid = uid
        self.photo = self.video = self.document = self.audio = self.voice = self.animation = None
        self.sent, self.edits, self.kbs = [], [], []
        self.chat = Chat(id=uid, type=ChatType.PRIVATE)
        self.chat_id = uid

    def all_text(self):
        return "\n".join([self.text or ""] + self.sent + self.edits)

    def replies(self):
        return "\n".join(self.sent + self.edits)

    def U(self):
        return norm(bot.unbold(self.replies())).upper()

    async def reply_text(self, text, **kw):
        self.sent.append(text)
        if kw.get("reply_markup"):
            self.kbs.append(kw["reply_markup"])
        return FakeSent(self, self.edits)

    async def reply_photo(self, photo=None, caption="", **kw):
        self.sent.append(caption or "")
        return FakeSent(self, self.edits)

    async def reply_document(self, document=None, caption="", **kw):
        self.sent.append(caption or "")
        return FakeSent(self, self.edits)

    async def reply_video(self, video=None, caption="", **kw):
        self.sent.append(caption or "")
        return FakeSent(self, self.edits)

    async def edit_text(self, text, **kw):
        self.edits.append(text)
        return FakeSent(self, self.edits)


class Ctx:
    def __init__(self, **kw):
        self.user_data = dict(kw)
        self.args = []


def _upd(text, uid=USER):
    m = FakeMsg(text, uid=uid)
    u = Update(update_id=1, message=m)
    u.message.from_user = User(id=uid, first_name="Test", is_bot=False)
    return u, m


def _grant_credits(uid, n=50):
    try:
        dbm.add_credits(uid, n)
    except Exception:
        pass


async def flows():
    print("\n--- 3) 🤖 bot handlers (numinfo / vehicle / hubstatus) ---")

    # ---------- NUMBER INFO (local metadata + official safety links) ----------
    uid3 = 880000903
    _grant_credits(uid3)
    ctx = Ctx(mode="numinfo")
    u, m = _upd("9876543210", uid=uid3)
    await bot.on_text(u, ctx)
    txt = m.replies()
    urls = [b.url for kb in m.kbs for row in getattr(kb, "inline_keyboard", []) for b in row if getattr(b, "url", None)]
    ok("numinfo: basic card", "NUMBER INFORMATION" in m.U(), txt[:200])
    ok("numinfo: operator", "OPERATOR" in m.U())
    ok("numinfo: safety link button", any("sancharsaathi.gov.in" in u for u in urls), urls)

    # ---------- VEHICLE ----------
    orig_fetch = bot.fetch_vehicle_report
    try:
        def _fake_veh(plate):
            return {
                "ok": True,
                "plate": "BR30AR0802",
                "rc": hub._rc_from_hub(VEH_PAYLOAD, "BR30AR0802"),
                "challans": VEH_PAYLOAD["challans"]["list"],
                "summary": {"count": 1, "pending": 1, "paid": 0, "other": 0,
                            "total_amount": 1000.0, "pending_amount": 1000.0},
                "sources": ["vehicle-report (hub v2)"],
            }
        bot.fetch_vehicle_report = _fake_veh
        uid5 = 880000905
        _grant_credits(uid5)
        ctx = Ctx(mode="rto")
        u, m = _upd("BR30AR0802", uid=uid5)
        await bot.on_text(u, ctx)
        txt = m.replies()
        ok("vehicle: HONDA aaya", "HONDA" in txt, txt[:300])
        ok("vehicle: SHINE aaya", "SHINE" in txt)
        ok("vehicle: challan amount", "1,000" in txt or "1000" in txt, txt[:600])
        ok("vehicle: RTO", "SITAMARHI" in txt.upper(), txt[:400])

        # ---------- VEHICLE: API down → free fallback + credit nahi ----------
        bot.fetch_vehicle_report = lambda p: {"ok": False, "error": "API down", "fallback": True}
        uid6 = 880000906
        _grant_credits(uid6)
        before = dbm.get_credits(uid6)
        ctx = Ctx(mode="rto")
        u, m = _upd("MH12AB1234", uid=uid6)
        await bot.on_text(u, ctx)
        txt = m.replies()
        ok("vehicle: API fail par crash nahi", bool(txt.strip()), txt[:150])
        ok("vehicle: API fail par credit NAHI kata", dbm.get_credits(uid6) == before,
           f"{before} -> {dbm.get_credits(uid6)}")
    finally:
        bot.fetch_vehicle_report = orig_fetch

    # ---------- /hubstatus admin ----------
    orig_test = api_hub.live_test
    orig_ready = api_hub.hub_ready
    try:
        api_hub.hub_ready = lambda: True
        api_hub.live_test = lambda: {"ok": True, "say": "PIN 800001 -> Bihar"}
        ctx = Ctx()
        u, m = _upd("/hubstatus", uid=OWNER)
        await bot.cmd_hubstatus(u, ctx)
        ok("/hubstatus admin ko status", "API HUB" in m.U(), m.replies()[:200])
        ok("/hubstatus me tools list", all(k in m.replies() for k in ("IFSC", "PINCODE", "IMEI", "VEHICLE")))
    finally:
        api_hub.live_test = orig_test
        api_hub.hub_ready = orig_ready

    uid7 = 880000907
    ctx = Ctx()
    u, m = _upd("/hubstatus", uid=uid7)
    await bot.cmd_hubstatus(u, ctx)
    ok("/hubstatus non-admin ko kuch nahi", not m.replies().strip(), m.replies()[:80])


# ======================================================================
#  4) LIVE SMOKE (optional)
# ======================================================================
def live_smoke():
    print("\n--- 4) 🌐 LIVE hub (agar internet ho) ---")
    try:
        import socket
        socket.create_connection(("osint-api-hub.onrender.com", 443), timeout=6).close()
    except Exception as e:                                     # noqa: BLE001
        print(f"⏭️  SKIP — hub reachable nahi ({type(e).__name__})")
        return
    try:
        lt = api_hub.live_test()
        ok("live hub ip-v2 + key-info ok", lt.get("ok") is True, str(lt)[:150])
        v = vc.fetch_vehicle_report("BR30AR0802")
        ok("live vehicle response ya safe disabled fallback", v.get("ok") is True or v.get("hub_disabled") is True, str(v)[:150])
    except Exception as e:                                     # noqa: BLE001
        ok("live hub reachable", False, f"{type(e).__name__}: {str(e)[:150]}")


# ======================================================================
if __name__ == "__main__":
    test_hub_module()
    test_wiring()
    asyncio.run(flows())
    live_smoke()
    print("\n" + "=" * 72)
    print(f"V45 OSINT HUB — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
    for f in FAIL:
        print("  ❌", f)
    print("=" * 72)
    sys.exit(1 if FAIL else 0)
