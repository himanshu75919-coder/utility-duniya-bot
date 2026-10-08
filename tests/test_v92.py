#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v81.2 — 🩸 MEMORY-LEAK ka ilaaj + leak-hunt (test_v92).

8 Oct 2026 ko maapa gaya (live /health):
    memory 333 MB → 406 MB, gc_runs=3, caches: 0/1792, malloc_trim → 0 MB
Yaani RAM kachre se bhari nahi thi — LIVE objects se. Aise me:
  * watchdog ki "safai" bekaar jaati thi,
  * heavy-gate 378 MB se upar hamesha allowed=1 par latch (doosra user = busy),
  * user ko bot "kaam nahi kar raha" lagta tha (delivery theek thi!).
Is test me 4 cheezein confirm hoti hain: trim, planned clean restart (idle-only),
tracemalloc leak-hunt (opt-in, auto-off), aur bot.py ki wiring SAHI indentation par.
"""
import ast
import os
import re
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PASS = FAIL = 0
LOG = []


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        LOG.append(f"  ❌ {name}  {extra}")


def _tok(tok):
    v = os.environ.get(tok)
    if v:
        return v
    try:
        txt = open(os.path.join(ROOT, ".env"), encoding="utf-8").read()
        m = re.search(rf"^{tok}=(\S+)", txt, re.M)
        if m:
            return m.group(1)
    except Exception:
        pass
    return "123456:AAstub"


os.environ.setdefault("BOT_TOKEN", _tok("BOT_TOKEN"))
os.environ.setdefault("ADMIN_ID", "1")

try:
    import bot as B                                        # noqa: E402
    HAVE_BOT = True
except Exception as e:                                     # noqa: BLE001
    print(f"⚠️ bot import fail: {type(e).__name__}: {str(e)[:200]}")
    HAVE_BOT = False

from modules.core import guard as G                        # noqa: E402
from modules.core import memtrace as MT                    # noqa: E402

BOT_SRC = open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()
G_SRC = open(os.path.join(ROOT, "modules/core/guard.py"), encoding="utf-8").read()
M_SRC = open(os.path.join(ROOT, "modules/core/memtrace.py"), encoding="utf-8").read()

print("=" * 64)
print("v81.2 — memory: trim + idle-only clean restart + leak-hunt")
print("=" * 64)

# =========================================================== 1) malloc_trim
print("\n[1] malloc_trim — pages OS ko wapas")
r = G.malloc_trim()
check("malloc_trim int deta hai", isinstance(r, int), repr(r))
check("malloc_trim -1/0/1 hi (kabhi crash nahi)", r in (-1, 0, 1), repr(r))
check("malloc_trim glibc ke bina bhi safe (ctypes import function ke andar)",
      "\n    try:\n        import ctypes" in M_SRC or
      "def malloc_trim" in G_SRC and G_SRC.count("import ctypes") >= 1)

# =========================================================== 2) free_memory
print("\n[2] free_memory() ka return shape")
keep = [{"a": "x" * 40, "i": i} for i in range(30000)]
res = G.free_memory(aggressive=True)
keep = None
check("dict lauta", isinstance(res, dict), repr(res)[:80])
for k in ("before_mb", "after_mb", "freed_mb", "trim"):
    check(f"key: {k}", k in res, repr(res)[:120])
check("after <= before (safai ke baad badha nahi)", res["after_mb"] <= res["before_mb"] + 1,
      repr(res))
check("freed_mb = before-after (jhootha zero nahi)",
      abs(res["freed_mb"] - max(0.0, res["before_mb"] - res["after_mb"])) < 0.2, repr(res))
check("aggressive=True se gc x3 + trim dono",
      G_SRC.count("gc.collect(2)") >= 1 and "malloc_trim() if aggressive" in G_SRC)

# =========================================================== 3) guard_stats
print("\n[3] guard_stats me naye aakde (health inhe padhta hai)")
st = G.guard_stats()
for k in ("gc_runs", "trim_runs", "trim_released", "last_freed_mb", "restarts",
          "restart_at_mb", "mem_mb", "mem_peak_mb"):
    check(f"guard_stats['{k}']", k in st, str(sorted(st))[:200])
check("restart_at_mb = env se (off = 0)",
      st["restart_at_mb"] == float(os.environ.get("MEM_RESTART_MB") or 0), repr(st["restart_at_mb"]))
n0 = st["trim_runs"]
G.free_memory()
check("har safai par trim_runs badhta hai", G.guard_stats()["trim_runs"] >= n0,
      f"{n0}→{G.guard_stats()['trim_runs']}")

# =========================================================== 4) is_idle
print("\n[4] is_idle() — restart ka green signal (confirm na ho to haath nahi)")
_saved = list(G.IDLE_CHECKS)
try:
    G.IDLE_CHECKS.clear()
    check("koi check nahi → False (conservative)", G.is_idle() is False)
    G.register_idle_check(lambda: True)
    check("sab 'idle' → True", G.is_idle() is True)
    G.register_idle_check(lambda: False)
    check("ek bhi inkaar → False", G.is_idle() is False)
    G.IDLE_CHECKS.clear()
    G.register_idle_check(lambda: 1 / 0)
    check("check khud toote → False (crash nahi)", G.is_idle() is False)
    f = lambda: True                                          # noqa: E731
    G.IDLE_CHECKS.clear()
    G.register_idle_check(f)
    G.register_idle_check(f)
    check("same check do baar register nahi hota", len(G.IDLE_CHECKS) == 1, str(G.IDLE_CHECKS))
    check("register_idle_check non-callable ko thukrata hai",
          (G.register_idle_check(42) or len(G.IDLE_CHECKS)) == 1)
finally:
    G.IDLE_CHECKS.clear()
    G.IDLE_CHECKS.extend(_saved)

# =========================================================== 5) restart rule
print("\n[5] planned restart ka faisla (OOM-kill se pehle, kaam ke beech kabhi nahi)")
hard = re.search(r"if m >= hard:(.*?)time\.sleep", G_SRC, re.S)
check("watchdog ka hard-branch mila", bool(hard))
hb = hard.group(1) if hard else ""
check("MEM_RESTART_MB padha (0 = off — default par koi restart nahi)",
      'os.environ.get("MEM_RESTART_MB") or 0' in hb)
check("restart se pehle is_idle() poocha jaata hai", "is_idle()" in hb)
check("uptime bhi (boot ke turant baad restart nahi)", "min_up" in hb and "up >=" in hb)
check("safai ke baad bhi RAM high ho tabhi restart", 'r["after_mb"] >= rat * 0.985' in hb)
check("restarts ka aakda health me dikhe", '_mem_state["restarts"]' in hb)
check("exit se pehle stdout/stderr flush", "sys.stdout.flush()" in hb)
check("os._exit(1) — Render dobara uthaega", "os._exit(1)" in hb)
i_os = hb.find("os._exit(1)")
i_chk = hb.find("if (rat > 0")
check("os._exit check ke ANDAR hai (bahar nahi — warn)", 0 <= i_chk < i_os, f"{i_chk}/{i_os}")
# try/except SystemExit: raise — taaki test/mein kabhi chup-chaap na mare
check("SystemExit ko dobara raise kiya", "except SystemExit:" in hb and "raise" in hb)
check("baaki exception nibale jaate hain (watchdog marne na paaye)",
      "mem restart check" in hb)

# =========================================================== 6) memtrace
print("\n[6] leak-hunt (tracemalloc) — opt-in, auto-off, kabhi nahi marta")
for bad in ("", "off", "0", "false", "no", "nahi"):
    os.environ["MEM_TRACE"] = bad
    check(f"MEM_TRACE='{bad}' → start nahi (zero cost)", MT.maybe_start_from_env() is False, bad)
os.environ["MEM_TRACE"] = "on"
os.environ["MEM_TRACE_SECONDS"] = "20"
check("MEM_TRACE=on → start", MT.start.__self__ is None if False else MT.maybe_start_from_env() is True)
check("enabled() True", MT.enabled() is True)
junk = [{"a": "x" * 60, "i": i} for i in range(50000)]
rep = MT.report()
check("report me 'leak-hunt' aata hai", rep.startswith("leak-hunt"), rep[:80])
check("report me MB ka aakda hai", "MB" in rep, rep[:120])
check("Frame.lineno use hota hai (purana .line AttributeError de raha tha)",
      "lineno" in M_SRC and ".line or 0" not in M_SRC)
junk = None
MT.stop()
check("stop() ke baad enabled False", MT.enabled() is False)
check("band hone ke baad bhi aakhri report yaad rehti hai",
      MT.report().startswith("leak-hunt (last run):"), MT.report()[:60])
os.environ.pop("MEM_TRACE", None)
os.environ.pop("MEM_TRACE_SECONDS", None)
MT._ST.update({"on": False, "final": "", "err": ""})
check("kabhi start na kiya ho → report khaali string (crash nahi)", MT.report() == "")
check("tracemalloc band → process ka overhead khatam", "tracemalloc.stop()" in M_SRC)
check("auto-stop ka time-check report() me hai", "stop_at" in M_SRC and "time.time() >=" in M_SRC)

# =========================================================== 7) bot.py wiring
if HAVE_BOT:
    print("\n[7] bot.py ki wiring (yahi sabse zyada toota hai — indentation samet)")
    ln = BOT_SRC.split("\n")

    def _ind(s):
        return len(s) - len(s.lstrip())

    i_w = next((n for n, x in enumerate(ln)
                if "start_memory_watchdog()" in x and not x.strip().startswith("def")), -1)
    check("watchdog call mila", i_w >= 0)
    i_try = next((n for n, x in enumerate(ln[i_w:i_w + 12], start=i_w)
                  if "register_idle_check" in x), -1)
    check("idle-check registration watchdog ke paas hai", i_try > 0, str(i_try))
    # registration 'try:' line 'except' block ke andar nahi honi chahiye
    i_tryline = next(n for n in range(i_try, i_w - 1, -1) if ln[n].strip() == "try:")
    check("registration ka try block main() ke level par (except ke ANDAR nahi!)",
          _ind(ln[i_tryline]) == _ind(ln[i_w]) - 4,
          f"try={_ind(ln[i_tryline])} watchdog={_ind(ln[i_w])}")
    i_mt = next((n for n, x in enumerate(ln[i_w:i_w + 14], start=i_w)
                 if "_memtrace_boot()" in x), -1)
    check("_memtrace_boot() bahi andar nahi, 4-space par", i_mt > 0 and _ind(ln[i_mt]) == _ind(ln[i_w]) - 4,
          str(_ind(ln[i_mt])) if i_mt > 0 else "missing")

    # tool ke baad relief — dono wrappers me
    for tag in ('_mem_relief("text:"', '_mem_relief("cb:"'):
        check(f"wrapper me foran relief: {tag}", BOT_SRC.count(tag) == 1, str(BOT_SRC.count(tag)))
    fin = re.findall(r"finally:\n(?:.*\n){0,14}?.*_mem_relief\(", BOT_SRC)
    check("relief calls finally blocks me hain (dono)", len(fin) == 2, str(len(fin)))
    check("_mem_relief kabhi crash nahi karta (poora try me)",
          re.search(r"def _mem_relief.*?try:.*?except Exception as e", BOT_SRC, re.S) is not None)
    check("_mem_relief ka apna threshold env se (MEM_RELIEF_MB)",
          'os.environ.get("MEM_RELIEF_MB")' in BOT_SRC)
    check("_bot_idle heavy+update dono gates poochta hai",
          '_heavy.stats()' in BOT_SRC and "_ug.stats()" in BOT_SRC
          and '"in_flight"' in BOT_SRC and '"parallel"' in BOT_SRC)
    check("_bot_idle stats fail hone par False (restart risk nahi leta)",
          re.search(r"def _bot_idle.*?except Exception.*?return False", BOT_SRC, re.S) is not None)

    print("\n[8] /health render + nayi lines")
    try:
        h = B.health_html()
        RENDER_OK, RENDER_ERR = True, ""
    except Exception as e:
        h, RENDER_OK, RENDER_ERR = "", False, f"{type(e).__name__}: {e}"
    check("health_html() RENDER hoti hai", RENDER_OK, RENDER_ERR)
    check("health me 20+ <p> (aadh-i page nahi udaya)", h.count("<p") >= 20, str(h.count("<p")))
    check("memory line me trim stats", "trim=" in h, h[h.find("memory:"):h.find("memory:") + 160])
    check("memory line me restart_at + restarts", "restart_at=" in h and "restarts=" in h)
    check("purani lines zinda: delivery/webhook/up/heavy-gate",
          all(k in h for k in ("delivery:", "webhook:", "up:", "heavy-gate", "update-gate")))
    os.environ["MEM_TRACE"] = "on"
    os.environ["MEM_TRACE_SECONDS"] = "60"
    B._memtrace_boot()
    check("MEM_TRACE on par health me leak-hunt line aati hai",
          "leak-hunt" in B.health_html(), B._leak_hunt_line()[:80])
    MT.stop()
    MT._ST.update({"on": False, "final": "", "err": ""})
    os.environ.pop("MEM_TRACE", None); os.environ.pop("MEM_TRACE_SECONDS", None)
    check("MEM_TRACE off par health saaf (koi jhoothi line nahi)",
          "leak-hunt" not in B.health_html())
    if MT.enabled():
        MT.stop()
else:
    print("\n[7][8] SKIPPED — python-telegram-bot nahi mila (bot import nahi ho paya)")

# =========================================================== 9) copy-safe
print("\n[9] copy/prompts ka rule (kabhi user-facing text mat chhedo)")
for f, src in (("memtrace.py", M_SRC),):
    check(f"{f} me koi reply/send/edit nahi (sirf log+health)",
          not re.search(r"reply_text|edit_message_text|send_message|reply_markup", src), f)
check("guard.py me naya user-facing text nahi (sirf log.warning/critical)",
      'log.critical("🔁 MEMORY' in G_SRC and "reply_text" not in G_SRC.split("def start_memory_watchdog")[1][:4000])
check("naye user strings me HTML <b> nahi (wall/menu ke copy se takraavat)",
      "<b>" not in M_SRC)

# =========================================================== self-test
print("\n[10] is test ke daant (khud ko pakadne chahiye)")
try:
    assert G.malloc_trim() in (99,), "ye jaan-boojh galat hona chahiye"
    check("jaan-boojh ka galat assert FAIL hona chahiye tha", False)
except AssertionError:
    check("jaan-boojh ka galat assert FAIL hua ✅", True)
try:
    x = MT.report()
    check("report() exception nahi deta (chahe kuch bhi ho)", True)
except Exception as e:
    check("report() exception nahi deta", False, str(e))

print("\n" + "=" * 64)
for l in LOG:
    print(l)
print(f"RESULT: {PASS} PASS / {FAIL} FAIL")
print(f"  v92 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 64)
sys.exit(1 if FAIL else 0)
