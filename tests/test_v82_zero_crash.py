# -*- coding: utf-8 -*-
"""
v82 SELFTEST — ZERO-CRASH PRO (v82.0 release ke liye).

Ye file 6 asli production problems lock karti hai:
  A. "SEND FAILED / Message text is empty" — free mode me credit note khaali hota hai;
     ab khaali text kabhi Telegram ko nahi jaata, aur media ke baad ka error user ko
     galat "SEND FAILED" nahi dikhata.
  B. "Event loop is closed" (webhook -> polling switch) — ab saaf process restart.
  C. Terabox "DIRECT LINK NOT FOUND" — jsToken + logid flow, file info, web fallback buttons,
     aur resolve sync (bot ko block) nahi karta.
  D. Instagram ?img_index=N — carousel ka sahi item.
  E. RAM safety — 512 MB plan par media RAM-cache cap (owner ka v81.2 trim/idle-restart alag hai).
  F. TikTok photo post fallback + bot prompts ka same rehna.

Network ki zaroorat nahi — sab fake session/monkeypatch se.
"""
import asyncio
import os
import re
import sys
import urllib.parse

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
os.environ.setdefault("DB_PATH", os.path.join(_HERE, "_v92_tmp.db"))

PASS = 0
FAIL = 0
FAILS = []


def check(label, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        FAILS.append(label)
        print(f"   ❌ FAIL: {label} {extra}")


def read(rel):
    with open(os.path.join(_ROOT, rel), encoding="utf-8") as f:
        return f.read()


print("v82 SELFTEST — ZERO-CRASH PRO (v82.0)")

# ---------------------------------------------------------------- static checks
BOT_SRC = read("bot.py")
CLOUD_SRC = read("modules/cloud_tools.py")
MEDIA_SRC = read("modules/media_downloader.py")

check("A1 koi bhi raw reply_text(spend_credit_msg( nahi bacha",
      not re.search(r"\.reply_text\(\s*spend_credit_msg\(", BOT_SRC))
check("A2 spend note sites _reply_nonempty se ja rahe hain (>=20)",
      len(re.findall(r"_reply_nonempty\(", BOT_SRC)) >= 21)   # 1 def + 20+ call sites
check("C1 Terabox sync call bot.py me thread me hai (to_thread)",
      "asyncio.to_thread(resolve_cloud_url, raw_text)" in BOT_SRC
      and "res = resolve_cloud_url(raw_text)" not in BOT_SRC)
check("B1 webhook fail par polling same loop me nahi, saaf restart",
      "_hard_restart(f\"webhook fail" in BOT_SRC)

# ---------------------------------------------------------------- import bot
import bot as B  # noqa: E402

# ---------------------------------------------------------------- A. empty-text
if B.ALL_FREE:
    check("A4 ALL_FREE par note khaali (wahi case jo 'SEND FAILED' deta tha)",
          B.spend_credit_msg(1, "insta_dl") == "")


class _FakeMsg:
    def __init__(self):
        self.sent = []

    async def reply_text(self, text, **kw):
        self.sent.append(text)
        return self


async def _run_empty_checks():
    m = _FakeMsg()
    r1 = await B._reply_nonempty(m, "")
    r2 = await B._reply_nonempty(m, "   \n ")
    r3 = await B._reply_nonempty(m, None)
    r4 = await B._reply_nonempty(m, "✅ ok", parse_mode="HTML")
    return m.sent, r1, r2, r3, r4


sent, r1, r2, r3, r4 = asyncio.run(_run_empty_checks())
check("A5 khaali text Telegram ko nahi gaya", sent == ["✅ ok"], f"sent={sent}")
check("A6 khaali text par None return", r1 is None and r2 is None and r3 is None)
check("A7 normal text par message return", r4 is not None)


class _FakeEffMsg:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text, **kw):
        self.replies.append(text)


class _FakeUpdate:
    def __init__(self):
        self.effective_message = _FakeEffMsg()


class _FakeCtx:
    def __init__(self, err):
        self.error = err


async def _run_on_error(err):
    up = _FakeUpdate()
    await B.on_error(up, _FakeCtx(err))
    return up.effective_message.replies


try:
    from telegram.error import BadRequest
    rep = asyncio.run(_run_on_error(BadRequest("Message text is empty")))
    check("A8 on_error: 'Message text is empty' par user ko error nahi", rep == [], f"rep={rep}")
except Exception as _e:  # noqa: BLE001
    check("A8 on_error skip", False, str(_e)[:80])

# ---------------------------------------------------------------- D. img_index
check("D1 img_index=3 parse", B._parse_img_index(
    "https://www.instagram.com/p/DeJgDvDIFg2/?img_index=3&stkn=abc") == 3)
check("D2 img_index na ho to None", B._parse_img_index("https://instagram.com/p/XYZ/") is None)
check("D3 img_index=0 ya bekaar value None", B._parse_img_index("x?img_index=0") is None
      and B._parse_img_index("x?img_index=abc") is None)

# ---------------------------------------------------------------- B. hard restart
_exec_calls = []
_real_execve = os.execve
_real_sleep = B.time.sleep


def _fake_execve(path, argv, env):
    _exec_calls.append((path, argv, dict(env)))


_real_argv0 = sys.argv[0] if sys.argv else ""
os.execve = _fake_execve
B.time.sleep = lambda *_a, **_k: None
try:
    os.environ.pop("UDB_LAST_RESTART", None)
    sys.argv[0] = os.path.join(_ROOT, "bot.py")      # production jaisa: `python bot.py`
    B._hard_restart("test reason", delay=0.0, extra_env={"UDB_FORCE_POLLING": "1"})
finally:
    sys.argv[0] = _real_argv0
    os.execve = _real_execve
    B.time.sleep = _real_sleep
# tests/import ke case me exec NAHI hona chahiye (test runner ko replace na ho)
_exec_calls_none = []
os.execve = lambda *a, **k: _exec_calls_none.append(a)
try:
    B._hard_restart("import-case", delay=0.0)
finally:
    os.execve = _real_execve
check("B6 test/import context me exec skip (runner safe)", _exec_calls_none == [])
check("B2 hard restart execve call hua", len(_exec_calls) == 1)
if _exec_calls:
    _p, _argv, _env = _exec_calls[0]
    check("B3 restart me bot.py ka path", _argv and _argv[-1].endswith("bot.py"), str(_argv))
    check("B4 restart env me FORCE_POLLING=1", _env.get("UDB_FORCE_POLLING") == "1")
    check("B5 restart counter badha", _env.get("UDB_RESTARTS") == "1")


# ---------------------------------------------------------------- E. RAM safety
import modules.media_downloader as MD  # noqa: E402
check("E3 RAM media cache <= 32 MB", MD._DL_MEM_MAX_BYTES <= 32 * 1024 * 1024)
MD._DL_MEM.clear()
MD._mem_put("https://example.com/big.mp4", b"x" * (13 * 1024 * 1024), {"t": 1}, "ig")
check("E4 13 MB file RAM cache me nahi jaati", MD._mem_get("https://example.com/big.mp4", "ig") is None)
MD._mem_put("https://example.com/small.mp4", b"x" * (1024 * 1024), {"t": 1}, "ig")
check("E5 1 MB file RAM cache me jaati hai", MD._mem_get("https://example.com/small.mp4", "ig") is not None)
import modules.core.guard as G  # noqa: E402
_fm = G.free_memory(aggressive=False)
check("E6 free_memory dict lautata hai", isinstance(_fm, dict) and "after_mb" in _fm)

# ---------------------------------------------------------------- C. Terabox token flow
import modules.cloud_tools as CT  # noqa: E402

check("C2 surl parse (1 prefix hata ke)",
      CT._extract_surl("https://1024tera.com/s/1YfyQ2DSJWSE8mbuw3QMxbA") == "YfyQ2DSJWSE8mbuw3QMxbA")

_fake_html = ('<html><script>window.x="' + urllib.parse.quote(
    'jsToken = a};fn("5E28A0D5CE0DB59A51EAD6E89F3CDF68ABCDEF0123456789ABCDEF0123456789");'
    'logid=8818620661677395411&x=1') + '"</script></html>')


class _Resp:
    def __init__(self, text):
        self.text = text

    def json(self):
        import json as _j
        return _j.loads(self.text)


class _FakeSession:
    def __init__(self, page_html, list_json):
        self.page_html = page_html
        self.list_json = list_json
        self.calls = []
        self.cookies = type("C", (), {"set": lambda *a, **k: None})()

    def get(self, url, params=None, headers=None, timeout=None, allow_redirects=None):
        self.calls.append((url, dict(params or {})))
        if "share/list" in url:
            return _Resp(self.list_json)
        return _Resp(self.page_html)


_fs = _FakeSession(_fake_html, "{}")
_js, _lg = CT._tb_page_tokens(_fs, "YfyQ2DSJWSE8mbuw3QMxbA")
check("C3 jsToken page HTML se mila", _js == "5E28A0D5CE0DB59A51EAD6E89F3CDF68ABCDEF0123456789ABCDEF0123456789",
      str(_js)[:20])
check("C4 logid page HTML se mila", _lg == "8818620661677395411", str(_lg))

_list_ok = ('{"errno":0,"list":[{"server_filename":"clip.mp4","size":44829267,"isdir":0,'
            '"fs_id":1,"path":"/clip.mp4"}]}')
_fs2 = _FakeSession(_fake_html, _list_ok)
CT._tb_share_list(_fs2, "YfyQ2DSJWSE8mbuw3QMxbA", _js, _lg, "/")
_lc = [c for c in _fs2.calls if "share/list" in c[0]]
_p = _lc[0][1] if _lc else {}
check("C5 share/list me shorturl bina '1' ke", _p.get("shorturl") == "YfyQ2DSJWSE8mbuw3QMxbA")
check("C6 share/list me jsToken + dplogid", _p.get("jsToken") == _js and _p.get("dplogid") == _lg)
check("C7 share/list me app_id=250528 + channel=dubox",
      _p.get("app_id") == "250528" and _p.get("channel") == "dubox")

# guest listing: dlink nahi, par file info stash ho
CT._TB_INFO_STASH.clear()
_orig_pool = CT.pooled_session
CT.pooled_session = lambda *a, **k: _FakeSession(_fake_html, _list_ok)
try:
    _files, _eng = CT._tb_guest_list("https://1024tera.com/s/1YfyQ2DSJWSE8mbuw3QMxbA")
finally:
    CT.pooled_session = _orig_pool
check("C8 guest listing bina dlink ke files=None", _files is None)
_stash = CT._TB_INFO_STASH.get("YfyQ2DSJWSE8mbuw3QMxbA") or []
check("C9 file info stash hui (naam + size)",
      bool(_stash) and _stash[0]["name"] == "clip.mp4" and "MB" in _stash[0]["size"], str(_stash))

# resolve_terabox: sab engines fail, file info + fallback buttons aate hain
_engine_names = ["_tb_hub", "_tb_robin", "_tb_hnn", "_tb_qtcloud", "_tb_surl_api", "_tb_custom_provider",
                 "_tb_ndus", "_tb_guest_list"]
_saved = {n: getattr(CT, n) for n in _engine_names}
for n in _engine_names:
    setattr(CT, n, (lambda *_a, **_k: (None, None)))
try:
    _res = CT.resolve_terabox("https://1024tera.com/s/1YfyQ2DSJWSE8mbuw3QMxbA")
finally:
    for n, fn in _saved.items():
        setattr(CT, n, fn)
check("C10 sab fail par ok=False", _res.get("ok") is False)
check("C11 error me file ka naam + size", "clip.mp4" in _res.get("error", "") and "MB" in _res.get("error", ""))
check("C12 fallback links + share page surl", len(_res.get("fallback_links") or []) >= 1
      and _res.get("surl") == "YfyQ2DSJWSE8mbuw3QMxbA")
# v93: headline wording badla — ab jhooth nahi bolta. Jaanch me pata chala listing
# chalti hai, sirf DOWNLOAD step CAPTCHA ("need verify_v2") se lock hai.
check("C13 error headline clear hai (v93 wording)",
      "Direct download link nahi mila" in _res.get("error", ""), _res.get("error", "")[:80])
check("C13b v93 report card bhi laut-ta hai",
      "clip.mp4" in str(_res.get("report") or ""), str(_res.get("report"))[:80])

# ---------------------------------------------------------------- F. TikTok photo + prompts
check("F1 TikTok photo fallback media_downloader me hai",
      '"/photo/" in url.lower()' in MEDIA_SRC and "_og_scrape(url, \"photo\"" in MEDIA_SRC)
check("F2 Terabox web fallback list 1+ entry", len(CT.TERABOX_WEB_FALLBACKS) >= 1)

print(f"   v82 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
if FAIL:
    print("   FAILED:", ", ".join(FAILS))
    sys.exit(1)
