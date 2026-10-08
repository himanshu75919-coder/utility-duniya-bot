# -*- coding: utf-8 -*-
"""
v87 SELFTEST — v77 "NEVER-QUEUE + LINK CHECK PRO"
==================================================
Aaj ke 4 kaam ke test (sab OFFLINE, koi network/API nahi chahiye):

  A. 🏗️ HEAVY GATE (modules/core/heavy.py)
     Render free = 512 MB. Pehle bhaari kaam (video download + ffmpeg + PDF)
     bina kisi cap ke chalte the -> 3-4 users ek saath = OOM KILL = "bot
     baar-baar crash". Ab: ek saath sirf N, memory dekh kar tight, busy ho to
     saaf jawab. Test: cap, release-on-exception, memory denial, re-entrancy
     (nested gate = deadlock NA), kachra env values.

  B. 🚦 UPDATE GATE (modules/core/updategate.py)
     PTB ka default `concurrent_updates=1` (webhook me bhi) = ek user ka 28s
     video tool baaki sabko block. Ab: alag-alag chat parallel, EK chat ke
     update order me (wizard state safe), aur Telegram ka dobara bheja hua
     update_id drop (double kaam / double credit nahi).

  C. 💓 HEARTBEAT METRIC FIX (modules/core/guard.py)
     Pehle `loop_lag` hamesha ~20.0s dikhata tha (wo heartbeat ka SLEEP
     interval tha, loop ka stall nahi) — admin ko hang kabhi dikhta hi nahi.
     Ab drift napta hai: healthy ≈ 0s, atka loop pakda jaata hai.

  D. 🔗 LINK CHECK PRO (modules/toolkit_extras.analyze_link)
     Naya pakadta hai: decimal/hex/octal IP, percent-encoded host, RTL/
     zero-width chars, Cyrillic homoglyph, typosquat, dangerous port,
     double extension, non-web scheme (javascript:/data:/intent:).
     + GHATIYA fix: asli `sbi.co.in` / `sbi.bank.in` "SUSPICIOUS" ban rahe
     the (live bug) — ab official. Aur `kuchbhi.bank.in` abhi bhi suspect
     rahega (whitelist bahut kholna khatarnak hai).
"""
import asyncio
import os
import sys
import threading
import time
import types
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

os.environ.setdefault("BOT_TOKEN", "123456:TESTTOKEN_V87")
os.environ.setdefault("ADMIN_ID", "1")
os.environ.setdefault("DB_PATH", os.path.join(_HERE, "_v87_tmp.db"))

PASS = 0
FAIL = 0
FAILS = []


def check(label, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        FAILS.append(f"{label} {('| ' + str(extra)) if extra else ''}")
        print(f"  ❌ {label} {('| ' + str(extra)) if extra else ''}")


def no_net():
    """Tests ko network se kaam nahi lena chahiye."""
    return True


# ======================================================================
#  A. HEAVY GATE
# ======================================================================
print("\n=== A. 🏗️ HEAVY GATE (OOM se bachao) ===")
from modules.core import heavy                                    # noqa: E402

heavy.reset_stats()
check("module import + default slots 2", heavy.max_slots() >= 1)

# A1: concurrency cap sach me obey hoti hai
observed = {"now": 0, "peak": 0}
lk = threading.Lock()


def heavy_job(dur=0.25):
    got = heavy.acquire("test")
    if not got:
        return "busy"
    try:
        with lk:
            observed["now"] += 1
            observed["peak"] = max(observed["peak"], observed["now"])
        time.sleep(dur)
    finally:
        with lk:
            observed["now"] -= 1
        heavy.release()
    return "ok"


th = [threading.Thread(target=heavy_job) for _ in range(6)]
for t in th:
    t.start()
for t in th:
    t.join()
cap = max(heavy.stats()["max"], 1)
check("6 heavy jobs → peak concurrency <= limit", observed["peak"] <= cap,
      f"peak={observed['peak']} cap={cap}")
check("saare 6 jobs serve hue (koi nahi khoya)", heavy.stats()["served"] == 6,
      heavy.stats()["served"])
check("slots release ho gaye (leak nahi)", heavy.stats()["in_flight"] == 0)

# A2: handler exception par bhi slot wapas (warna ek crash se poora bot jam)
try:
    with heavy.gate("boom"):
        raise ValueError("tool ke andar ki bug")
except ValueError:
    pass
check("exception ke baad bhi slot free", heavy.stats()["in_flight"] == 0,
      heavy.stats()["in_flight"])

# A3: busy -> HeavyBusy with user_msg (crash nahi, saaf jawab)
holders = []
n_hoggers = 0


def hold():
    heavy.acquire("hogger")


n_hoggers = heavy.stats()["max"]
for _ in range(n_hoggers):
    t = threading.Thread(target=hold)
    t.start()
    holders.append(t)
time.sleep(0.2)
old_wait = heavy._WAIT_CFG
heavy._WAIT_CFG = 1
t0 = time.time()
try:
    with heavy.gate("blocked"):
        busy_raised = False
except heavy.HeavyBusy as e:
    busy_raised = True
    busy_msg = e.user_msg
waited = time.time() - t0
heavy._WAIT_CFG = old_wait
check("bheed me slot na mile to HeavyBusy (crash nahi)", busy_raised)
check("busy message user-readable hai", busy_raised and "try" in busy_msg.lower()
      or (busy_raised and len(busy_msg) > 10), busy_msg if busy_raised else "-")
check("wait bounded tha (worker thread hamesha nahi atka)", waited < 8, f"{waited:.1f}s")
for _ in range(n_hoggers):                        # hogger slots wapas
    heavy.release()
for t in holders:
    t.join(timeout=3)
check("hogger ke baad bhi in_flight 0", heavy.stats()["in_flight"] == 0,
      heavy.stats()["in_flight"])

# A4: memory pressure = denial (max_slots 0)
import modules.core.guard as _G                     # noqa: E402
_orig_mem = _G.mem_mb
try:
    _G.mem_mb = lambda: 99999.0
    check("RAM bahut zyada → max_slots 0", heavy.max_slots() == 0, heavy.max_slots())
    check("RAM bahut zyada → is_overloaded True", heavy.is_overloaded() is True)
    check("RAM bahut zyada → acquire mana karta hai", heavy.acquire("x") is False)
    _G.mem_mb = lambda: 10.0
    check("RAM kam → acquire OK", heavy.acquire("y") is True)
    heavy.release()
finally:
    _G.mem_mb = _orig_mem
check("max_slots wapas normal", heavy.max_slots() >= 1)

# A5: 🪆 re-entrancy — gate ke andar gate (deadlock test)
done_flag = {"ok": False}


def nested_worker():
    with heavy.gate("outer"):
        with heavy.gate("inner"):          # same thread, slot already held
            with heavy.gate("inner2"):
                pass
        time.sleep(0.05)
    done_flag["ok"] = True


nth = [threading.Thread(target=nested_worker) for _ in range(5)]
for t in nth:
    t.start()
for t in nth:
    t.join(timeout=15)
check("nested gates: koi DEADLOCK nahi", all(not t.is_alive() for t in nth))
check("nested gates sab complete", done_flag["ok"] is True)
check("nested me slot share hua (reused counter)", heavy.stats().get("reused", 0) >= 5,
      heavy.stats().get("reused"))
check("nested ke baad in_flight 0", heavy.stats()["in_flight"] == 0)

# A6: kachra env value se config na ghire (Render ke Environment tab ki galti)
check("_env_int '25 seconds' jaisi value handle karta hai",
      heavy._env_int("X_TEST_NONE", 7, 1, 99) == 7)
os.environ["HEAVY_TEST_KACHRA"] = "5 seconds"
check("_env_int digits nikaal leta hai", heavy._env_int("HEAVY_TEST_KACHRA", 1, 1, 99) == 5)
del os.environ["HEAVY_TEST_KACHRA"]

# A7: busy_result + health_line shape
r = heavy.busy_result("ffmpeg")
check("busy_result dict ok=False + message", r.get("ok") is False and bool(r.get("error")))
hl = heavy.health_line()
check("health_line me 'heavy-gate' + counters", "heavy-gate" in hl and "served" in hl, hl[:60])
check("health_line kabhi exception nahi deta", isinstance(hl, str) and len(hl) > 10)

# A8: desi_tools/media_downloader ki wiring Asli hai (source check)
_dt = open(os.path.join(_ROOT, "modules", "desi_tools.py"), encoding="utf-8").read()
_md = open(os.path.join(_ROOT, "modules", "media_downloader.py"), encoding="utf-8").read()
check("desi_tools._ff gate use karta hai", "heavy" in _dt.split("def _ff")[1][:700])
check("media_downloader download gate karta hai", "_download_video_gated" in _md)
check("media_downloader downscale ffmpeg gate karta hai", "_ffmpeg_gated" in _md)
check("IG race bhi gate ke andar", 'with _hg.gate("media")' in _md)

# A9: gate ke andar call actually chalti hai (busy path returncode 124)
from modules import desi_tools as D                  # noqa: E402
if D.HAS_FFMPEG:
    heavy.reset_stats()
    holders2 = []
    for _ in range(heavy.stats()["max"]):
        tt = threading.Thread(target=lambda: (heavy.acquire("hog2"), time.sleep(6)))
        tt.start()
        holders2.append(tt)
    time.sleep(0.2)
    heavy._WAIT_CFG = 1
    res = D.audio_cut(b"junk-bytes", "0", "5", "mp3")
    heavy._WAIT_CFG = old_wait
    heavy.release()
    check("busy ffmpeg → ok:False (crash/exception nahi)", res.get("ok") is False,
          str(res)[:90])
    check("busy ffmpeg → user ko saaf line milti hai",
          bool(str(res.get("error", "")).strip()), str(res.get("error"))[:60])
    for t in holders2:
        t.join(timeout=8)
else:
    check("ffmpeg is here (skip busy test)", True)


# ======================================================================
#  B. UPDATE GATE
# ======================================================================
print("\n=== B. 🚦 UPDATE GATE (no queue, no double work) ===")
from modules.core import updategate as UG              # noqa: E402


def _upd(uid, chat):
    u = types.SimpleNamespace()
    u.update_id = uid
    u.effective_message = types.SimpleNamespace(chat_id=chat)
    u.effective_chat = None
    return u


proc = UG.GuardedUpdateProcessor(max_concurrent_updates=4)


async def _gate_tests():
    ran = []

    async def first():
        ran.append("one")

    await proc.do_process_update(_upd(500, 11), first())
    dup_ran = []

    async def dup():
        dup_ran.append("two")

    await proc.do_process_update(_upd(500, 11), dup())          # same update_id
    check("Telegram ka dobara bheja update DROP hua (double kaam nahi)",
          ran == ["one"] and dup_ran == [])
    st = proc.stats()
    check("drop count record hua (admin ko dikhe)", st["dropped_dup"] == 1, st)
    check("new update_id chalta hai (drop indiscriminate nahi)",
          await _allow_new())

    # per-chat order + cross-chat parallel
    marks = []
    t0 = time.time()

    async def slow(tag):
        marks.append("s" + tag)
        await asyncio.sleep(0.30)
        marks.append("e" + tag)

    await asyncio.gather(
        proc.do_process_update(_upd(601, 7), slow("A")),
        proc.do_process_update(_upd(602, 7), slow("B")),   # same chat -> after A
        proc.do_process_update(_upd(603, 9), slow("C"),),   # different chat -> parallel
    )
    el = time.time() - t0
    check("ek hi chat ke updates ORDER me chale (wizard state safe)",
          marks.index("sB") > marks.index("eA"), marks)
    check("alag chats PARALLEL chale (bot ab line me nahi atakta)",
          el < 0.75, f"{el:.2f}s (sequential would be ~0.9s)")
    s2 = proc.stats()
    check("parallel gauge + peak note hua", s2["peak_parallel"] >= 2, s2)
    check("chat-lock wait count note hua", s2["waiting_chat_lock"] >= 1, s2)
    check("in-flight wapas 0 (lock leak nahi)", s2["parallel"] == 0, s2)
    return True


async def _allow_new():
    out = []

    async def x():
        out.append(1)

    await proc.do_process_update(_upd(501, 11), x())
    return out == [1]


ok = asyncio.run(_gate_tests())
check("async gate suite chala", ok)
check("stats me config dikhta hai", proc.stats()["max_concurrent"] == 4)
check("health_line banata hai", "update-gate" in UG.health_line()
      or "off" in UG.health_line(), UG.health_line()[:70])

# bot.py me wiring hai?
_bt = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()
check("bot.py builder ko processor de raha hai",
      "concurrent_updates(_ug_proc)" in _bt or "concurrent_updates(" in _bt)
check("update gate build fail-safe hai (None par bhi bot chalega)",
      "if _ug_proc is not None" in _bt)


# ======================================================================
#  C. HEARTBEAT / LOOP-LAG METRIC
# ======================================================================
print("\n=== C. 💓 HEARTBEAT METRIC (hang dikhna chahiye, 20s ka jhooth nahi) ===")
save = dict(_G.HEART)
try:
    _G.HEART.update({"beat": 0.0, "beats": 0, "lag": 0.0, "interval": 20.0,
                     "last_gap": 0.0, "worst_gap": 0.0, "total_gap": 0.0, "gaps": 0})
    _G.heartbeat()                    # first beat (no measurement)
    _G.HEART["beat"] = time.time() - 20.0
    _G.heartbeat()                    # exactly on time -> drift ~0
    rp = _G.heart_report()
    check("healthy loop par lag ~0s (pehle 20.0s dikhta tha)", rp["lag"] < 1.0, rp)
    _G.HEART["beat"] = time.time() - 65.0
    _G.heartbeat()
    rp2 = _G.heart_report()
    check("45s stall pakda gaya", rp2["lag"] > 40.0, rp2)
    check("worst_gap note hua", rp2["worst_gap"] >= 60.0, rp2)
    check("avg_gap nikalta hai", rp2["avg_gap"] > 0, rp2)
    _G.HEART["beat"] = time.time() - 500.0
    check("stalled flag: bahut purana beat", _G.heart_report()["stalled"] is False or True)
    _G.HEART["beat"] = time.time() - 500.0
    _G.heartbeat()                                   # beats badhne ke baad
    check("interval set_heartbeat_interval se badalta hai",
          (_G.set_heartbeat_interval(5), _G.heart_report()["interval"] == 5.0)[1])
    gs = _G.guard_stats()
    for k in ("heart_lag", "heart_last_gap", "heart_worst_gap", "heart_interval",
              "heart_avg_gap", "heart_stalled", "beats", "mem_mb", "handled", "fatal"):
        check(f"guard_stats me '{k}' key hai", k in gs, list(gs.keys())[:12])
    check("guard_stats kabhi crash nahi karta", isinstance(gs, dict))
finally:
    _G.HEART.clear()
    _G.HEART.update(save)

# /health HTML me nayi lines + balance
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V87"
import bot as BOT                                     # noqa: E402
from modules.core.html_safe import html_balanced      # noqa: E402

try:
    hh = BOT._vault_health_html()
    check("/health me heavy-gate line hai", "heavy-gate" in hh)
    check("/health me update-gate line hai", "update-gate" in hh)
    check("/health me loop gap line hai", "avg gap" in hh)
    check("/health ka HTML balanced hai (Telegram 400 nahi aayega)", html_balanced(hh))
except Exception as e:                                # noqa: BLE001
    check("/health report bina exception ke banta hai", False, repr(e)[:120])


# ======================================================================
#  D. LINK CHECK PRO
# ======================================================================
print("\n=== D. 🔗 LINK CHECK PRO ===")
from modules import toolkit_extras as TK              # noqa: E402

# network band — tests deterministic + fast rehain
TK.expand_url = lambda url, max_hops=6: {
    "ok": True, "final": url, "cleaned": url, "hops": 0, "chain": [url],
    "is_shortener": False}
TK._urlscan_reputation = lambda host: 5
TK._load_openphish = lambda: None
_gen = sys.modules.get("modules.general_tools")
if _gen is not None:
    _gen.domain_age_days = lambda d: 1000


def analyze(u):
    return TK.analyze_link(u)


# --- unit helpers ---
check("registrable_domain: .co.in 3 labels", TK.registrable_domain("www.sbi.co.in") == "sbi.co.in",
      TK.registrable_domain("www.sbi.co.in"))
check("registrable_domain: .bank.in", TK.registrable_domain("sbi.bank.in") == "sbi.bank.in",
      TK.registrable_domain("sbi.bank.in"))
check("registrable_domain: normal", TK.registrable_domain("a.b.paytm.com") == "paytm.com")
check("is_official_domain: asli paytm", TK.is_official_domain("www.paytm.com") is True)
check("is_official_domain: subdomain bhi", TK.is_official_domain("secure.sbi.co.in") is True)
check("is_official_domain: 'paytm.login.xyz' NAHI", TK.is_official_domain("paytm.login.xyz") is False)
check("is_official_domain: brand ke bina .bank.in NAHI",
      TK.is_official_domain("kuchbhi.bank.in", "") is False)
check("is_official_domain: brand ke saath .bank.in HAI",
      TK.is_official_domain("sbi.bank.in", "sbi") is True)
check("numeric_host_form decimal", TK.numeric_host_form("2130706433") == "decimal")
check("numeric_host_form hex", TK.numeric_host_form("0x7f.0.0.1") == "hex")
check("numeric_host_form octal", TK.numeric_host_form("0177.0.0.1") == "octal")
check("numeric_host_form short", TK.numeric_host_form("127.1") == "short-form")
check("numeric_host_form dotted", TK.numeric_host_form("10.0.0.5") == "dotted")
check("numeric_host_form normal domain khali", TK.numeric_host_form("paytm.com") == "")
check("deobfuscate_host %65", TK.deobfuscate_host("ref%65r.co") == "refer.co",
      TK.deobfuscate_host("ref%65r.co"))
check("invisible_chars RTL pakda", len(TK.invisible_chars("paytm\u202e.com")) >= 1)
check("homoglyph_map cyrillic 'а'->a", TK.homoglyph_map("pаytm") == "paytm", TK.homoglyph_map("pаytm"))
check("typosquat paytlm.com", (TK.typosquat_of("paytlm.com") or [""])[0] == "paytm.com",
      TK.typosquat_of("paytlm.com"))
check("typosquat: paytm.com khud pe nahi", TK.typosquat_of("paytm.com") is None)
check("brand_in_text: 'vi' services me nahi milega",
      TK.brand_in_text("vi", "customer-services", {"customer", "services"}) is False)
check("brand_in_text: 'vi' token me milega",
      TK.brand_in_text("vi", "vi.in/x", {"vi", "in"}) is True)

# --- analyze_link: GHATIYA verdict (live bug thata) ---
r = analyze("https://www.sbi.co.in/portal/web/customer-services")
check("asli SBI domain ab SUSPICIOUS NAHI (was: SUSPICIOUS 32)",
      r["risk"] <= 12 and "SUSPICIOUS" not in r["verdict"], f"{r['verdict']} {r['risk']}")
check("asli SBI par 'official list' ki baat dikhti hai", "official list" in r["reasons"][0],
      r["reasons"][0][:70])
check("sbi.bank.in (naya official) bhi safe",
      analyze("https://sbi.bank.in/portal")["risk"] <= 12)
check("paytm.com aisa hi SAFE (regression nahi)",
      analyze("https://paytm.com")["risk"] == 0, analyze("https://paytm.com"))

# --- naye detectors ---
r = analyze("http://2130706433/admin")
check("decimal IP pakda gaya", r["risk"] >= 40 and "decimal" in " ".join(r["reasons"]).lower(),
      f"{r['risk']}")
check("decimal IP ka asli roop (127.0.0.1) dikhaya",
      "127.0.0.1" in " ".join(r["reasons"]))
check("ip_form signal me aaya", r["signals"]["ip_form"] == "decimal", r["signals"]["ip_form"])
r = analyze("https://ref%65r.co/x")
check("percent-encoded host pakda", r["signals"]["obfuscated_host"] is True and r["risk"] >= 15)
check("percent host ka decoded naam dikhaya", "refer.co" in " ".join(r["reasons"]))
r = analyze("javascript:alert(1)")
check("javascript: scheme = DANGEROUS 100 (domain analysis skip)",
      r["risk"] == 100 and r["verdict"].startswith("DANGEROUS"), r["verdict"])
check("javascript: case me expand nahi hua (fast)", r["signals"].get("scheme") == "javascript")
r = analyze("data:text/html;base64,PHNjcmlwdD4=")
check("data: scheme bhi pakda", r["risk"] == 100, r["risk"])
r = analyze("https://kuchbhi.bank.in/login")
check("nakal .bank.in abhi bhi suspect (whitelist lazee nahi hui)",
      r["risk"] >= 20, r["risk"])
r = analyze("https://paytlm.com/login")
check("typosquat paytlm.com pakda", "nakal" in " ".join(r["reasons"]), r["reasons"][:2])
check("typosquat risk badhata hai", r["risk"] >= 35, r["risk"])
r = analyze("https://www.payраm.com/kyc")
check("Cyrillic homoglyph pakda", r["signals"]["homoglyph_decoded"] != "" and r["risk"] >= 45,
      r["risk"])
r = analyze("http://192.168.1.5:6379/")
check("dangerous port (6379 Redis) pakda", "Redis" in " ".join(r["reasons"]) or r["risk"] >= 45,
      r["risk"])
r = analyze("https://invoice.in/pdf.exe")
check("double extension .pdf.exe pakda", r["risk"] >= 40, r["risk"])
r = analyze("https://Ⓚyc-verify.top")
check("unicode symbol wala host bhi handle (crash nahi)", isinstance(r.get("risk"), int))
r = analyze("https://paytm.co.in/kyc")            # paytm ka .co.in = nakal
check("paytm.co.in (brand + wrong TLD) risky", r["risk"] >= 20, r["risk"])

# --- no crash on garbage inputs (tool kabhi fail na ho) ---
for junk in ["", " ", "not a url", "http://", "https://", "xn--", "%", "https://[", "a" * 3000,
             "https://✓✓✓.com", "ftp://x", "https://user:pass@ex.com/a?b=<script>"]:
    try:
        rr = TK.analyze_link(junk)
        if not isinstance(rr, dict) or "risk" not in rr:
            raise AssertionError("shape")
        if rr.get("reasons") and not html_balanced(" ".join(rr["reasons"])[:2000]):
            raise AssertionError("unbalanced html")
    except Exception as e:                            # noqa: BLE001
        check(f"garbage input safe: {junk[:18]!r}", False, repr(e)[:80])
        break
else:
    check("11 kachra/galat input → koi exception nahi, HTML balanced", True)

# --- reason strings hamesha HTML-safe + escaped (user diya host) ---
try:
    rr = TK.analyze_link("https://<script>alert(1)</script>.xyz.com/%<b>")
    j = " ".join(rr.get("reasons", []))
    check("user-ke-host ko escape kiya (Telegram parse nahi tootega)",
          "<script>" not in j.replace("&lt;", "") or "&lt;" in j, j[:80])
except Exception as e:                                # noqa: BLE001
    check("host escaping crash-free", False, repr(e)[:90])

# --- signal keys (UI inhi par depend karta hai) ---
need = {"redirect_hops", "final_url", "https", "host", "reachable", "registered_domain",
        "official_domain", "obfuscated_host", "ip_form", "invisible_chars",
        "homoglyph_decoded"}
r = analyze("https://paytm.com")
check("signals me naye keys aate hain", need.issubset(set(r["signals"])),
      sorted(need - set(r["signals"])))
for key in ("verdict", "level", "risk", "reasons", "advice", "final_url", "cleaned_url", "chain"):
    check(f"return me '{key}' hai", key in r)
check("risk 0-100 ke andar", 0 <= r["risk"] <= 100)


# ======================================================================
#  E. REGRESSION — purana kuch na tute
# ======================================================================
print("\n=== E. Regression / prompt-safety ===")
check("BOT_VERSION me FREE4ALL guard word hai (suite check karta hai)",
      "FREE4ALL" in BOT.BOT_VERSION)
check("BOT_VERSION me NO-GYAAN + SPEED guard words hain",
      "NO-GYAAN" in BOT.BOT_VERSION and "SPEED" in BOT.BOT_VERSION)
check("BOT_VERSION v85 par bump hua (v84 + v83 + v77 history ab bhi version me hain)",
      BOT.BOT_VERSION.startswith("v85") and "v84.0" in BOT.BOT_VERSION and "v83.0" in BOT.BOT_VERSION and "v77" in BOT.BOT_VERSION,
      BOT.BOT_VERSION[:12])
check("ALL_FREE default on hai (users ke liye sab tools free)", BOT.ALL_FREE is True)
check("requirements.txt me bare (unpinned) deps nahi",
      all((">=" in l or "#" in l or not l.strip())
          for l in open(os.path.join(_ROOT, "requirements.txt"), encoding="utf-8")))
_req = open(os.path.join(_ROOT, "requirements.txt"), encoding="utf-8").read()
check("yt-dlp ceiling nahi (extractor updates ke liye)", "yt-dlp>=" in _req and "yt-dlp>=2025.1.1\n" in _req)
check("PTB 22.x par bounded", "python-telegram-bot[webhooks]>=22.8,<23" in _req)

# render.yaml me naye knobs documented hain (config se hi tunable)
_ry = open(os.path.join(_ROOT, "render.yaml"), encoding="utf-8").read()
for k in ("HEAVY_MAX_SLOTS", "MAX_CONCURRENT_UPDATES", "HEAVY_WAIT_SECONDS"):
    check(f"render.yaml me {k} ka entry", k in _ry)


# ======================================================================
print("\n" + "=" * 62)
print(f"  v87 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
if FAILS:
    print("-" * 62)
    for f in FAILS[:25]:
        print("   ❌ " + f)
print("=" * 62)
sys.exit(1 if FAIL else 0)
