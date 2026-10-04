"""v45 TEST — 🔌 API HUB integration (local mock hub server, asli HTTP).

Kya test hota hai:
  1. api_hub client: ready/key/base, saare endpoints ka normalization, 401 handling
  2. Tools hub par shift: IP, IFSC, PINCODE, TERABOX, YouTube, X-video, GST, PAN, num-info
  3. Fallback: hub key na ho to purane API chalte rehte hain (kuch tootta nahi)
  4. Bot flows: KAGAZ GST/PAN card, ID finder profiles, /hubstatus, clip gate
"""
import asyncio
import json
import os
import sys

os.environ.setdefault("PREMIUM_ONLY", "off")   # tools ka behaviour test karne ke liye
import threading
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

os.environ["DB_PATH"] = "/tmp/_v45.db"
os.environ["BOT_TOKEN"] = "123456789:AAHtesttoken_testtoken_testtoken_testtok"
os.environ["ADMIN_ID"] = "8607774564"
os.environ["CLIP_YTDLP"] = "0"
os.environ.pop("AI_MOCK", None)
if os.path.exists("/tmp/_v45.db"):
    os.remove("/tmp/_v45.db")

PORT = 8899
os.environ["HUB_API_BASE"] = f"http://127.0.0.1:{PORT}/api"
os.environ["HUB_API_KEY"] = "testkey123"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Chat, Update, User                      # noqa: E402
from telegram.constants import ChatType                      # noqa: E402

import bot                                                   # noqa: E402
import database as dbm                                       # noqa: E402
from modules import api_hub as hub                           # noqa: E402
from modules import osint_tools as ost                       # noqa: E402
from modules import cloud_tools as ct                        # noqa: E402
from modules import media_downloader as md                   # noqa: E402

PASS, FAIL = [], []
OWNER, USER = 8607774564, 880000555

OK_KEY = "testkey123"


def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'✅' if cond else '❌'} {name}" + (f"  — {str(detail)[:220]}" if detail and not cond else ""))


# ======================================================================
# MOCK HUB SERVER
# ======================================================================
class HubHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        raw_path = u.path
        if raw_path.startswith("/dl/") or raw_path.startswith("/snap/"):
            data = b"D" * 150_000
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        path = raw_path.replace("/api", "", 1) or "/"
        if q.get("key", [""])[0] != OK_KEY:
            return self._json(401, {"error": "Invalid API key"})
        if path == "/ip-v2":
            return self._json(200, {"ip": q.get("ip", [""])[0], "country": "United States",
                                    "countryCode": "US", "regionName": "California", "city": "Mountain View",
                                    "zip": "94043", "lat": 37.4, "lon": -122.07, "timezone": "America/Los_Angeles",
                                    "isp": "Google LLC", "org": "Google Public DNS", "as": "AS15169",
                                    "proxy": False, "mobile": False, "hosting": True})
        if path == "/ifsc":
            return self._json(200, {"BANK": "State Bank of India", "BRANCH": "PATNA MAIN",
                                    "ADDRESS": "Gandhi Maidan, Patna", "CITY": "PATNA", "DISTRICT": "PATNA",
                                    "STATE": "BIHAR", "CONTACT": "0612-2222222", "MICR": "800002001",
                                    "NEFT": True, "RTGS": True, "IMPS": True, "UPI": True})
        if path == "/pincode":
            return self._json(200, {"district": "Patna", "state": "Bihar", "taluk": "Patna Sadar",
                                    "division": "Patna", "region": "Patna HQ", "circle": "Bihar",
                                    "postoffice": [{"name": "Patna GPO"}, {"name": "Rajendra Nagar SO"}],
                                    "total": 2})
        if path in ("/terabox-file", "/terabox-stream", "/terabox-stream-v2", "/terabox-stream-v3"):
            return self._json(200, {"files": [{"name": "movie.mp4", "size": 104857600,
                                               "link": f"http://127.0.0.1:{PORT}/dl/movie.mp4",
                                               "thumb": ""}]})
        if path in ("/youtube-all", "/youtube-info"):
            return self._json(200, {"title": "Test Video", "duration": 120,
                                    "hd": f"http://127.0.0.1:{PORT}/dl/yt.mp4"})
        if path in ("/youtube-download", "/ytdl", "/youtube-mp3"):
            _dl = f"http://127.0.0.1:{PORT}/dl/yt.mp4"
            _au = f"http://127.0.0.1:{PORT}/dl/yt.m4a"
            return self._json(200, {"success": True, "title": "Test Video", "duration": 120,
                                    "links": [{"type": "video", "quality": "720p", "ext": "mp4",
                                               "url": _dl, "proxy_url": _dl},
                                              {"type": "audio", "quality": "128kbps", "ext": "m4a",
                                               "url": _au, "proxy_url": _au}],
                                    "download_url": _dl, "audio_url": _au,
                                    "proxy_download_url": _dl, "proxy_audio_url": _au})
        if path.startswith("/twitter-video") or path == "/twitter-hd-video":
            return self._json(200, {"hd": f"http://127.0.0.1:{PORT}/dl/tw.mp4", "title": "Tweet video"})
        if path == "/instagram-profile":
            return self._json(200, {"full_name": "Sumit Sharma", "biography": "travel | food",
                                    "followers": 12000, "following": 350, "posts": 210,
                                    "private": False, "verified": True, "profile_pic_url": "http://x/p.jpg"})
        if path == "/snap-stories":
            return self._json(200, {"stories": [f"http://127.0.0.1:{PORT}/snap/{i}.jpg" for i in range(3)]})
        if path in ("/twitter-profile-v2", "/twitter-profile"):
            return self._json(200, {"name": "News Laundry", "username": "newslaundry",
                                    "description": "media", "followers": 500000, "verified": True})
        if path == "/gst-search":
            return self._json(200, {"legalName": "TEST ENTERPRISES", "tradeName": "TEST TRADERS",
                                    "status": "Active", "gstType": "Regular", "state": "Bihar",
                                    "address": "Patna, Bihar", "regDate": "01-07-2019", "pan": "BOKPS7056D"})
        if path == "/pan-to-gst-v4":
            return self._json(200, {"pan": q.get("pan", [""])[0],
                                    "gstins": [{"gstin": "19BOKPS7056D1ZI", "status": "Active",
                                                "name": "TEST ENTERPRISES"}]})
        if path in ("/num-info", "/leak-v1"):
            return self._json(200, {"success": True, "query": q.get("q", [""])[0], "record_count": 1,
                                    "people": [{"name": "TEST USER", "father_name": "TEST FATHER",
                                                "phones": ["9058390341"], "region": "JIO UPW",
                                                "addresses": ["Patna, Bihar"], "govt_ids": ["123456789012"]}],
                                    "sources_used": ["num-info"], "formatted": "NUMBER REPORT"})
        if path in ("/num-disabled",):
            return self._json(410, {"success": False, "status": "disabled",
                                    "error": "Leaked personal-record lookup yahan supported nahi.",
                                    "official_links": {"report": "https://cybercrime.gov.in/"}})
        if path in ("/vehicle-report", "/vehicle-full", "/rc-info"):
            if os.environ.get("MOCK_VEH_DISABLED") == "1":
                return self._json(410, {"success": False, "status": "disabled",
                                        "error": "Live vehicle/owner/challan lookup disabled hai."})
            return self._json(200, {"vehicle": {"maker": "HONDA", "model": "SHINE"},
                                    "owner": {"name": "S*****U S*H"},
                                    "rto": {"code": "BR30", "name": "SITAMARHI", "state": "BIHAR"},
                                    "rc": {"registration": "29-Aug-2025", "fitness": "28-Aug-2040"},
                                    "insurance": {"company": "GO DIGIT", "valid_upto": "27-Jul-2030"},
                                    "puc": {"valid_upto": "28-Aug-2026"},
                                    "challans": {"count": 1, "pending_count": 1, "pending_amount": 1000,
                                                 "total_amount": 1000,
                                                 "list": [{"challan_number": "BR250023260716183506",
                                                           "amount": 1000, "status": "PENDING",
                                                           "offence": "Driving without helmet",
                                                           "date": "16-07-2026"}]}})
        if path == "/key-info":
            return self._json(200, {"success": True, "plan": "ALL ENDPOINTS", "status": "active",
                                    "expires_at_ist": "Never (lifetime)"})
        if path == "/song":
            return self._json(200, {"results": [{"title": "Chandni", "artists": "Sachet Tandon",
                                                 "download_url": "http://127.0.0.1:%d/dl/s.mp3" % PORT}]})
        if path == "/imei":
            return self._json(200, {"success": True, "tac": "35301011", "brand": "APPLE",
                                    "model": "iPhone 12 mini", "reporting_body": "BABT (UK)"})
        return self._json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        self.do_GET()


srv = ThreadingHTTPServer(("127.0.0.1", PORT), HubHandler)
threading.Thread(target=srv.serve_forever, daemon=True).start()


# ======================================================================
def test_client():
    print("\n--- 1) 🔌 API HUB CLIENT ---")
    ok("hub ready (key lagi)", hub.hub_ready() is True, hub.status_card()[:80])
    ok("base env se uthaya", hub.hub_base() == f"http://127.0.0.1:{PORT}/api", hub.hub_base())
    ok("key name batata hai", hub.hub_key_name() in ("HUB_API_KEY", "VEHICLE_API_KEY"), hub.hub_key_name())
    ok("Demo key valid hai (hub ka public lifetime key)",
       (os.environ.__setitem__("HUB_API_KEY", "Demo") or hub.hub_ready()) is True)
    ok("key khaali ho to bhi default Demo chalti hai",
       (os.environ.__setitem__("HUB_API_KEY", "") or hub.hub_key()) == "Demo")
    os.environ["HUB_API_KEY"] = OK_KEY

    ip = hub.hub_ip("8.8.8.8")
    ok("IP normalise (ip-v2)", ip.get("ok") and ip["isp"] == "Google LLC" and ip["is_hosting"] is True,
       ip)
    ok("IP maps link bana", "maps.google.com" in ip.get("maps_link", ""), ip.get("maps_link"))
    ok("IP source hub batata hai", "ip-v2" in ip.get("source", ""), ip.get("source"))

    ifc = hub.hub_ifsc("SBIN0000001")
    ok("IFSC normalise", ifc.get("ok") and ifc["bank"] == "State Bank of India"
       and ifc["micr"] == "800002001" and ifc["upi"] is True, ifc)

    pin = hub.hub_pincode("800001")
    ok("PINCODE normalise", pin.get("ok") and pin["district"] == "Patna"
       and pin["post_offices"] == ["Patna GPO", "Rajendra Nagar SO"], pin)

    tb = hub.hub_terabox("https://1024terabox.com/s/1ahJz-qdH7h_9One0lXxDoA")
    ok("TERABOX files mile", tb.get("ok") and tb["files"][0]["name"] == "movie.mp4"
       and tb["files"][0]["size_h"].endswith("MB"), tb)

    ytd = hub.hub_yt_download("https://youtu.be/X8X-XyK4CYE")
    ok("hub_yt_download → video+audio links (v47)", ytd.get("ok") and "dl/yt.mp4" in ytd.get("best_url", "")
       and "dl/yt.m4a" in ytd.get("audio_url", ""), {k: v for k, v in ytd.items() if k != "links"})

    yt = hub.hub_youtube("https://youtu.be/X8X-XyK4CYE")
    ok("YouTube direct link mila", yt.get("ok") and yt["video"].endswith("yt.mp4"), yt)

    tw = hub.hub_twitter_video("https://twitter.com/x/status/123")
    ok("Twitter video link mila", tw.get("ok") and tw["url"].endswith("tw.mp4"), tw)

    ig = hub.hub_insta_profile("@sumit")
    ok("Instagram profile data", ig.get("ok") and ig["followers"] == 12000 and ig["verified"] is True, ig)

    sp = hub.hub_snap_stories("priya")
    ok("Snap stories mili", sp.get("ok") and sp["count"] == 3, sp)

    gst = hub.hub_gst("19BOKPS7056D1ZI")
    ok("GST details mile", gst.get("ok") and gst["legal_name"] == "TEST ENTERPRISES"
       and gst["status"] == "Active", gst)

    pan = hub.hub_pan("BOKPS7056D")
    ok("PAN → GST mile", pan.get("ok") and pan["gstins"][0]["gstin"] == "19BOKPS7056D1ZI", pan)

    ni = hub.hub_num_info("9876543210")
    ok("num-info hub se", ni.get("ok") is True and isinstance(ni.get("data"), dict), ni)

    # v49.9: leaked record parser (naam/papa/address) poora code se hata diya — kanoon
    ok("leaked-records parser code me nahi hai (legal saaf)",
       not hasattr(hub, "hub_num_report"), dir(hub))

    veh = hub.hub_vehicle_report_new("BR30AR0802")
    ok("vehicle-report parse hua", veh.get("ok") and veh["vehicle"]["maker"] == "HONDA"
       and veh["challans"]["count"] == 1, veh)

    ki = hub.hub_key_info()
    ok("key-info plan batata hai", ki.get("ok") and "ALL" in str(ki.get("plan", "")).upper(), ki)

    sg = hub.hub_song("chandani")
    ok("song search chala", sg.get("ok") and sg["songs"][0]["title"] == "Chandni", sg)

    ok("live_test me plan bhi aata hai", "plan" in str(hub.live_test().get("say", "")).lower(), hub.live_test())

    ok("galat input par saaf error (crash nahi)", hub.hub_ifsc("ABC").get("ok") is False
       and "11 characters" in hub.hub_ifsc("ABC")["error"], hub.hub_ifsc("ABC"))
    ok("GST galat length par saaf error", hub.hub_gst("123")["error"].startswith("GSTIN"), hub.hub_gst("123"))

    # 401 handling
    os.environ["HUB_API_KEY"] = "WRONGKEY"
    r = hub.hub_get("/ip-v2", {"ip": "8.8.8.8"})
    ok("galat key par auth error", r.get("ok") is False and r.get("auth") is True, r)
    os.environ["HUB_API_KEY"] = OK_KEY

    # hub off karne par: disabled error + status card
    os.environ["HUB_ENABLED"] = "off"
    ok("HUB_ENABLED=off par disabled error", hub.hub_get("/ip-v2", {}).get("disabled") is True)
    ok("off hone par ready False", hub.hub_ready() is False)
    os.environ.pop("HUB_ENABLED", None)
    ok("status card Demo + OFF wale endpoints batata hai",
       "Demo" in hub.status_card() and "Vehicle" in hub.status_card() and "OFF" in hub.status_card().upper(),
       hub.status_card()[:160])
    ok("default base = user ka hub (module constant)",
       "osint-api-hub.onrender.com" in hub.DEFAULT_BASE, hub.DEFAULT_BASE)

    # v46: 410 disabled detection
    os.environ["MOCK_VEH_DISABLED"] = "1"
    dv = hub.hub_vehicle_report_new("BR30AR0802")
    ok("410 par disabled_by_hub detect hota hai", dv.get("ok") is False and dv.get("disabled_by_hub") is True, dv)
    os.environ.pop("MOCK_VEH_DISABLED", None)


def test_tools_hub():
    print("\n--- 2) 🧰 TOOLS HUB PAR SHIFT ---")
    ip = ost.lookup_ip_domain("8.8.8.8")
    ok("IP tool hub se ja raha hai", ip.get("ok") and "hub" in str(ip.get("source", "")), ip.get("source"))

    ifc = ost.lookup_ifsc("SBIN0000001")
    ok("IFSC tool hub se", ifc.get("ok") and "hub" in str(ifc.get("source", "")), ifc.get("source"))

    pin = ost.lookup_pincode("800001")
    ok("PINCODE tool hub se", pin.get("ok") and "hub" in str(pin.get("source", "")), pin.get("source"))

    tb = ct.resolve_terabox("https://1024terabox.com/s/1ahJz-qdH7h_9One0lXxDoA")
    ok("TERABOX tool hub engine se", tb.get("ok") and "API Hub" in str(tb.get("provider", "")), tb.get("provider"))

    # v49.9: leaked personal records (naam/pata/Aadhaar) HAMESHA blocked — kanoon (DPDP/Aadhaar Act)
    rec = ost.lookup_public_records("9876543210")
    ok("LEAKED RECORDS BLOCKED (kanooni safety)", rec.get("ok") is False and rec.get("blocked") is True,
       f"blocked={rec.get('blocked')}")

    sf = ost.number_safety_info("9876543210")
    ok("SAFETY CARD (legal) links", sf.get("ok") and len(sf.get("links") or []) >= 3, len(sf.get("links") or []))

    un = ost.check_username_platforms("sumit_sharma2")
    ok("ID finder profiles bhi deta hai", un.get("ok") and "instagram" in (un.get("profiles") or {}),
       list((un.get("profiles") or {}).keys()))

    # v49: YouTube hub path (clip maker hata diya — ab media_downloader ka engine)
    res = md._hub_youtube_download("https://youtu.be/X8X-XyK4CYE", 48)
    ok("YouTube hub se video/link mila", res.get("ok") is True, res.get("engine") or res)
    ok("engine me hub likha", "hub" in str(res.get("engine", "")), res.get("engine"))


def test_fallback():
    print("\n--- 3) 🛟 FALLBACK (hub band ho to bhi sab chale) ---")
    saved = os.environ.pop("HUB_API_KEY")
    os.environ["HUB_ENABLED"] = "off"
    try:
        ok("hub ready nahi (off)", hub.hub_ready() is False)
        # ip-api (network) — real internet chahiye; fail bhi ho to crash nahi hona chahiye
        r = ost.lookup_ip_domain("8.8.8.8")
        ok("IP tool phir bhi jawab deta hai (fallback/khali error)", isinstance(r, dict) and "ok" in r, r)
        ok("IFSC tool fallback", ost.lookup_ifsc("SBIN0000001").get("ok") in (True, False))
        ok("Pincode tool fallback", isinstance(ost.lookup_pincode("800001"), dict))
        tb = ct.resolve_terabox("https://1024terabox.com/s/1ahJz-qdH7h_9One0lXxDoA")
        ok("TERABOX fallback crash nahi karta", isinstance(tb, dict) and "ok" in tb, tb.get("error"))
        res = md._hub_youtube_download("https://youtu.be/x", 48)
        ok("Hub youtube path band hub par saaf mana karta hai", res.get("ok") is False, res)
    finally:
        os.environ["HUB_API_KEY"] = saved
        os.environ.pop("HUB_ENABLED", None)


# ======================================================================
class FakeSent:
    def __init__(self, owner=None, bucket=None):
        self.owner, self.bucket = owner, bucket if bucket is not None else []

    async def edit_text(self, text, **kw):
        self.bucket.append(text)
        if kw.get("reply_markup") and self.owner:
            self.owner.kbs.append(kw["reply_markup"])
        return self

    async def delete(self):
        return True


class FakeMsg:
    def __init__(self, text="", uid=USER):
        self.text, self.uid = text, uid
        self.caption = None
        self.photo = self.video = self.document = None
        self.audio = self.voice = self.animation = None
        self.sent, self.edits, self.kbs = [], [], []
        self.chat = Chat(id=uid, type=ChatType.PRIVATE)

    def replies_text(self):
        return "\n".join(self.sent + self.edits)

    def U(self):
        return unicodedata.normalize("NFKC", bot.unbold(self.replies_text())).upper()

    async def reply_text(self, text, **kw):
        self.sent.append(text)
        if kw.get("reply_markup"):
            self.kbs.append(kw["reply_markup"])
        return FakeSent(self, self.edits)

    async def reply_photo(self, photo=None, caption="", **kw):
        self.sent.append(caption or "")
        return FakeSent(self, self.edits)

    async def reply_video(self, video=None, caption="", **kw):
        self.sent.append(caption or "")
        return FakeSent(self, self.edits)

    async def reply_document(self, document=None, caption="", **kw):
        self.sent.append(caption or "")
        return FakeSent(self, self.edits)

    async def edit_text(self, text, **kw):
        self.edits.append(text)
        return FakeSent(self, self.edits)

    def cb_data(self):
        out = []
        for kb in self.kbs:
            for row in getattr(kb, "inline_keyboard", []):
                for b in row:
                    out.append(getattr(b, "callback_data", "") or b.text)
        return out


class FakeQuery:
    def __init__(self, data, uid=USER):
        self.data, self.from_user = data, User(id=uid, first_name="Tester", is_bot=False)
        self.message = FakeMsg("", uid=uid)
        self.answers = []

    async def answer(self, text=None, show_alert=False):
        self.answers.append(text)


class Ctx:
    def __init__(self):
        self.user_data, self.args, self.bot = {}, [], None


def upd(msg, uid=USER, n=1):
    u = Update(update_id=n, message=msg)
    u.message.from_user = User(id=uid, first_name="Tester", is_bot=False)
    return u


async def test_bot_flows():
    print("\n--- 4) 🤖 BOT FLOWS ---")
    dbm.set_credits(USER, 5)
    dbm.get_user(USER, "Tester")

    # kagaz menu me naye buttons
    ctx = Ctx()
    q = FakeQuery("kagaz_menu", uid=USER)
    await bot.on_cb(Update(update_id=100, callback_query=q), ctx)
    d = q.message.cb_data()
    ok("kagaz menu me GST button", "kagaz_gst" in d, d)
    ok("kagaz menu me PAN button", "kagaz_pan" in d, d)

    # GST flow
    q2 = FakeQuery("kagaz_gst", uid=USER)
    await bot.on_cb(Update(update_id=101, callback_query=q2), ctx)
    ok("GST prompt aaya", ctx.user_data.get("mode") == "kagaz_gst"
       and "15 character GSTIN" in q2.message.replies_text(), q2.message.replies_text()[:140])
    m = FakeMsg("19BOKPS7056D1ZI", uid=USER)
    before = dbm.get_credits(USER)
    await bot.on_text(upd(m, n=102), ctx)
    ok("GST card bana (legal name)", "TEST ENTERPRISES" in m.U(), m.replies_text()[:200])
    ok("GST card me status + source", "ACTIVE" in m.U() and "HUB" in m.U(), m.replies_text()[:220])
    ok("GST success par 1 credit kata", dbm.get_credits(USER) == before - 1,
       (before, dbm.get_credits(USER)))
    ok("mode saaf hua", ctx.user_data.get("mode") is None)

    # GST galat input → credit nahi kata
    ctx2 = Ctx()
    q3 = FakeQuery("kagaz_gst", uid=USER)
    await bot.on_cb(Update(update_id=103, callback_query=q3), ctx2)
    m2 = FakeMsg("12345", uid=USER)
    before2 = dbm.get_credits(USER)
    await bot.on_text(upd(m2, n=104), ctx2)
    ok("galat GSTIN par saaf fail + credit nahi", ("GST CHECK FAILED" in m2.U() or "GST CHECK NAHI HO PAYA" in m2.U())
       and dbm.get_credits(USER) == before2 and "GSTIN" in m2.U(), m2.replies_text()[:200])

    # PAN flow
    ctx3 = Ctx()
    q4 = FakeQuery("kagaz_pan", uid=USER)
    await bot.on_cb(Update(update_id=105, callback_query=q4), ctx3)
    m3 = FakeMsg("BOKPS7056D", uid=USER)
    await bot.on_text(upd(m3, n=106), ctx3)
    ok("PAN card bana (GST number mila)", "19BOKPS7056D1ZI" in m3.replies_text(), m3.replies_text()[:200])

    # ID finder with hub profiles
    ctx4 = Ctx()
    ctx4.user_data["mode"] = "idfind"
    m4 = FakeMsg("sumit_sharma2", uid=USER)
    await bot.on_text(upd(m4, n=107), ctx4)
    ok("ID finder me Instagram profile dikhi", "INSTAGRAM" in m4.U() and "SUM" in m4.U(), m4.replies_text()[:250])
    ok("ID finder me followers bhi", "12000" in m4.replies_text(), m4.replies_text()[:250])

    # /hubstatus
    ctx5 = Ctx()
    m5 = FakeMsg("", uid=OWNER)
    await bot.cmd_hubstatus(upd(m5, uid=OWNER, n=108), ctx5)
    ok("/hubstatus card aata hai", "API HUB" in m5.U(), m5.replies_text()[:160])
    ok("/hubstatus live test pass", "WORKING" in m5.U(), m5.replies_text()[:260])

    ctx6 = Ctx()
    m6 = FakeMsg("", uid=OWNER)
    # v49: CLIP MAKER tool hata diya gaya — clipstatus test bhi hata diya

    # hub off ho to kagaz GST mana kare
    os.environ["HUB_ENABLED"] = "off"
    try:
        ctx7 = Ctx()
        q7 = FakeQuery("kagaz_gst", uid=USER)
        await bot.on_cb(Update(update_id=110, callback_query=q7), ctx7)
        ok("hub off hone par GST saaf message deta hai", "API HUB" in q7.message.replies_text(),
           q7.message.replies_text()[:200])
    finally:
        os.environ.pop("HUB_ENABLED", None)


test_client()
test_tools_hub()
test_fallback()
asyncio.run(test_bot_flows())

print("\n" + "=" * 70)
print(f"V45 API HUB — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
for f in FAIL:
    print("  ❌", f)
print("=" * 70)
sys.exit(1 if FAIL else 0)
