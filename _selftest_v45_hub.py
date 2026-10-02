# -*- coding: utf-8 -*-
"""
v45 TEST — Aapka apna OSINT HUB bot me laga (Number Info / Vehicle / Aadhaar Family)
====================================================================================
Offline chalne wale tests:
  1) modules/osint_hub.py — parsing, masking, error, cache (hub_get mock)
  2) bot.py wiring — menu button, premium set, prompt, handler, /hubstatus
  3) bot ke asli handlers (fake Telegram objects se) — numinfo / aadhaar / vehicle
  4) live smoke test — agar internet hai to asli hub se (nahi to SKIP)

Chalao:  python3 _selftest_v45_hub.py
"""
import asyncio
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.environ["DB_PATH"] = "/tmp/_v45.db"
os.environ["BOT_TOKEN"] = "123456789:AAHtesttoken_testtoken_testtoken_testtok"
os.environ["ADMIN_ID"] = "8607774564"
os.environ["OSINT_API_KEY"] = "Demo"
sys.path.insert(0, ROOT)

for f in ("/tmp/_v45.db",):
    if os.path.exists(f):
        os.remove(f)

from telegram import Chat, Update, User                       # noqa: E402
from telegram.constants import ChatType                        # noqa: E402

import bot                                                     # noqa: E402
import database as dbm                                         # noqa: E402
from modules import osint_hub as hub                           # noqa: E402

REAL_HUB_GET = hub.hub_get          # mock lagne se pehle asli wala bacha lo

PASS, FAIL = [], []
OWNER = 8607774564
USER = 880000444


def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'✅' if cond else '❌'} {name}" + (f"  — {str(detail)[:200]}" if detail and not cond else ""))


def norm(t):
    import unicodedata
    return unicodedata.normalize("NFKC", t or "")


# ======================================================================
#  SAMPLE PAYLOADS (asli hub ke shape par)
# ======================================================================
NUM_PAYLOAD = {
    "success": True, "query": "9058390341", "record_count": 2,
    "people": [{
        "name": "Brajesh Kumar", "father_name": "Rabendra Singh",
        "phones": ["9058390341", "916395131687"], "alt_phones": ["916395131687"],
        "region": "JIO UPE UPW; AIRTEL UPW", "govt_ids": ["861313813129"],
        "emails": [], "addresses": ["S/O Rabendra Singh,puraiya,JOGAAMainpuri,Uttar Pradesh,206301"],
        "sources": ["num-info", "leak-v1"], "record_count": 2,
    }],
    "sources_used": ["num-info", "leak-v1"],
}

NUM_EMPTY = {"success": True, "query": "9000000000", "record_count": 0, "people": [],
             "sources_used": ["num-info"]}

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

AADHAAR_PAYLOAD = {
    "success": True, "aadhaar_masked": "XXXXXXXX3129", "aadhaar_valid_checksum": True,
    "ration_card_number": "NA", "fps_id": "NA", "member_count": 13,
    "primary": {"name": "Brajesh Kumar", "father_name": "Rabendra Singh",
                "phones": ["916395131687"], "govt_ids": ["861313813129"],
                "addresses": ["S/O Rabendra Singh,puraiya,JOGAAMainpuri,Uttar Pradesh,206301"]},
    "members": [
        {"name": "Brajesh Kumar", "aadhaar_masked": "XXXXXXXX3129",
         "relation": "searched Aadhaar holder", "father_name": "Rabendra Singh",
         "phones": ["916395131687"], "address": "S/O Rabendra Singh,puraiya"},
        {"name": "Shailendra Singh", "aadhaar_masked": "XXXXXXXX4321", "relation": "family",
         "father_name": "Jansan Singh", "phones": [], "address": ""},
    ],
    "location": {"district": "JOGAAMAINPURI", "state": "UTTAR PRADESH", "pincode": "206301"},
    "sources_used": ["num-info", "leak-v1"],
}


class _MockHub:
    """hub_get ko replace kar deta hai — bina internet ke poora rasta test ho jata hai."""

    def __init__(self, mapping):
        self.mapping = mapping
        self.calls = []

    def __call__(self, path, params=None, tmo=None, tries=1):
        self.calls.append((path, dict(params or {})))
        for key, val in self.mapping.items():
            if key in path:
                if isinstance(val, Exception):
                    raise val
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

    # ---- num-info ----
    m = _patch({"num-info": NUM_PAYLOAD})
    r = hub.num_info_report("9058390341")
    ok("num-info ok", r.get("ok") is True, r)
    ok("num-info has_data", r.get("has_data") is True)
    ok("naam mila", (r["people"][0]["name"] == "Brajesh Kumar"), r.get("people"))
    ok("father mila", r["people"][0]["father_name"] == "Rabendra Singh")
    ok("alt number juda", "916395131687" in r["people"][0]["phones"])
    ok("address mila", "206301" in r["people"][0]["addresses"][0])
    ok("query normalise (10 digit)", m.calls[-1][1]["q"] == "9058390341", m.calls[-1])
    # asli hub_get (requests layer) → URL + key sahi jata hai
    captured = {}

    class _Resp:
        status_code = 200

        def json(self):
            return {"success": True, "people": [], "sources_used": []}

    def _fake_get(url, params=None, headers=None, timeout=None):
        captured["url"], captured["params"] = url, dict(params or {})
        return _Resp()

    real_get = hub.requests.get
    real_hub_get = hub.hub_get
    hub.requests.get = _fake_get
    hub.hub_get = REAL_HUB_GET
    try:
        hub.cache_clear()
        hub.num_info_report("9058390341")
    finally:
        hub.requests.get = real_get
        hub.hub_get = real_hub_get
    ok("hub_get URL sahi", str(captured.get("url", "")).endswith("/api/num-info"), captured.get("url"))
    ok("hub_get me key jata hai", captured.get("params", {}).get("key") == "Demo", captured.get("params"))
    ok("format=json bheja", m.calls[-1][1].get("format") == "json")

    r2 = hub.num_info_report("+91 90583-90341")
    ok("11-12 digit se bhi 10 nikalta hai", m.calls[-1][1]["q"] == "9058390341", m.calls[-1][1])
    r3 = hub.num_info_report("123")
    ok("chhota number reject", r3.get("ok") is False)

    # ---- empty record ----
    _patch({"num-info": NUM_EMPTY})
    r4 = hub.num_info_report("9000000000")
    ok("khaali record par has_data False", r4.get("has_data") is False, r4)

    # ---- error ----
    _patch({"num-info": None})
    r5 = hub.num_info_report("9058390341")
    ok("API error par ok=False", r5.get("ok") is False)
    ok("API error par saaf message", bool(r5.get("error")), r5)

    # ---- vehicle ----
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

    # ---- aadhaar ----
    m = _patch({"aadhaar-family": AADHAAR_PAYLOAD})
    a = hub.aadhaar_family_report("861313813129")
    ok("aadhaar ok", a.get("ok") is True, a)
    ok("aadhaar masked", a["aadhaar_masked"] == "XXXXXXXX3129", a.get("aadhaar_masked"))
    ok("members mile", len(a["members"]) == 2, len(a["members"]))
    ok("member_count", a["member_count"] == 13)
    ok("location district", a["location"]["district"] == "JOGAAMAINPURI")
    ok("location pincode", a["location"]["pincode"] == "206301")
    ok("has_data True", a.get("has_data") is True)
    ok("12 digit chhota reject", hub.aadhaar_family_report("12345").get("ok") is False)
    ok("poora 12 digit bheja gaya", m.calls[-1][1]["aadhaar"] == "861313813129", m.calls[-1])


# ======================================================================
#  2) BOT WIRING
# ======================================================================
def test_wiring():
    print("\n--- 2) 🔌 bot.py wiring ---")
    src = io.open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()

    kb_txt = norm(str(bot.KB_BTNS)).upper()
    ok("menu me AADHAAR FAMILY button", "AADHAAR FAMILY" in kb_txt, kb_txt[:150])
    ok("BTN_MODE_MAP me aadhaar", bot.BTN_MODE_MAP.get("AADHAAR FAMILY") == "aadhaar",
       bot.BTN_MODE_MAP.get("AADHAAR FAMILY"))
    ok("aadhaar premium tool hai", "aadhaar" in bot.PREMIUM_TOOLS)
    ok("aadhaar ka premium naam", "Aadhaar" in (bot.PREMIUM_TOOL_NAMES.get("aadhaar") or ""))
    ok("aadhaar prompt maujood", "aadhaar" in bot.PROMPTS and "12 digit" in bot.PROMPTS["aadhaar"])
    ok("numinfo handler hub use karta hai", "hub_numinfo" in src)
    ok("vehicle handler hub v2 use karta hai", "hub_vehicle" in src)
    ok("aadhaar handler hub use karta hai", "hub_aadhaar" in src)
    ok("mode == \"aadhaar\" handler", 'mode == "aadhaar"' in src)
    ok("/hubstatus registered", 'CommandHandler(["hubstatus"' in src)
    ok("BRAND_LINE defined", "BRAND_LINE" in src and "@Supermannn_x" in src)
    ok("_mask_govt_id helper", "_mask_govt_id" in src)
    ok("tutorial video map me aadhaar",
       '"aadhaar"' in io.open(os.path.join(ROOT, "modules/tutorial_hub.py"), encoding="utf-8").read())
    ok("env example me OSINT_API_BASE",
       "OSINT_API_BASE" in io.open(os.path.join(ROOT, ".env.example"), encoding="utf-8").read())

    # masking
    os.environ.pop("NUM_SHOW_FULL_IDS", None)
    ok("Aadhaar mask hota hai", bot._mask_govt_id("861313813129") == "8613****3129",
       bot._mask_govt_id("861313813129"))
    os.environ["NUM_SHOW_FULL_IDS"] = "1"
    ok("env se full ID on", bot._mask_govt_id("861313813129") == "861313813129")
    os.environ.pop("NUM_SHOW_FULL_IDS", None)


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
    print("\n--- 3) 🤖 bot handlers (numinfo / aadhaar / vehicle) ---")
    hub.hub_get = _MockHub({})
    me = await bot.application.bot.get_me() if False else None   # noqa: F841

    # ---------- AADHAAR: galat input ----------
    ctx = Ctx(mode="aadhaar")
    u, m = _upd("12345")
    await bot.on_text(u, ctx)
    ok("aadhaar: galat input par error", "GALAT" in m.U() or "12 digit" in m.replies(), m.replies()[:150])

    # ---------- AADHAAR: sahi input, record mila ----------
    _patch({"aadhaar-family": AADHAAR_PAYLOAD})
    uid = 880000901
    _grant_credits(uid)
    ctx = Ctx(mode="aadhaar")
    u, m = _upd("861313813129", uid=uid)
    await bot.on_text(u, ctx)
    txt = m.replies()
    ok("aadhaar: card bana", "AADHAAR FAMILY CARD" in m.U(), txt[:200])
    ok("aadhaar: masked number", "XXXXXXXX3129" in txt, txt[:300])
    ok("aadhaar: district", "JOGAAMAINPURI" in txt)
    ok("aadhaar: member naam", "Brajesh Kumar" in txt)
    ok("aadhaar: member count", "MEMBERS — 13" in txt or "MEMBERS — 2" in txt, txt[:400])
    ok("aadhaar: branding", "SUPERMANNN_X" in m.U() or "@Supermannn_x" in txt)
    ok("aadhaar: credit kata", "credit" in txt.lower(), txt[:200])

    # ---------- AADHAAR: koi record nahi → credit NAHI katte ----------
    _patch({"aadhaar-family": {"success": True, "aadhaar_masked": "XXXXXXXX0000",
                               "members": [], "member_count": 0, "location": {},
                               "sources_used": []}})
    uid2 = 880000902
    _grant_credits(uid2)
    before = dbm.get_credits(uid2)
    ctx = Ctx(mode="aadhaar")
    u, m = _upd("999999999999", uid=uid2)
    await bot.on_text(u, ctx)
    txt = m.replies()
    ok("aadhaar: no record message", "RECORD NAHI MILA" in m.U(), txt[:200])
    ok("aadhaar: no record par credit NAHI kata", dbm.get_credits(uid2) == before,
       f"{before} -> {dbm.get_credits(uid2)}")
    ok("aadhaar: 'koi credit nahi kata' likha", "CREDIT NAHI KATA" in m.U())

    # ---------- NUMBER INFO ----------
    _patch({"num-info": NUM_PAYLOAD})
    uid3 = 880000903
    _grant_credits(uid3)
    ctx = Ctx(mode="numinfo")
    u, m = _upd("9058390341", uid=uid3)
    await bot.on_text(u, ctx)
    txt = m.replies()
    ok("numinfo: basic card", "NUMBER INFORMATION" in m.U(), txt[:200])
    ok("numinfo: operator", "OPERATOR" in m.U())
    ok("numinfo: public records section", "PUBLIC RECORDS" in m.U())
    ok("numinfo: naam aaya", "Brajesh Kumar" in txt, txt[:400])
    ok("numinfo: father aaya", "Rabendra Singh" in txt)
    ok("numinfo: alt number aaya", "916395131687" in txt)
    ok("numinfo: ID masked (poora Aadhaar nahi)", "861313813129" not in txt, txt[:600])
    ok("numinfo: masked ID dikha", "8613****3129" in txt or "8613" in txt, txt[:600])

    # ---------- NUMBER INFO: koi record nahi → credit NAHI ----------
    _patch({"num-info": NUM_EMPTY})
    uid4 = 880000904
    _grant_credits(uid4)
    before = dbm.get_credits(uid4)
    ctx = Ctx(mode="numinfo")
    u, m = _upd("9000000000", uid=uid4)
    await bot.on_text(u, ctx)
    txt = m.replies()
    ok("numinfo: no record message", "RECORD NAHI MILA" in m.U(), txt[:250])
    ok("numinfo: no record par credit NAHI kata", dbm.get_credits(uid4) == before,
       f"{before} -> {dbm.get_credits(uid4)}")

    # ---------- VEHICLE ----------
    _patch({"vehicle-report": VEH_PAYLOAD})
    uid5 = 880000905
    _grant_credits(uid5)
    ctx = Ctx(mode="rto")
    u, m = _upd("BR30AR0802", uid=uid5)
    await bot.on_text(u, ctx)
    txt = m.replies()
    ok("vehicle: HONDA aaya", "HONDA" in txt, txt[:300])
    ok("vehicle: SHINE aaya", "SHINE" in txt)
    ok("vehicle: challan amount", "1,000" in txt or "1000" in txt, txt[:600])
    ok("vehicle: RC section", "RC" in m.U() or "REGISTRATION" in m.U() or "OWNER" in m.U(), txt[:300])
    ok("vehicle: RTO", "SITAMARHI" in txt.upper(), txt[:400])

    # ---------- VEHICLE: API down → free fallback + credit nahi ----------
    _patch({"vehicle-report": None})
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

    # ---------- /hubstatus admin ----------
    _patch({"num-info": NUM_PAYLOAD, "vehicle-report": VEH_PAYLOAD,
            "aadhaar-family": AADHAAR_PAYLOAD})
    ctx = Ctx()
    u, m = _upd("/hubstatus", uid=OWNER)
    await bot.cmd_hubstatus(u, ctx)
    ok("/hubstatus admin ko status", "HUB STATUS" in m.U(), m.replies()[:200])
    ok("/hubstatus me teeno API", all(k in m.replies() for k in ("num-info", "vehicle-report", "aadhaar-family")))

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
    import importlib
    importlib.reload(hub)
    try:
        import socket
        socket.create_connection(("osint-api-hub.onrender.com", 443), timeout=6).close()
    except Exception as e:                                     # noqa: BLE001
        print(f"⏭️  SKIP — hub reachable nahi ({type(e).__name__})")
        return
    try:
        v = hub.vehicle_report_v2("BR30AR0802")
        ok("live vehicle ok", v.get("ok") is True, str(v)[:150])
        n = hub.num_info_report("9058390341")
        ok("live num-info ok", n.get("ok") is True, str(n)[:150])
        a = hub.aadhaar_family_report("861313813129")
        ok("live aadhaar ok", a.get("ok") is True, str(a)[:150])
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
