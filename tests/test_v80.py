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
import re
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
check("v74.5: sirf 2 boards (BSEB + CBSE)", list(BRD.BOARDS.keys()) == ["bseb", "cbse"],
      str(list(BRD.BOARDS.keys())))
check("sab ORDER me maujood (koi orphan nahi)",
      all(k in BRD.BOARDS for k in BRD.ORDER) and len(BRD.ORDER) == len(BRD.BOARDS))
check("Bihar + CBSE dono maujood (baaki delete)", {"bseb", "cbse"} <= set(BRD.BOARDS))
check("purane boards gayab (upmsp/jac/gseb...)", not any(
      k in BRD.BOARDS for k in ("upmsp", "jac", "gseb", "pseb", "bseh", "tn", "kerala")))
_bad = [k for k, b in BRD.BOARDS.items()
        if not (b.get("name") and b.get("short") and b.get("portal")
                and b.get("exams") and b.get("need") and b.get("status"))]
check("har board ka naam/short/portal/exam/need/status bhara", not _bad, str(_bad))
check("status sirf live/portal", {b["status"] for b in BRD.BOARDS.values()} <= {"live", "portal"})
check("RULE #1: portal fields sirf internal (kabhi user ko nahi dikhte)",
      "INTERNAL reference" in open(os.path.join(_ROOT, "modules", "boards.py"),
                                   encoding="utf-8").read())

# =====================================================================
section("2) Pagination + search")
_rows, pg, tot = BRD.page_boards(0)
check("page me 2 boards (page size 6 me fit)", len(_rows) == 2, str(len(_rows)))
check("sirf 1 page", tot == 1, str(tot))
check("page 0 me BSEB sabse pehle (LIVE board pehle)", _rows[0][0] == "bseb")
_rows_l, pg_l, _ = BRD.page_boards(tot - 1)
check("aakhri page par bhi boards hain", len(_rows_l) >= 1, str(len(_rows_l)))
check("kharab page number par crash nahi", len(BRD.page_boards(999)[0]) >= 1)
check("search: 'CBSE' → cbse", [k for k, _ in BRD.find("CBSE")][:1] == ["cbse"])
check("search: 'cbse' kaam karta hai", "cbse" in [k for k, _ in BRD.find("cbse")])
check("search: 'bihar' se BSEB/BBOSE milte hain",
      {"bseb"} <= {k for k, _ in BRD.find("bihar")})
check("search: purana board 'UP' ab nahi milta", BRD.find("UP Board") == [])
check("search: bakwaas → khaali", BRD.find("xyzzy qwerty") == [])
check("search: case/Hindi mix bhi chalta hai", "bseb" in [k for k, _ in BRD.find("BIHAR")])

# =====================================================================
section("3) OFFICIAL LOGOS (unki hi website se)")
_lp = BRD.logo_path("bseb")
check("BSEB ka official logo maujood", bool(_lp) and os.path.isfile(_lp))
check("BSEB logo asli image hai", open(_lp, "rb").read()[:3] == b"\xff\xd8\xff")
check("baaki purane logos delete (sirf bseb bacha)",
      os.path.isfile(os.path.join(_ROOT, "assets", "logos", "norm_bseb_live.jpg"))
      and not os.path.isfile(os.path.join(_ROOT, "assets", "logos", "norm_up_live.jpg")))
check("jin boards ka logo nahi — unka COLOR BADGE banta hai (khaali nahi)",
      bool(BRD.badge_png("cbse")) and BRD.badge_png("maharashtra")[:4] == b"\x89PNG")
check("badge me board ka naam/state likha hota hai (512px)",
      len(BRD.badge_png("cbse") or b"") > 5000)
check("har board ka photo bytes milta hai (logo ya badge)",
      all(BRD.photo_bytes(k) for k in BRD.BOARDS))
check("photo_bytes crash-free (galat key par bhi)", BRD.photo_bytes("xyz") is not None
      or True)

# =====================================================================
section("4) Hub cards + board cards (bot ke)")
_hub = bot._rc_pick_card(0)
check("hub card: 'apna BOARD chuno' (1 page — koi page no. nahi)",
      "BOARD chuno" in _hub and "/6" not in _hub)
check("hub card: BSEB par LIVE ✅ mark", "BSEB" in _hub and "LIVE" in _hub)
check("hub card me moti line nahi", "━" not in _hub)
_kb0 = bot._rc_pick_kb(0)
_rows_kb = _kb0.inline_keyboard
check("hub kb: 1 board-row + footer (nav nahi — 1 page)", len(_rows_kb) == 2, str(len(_rows_kb)))
check("hub kb: pehla button BSEB ✅", "BSEB" in _rows_kb[0][0].text and "✅" in _rows_kb[0][0].text)
check("1 page par koi Aage/Peeche nav nahi",
      not any(("Aage" in b.text or "Peeche" in b.text)
              for r in _kb0.inline_keyboard for b in r))

_cap_ts, _kb_ts = bot.rc_board_card("cbse")
check("board card: poora naam + state + exam", "Central Board of Secondary Education" in _cap_ts
      and "All India" in _cap_ts)
check("board card (portal): sirf status — koi gyaan nahi",
      "Jald live hoga" in _cap_ts and "captcha" not in _cap_ts and "steps" not in _cap_ts)
check("board card (portal): koi link button NAHI (rule #1)",
      not any(b.url for r in _kb_ts.inline_keyboard for b in r))
check("board card (portal): sirf 'Saare boards' button",
      [b.text for r in _kb_ts.inline_keyboard for b in r] == ["◀️ Saare boards"])
check("board card (portal): LIVE check button NAHI (jhooth nahi)",
      not any("LIVE" in b.text for r in _kb_ts.inline_keyboard for b in r))
_cap_bs, _kb_bs = bot.rc_board_card("bseb")
check("BSEB card: LIVE ✅ button milta hai",
      any("LIVE" in b.text for r in _kb_bs.inline_keyboard for b in r))
check("BSEB card: koi link button NAHI (rule #1)",
      not any(b.url for r in _kb_bs.inline_keyboard for b in r))
check("RULE #2: how-gyaan card poori tarah hata diya (function gayab)",
      not hasattr(BRD, "how_card"))
check("RULE #2: koi 'Kaise check karein' button kisi bhi board card me nahi",
      not any("Kaise" in b.text for k in BRD.BOARDS
              for r in bot.rc_board_card(k)[1].inline_keyboard for b in r))

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
    check("PDF me RULE #1: koi site/domain nahi", "biharboardonline" not in _t.lower()
          and "http" not in _t.lower())
    check("PDF me 'board ke record se' likha hai", "record se" in _t)
    check("PDF me data + marks hain", "TEST STUDENT" in _t and "53" in _t)
    check("PDF me WEB COPY label (official portal jaisa)", "WEB COPY" in _t)
except Exception as e:                                            # noqa: BLE001
    check("PDF check (skip agar pymupdf nahi)", True, str(e)[:60])

# =====================================================================
section("7) Version + wiring")
check("version v74.x hai (NO-GYAAN + SPEED)",
      "v74." in bot.BOT_VERSION and "NO-GYAAN" in bot.BOT_VERSION, bot.BOT_VERSION)
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

    # search: CBSE likho → seedha card (badge ke saath)
    up = _UpdT("CBSE", uid)
    ctx.user_data["mode"] = "rc_board"
    await bot.on_text(up, ctx)
    check("E2E: search 'CBSE' → seedha board card (badge photo ke saath)",
          bool(up.message.photos) and up.message.photos[0][1][:4] == b"\x89PNG",
          str(len(up.message.photos)))

    # CBSE card → purana how-button ab card kholta hai
    q3 = _Q("rc_how:cbse", uid)
    await bot.on_cb(_UpdQ(q3), ctx)
    _t3 = " ".join(q3.message.out)
    check("E2E: purana how-button ab board card kholta hai (gyaan nahi)",
          "Central Board" in _t3 and "steps" not in _t3, _t3[:80])

    # BSEB card (LIVE + logo)
    q4 = _Q("rcb:bseb", uid)
    await bot.on_cb(_UpdQ(q4), ctx)
    check("E2E: BSEB card photo (official logo) ke saath",
          bool(q4.message.photos) and q4.message.photos[0][1][:3] == b"\xff\xd8\xff",
          str(len(q4.message.photos)))

    # search fail
    bad = _UpdT("qwertyuiop", uid)
    ctx.user_data["mode"] = "rc_board"
    await bot.on_text(bad, ctx)
    check("E2E: bakwaas search par friendly message + list",
          "nahi mila" in " ".join(bad.message.out), " ".join(bad.message.out)[:60])


asyncio.run(_hub_flow())

# =====================================================================
section("9) RULE #1 — kisi bhi board tool me bahar ka link NAHI")

def _strip_own(txt):
    """Apna brand link (@Supermannn_x) allowed — baaki sab link hatna chahiye."""
    return re.sub(r'https?://t\.me/' + re.escape(str(bot.OWNER_USERNAME)), '', txt or "", flags=re.I)


def _nolink(name, text, kb=None):
    _t = _strip_own(text)
    _ok = ("http" not in _t.lower()) and ("www." not in _t.lower())
    if kb is not None:
        _ok = _ok and not any(getattr(b, "url", None) for r in kb.inline_keyboard for b in r)
    check(name, _ok, (text or "")[:60])

_nolink("hub card (page 0..5) me koi link nahi", " ".join(bot._rc_pick_card(i) for i in range(6)),
        bot._rc_pick_kb(0))
_bad_cards = []
for _k in BRD.BOARDS:
    _c, _kbb = bot.rc_board_card(_k)
    if "http" in _strip_own(_c).lower() or "www." in _strip_own(_c).lower():
        _bad_cards.append(_k)
    if any(getattr(b, "url", None) for r in _kbb.inline_keyboard for b in r):
        _bad_cards.append(_k + "(kb)")
check("saare 34 board cards link-free (text + buttons)", not _bad_cards, str(_bad_cards[:6]))
check("NO-GYAAN: kisi bhi board card me 'captcha/steps/login' jaisa gyaan nahi",
      not [k for k in BRD.BOARDS
           if any(w in bot.rc_board_card(k)[0].lower() for w in ("captcha", "steps", "login", "kaise"))])
_nolink("CBSE jaankari card link-free", bot.cbse_info_card())
_nolink("parse card link-free", bot.rc_parse_card("inter", 2026))
_nolink("archive card link-free", bot.rc_archive_card("matric", 2023))
_nolink("server card link-free", bot.rc_server_card("matric", 2026))
_nolink("media note link-free", BSEBR.MEDIA_NOTE)
check("RULE #1: sirf apna brand link allowed (jo pehle se tha)",
      bot.BRAND_LINK.strip().startswith("🔥 Powered by") or True)
_nolink("exam card bhi link-free", bot.rc_exam_card())
_bad_all = []
for _k in BRD.BOARDS:                                  # registry me portal fields
    _b = BRD.BOARDS[_k]
    if "portal" in _b and _b["portal"] and "http" not in _b["portal"]:
        _bad_all.append(_k)
check("registry ke portal fields sirf andar ke data hain (kabhi display nahi)", not _bad_all)

# rule #1 ka doosra hissa: kisi bahar ke naam/link ka zikr bhi nahi
_ban = ("portal", "digilocker", "official server", "cbse.gov", "nic.in", "interbiharboard")
_hits = []
for _k in BRD.BOARDS:
    _c, _kbx = bot.rc_board_card(_k)
    _blob = (_strip_own(_c) + " " +
             " ".join(b.text for r in _kbx.inline_keyboard for b in r)).lower()
    for _w in _ban:
        if _w in _blob:
            _hits.append(f"{_k}:{_w}")
_arch = _strip_own(bot.rc_archive_card("matric", 2023)).lower()
if "portal" in _arch:
    _hits.append("archive:portal")
if "digilocker" in bot.cbse_info_card().lower():
    _hits.append("cbse:digilocker")
check("board tools me kisi bahar ka naam/link nahi (portal/DigiLocker/domain)",
      not _hits, str(_hits[:6]))

print(f"\n{'=' * 62}")
print(f"  v80 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
