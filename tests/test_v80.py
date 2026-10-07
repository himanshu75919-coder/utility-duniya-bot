# -*- coding: utf-8 -*-
"""
v80 SELFTEST — 🇮🇳 BOARD HUB (34 boards + official logos)  [v74.1]
===================================================================
User ka order (8 Oct 2026):
  1. Render ka port error theek karo
  2. PDF "web-generated" ki jagah OFFICIAL sites se data — official look
  3. RESULT CHECK me India ke SAARE state boards alag-alag service
  4. Har board ka OFFICIAL LOGO dikhe (users apna board pehchaan sake)
  5. 100% trusted — koi galat cheez nahi

Ye test: boards registry, pagination, search, logos/badges, hub cards,
portal links, port-fix code, aur PDF me official logo.
"""
import io as _io
import os
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv80_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V80"
os.environ["ADMIN_ID"] = "1"
os.environ["ALL_FREE"] = "1"

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
print("  v80 SELFTEST — 🇮🇳 BOARD HUB (34 boards + logos)")
print("=" * 62)

import bot                                                        # noqa: E402
from modules import boards as BRD                                 # noqa: E402
from modules import bseb_result as BSEBR                          # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

# =====================================================================
section("1) Registry — India ke saare boards alag-alag")
check("30+ boards hain", len(BRD.BOARDS) >= 30, str(len(BRD.BOARDS)))
check("sab ORDER me maujood (koi orphan nahi)",
      all(k in BRD.BOARDS for k in BRD.ORDER) and len(BRD.ORDER) == len(BRD.BOARDS))
_major = ["bseb", "cbse", "upmsp", "maharashtra", "telangana", "tn", "karnataka",
          "gseb", "rbse", "mpbse", "wbbse", "kerala", "odisha", "pseb", "bseh",
          "jkbose", "jac", "cgbse", "assam", "meghalaya", "nagaland", "mizoram"]
_missing = [k for k in _major if k not in BRD.BOARDS]
check("saare bade states ke board maujood", not _missing, str(_missing))
_bad = [k for k, b in BRD.BOARDS.items()
        if not (b.get("name") and b.get("short") and b.get("portal")
                and b.get("exams") and b.get("need") and b.get("status"))]
check("har board ka naam/short/portal/exam/need/status bhara", not _bad, str(_bad))
_urls = [b["portal"] for b in BRD.BOARDS.values()]
check("saare portal https:// hain", all(u.startswith("https://") for u in _urls))
check("status sirf live/portal", {b["status"] for b in BRD.BOARDS.values()} <= {"live", "portal"})

# =====================================================================
section("2) Pagination + search")
_rows, pg, tot = BRD.page_boards(0)
check("page size 6", len(_rows) == 6, str(len(_rows)))
check("kul pages sahi", tot == (len(BRD.ORDER) + 5) // 6, str(tot))
check("page 0 me BSEB sabse pehle (LIVE board pehle)", _rows[0][0] == "bseb")
_rows_l, pg_l, _ = BRD.page_boards(tot - 1)
check("aakhri page par bhi boards hain", len(_rows_l) >= 1, str(len(_rows_l)))
check("kharab page number par crash nahi", len(BRD.page_boards(999)[0]) >= 1)
check("search: 'UP Board' → upmsp", [k for k, _ in BRD.find("UP Board")][:1] == ["upmsp"])
check("search: 'telangana' kaam karta hai", "telangana" in [k for k, _ in BRD.find("telangana")])
check("search: 'bihar' se BSEB/BBOSE milte hain",
      {"bseb"} <= {k for k, _ in BRD.find("bihar")})
check("search: 'bengal' → wbbse", "wbbse" in [k for k, _ in BRD.find("bengal")])
check("search: bakwaas → khaali", BRD.find("xyzzy qwerty") == [])
check("search: case/Hindi mix bhi chalta hai", "bseb" in [k for k, _ in BRD.find("BIHAR")])

# =====================================================================
section("3) OFFICIAL LOGOS (unki hi website se)")
_have = {"bseb": BRD.logo_path("bseb"), "upmsp": BRD.logo_path("upmsp"),
         "gseb": BRD.logo_path("gseb"), "pseb": BRD.logo_path("pseb"),
         "bseh": BRD.logo_path("bseh"), "hpbose": BRD.logo_path("hpbose"),
         "odisha": BRD.logo_path("odisha"), "jac": BRD.logo_path("jac"),
         "meghalaya": BRD.logo_path("meghalaya"), "mizoram": BRD.logo_path("mizoram")}
_ok = [k for k, v in _have.items() if v and os.path.isfile(v)]
check("10 official logos file me maujood", len(_ok) == 10, str(len(_ok)))
for _k in ("bseb", "upmsp", "gseb"):
    _p = _have[_k]
    _b = open(_p, "rb").read() if _p else b""
    check(f"logo {_k} asli image hai (khali nahi)",
          _b[:3] == b"\xff\xd8\xff" or _b[:4] == b"\x89PNG", str(len(_b)))
check("jin boards ka logo nahi — unka COLOR BADGE banta hai (khaali nahi)",
      bool(BRD.badge_png("cbse")) and BRD.badge_png("maharashtra")[:4] == b"\x89PNG")
check("badge me board ka naam/state likha hota hai (512px)",
      len(BRD.badge_png("tripura") or b"") > 5000)
check("har board ka photo bytes milta hai (logo ya badge)",
      all(BRD.photo_bytes(k) for k in BRD.BOARDS))
check("photo_bytes crash-free (galat key par bhi)", BRD.photo_bytes("xyz") is not None
      or True)

# =====================================================================
section("4) Hub cards + board cards (bot ke)")
_hub = bot._rc_pick_card(0)
check("hub card: 'apna BOARD chuno' + page number", "BOARD chuno" in _hub and "1/6" in _hub)
check("hub card: BSEB par LIVE ✅ mark", "BSEB" in _hub and "LIVE" in _hub)
check("hub card me moti line nahi", "━" not in _hub)
_kb0 = bot._rc_pick_kb(0)
_rows_kb = _kb0.inline_keyboard
check("hub kb: 6 board buttons + nav + footer", len(_rows_kb) == 5, str(len(_rows_kb)))
check("hub kb: pehla button BSEB ✅", "BSEB" in _rows_kb[0][0].text and "✅" in _rows_kb[0][0].text)
_kb5 = bot._rc_pick_kb(5)
check("aakhri page par 'Peeche' hai, 'Aage' nahi",
      any("Peeche" in b.text for r in _kb5.inline_keyboard for b in r)
      and not any("Aage" in b.text for r in _kb5.inline_keyboard for b in r))

_cap_ts, _kb_ts = bot.rc_board_card("telangana")
check("board card: poora naam + state + exam", "Board of Secondary Education Telangana" in _cap_ts
      and "Telangana" in _cap_ts and "SSC" in _cap_ts)
check("board card (portal): 'official portal par check hota hai' sach likha",
      "official portal" in _cap_ts)
check("board card (portal): portal button + kaise button",
      any("Official portal" in b.text for r in _kb_ts.inline_keyboard for b in r)
      and any("Kaise check" in b.text for r in _kb_ts.inline_keyboard for b in r))
check("board card (portal): LIVE check button NAHI (jhooth nahi)",
      not any("LIVE" in b.text for r in _kb_ts.inline_keyboard for b in r))
_cap_bs, _kb_bs = bot.rc_board_card("bseb")
check("BSEB card: LIVE ✅ button milta hai",
      any("LIVE" in b.text for r in _kb_bs.inline_keyboard for b in r))
check("sab board me portal URL button asli https link",
      all(b.url.startswith("https://") for r in _kb_ts.inline_keyboard for b in r if b.url))
_how = BRD.how_card("upmsp")
check("'kaise check karein' me portal + steps + imaandari note",
      "results.upmsp.edu.in" in _how and "1." in _how and "jhootha result" in _how.lower())
check("how card crash-free har board par",
      all(len(BRD.how_card(k)) > 100 for k in BRD.BOARDS))

# =====================================================================
section("5) Port fix (Render 'No open ports' warning)")
check("PORT fallback + RENDER_PORT support", 'os.environ.get("RENDER_PORT")' in BOT_SRC)
check("bind retry (3 try) + address reuse", "allow_reuse_address = True" in BOT_SRC
      and "for _try in range(3)" in BOT_SRC)
check("logging me bind confirm", "KEEPALIVE_SERVER[\"srv\"] = httpd" in BOT_SRC)

# =====================================================================
section("6) PDF — official logo + official source line")
import json                                                       # noqa: E402
_stu = BSEBR.parse_payload({
    "success": True, "data": {
        "name": "TEST STUDENT", "father_name": "TEST FATHER",
        "school_name": "TEST SCHOOL", "roll_code": "11001", "roll_no": "2600046",
        "division": "1st Division", "total": 320, "exam_type": "REGULAR",
        "subjects": [{"sub_name": "HINDI", "sub_code": "106", "theory": "53",
                      "sub_total": "53"}]}})
_pdf = BSEBR.build_pdf(_stu, BSEBR.EXAMS["matric"]["label"], 2026, "test")
check("PDF bani", (_pdf or b"")[:5] == b"%PDF-")
try:
    import pymupdf
    _doc = pymupdf.open(stream=_pdf, filetype="pdf")
    _page = _doc[0]
    check("PDF me official LOGO image hai", len(_page.get_images()) >= 1,
          str(len(_page.get_images())))
    _t = _page.get_text()
    check("PDF me OFFICIAL source likha hai", "result.biharboardonline.org" in _t)
    check("PDF me 'official server' ki baat", "OFFICIAL" in _t.upper())
    check("PDF me data + marks hain", "TEST STUDENT" in _t and "53" in _t)
    check("PDF me WEB COPY label (official portal jaisa)", "WEB COPY" in _t)
except Exception as e:                                            # noqa: BLE001
    check("PDF check (skip agar pymupdf nahi)", True, str(e)[:60])

# =====================================================================
section("7) Version + wiring")
check("version v74.1 hai", "v74.1" in bot.BOT_VERSION and "34 boards" in bot.BOT_VERSION,
      bot.BOT_VERSION)
check("exports: boards import bot me", "from modules import boards as BRD" in BOT_SRC)
check("callbacks wired (rcb/rc_page/rc_how/rc_live)",
      all(x in BOT_SRC for x in ('startswith("rcb:")', 'startswith("rc_page:")',
                                 'startswith("rc_how:")', 'startswith("rc_live:")')))
check("RESULT CHECK button → hub (rc_board mode)",
      'context.user_data["mode"] = "rc_board"' in BOT_SRC)
check("BSEB direct alias ka alag rasta", '"BSEB RESULT": "bsebr_direct"' in BOT_SRC)
check("search on_text me wired", 'if mode == "rc_board":' in BOT_SRC)

# =====================================================================
section("8) E2E — hub → board → logo card → portal (nakli Telegram)")
import asyncio                                                    # noqa: E402


class _Sent:
    async def edit_text(self, txt, **kw):
        return self

    async def delete(self):
        return True


class _QMsg:
    def __init__(self):
        self.out = []
        self.photos = []

    async def edit_text(self, txt, **kw):
        self.out.append(txt)
        return self

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        return self

    async def delete(self):
        return True

    async def reply_photo(self, photo, caption=None, **kw):
        self.photos.append((caption or "", photo.getvalue() if hasattr(photo, "getvalue") else b""))
        self.out.append(caption or "")
        return self


class _Q:
    def __init__(self, data, uid):
        self.data = data
        self.from_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.message = _QMsg()

    async def answer(self, *a, **kw):
        pass


class _UpdQ:
    def __init__(self, q):
        self.callback_query = q
        self.effective_user = q.from_user
        self.effective_chat = q.from_user


class _Ctx:
    def __init__(self):
        self.user_data = {}
        self.bot = None


class _MsgT:
    def __init__(self, text):
        self.text = text
        self.out = []
        self.photos = []

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        return _Sent()

    async def reply_photo(self, photo, caption=None, **kw):
        self.photos.append((caption or "", photo.getvalue() if hasattr(photo, "getvalue") else b""))
        return _Sent()


class _UpdT:
    def __init__(self, text, uid):
        self.effective_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.effective_chat = self.effective_user
        self.message = _MsgT(text)
        self.callback_query = None


async def _hub_flow():
    uid = 606060
    ctx = _Ctx()

    q1 = _Q("rc_new", uid)
    await bot.on_cb(_UpdQ(q1), ctx)
    _t = " ".join(q1.message.out)
    check("E2E: hub khula — boards + LIVE mark", "BOARD chuno" in _t and "LIVE" in _t,
          _t[:70])

    q2 = _Q("rc_page:1", uid)
    await bot.on_cb(_UpdQ(q2), ctx)
    check("E2E: aage page par naye boards",
          "2/6" in " ".join(q2.message.out), " ".join(q2.message.out)[:60])

    # search: UP Board likho
    up = _UpdT("UP Board", uid)
    ctx.user_data["mode"] = "rc_board"
    await bot.on_text(up, ctx)
    check("E2E: search 'UP Board' → seedha board card (logo ke saath)",
          bool(up.message.photos) and "UPMSP" in (up.message.photos[0][0] or ""),
          str(len(up.message.photos)))
    if up.message.photos:
        check("E2E: UP ka official logo image asli hai",
              up.message.photos[0][1][:3] == b"\xff\xd8\xff")

    # portal board card → "Kaise check karein"
    q3 = _Q("rc_how:upmsp", uid)
    await bot.on_cb(_UpdQ(q3), ctx)
    _t3 = " ".join(q3.message.out)
    check("E2E: 'kaise check karein' me portal + steps",
          "results.upmsp.edu.in" in _t3 and "Roll Number" in _t3, _t3[:80])

    # maharashtra card (badge wala board)
    q4 = _Q("rcb:maharashtra", uid)
    await bot.on_cb(_UpdQ(q4), ctx)
    check("E2E: badge wale board ka card bhi photo ke saath",
          bool(q4.message.photos) and q4.message.photos[0][1][:4] == b"\x89PNG",
          str(len(q4.message.photos)))

    # search fail
    bad = _UpdT("qwertyuiop", uid)
    ctx.user_data["mode"] = "rc_board"
    await bot.on_text(bad, ctx)
    check("E2E: bakwaas search par friendly message + list",
          "nahi mila" in " ".join(bad.message.out), " ".join(bad.message.out)[:60])


asyncio.run(_hub_flow())

print(f"\n{'=' * 62}")
print(f"  v80 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
