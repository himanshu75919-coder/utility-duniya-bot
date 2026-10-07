# -*- coding: utf-8 -*-
"""
v86 SELFTEST — v76 "FORTRESS + EARN STUDIO"
===========================================
Aaj ke 3 kaam ke test:

  A. 🪣 BOUNDED CACHE — cache jo KABHI unlimited nahi badhta
     v76 se pehle: osint_hub / username_hunter / vehicle_tool ke cache aam
     `dict` the — kabhi saaf nahi hote the. Har nayi query = pakki entry.
     Hafton me lakhon entry -> Render free (512 MB) par OOM KILL.
     Ab: maxsize + TTL + LRU + global registry (watchdog ek saath saaf kare).

  B. 🧹 JANITOR — khud-safai
     1) /tmp me chhoote hue udl_* folder (crash ke baad) hatate hain
     2) atke hue ffmpeg/yt-dlp process maarte hain (RAM+CPU bachao)
     3) expire cache entry nikaalte hain
     4) disk 88% se upar -> turant aggressive safai

  C. 💰 EARN STUDIO — 5 naye premium kamai wale tools
     Rent Receipt · Udhaar Khata · Offer Poster · Quotation · Profit Card
     Har tool: PNG + PDF, Hindi+English, aur galat input par bhi CRASH NAHI.

  D. 🔗 WIRING — naye tools BIZ_MENU / PREMIUM / STEPS / keyboard me hain,
     aur purane tools ka kuch nahi bigda (regression check).
"""
import io
import os
import re
import sys
import tempfile
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv86_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V86"
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


# ======================================================================
section("A) 🪣 BOUNDED CACHE — kabhi unlimited nahi badhta")
# ======================================================================
from modules.core.bounded import (BoundedCache, cache_report,      # noqa: E402
                                  clear_all_caches, prune_all_caches,
                                  registry)

c = BoundedCache("v86_test", maxsize=5, default_ttl=60)
for i in range(200):
    c.put(f"key{i}", i)
check("200 entry daalne ke baad bhi size 5 se upar nahi gaya",
      len(c) == 5, f"size={len(c)}")
check("nayi entry (key199) mili — LRU ne purani hatayi",
      c.get("key199") == 199, f"got={c.get('key199')}")
check("purani entry (key0) ud gayi", c.get("key0") is None)
check("evictions count hua", c.stats()["evictions"] > 0,
      f"evict={c.stats()['evictions']}")

# TTL
c2 = BoundedCache("v86_ttl", maxsize=10, default_ttl=1)
c2.put("soon", "value", ttl=1)
check("TTL se pehle value milti hai", c2.get("soon") == "value")
import time as _t                                                  # noqa: E402
_t.sleep(1.3)
check("TTL ke baad value expire (None)", c2.get("soon") is None,
      f"got={c2.get('soon')}")

# registry + clear
c3 = BoundedCache("v86_reg", maxsize=50, default_ttl=600)
c3.put("a", 1)
names = [x["name"] for x in cache_report()["caches"]]
check("registry me saare cache dikhte hain",
      "v86_reg" in names and "v86_test" in names, f"names={names[:6]}")
check("prune_all_caches chalta hai (int return)",
      isinstance(prune_all_caches(), int))
n = clear_all_caches()
check("clear_all_caches saare cache saaf karta hai", n >= 3, f"cleared={n}")
check("clear ke baad cache khali", len(c3) == 0, f"size={len(c3)}")

# thread safety (crash na ho)
import threading                                                   # noqa: E402
c4 = BoundedCache("v86_thread", maxsize=100, default_ttl=60)


def _worker(w):
    for i in range(300):
        c4.put(f"{w}-{i}", i)
        c4.get(f"{w}-{i}")


ths = [threading.Thread(target=_worker, args=(w,)) for w in range(6)]
[t.start() for t in ths]
[t.join() for t in ths]
check("6 thread ek saath — koi crash nahi, size limit me",
      len(c4) <= 100, f"size={len(c4)}")


# ======================================================================
section("B) 🧹 JANITOR — khud-safai (temp · process · cache · disk)")
# ======================================================================
from modules.core import janitor as J                              # noqa: E402

# 1) purana temp folder hatana
old_dir = tempfile.mkdtemp(prefix="udl_v86_old_")
with open(os.path.join(old_dir, "video.mp4"), "wb") as fh:
    fh.write(b"x" * 4096)
os.utime(old_dir, (_t.time() - 7200, _t.time() - 7200))     # 2 ghante purana
fresh_dir = tempfile.mkdtemp(prefix="udl_v86_fresh_")        # abhi bana hai
res = J.sweep_now()
check("purana udl_ folder hat gaya", not os.path.exists(old_dir))
check("JANITOR ne folder ginati badhayi", J.JAN["tmp_dirs"] >= 1,
      f"dirs={J.JAN['tmp_dirs']}")
check("naya (fresh) folder NAHI hata — abhi use ho raha hai",
      os.path.exists(fresh_dir))
check("bytes_freed record hua", J.JAN["bytes_freed"] >= 4096,
      f"freed={J.JAN['bytes_freed']}")

# 2) doosre program ki cheez nahi chhooni chahiye
safe_file = os.path.join(tempfile.gettempdir(), "someone_else_v86.txt")
with open(safe_file, "w") as fh:
    fh.write("important")
os.utime(safe_file, (_t.time() - 7200, _t.time() - 7200))
J.sweep_tmp(max_age_min=1)
check("doosre program ki file ko haath nahi lagaya (sirf udl_/qsc_/ud_)",
      os.path.exists(safe_file))
try:
    os.remove(safe_file)
except Exception:
    pass

# 3) cache prune + stats
J.sweep_now()
st = J.janitor_stats()
check("janitor_stats dict deta hai", isinstance(st, dict) and "runs" in st)
check("janitor runs badha", st["runs"] >= 2, f"runs={st['runs']}")
check("janitor_block() HTML text deta hai",
      isinstance(J.janitor_block(), str))
check("disk_pct 0 se 100 ke beech", 0.0 <= st["disk_pct"] <= 100.0,
      f"disk={st['disk_pct']}")


# ======================================================================
section("C) 💰 EARN STUDIO — 5 naye premium kamai wale tools")
# ======================================================================
from modules import earn_studio as ES                              # noqa: E402
from PIL import Image                                              # noqa: E402

GOOD = {
    "biz_rent": dict(owner="Ramesh Kumar", tenant="Himanshu Kumar",
                     address="Makan 42, Bihta, Patna", amount=8500,
                     month="September 2026", mode="UPI", pan="ABCPK1234K",
                     start_no=11),
    "biz_khata": dict(shop="Sharma Kirana", customer="Mohan Yadav",
                      phone="9876543210",
                      entries="01-09, aata, 500, 0 | 10-09, jama, 0, 300"),
    "biz_poster": dict(shop="Sharma Electronics", offer="50% OFF",
                       theme="diwali", phone="9876543210",
                       address="Main Road, Patna", dates="20 Oct se 5 Nov",
                       items="LED TV, Mixer, Cooler"),
    "biz_quote": dict(shop="Himanshu Interiors", to="Ramesh Kumar",
                      items=[{"name": "Wardrobe", "qty": 2, "rate": 45000},
                             {"name": "Kitchen", "qty": 1, "rate": 78000}],
                      gst=18, valid="30 din", upi="9876543210@ybl"),
    "biz_profit": dict(shop="Sharma Kirana", month="September 2026",
                       sale=420000, cost=330000, expense=58000,
                       expense_items="Kiraya 12000, Bijli 3500, Staff 30000"),
}

for key, data in GOOD.items():
    r = ES.earn_build(key, data)
    ok = bool(r.get("ok"))
    check(f"{key}: image bani", ok, str(r.get("error"))[:80])
    if not ok:
        continue
    png = r.get("png") or b""
    check(f"{key}: PNG bytes mile (>10 KB)", len(png) > 10000,
          f"{len(png)}B")
    try:
        im = Image.open(io.BytesIO(png))
        check(f"{key}: image khulti hai {im.size}", im.size[0] > 500)
    except Exception as e:
        check(f"{key}: image khulti hai", False, str(e)[:80])
    pdf = ES.earn_pdf(r)
    check(f"{key}: PDF bhi bana (print ke liye)", bool(pdf), "pdf=None")

# ---- Rent receipt khaas baatein ----
r = ES.earn_build("biz_rent", GOOD["biz_rent"])
check("rent receipt: ek page par 3 receipt", r.get("count") == 3,
      f"count={r.get('count')}")
check("rent receipt: stamp lagane ki salah deta hai",
      "stamp" in str(r.get("notice", "")).lower())

# ---- Khata ka hisaab ----
r = ES.earn_build("biz_khata", dict(shop="S", customer="M",
                                    entries="01-09, aata, 500, 0 | 10-09, jama, 0, 300"))
check("khata: hisaab sahi (500 udhaar - 300 jama = 200 baaki)",
      abs(r.get("amount", 0) - 200.0) < 0.01, f"amount={r.get('amount')}")

# ---- Quotation ka hisaab ----
r = ES.earn_build("biz_quote", dict(shop="X", to="Y",
                                    items=[{"name": "A", "qty": 2, "rate": 1000}],
                                    gst=18))
# 2000 + 18% = 2360
check("quotation: 2000 + 18% GST = 2360", abs(r.get("amount", 0) - 2360.0) < 0.01,
      f"amount={r.get('amount')}")

# ---- Profit card ka hisaab ----
r = ES.earn_build("biz_profit", dict(shop="X", sale=100000, cost=60000,
                                     expense=20000))
check("profit: 100000 - 60000 - 20000 = 20000",
      abs(r.get("amount", 0) - 20000.0) < 0.01, f"amount={r.get('amount')}")
r_loss = ES.earn_build("biz_profit", dict(shop="X", sale=50000, cost=60000,
                                          expense=10000))
check("profit: ghata wala case bhi chalta hai (negative)",
      bool(r_loss.get("ok")) and r_loss.get("amount", 0) < 0,
      f"amount={r_loss.get('amount')}")

# ---- Poster themes ----
for theme in ("diwali", "holi", "sale", "newyear", "eid", "republic",
              "independence", "opening", "custom", "kuch-bhi-galat"):
    rr = ES.poster_image(dict(shop="Test", offer="50% OFF", theme=theme,
                              phone="9876543210"))
    check(f"poster theme '{theme}' chalta hai", bool(rr.get("ok")),
          str(rr.get("error"))[:60])

# ---- CRASH TEST: har tarah ka kharaab input ----
BAD = ["", "   ", "|", "|||", "abc", "0", "-5", "99999999999999",
       "😀😀😀", "a" * 5000, None, 12345, [], {}]
crashes = 0
for key in GOOD:
    for bad in BAD:
        try:
            out = ES.earn_build(key, bad if isinstance(bad, dict) else
                                {"shop": bad, "amount": bad, "sale": bad,
                                 "entries": bad, "items": bad})
            if not isinstance(out, dict):
                crashes += 1
                print(f"     ⚠️ {key}: dict nahi mila -> {type(out)}")
        except Exception as e:
            crashes += 1
            print(f"     ⚠️ CRASH {key} input={str(bad)[:20]!r}: "
                  f"{type(e).__name__}: {e}")
check("❌ ZERO crash — 65 kharaab input ke bawajood (sab dict return)",
      crashes == 0, f"crashes={crashes}")


# ======================================================================
section("D) 🔗 WIRING — bot.py me sab juda hai (regression ke saath)")
# ======================================================================
import bot                                                         # noqa: E402

NEW = ["biz_rent", "biz_khata", "biz_poster", "biz_quote", "biz_profit"]
for k in NEW:
    check(f"{k}: BIZ_MENU me hai (routing isi se hoti hai)", k in bot.BIZ_MENU)
    check(f"{k}: PREMIUM_TOOLS me hai (kamai ka model)", k in bot.PREMIUM_TOOLS)
    check(f"{k}: TOOL_RATE_LIMITS me hai (rate-limit to crash na ho)",
          k in bot.TOOL_RATE_LIMITS)
    check(f"{k}: PREMIUM_TOOL_NAMES me hai", k in bot.PREMIUM_TOOL_NAMES)
    check(f"{k}: BIZ_STEPS (step-by-step wizard) me hai",
          len(bot.biz_steps(k)) >= 3, f"steps={len(bot.biz_steps(k))}")
    check(f"{k}: PROMPT_DATA me hai (tool ka prompt)", k in bot.PROMPT_DATA)

check("EARN_STUDIO_MENU me 5 tools", len(bot.EARN_STUDIO_MENU) == 5)
check("EARN_STUDIO_ORDER sahi kram me", bot.EARN_STUDIO_ORDER[0] == "biz_rent")
check("'EARN STUDIO' keyword → earnstudio action",
      bot.BTN_MODE_MAP.get("EARN STUDIO") == "earnstudio")
for kw, want in (("RENT RECEIPT", "biz_rent"), ("KIRAYA RASID", "biz_rent"),
                 ("UDHAAR KHATA", "biz_khata"), ("OFFER POSTER", "biz_poster"),
                 ("QUOTATION", "biz_quote"), ("PROFIT CARD", "biz_profit"),
                 ("KHATA", "biz_khata"), ("ESTIMATE", "biz_quote")):
    check(f"keyword '{kw}' → {want}", bot.BTN_MODE_MAP.get(kw) == want,
          f"got={bot.BTN_MODE_MAP.get(kw)}")

# menu keyboards
try:
    kb = bot.earn_menu_kb()
    flat = [b.callback_data for row in kb.inline_keyboard for b in row]
    check("earn_menu_kb: 5 tool buttons hain",
          sum(1 for x in flat if x.startswith("biz:biz_")) == 5, f"{flat}")
    check("earn_menu_kb: callback data 64 byte se chhota (Telegram limit)",
          all(len(x.encode()) <= 64 for x in flat))
except Exception as e:
    check("earn_menu_kb banta hai", False, str(e)[:90])

try:
    kb2 = bot.biz_menu_kb()
    flat2 = [b.callback_data for row in kb2.inline_keyboard for b in row]
    check("biz_menu_kb: EARN STUDIO ka shortcut button hai",
          "earnstudio" in flat2)
    check("biz_menu_kb: 12 purane tool abhi bhi hain (regression)",
          sum(1 for x in flat2 if x.startswith("biz:biz_")) == 12,
          f"n={sum(1 for x in flat2 if x.startswith('biz:biz_'))}")
    check("biz_menu_kb: callback 64 byte limit me",
          all(len(x.encode()) <= 64 for x in flat2))
except Exception as e:
    check("biz_menu_kb banta hai", False, str(e)[:90])

# main keyboard me EARN STUDIO button
try:
    kb_rows = bot.KB_BTNS
    has_earn = any(any("EARN STUDIO" in bot.unbold(t).upper() for t in row)
                   for row in kb_rows)
    check("main keyboard me 💰 EARN STUDIO button hai", has_earn)
except Exception as e:
    check("main keyboard check", False, str(e)[:90])

# ---- ek-line input se poora flow (parse -> build) ----
LINES = {
    "biz_rent": "Ramesh Kumar | Himanshu Kumar | Makan 42, Patna | 8500 | September 2026",
    "biz_khata": "Sharma Kirana | Mohan Yadav | 9876543210 | 01-09, aata, 500, 0",
    "biz_poster": "Diwali | Sharma Electronics | 50% OFF | 9876543210",
    "biz_quote": "Himanshu Interiors | Ramesh | Wardrobe 2x45000 | 18 | 30 din",
    "biz_profit": "Sharma Kirana | September 2026 | 420000 | 330000 | 58000",
}
for k, line in LINES.items():
    try:
        d = bot.biz_parse(k, line, "Owner")
        rr = bot.biz_build(k, d)
        check(f"ek-line flow {k}: image bani", bool(rr.get("ok")),
              str(rr.get("error"))[:70])
    except Exception as e:
        check(f"ek-line flow {k}", False, f"{type(e).__name__}: {e}")

# poster theme mapping (user "Diwali" likhe ya "1")
check("theme 'Diwali' → diwali", bot._poster_theme("Diwali") == "diwali")
check("theme '1' → diwali", bot._poster_theme("1") == "diwali")
check("theme 'holi' → holi", bot._poster_theme("holi") == "holi")
check("theme galat ho to default 'sale' (crash nahi)",
      bot._poster_theme("kuch bhi") == "sale")

# ---- REGRESSION: purane tools abhi bhi hain ----
OLD = ["biz_invoice", "biz_resume", "biz_biodata", "biz_certificate",
       "biz_idcard", "biz_vcard", "biz_letter", "biz_upi", "biz_labels",
       "biz_emi", "biz_salary", "biz_menucard"]
missing = [k for k in OLD if k not in bot.BIZ_MENU]
check("sab 12 PURANE Business Studio tool abhi bhi hain (koi nahi hata)",
      not missing, f"missing={missing}")
check("purane tools ke steps wahi rahe (regression)",
      len(bot.biz_steps("biz_invoice")) == 5,
      f"steps={len(bot.biz_steps('biz_invoice'))}")


# ======================================================================
section("E) 🛡️ CRASH-SHIELD — v60 wali cheezein abhi bhi ON hain")
# ======================================================================
check("arm_all_handlers() maujood hai", callable(getattr(bot, "arm_all_handlers", None)))
check("on_error handler maujood hai", callable(getattr(bot, "on_error", None)))
check("start_janitor import hua hai", callable(getattr(bot, "start_janitor", None)))
check("_clear_caches_mem ab module cache bhi saaf karta hai",
      callable(getattr(bot, "_clear_caches_mem", None)))
try:
    bot._clear_caches_mem()
    check("_clear_caches_mem bina crash chal gaya", True)
except Exception as e:
    check("_clear_caches_mem bina crash chal gaya", False, str(e)[:80])

# bounded caches registered hone chahiye (module import ke baad)
# NOTE: osint_hub lazy-import hota hai — isliye pehle import karte hain
try:
    import modules.osint_hub as _oh                               # noqa: F401
except Exception:
    pass
reg_names = [getattr(x, "name", "") for x in registry()]
for want in ("osint_hub", "username_hunter", "vehicle_tool"):
    check(f"module cache '{want}' registry me registered hai",
          want in reg_names, f"registry={reg_names}")
check("business font cache bhi bounded hai", "biz_fonts" in reg_names)

# janitor / bounded reports /sys me lagane layak hain
try:
    rep = bot._janitor_stats()
    check("_janitor_stats() dict deta hai", isinstance(rep, dict))
    rep2 = bot._bounded_report()
    check("_bounded_report() dict deta hai",
          isinstance(rep2, dict) and "caches" in rep2)
except Exception as e:
    check("janitor/bounded report", False, str(e)[:90])


# ======================================================================
print("\n" + "=" * 62)
print(f"  v86 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
if FAILS:
    print("-" * 62)
    for f in FAILS[:25]:
        print("   ❌ " + f)
print("=" * 62)
sys.exit(1 if FAIL else 0)
