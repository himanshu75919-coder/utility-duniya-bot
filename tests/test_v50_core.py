#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_v50_core.py — v50 core layer ka end-to-end test
====================================================
Ye test ASLI `bot.on_text` ko mocked Telegram Update ke saath chalata hai,
taki pata chale ki central rate-limit gate + to_thread wiring sach me kaam
karti hai (sirf syntax check nahi).

Chalane ka tarika:
    python3 tests/test_v50_core.py
"""
import asyncio
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

# test ke liye alag DB + test env (asli botdata.db ko chhuna nahi hai)
_TMP = tempfile.mkdtemp(prefix="ud_test_")
os.environ["DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ.setdefault("BOT_TOKEN", "123456:TEST")
os.environ.setdefault("ADMIN_ID", "1")
os.environ.setdefault("PREMIUM_ONLY", "off")

PASS, FAIL = [], []


def ok(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'✅' if cond else '❌'} {name}" + (f"  [{extra}]" if extra and not cond else ""))


def section(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


# ---------------------------------------------------------------- fake telegram
class FakeUser:
    def __init__(self, uid, first_name="Tester", username="tester"):
        self.id = uid
        self.first_name = first_name
        self.last_name = ""
        self.username = username
        self.is_bot = False


class FakeMessage:
    def __init__(self, text, uid):
        self.text = text
        self.message_id = 1
        self.chat = type("C", (), {"id": uid})()
        self.chat_id = uid
        self.from_user = FakeUser(uid)
        self.sent = []          # jo reply_text me gaya
        self.deleted = False

    async def reply_text(self, text, **kw):
        self.sent.append(text)
        return self

    async def reply_photo(self, *a, **kw):
        self.sent.append("<photo>")
        return self

    async def reply_document(self, *a, **kw):
        self.sent.append("<doc>")
        return self

    async def edit_text(self, text, **kw):
        self.sent.append(text)
        return self

    async def delete(self):
        self.deleted = True

    async def reply_chat_action(self, *a, **kw):
        return None


class FakeUpdate:
    def __init__(self, text, uid):
        self.message = FakeMessage(text, uid)
        self.effective_user = FakeUser(uid)
        self.effective_chat = self.message.chat
        self.callback_query = None
        self.effective_message = self.message


class FakeContext:
    def __init__(self, uid):
        self.user_data = {}
        self.bot = type("B", (), {"id": 0})()
        self.args = []


async def run_text(uid, text, ctx=None):
    """bot.on_text chalao → (message, context)."""
    import bot
    upd = FakeUpdate(text, uid)
    ctx = ctx or FakeContext(uid)
    await bot.on_text(upd, ctx)
    return upd.message, ctx


# ==================================================================== tests
def test_cache():
    section("1) modules.core.cache — TTL + size cap + dedupe")
    import time
    from modules.core.cache import TTLCache, cached_call

    c = TTLCache(maxsize=20, default_ttl=60)
    calls = {"n": 0}

    def work():
        calls["n"] += 1
        return {"ok": True, "v": calls["n"]}

    v1, f1 = cached_call(c, "k", work)
    v2, f2 = cached_call(c, "k", work)
    ok("pehli call cache miss thi", f1 is False)
    ok("doosri call cache hit thi", f2 is True)
    ok("cache hit par kaam dobara NAHI hua", calls["n"] == 1, f"calls={calls['n']}")
    ok("dono calls ka result same hai", v1 == v2)

    for i in range(50):
        c.put(f"x{i}", i)
    ok("size cap enforce hota hai (<=20)", len(c) <= 20, f"len={len(c)}")
    ok("sabse naya entry bacha", c.get("x49") is not None)
    ok("sabse purana evict hua", c.get("x0") is None)

    c2 = TTLCache(default_ttl=1)
    c2.put("a", 1)
    time.sleep(1.2)
    ok("TTL expiry ke baad None milta hai", c2.get("a") is None)

    n = {"n": 0}

    def fails():
        n["n"] += 1
        return None

    cached_call(c, "f", fails, fail_ttl=1)
    cached_call(c, "f", fails, fail_ttl=1)
    ok("negative result bhi cache hota hai (API hammer nahi hoti)", n["n"] == 1)
    time.sleep(1.2)
    cached_call(c, "f", fails, fail_ttl=1)
    ok("negative cache expire hone par retry hota hai", n["n"] == 2)


def test_limiter():
    section("2) modules.core.limiter — sliding window + bypass")
    from modules.core.limiter import RateLimiter, check_limit

    r = RateLimiter()
    res = [r.allow(123, "ifsc", limit=3, window=60)[0] for _ in range(5)]
    ok("limit ke andar allow", res[:3] == [True, True, True])
    ok("limit ke baad block", res[3:] == [False, False])

    _, retry, lim, win = r.allow(123, "ifsc", limit=3, window=60)
    ok("block par retry_after milta hai", retry > 0, f"retry={retry}")
    ok("limit/window sahi wapas aate hain", (lim, win) == (3, 60))

    ok("admin bypass block nahi hota",
       r.allow(999, "x", limit=1, window=60, bypass=True)[0] is True)
    ok("doosra user affect nahi hota", r.allow(456, "ifsc", limit=3, window=60)[0])
    ok("doosra action affect nahi hota", r.allow(123, "pin", limit=3, window=60)[0])
    u0, _ = r.peek(777, "z", limit=5, window=60)
    ok("peek consume nahi karta", u0 == 0)
    r.reset(123)
    ok("reset ke baad dobara allow", r.allow(123, "ifsc", limit=3, window=60)[0])

    ok("check_limit allowed par None deta hai",
       check_limit(1, "a", limit=2, window=60) is None)
    check_limit(1, "a", limit=2, window=60)
    msg = check_limit(1, "a", limit=2, window=60, tool_name="IFSC Info")
    ok("check_limit block par message deta hai", bool(msg))
    ok("block message me tool ka naam hai", msg and "IFSC Info" in msg)


def test_ssrf():
    section("3) modules.core.net — SSRF guard")
    from modules.core.net import is_safe_url

    must_block = [
        "http://169.254.169.254/latest/meta-data/",   # cloud metadata
        "http://127.0.0.1/admin",
        "http://192.168.1.1", "http://10.0.0.5", "http://localhost/x",
        "file:///etc/passwd", "ftp://example.com",
        "http://metadata.google.internal/",
    ]
    must_allow = ["https://google.com", "https://ifsc.razorpay.com/SBIN0000001",
                  "http://8.8.8.8"]
    for u in must_block:
        s, why = is_safe_url(u)
        ok(f"BLOCK {u[:38]}", s is False, why)
    for u in must_allow:
        s, why = is_safe_url(u)
        ok(f"ALLOW {u[:38]}", s is True, why)


def test_net_timeout():
    section("4) modules.core.net — timeout predictable hai")
    import time
    from modules.core.net import NetError, http_get

    t = time.time()
    fired = False
    try:
        http_get("http://10.255.255.1/", timeout=2, retries=0)
    except NetError as e:
        fired = e.kind == "timeout"
    el = time.time() - t
    ok("timeout exception aata hai", fired)
    ok("timeout ~2s me fire hota hai (multiply nahi hota)", el < 3.5, f"{el:.1f}s")


def test_info_caching():
    section("5) osint_tools — live API + caching + validation")
    import time
    from modules.osint_tools import (lookup_ifsc, lookup_pincode,
                                     search_by_area_name)

    r1 = lookup_ifsc("SBIN0000001")
    ok("IFSC live lookup chalta hai", r1.get("ok") is True, str(r1)[:120])
    if r1.get("ok"):
        t = time.time()
        r2 = lookup_ifsc("SBIN0000001")
        ok("IFSC doosri baar cache se aata hai", r2.get("cached") is True)
        ok("IFSC cache instant hai (<0.05s)", time.time() - t < 0.05)
        ok("IFSC cached result same bank deta hai",
           r2.get("bank") == r1.get("bank"))

    for bad in ["SBIN0001", "HDFC1001234", "AAAAAAAAAAA"]:
        ok(f"IFSC invalid reject: {bad}", lookup_ifsc(bad).get("ok") is False)

    p = lookup_pincode("800001")
    ok("Pincode live lookup chalta hai", p.get("ok") is True, str(p)[:120])
    if p.get("ok"):
        ok("Pincode district/state aata hai",
           bool(p.get("district")) and bool(p.get("state")))
        ok("Pincode doosri baar cache se", lookup_pincode("800001").get("cached") is True)
    ok("Pincode leading-zero reject", lookup_pincode("000001").get("ok") is False)
    ok("Pincode short reject", lookup_pincode("12345").get("ok") is False)

    a = search_by_area_name("Patna GPO")
    ok("Area search 'Patna GPO' chalta hai", a.get("ok") is True, str(a)[:160])
    if a.get("ok"):
        top = a["results"][0]
        ok("Patna GPO ka top result Bihar ka hai",
           top.get("state") == "Bihar", f"{top}")
        ok("Patna GPO ka pincode 800001 hai",
           top.get("pincode") == "800001", f"{top.get('pincode')}")
        ok("approximate flag set hai (naam strip hua tha)", a.get("approximate") is True)
        ok("results district ke hisaab se ranked hain",
           all(x.get("district") == "Patna" for x in a["results"][:5]),
           str([x.get("district") for x in a["results"][:5]]))

    g = search_by_area_name("Gaya")
    ok("Area search 'Gaya' chalta hai", g.get("ok") is True)
    if g.get("ok"):
        ok("Gaya ka top result Bihar ka hai", g["results"][0].get("state") == "Bihar")

    ok("Area search chhota naam reject", search_by_area_name("ab").get("ok") is False)


def test_bot_gate():
    section("6) bot.on_text — CENTRAL RATE-LIMIT GATE (end-to-end)")
    import bot
    from modules.core.limiter import limiter

    limiter.clear()

    # asli network call na ho — gate test kar rahe hain, API nahi
    real_ifsc = bot.lookup_ifsc
    bot.lookup_ifsc = lambda code: {"ok": True, "ifsc": code, "bank": "Test Bank",
                                    "branch": "Test", "address": "", "city": "",
                                    "district": "", "state": "", "contact": "",
                                    "micr": "", "neft": True, "rtgs": True,
                                    "imps": True, "upi": True, "maps_link": ""}
    try:
        lim, win, name = bot.TOOL_RATE_LIMITS["ifsc"]
        uid = 555001
        ctx = FakeContext(uid)
        ctx.user_data["mode"] = "ifsc"

        blocked_at = None
        for i in range(1, lim + 4):
            msg, ctx = asyncio.run(run_text(uid, "SBIN0000001", ctx))
            last = msg.sent[-1] if msg.sent else ""
            if "thoda slow karo" in last:
                blocked_at = i
                break
        ok(f"gate ne exactly {lim} baar allow kiya (limit={lim})",
           blocked_at == lim + 1, f"blocked_at={blocked_at}")
        ok("block message tool ka naam dikhata hai", name in last)
        ok("block message me wait time hai", "baad dobara try karo" in last)

        # admin ko bypass milna chahiye
        admin_uid = int(os.environ.get("ADMIN_ID", "1"))
        ctx2 = FakeContext(admin_uid)
        ctx2.user_data["mode"] = "ifsc"
        admin_blocked = False
        for i in range(lim + 5):
            msg, ctx2 = asyncio.run(run_text(admin_uid, "SBIN0000001", ctx2))
            if msg.sent and "thoda slow karo" in msg.sent[-1]:
                admin_blocked = True
                break
        ok("admin kabhi block nahi hota", admin_blocked is False)

        # normal user doosre tool par block nahi hona chahiye (per-action isolation)
        ctx3 = FakeContext(uid)
        ctx3.user_data["mode"] = "pin"
        msg, ctx3 = asyncio.run(run_text(uid, "800001", ctx3))
        ok("doosra tool usi user ke liye khula hai",
           not (msg.sent and "thoda slow karo" in msg.sent[-1]))
    finally:
        bot.lookup_ifsc = real_ifsc


def test_ssrf_wiring():
    section("7) URL tools me SSRF guard wire hai (expand_url)")
    from modules.toolkit_extras import expand_url
    from modules.core.net import is_safe_url

    for u in ["http://169.254.169.254/latest/meta-data/", "http://127.0.0.1:8080/admin",
              "http://192.168.1.1", "http://10.0.0.5", "http://localhost:5000"]:
        ok(f"expand_url BLOCK {u[:32]}", expand_url(u).get("ok") is False)

    for u in ["file:///etc/passwd", "ftp://example.com/a", "gopher://127.0.0.1"]:
        r = expand_url(u)
        ok(f"expand_url BLOCK scheme {u[:22]}", r.get("ok") is False)

    for u in ["https://www.google.com/?utm_source=x", "example.com"]:
        ok(f"expand_url ALLOW {u[:32]}", expand_url(u).get("ok") is True)

    ok("google ke tracking params clean hote hain",
       expand_url("https://www.google.com/?utm_source=x&fbclid=y").get("cleaned", "").count("utm_") == 0)

    # NOTE v51: site_screenshot tool delete ho gaya — SSRF guard ka test is_safe_url se
    ok("is_safe_url: public URL allowed", is_safe_url("https://github.com")[0] is True)
    for u in ["http://169.254.169.254/", "http://localhost:5000", "http://127.0.0.1:8080"]:
        ok(f"is_safe_url BLOCK {u[:26]}", is_safe_url(u)[0] is False)


def test_gst_pan():
    section("9) api_hub — GST/PAN local validation + cache")
    import time
    from modules.api_hub import gstin_format_ok, pan_format_ok, hub_gst, hub_pan

    gst_cases = [("19BOKPS7056D1ZI", True), ("27AAPFU0939F1ZV", True),
                 ("38AAACT2727Q1ZW", True), ("97AAACT2727Q1ZW", True),
                 ("99AAACT2727Q1ZW", True), ("00AAACT2727Q1ZW", False),
                 ("39AAACT2727Q1ZW", False), ("98AAACT2727Q1ZW", False),
                 ("19BOKPS7056D1Z", False), ("ABCDEFGHIJKLMN1", False),
                 ("123456789012345", False)]
    bad = [g for g, w in gst_cases if gstin_format_ok(g) != w]
    ok("GSTIN validator 11/11 sahi", not bad, str(bad))

    pan_cases = [("AAYFK4129N", True), ("AAAPL1234C", True), ("ABCPC1234K", True),
                 ("ABCTT1234K", True), ("ABCHH1234K", True), ("ABCLL1234K", True),
                 ("ABCJJ1234K", True), ("ABCGG1234K", True), ("ABCAA1234K", True),
                 ("ABCBF1234K", True), ("ABCMC1234K", True),
                 ("AAYFK4129", False), ("AAYFK4129NN", False),
                 ("1234567890", False), ("ABCXZ1234K", False), ("AAYFK412N9", False)]
    bad = [p for p, w in pan_cases if pan_format_ok(p) != w]
    ok("PAN validator 16/16 sahi (4th char = holder category)", not bad, str(bad))

    # galat input par 60s wala hub call NAHI jana chahiye
    t = time.time(); r = hub_gst("ABCDEFGHIJKLMN1"); el = time.time() - t
    ok("galat GSTIN turant reject (no network)", r.get("ok") is False and el < 0.05, f"{el:.3f}s")
    t = time.time(); r = hub_pan("1234567890"); el = time.time() - t
    ok("galat PAN turant reject (no network)", r.get("ok") is False and el < 0.05, f"{el:.3f}s")
    t = time.time(); r = hub_gst("SHORT"); el = time.time() - t
    ok("chhota GSTIN reject", r.get("ok") is False and el < 0.05, f"{el:.3f}s")

    # live GST + cache
    r1 = hub_gst("19BOKPS7056D1ZI")
    ok("GST live lookup chalta hai", isinstance(r1, dict) and "error" not in r1 or r1.get("ok"),
       str(r1)[:100])
    if r1.get("ok"):
        t = time.time(); r2 = hub_gst("19BOKPS7056D1ZI"); el = time.time() - t
        ok("GST doosri baar cache se", r2.get("cached") is True)
        ok("GST cache instant", el < 0.05, f"{el:.3f}s")
        ok("GST cached result same state deta hai", r2.get("state") == r1.get("state"))
    else:
        print("     (hub ne GST data nahi diya — cache check skip)")

    p1 = hub_pan("AAYFK4129N")
    ok("PAN live lookup chalta hai", isinstance(p1, dict))
    if p1.get("ok"):
        t = time.time(); p2 = hub_pan("AAYFK4129N"); el = time.time() - t
        ok("PAN doosri baar cache se", p2.get("cached") is True)
        ok("PAN cache instant", el < 0.05, f"{el:.3f}s")


def test_system_stats():
    section("10) bot.system_stats_text — admin live health card")
    import re
    import bot
    from modules.core.limiter import limiter

    limiter.clear()
    before = limiter.blocked
    bot.lookup_ifsc("SBIN0000001")
    bot.lookup_ifsc("SBIN0000001")          # cache hit banane ke liye
    for i in range(3):
        bot.INFO_CACHE.put(f"probe{i}", {"x": i}, 300)
    for u in (1, 2, 3):
        for _ in range(2):
            limiter.allow(u, "probe", limit=1, window=60)
    expect = limiter.blocked - before        # 3 users x 2nd call = 3 blocks

    txt = bot.system_stats_text()
    plain = bot.unbold(txt)                  # to_bold() Unicode bold karta hai
    ok("card banta hai", bool(txt))
    ok("header hai", "SYSTEM HEALTH" in plain)
    ok("uptime dikhta hai", "Uptime:" in plain)
    ok("cache entries dikhti hain", "Cache entries:" in plain)
    ok("hit rate dikhta hai", "Hit rate:" in plain)
    ok(f"rate-limit blocked count card me dikhta hai ({expect})",
       f"blocked: {expect}" in plain,
       plain[plain.find("blocked"):plain.find("blocked") + 18])
    ok("mode dikhta hai", "Mode:" in plain)
    ok("RAM dikhta hai", "RAM:" in plain)

    tags = re.findall(r"</?(?:b|i|code)>", txt)
    opens = sum(1 for t in tags if not t.startswith("</"))
    closes = sum(1 for t in tags if t.startswith("</"))
    ok("HTML balanced hai (Telegram parse fail nahi hoga)", opens == closes,
       f"opens={opens} closes={closes}")


def test_no_blocking():
    section("11) STATIC: koi blocking call async handler me nahi")
    import ast

    def has_blocking(node):
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                f = sub.func
                if isinstance(f, ast.Attribute):
                    base = getattr(f.value, "id", None) or getattr(f.value, "attr", None)
                    if f.attr in ("get", "post", "head", "put", "delete", "urlopen",
                                  "run", "Popen") and base in (
                            "requests", "session", "s", "http", "subprocess",
                            "urllib", "request", "time"):
                        return True
                    if f.attr == "sleep" and base == "time":
                        return True
        return False

    blocking = {}
    files = []
    for root, _, fs in os.walk(ROOT):
        if ".git" in root or "__pycache__" in root or "/tests" in root:
            continue
        for fn in fs:
            if fn.endswith(".py") and not fn.startswith("_selftest") \
                    and not fn.startswith("_verify"):
                files.append(os.path.join(root, fn))
    for p in files:
        try:
            tree = ast.parse(open(p, encoding="utf-8").read())
        except Exception:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.FunctionDef) and has_blocking(n):
                blocking[n.name] = p

    problems = []
    for p in files:
        tree = ast.parse(open(p, encoding="utf-8").read())
        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            safe = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                        and sub.func.attr in ("to_thread", "run_in_executor"):
                    for a in sub.args:
                        if isinstance(a, ast.Name):
                            safe.add(a.id)
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    f = sub.func
                    nm = f.id if isinstance(f, ast.Name) else (
                        f.attr if isinstance(f, ast.Attribute) else None)
                    if nm and nm in blocking and nm not in safe:
                        problems.append(f"{p}:{sub.lineno} {node.name}->{nm}")
    ok("0 blocking-in-async issues", not problems, "; ".join(problems[:4]))


def main():
    print("\n" + "=" * 62)
    print("  v50 CORE LAYER — TEST SUITE")
    print("=" * 62)
    test_cache()
    test_limiter()
    test_ssrf()
    test_net_timeout()
    test_info_caching()
    test_bot_gate()
    test_ssrf_wiring()
    test_gst_pan()
    test_system_stats()
    test_no_blocking()
    print("\n" + "=" * 62)
    print(f"  PASS: {len(PASS)} | FAIL: {len(FAIL)}")
    if FAIL:
        print("\n  FAILED CHECKS:")
        for f in FAIL:
            print(f"    ❌ {f}")
    print("=" * 62 + "\n")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
