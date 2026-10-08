# -*- coding: utf-8 -*-
"""
v89 SELFTEST — "🐘 BADE FILE (150MB) + 📥 INSTA REEL FIX + 🧹 3 TOOLS HATE"
===========================================================================
Aapke 3 screenshots se 3 asli bug napne gaye the; ye file un teeno ko
regression-lock karti hai (sab OFFLINE — koi network/API nahi):

  A. 🐘 BIGFILE (modules/core/bigfile.py) — 20 MB / 50 MB Bot API deewar
     Telegram ka rule: bot 20MB se badi file LE nahi sakta aur 50MB se badi
     DE nahi sakta. Ilaja = MTProto (same bot token, Telegram ka apna API).
     TG_API_ID/TG_API_HASH na ho to sab kuch PEHLE jaisa (safe deploy) —
     isliye ye test "disabled" state bhi verify karta hai.
     + MappedFile: 150MB file RAM me nahi aati (mmap) — Render ke 512MB par
       OOM (hamara purana crash) dobara na ho.

  B. 💬 CHAT X-RAY badi file — 66.5MB zip ab DISK se stream hoti hai
     (pehle 20MB gate par hi "bigger than 20MB" kehke wapas bhej deta tha).

  C. 📥 INSTA REEL → PHOTO bug (aapka link: /reel/Db8Kg5qyVYC/?stkn=...)
     v77 me `_og_scrape` ek HTML GET me jeet jaata tha aur `og:image`
     (reel ka COVER) bhej deta tha — video engines 10-25s le rahe the.
     Ab: referee (`_ig_kind_ok`) reel ke liye photo KABHI qabool nahi karta,
     + `_og_scrape(allow_photo=False)`, + 4th engine `_ig_embed`,
     + budget 22s → 26s (aapne 33s tak progress dekha tha = deadline se bahar).

  D. 🧹 3 TOOLS HATE: 🎁 REFER & EARN · ❓ HELP / TUTORIAL · 📤 BULK MODE (EXCEL)
     + saare tutorial videos repo se permanent delete (git index me 0 .mp4).

  E. 📨 Progress message flood: har 5 second NAYA message (10s/16s/22s/27s/33s)
     -> ab ek hi status card EDIT hota hai; aur status card delete ho gaya ho to
     bhi exception crash-shield tak nahi jaata (pehle '⚠️ Ye kaam poora nahi ho
     paya' isiliye aata tha).
"""
import asyncio
import re
import io
import os
import sys
import zipfile
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
os.environ.setdefault("DB_PATH", os.path.join(_HERE, "_v89_tmp.db"))

PASS = 0
FAIL = 0
FAILS = []


def check(label, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        FAILS.append(f"{label}{(' — ' + extra) if extra else ''}")
        print(f"  ❌ {label}{(' — ' + extra) if extra else ''}")


def section(t):
    print(f"\n{'=' * 62}\n{t}\n{'=' * 62}")


# ======================================================================
section("A. 🐘 BIGFILE — caps, safe-default, MappedFile")
# ======================================================================
from modules.core import bigfile as BF                      # noqa: E402

check("BOT API ki hadd sahi likhi hai (in 20 / out 48)",
      BF.BOT_API_IN_MB == 20 and BF.BOT_API_OUT_MB == 48)
check("MAX_FILE_MB default 150 (aapki demand)", BF.MAX_IN_MB >= 150, str(BF.MAX_IN_MB))
check("MAX_SEND_MB default 150", BF.MAX_OUT_MB >= 150, str(BF.MAX_OUT_MB))
check("env na ho to MTProto OFF (deploy safe — purana behaviour)",
      BF.enabled() is False or BF.status().get("ready") is True, str(BF.status())[:70])
_st = BF.status()
# enabled() har context me safe ho (bot ke andar ye sync + thread dono se call
# hota hai; Python 3.13 me asyncio.get_event_loop() bina loop par RuntimeError
# deta hai — ek baar ye galti ho chuki hai, isliye lock)
import threading                                              # noqa: E402
_res = {}


def _thread_probe():
    try:
        _res["ok"] = BF.enabled()
    except BaseException as e:                                  # noqa: BLE001
        _res["err"] = f"{type(e).__name__}: {e}"


_t = threading.Thread(target=_thread_probe)
_t.start(); _t.join(10)
check("enabled() bina event-loop wale thread par bhi exception nahi deta",
      "err" not in _res, _res.get("err", ""))
_bfsrc = open(os.path.join(_ROOT, "modules", "core", "bigfile.py"),
              encoding="utf-8").read().split("def _started")[0]
_bfcode = "\n".join(l for l in _bfsrc.splitlines() if not l.strip().startswith("#"))
check("_client_ready khud event loop na mange (py3.12+ me ye RuntimeError deta hai)",
      "get_event_loop" not in _bfcode and "get_running_loop" not in _bfcode)
check("bigfile sync context se call hone par bhi clean rahe (no await-only API)",
      "asyncio.run" not in _bfcode)
check("status() reason deta hai (admin ko dikhe kya missing hai)",
      "TG_API_ID" in str(_st.get("note")) or _st.get("ready") is True, str(_st)[:90])
check("cap_in_mb() = 20 jab MTProto off, warna 150+",
      (BF.cap_in_mb() == 20) if not _st.get("ready") else (BF.cap_in_mb() >= 150))
check("dl_limit_mb(48) = 48 off / 150 on",
      (BF.dl_limit_mb(48) == 48) if not _st.get("ready") else (BF.dl_limit_mb(48) >= 150))

# MappedFile — badi file RAM me na aaye
_fd, _pth = tempfile.mkstemp(suffix=".txt")
with os.fdopen(_fd, "wb") as fh:
    fh.write(b"L" * 3_000_000)
mf = BF.MappedFile(_pth, 3_000_000)
check("MappedFile len = file size", len(mf) == 3_000_000)
check("MappedFile.getvalue() memoryview deta hai (copy nahi)",
      isinstance(mf.getvalue(), memoryview) and len(mf.getvalue()) == 3_000_000)
check("io.BytesIO(mmap) chalta hai (tools ke liye zaroori)",
      len(io.BytesIO(mf.getvalue()).getvalue()) == 3_000_000)
check("MappedFile.read() pura data deta hai", mf.read()[:1] == b"L")
check("MappedFile.path milta hai (disk-first tools)", mf.path == _pth)
mf.close()
mf.unlink()
check("unlink() ke baad file gayi", not os.path.exists(_pth))

# caps ka parsing (kachra env = default, clamp)
_old = {k: os.environ.get(k) for k in ("MAX_FILE_MB", "MAX_SEND_MB", "MAX_TG_MB")}
try:
    os.environ["MAX_FILE_MB"] = ""
    check("_i('') -> default 150", BF._i("MAX_FILE_MB", 150, 20, 2000) == 150)
    os.environ["MAX_FILE_MB"] = "banana"
    check("_i('banana') -> default (crash nahi)", BF._i("MAX_FILE_MB", 150, 20, 2000) == 150)
    os.environ["MAX_FILE_MB"] = "999999"
    check("_i clamp hi 2000 (blast se bacha)", BF._i("MAX_FILE_MB", 150, 20, 2000) == 2000)
    os.environ["MAX_FILE_MB"] = "1"
    check("_i clamp lo 20 (0MB limit se bot mar jaata)", BF._i("MAX_FILE_MB", 150, 20, 2000) == 20)
finally:
    for k, v in _old.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

# MTProto off = download/send saaf mana karein, exception na dein
_r = asyncio.run(BF.download_to_path(object()))
check("download_to_path bina config par {ok:False, need_env} (crash nahi)",
      _r.get("ok") is False and "TG_API" in str(_r.get("reason")) + str(_r.get("need_env")),
      str(_r)[:90])
_r2 = asyncio.run(BF.mt_send(1, b"x" * 10, kind="video"))
check("mt_send bina config par {ok:False} (crash nahi)", _r2.get("ok") is False, str(_r2)[:70])
_r3 = asyncio.run(BF.send_via_mt(None, 1, b"x" * 100))
check("send_via_mt off -> skip", _r3.get("ok") is False, str(_r3)[:70])

# ======================================================================
section("B. 💬 CHAT X-RAY — 66MB zip DISK se stream (RAM nahi)")
# ======================================================================
from modules import chat_xray as CXR                         # noqa: E402

check("MAX_BYTES 12MB se upar gaya hai", CXR.MAX_BYTES >= 20 * 1048576,
      f"{CXR.MAX_BYTES // 1048576}MB")
_lines = "\n".join(f"08/10/2026, 13:0{i % 9} - Rahul: message number {i} hello bro"
                  for i in range(1, 60))
_fd, _txtp = tempfile.mkstemp(suffix=".txt")
with os.fdopen(_fd, "w", encoding="utf-8") as fh:
    fh.write(_lines)
_h, _e = CXR._head_from_path(_txtp, "chat.txt", 10 ** 6)
check("txt head-read: pura content aaya", _e == "" and b"message number 59" in _h, str(_e)[:60])
_h2, _ = CXR._head_from_path(_txtp, "chat.txt", 100)
check("txt head-read LIMIT ke saath (RAM safe)", len(_h2) == 100, str(len(_h2)))
os.remove(_txtp)

# zip: _head_from_path sirf .txt member padhta hai
_fd, _zipt = tempfile.mkstemp(suffix=".zip")
os.close(_fd)
with zipfile.ZipFile(_zipt, "w") as z:
    z.writestr("_media/ignored.txt", "junk")
    z.writestr("chat.txt", _lines)
    z.writestr("__MACOSX/ghost.txt", "junk")
_hz, _ez = CXR._head_from_path(_zipt, "chat.zip", 10 ** 6)
check("zip se chat.txt nikla (media/MACOSX nahi)",
      _ez == "" and b"message number 59" in _hz and b"junk" not in _hz, str(_ez)[:60])
res_disk = CXR.extract_text(BF.MappedFile(_zipt, os.path.getsize(_zipt)), "chat.zip")
check("extract_text MappedFile (.zip) se kaam karta hai",
      res_disk[1] == "" and "Rahul" in res_disk[0], str(res_disk[1])[:60])
res_zbytes = CXR.extract_text(open(_zipt, "rb").read(), "chat.zip")
check("extract_text purane bytes-raaste par bhi chalta hai (non-regression)",
      res_zbytes[1] == "" and "Rahul" in res_zbytes[0], str(res_zbytes[1])[:60])
os.remove(_zipt)

_fd, _bad = tempfile.mkstemp(suffix=".zip")
with os.fdopen(_fd, "wb") as fh:
    fh.write(b"not a zip at all")
check("kharab .zip -> saaf error (crash nahi)",
      "zip" in CXR.extract_text(b"not a zip at all", "x.zip")[1].lower(),
      CXR.extract_text(b"not a zip at all", "x.zip")[1][:60])
_r_big = CXR.extract_text(b"Q" * (CXR.MAX_BYTES + 10), "chat.txt")
check("bytes mode me MAX_BYTES se badi file -> saaf message (crash nahi)",
      _r_big[1] != "" and "MB" in _r_big[1], str(_r_big[1])[:70])
os.remove(_bad)
_res_analyze = CXR.analyze_file(_lines.encode(), "chat.txt")
check("analyze_file (bytes) aaj bhi report deta hai", _res_analyze.get("ok") is True,
      str(_res_analyze)[:70])

# ======================================================================
section("C. 📥 INSTA — reel par photo KABHI nahi (aapka link)")
# ======================================================================
from modules import media_downloader as MD                   # noqa: E402

_U = "https://www.instagram.com/reel/Db8Kg5qyVYC/?stkn=aGl2NThjdWtvcm1y"
check("?stkn= jaisa tracking param clean hota hai (URL split)",
      MD.classify_instagram_url(_U.split("?")[0]) == "reel")
check("_ig_code_of aapke link se shortcode nikalta hai",
      MD._ig_code_of(_U.split("?")[0]) == "Db8Kg5qyVYC")
for u, want in (("https://www.instagram.com/p/Cabc123/", "Cabc123"),
                ("https://instagram.com/tv/Cabc123", "Cabc123"),
                ("https://www.instagram.com/reels/Cabc123/?igshid=x", "Cabc123"),
                ("https://example.com/reel/xx", ""), ("", ""), (None, "")):
    check(f"_ig_code_of({str(u)[:34]}) -> {want or '(khaali)'}",
          MD._ig_code_of(u) == want)
_ok = MD._ig_kind_ok
check("REFEE: reel ke liye photo REJECT", _ok({"ok": True, "type": "photo"}, True) is False)
check("REFEE: reel ke liye video accept", _ok({"ok": True, "type": "video"}, True) is True)
check("REFEE: reel ke liye link accept (badi file)", _ok({"ok": True, "type": "link"}, True) is True)
check("REFEE: image post ke liye photo accept (wo asli photo hai)",
      _ok({"ok": True, "type": "photo"}, False) is True)
check("REFEE: carousel post accept", _ok({"ok": True, "type": "carousel"}, False) is True)
check("REFEE: ok=False / None kabhi accept nahi",
      _ok(None, True) is False and _ok({"ok": False}, True) is False)
check("REFEE: kachra type (int/None) accept nahi",
      _ok({"ok": True, "type": None}, True) is False
      and _ok({"ok": True, "type": 7}, True) is False)

import inspect                                               # noqa: E402
_sig = inspect.signature(MD._og_scrape)
check("_og_scrape me allow_photo param aaya", "allow_photo" in _sig.parameters)
check("_og_scrape ka default photo allow karta hai (post ke liye non-regression)",
      _sig.parameters["allow_photo"].default is True)
check("_ig_embed naya 4th engine maujood hai", callable(getattr(MD, "_ig_embed", None)))
_src_dl = inspect.getsource(MD.download_instagram_media)
for eng in ("_ig_parth", "_ig_ytdlp", "_ig_embed", "_og_scrape"):
    check(f"pipeline me engine {eng}", eng in _src_dl)
check("reel/video ka budget 26s (pehle 22s = aapka 33s wait fail)",
      "26.0 if want_video else 22.0" in _src_dl)
check("want_video flag category + URL dono se banta hai",
      'media_cat in ("reel", "video", "igtv", "story")' in _src_dl and '"/reel" in clean' in _src_dl)
check("cache ab bhi laga hai (2nd try TURANT)", '_mem_get(clean, "ig")' in _src_dl)
check("MAX_TG_MB ab dynamic hai (MTProto on = 96MB tak download)",
      "MAX_TG_MB = _tg_cap_mb()" in inspect.getsource(MD))
check("yt-dlp direct-link fallback ab bhi hai (badi file ka raasta)",
      callable(getattr(MD, "_ytdlp_direct_link", None)))

# ======================================================================
section("D. 🧹 3 TOOLS HATE + tutorial videos permanent delete")
# ======================================================================
import bot as B                                              # noqa: E402

_labels = [B.unbold(x).upper() for r in B.KB_BTNS for x in r]
for gone in ("REFER & EARN", "HELP / TUTORIAL", "BULK MODE"):
    check(f"menu me '{gone}' nahi hai", not any(gone in l for l in _labels))
check("MY ACCOUNT bacha hua hai (row sirf split hui)",
      any("MY ACCOUNT" in l for l in _labels))
check("SUPPORT / MADAD ab bhi hai", any("SUPPORT / MADAD" in l for l in _labels))
for dead in ("BULK MODE", "REFER & EARN", "HELP / TUTORIAL"):
    check(f"BTN_MODE_MAP se {dead} hataya", dead not in B.BTN_MODE_MAP)
with open(os.path.join(_ROOT, "bot.py"), encoding="utf-8") as fh:
    _bsrc = fh.read()
for dead_cmd in ('CommandHandler("refer"', 'CommandHandler(["bulk", "bulkexcel", "report"]',
                 'CommandHandler(["tutorial", "madad", "guide"]'):
    check(f"command band: {dead_cmd[:30]}…", dead_cmd not in _bsrc)
check("/help command ab bhi registered (standard cheez, hatayi nahi)",
      'CommandHandler("help"' in _bsrc)
_cmd_blk = _bsrc[_bsrc.index("commands = ["):_bsrc.index("await app.bot.set_my_commands")]
for dead in ("refer", "bulk", "tutorial", "madad", "guide"):
    check(f"Telegram ke / menu me dead command '{dead}' nahi",
          f'BotCommand("{dead}"' not in _cmd_blk)
check("start/menu/account/cancel/refresh commands zinda (kuch aur na tute)",
      all(f'BotCommand("{c}"' in _cmd_blk for c in ("start", "menu", "account", "cancel", "refresh")))
import subprocess                                            # noqa: E402
_git = subprocess.run(["git", "-C", _ROOT, "ls-files"], capture_output=True, text=True).stdout
check("git me koi .mp4 nahi (GitHub + Render se delete ho gaya)", ".mp4" not in _git)
check("tutorial_videos/ folder nahi hai", not os.path.isdir(os.path.join(_ROOT, "tutorial_videos")))
from modules import tutorial_hub as TH                       # noqa: E402
check("tutorial_hub: VIDEOS_REMOVED flag", TH.VIDEOS_REMOVED is True)
check("tutorial_hub: video map khali", TH.TUTORIAL_VIDEO_KEYS == {})
check("tutorial_hub: has_video hamesha False",
      not any(TH.has_video(a) for a in ("video_dl", "qr", "terabox", "cloner", "refer", "premium")))
check("tutorial_hub: video_urls khaali", TH.video_urls("qr") == [] == TH.video_urls("kuch_bhi"))
# v80: tutorial-video ki MACHINERY hi delete — koi gated row nahi, kuch nahi
_bsrc_nc = re.sub(r"(?m)^\s*#.*$", "", _bsrc)          # comment lines hatake scan
_VID_BTNS = re.findall(r'InlineKeyboardButton\("[^"]*(?:🎬[^"]*Tutorial|Tutorial Video)[^"]*"', _bsrc)
check("bot me koi 🎬 Tutorial button nahi bacha (VIP wall/plans/cloner/business/kagaz sab saaf)",
      not _VID_BTNS, str(_VID_BTNS)[:110])
check("vip_wall se 🎁 Refer ka button bhi gaya (tool hi hata hai)",
      'open_refer_menu")]' not in _bsrc.split("def vip_wall_kb")[1].split("def ")[0])
check("get_limit_exceeded_kb me 🎬/ rows nahi, VIP + Support bache hain",
      "🎬 VIP kaise milega" not in _bsrc and "🎁 Refer karo (Free VIP)" not in _bsrc
      and 'callback_data="open_vip_menu"' in _bsrc)
check("tutorial_kb() me ab koi video button nahi (dead tap nahi)",
      "toolvid" not in inspect.getsource(B.tutorial_kb))
check("toolvid: callback bot se POORI tarah gaya (handler + prefix + button)",
      "toolvid" not in _bsrc_nc)
check("video machinery bot me import bhi nahi hoti (has_video/video_urls/video_caption)",
      not re.search(r"\b(has_video|video_urls|video_caption)\b", _bsrc_nc))
check("send_tool_video / tool_tutorial_kb / TUTORIAL_NOTICE naam se kuch nahi raha",
      not any(k in _bsrc_nc for k in ("send_tool_video", "tool_tutorial_kb", "TUTORIAL_NOTICE")))
check("tool_support_kb sirf 📩 Support row deta hai (koi video row nahi)",
      len(B.tool_support_kb("qr").inline_keyboard) == 1
      and "Support" in B.tool_support_kb("qr").inline_keyboard[0][0].text)
check("HELP_NOTICE me 'video' shabd nahi (jhootha waada nahi)",
      "video" not in B.HELP_NOTICE.lower() and "🎬" not in B.HELP_NOTICE)
check("menu card copy me 'Tutorial Video button' wala waada nahi",
      "Tutorial Video button" not in _bsrc and "🎬 Tutorial Video" not in _bsrc)
check("/start aur /account copy me hataye hue /refer ka waada nahi",
      "dost ko bulao (/refer)" not in _bsrc and "dost ko share karo (/refer)" not in _bsrc)
check("publish_tutorial ab bhi import ho jaata hai (bot import na tute)",
      callable(getattr(TH, "publish_tutorial", None)))

# ======================================================================
section("E. 📨 Progress = ek card EDIT, flood nahi")
# ======================================================================
_psig = inspect.signature(B._progress_pinger)
check("_progress_pinger ko edit_msg milta hai", "edit_msg" in _psig.parameters)
check("_progress_pinger edit raasta safe_edit use karta hai",
      "safe_edit(edit_msg" in inspect.getsource(B._progress_pinger))
check("flood-control: 2 edit fail = chup ho jaata hai",
      "_fails >= 2" in inspect.getsource(B._progress_pinger))
check("downloader ab edit_msg=st bhejta hai (naya message nahi)",
      "every=6, stop=_ping_stop, edit_msg=st" in _bsrc)


class _FakeMsg:
    def __init__(self):
        self.texts = []
        self.edits = []
        self.deleted = False

    async def reply_text(self, *a, **kw):
        self.texts.append(kw.get("text", a[0] if a else ""))
        return self

    async def edit_text(self, *a, **kw):
        if self.deleted:
            raise RuntimeError("message was deleted")
        self.edits.append(kw.get("text", a[0] if a else ""))
        return self

    async def delete(self):
        self.deleted = True


async def _pinger_test():
    st = _FakeMsg()
    stop = asyncio.Event()
    task = asyncio.create_task(B._progress_pinger(
        _FakeMsg(), lambda el: f"chal raha hai {el}s", every=0.02, stop=stop,
        max_pings=5, edit_msg=st))
    await asyncio.sleep(0.15)
    stop.set()
    await asyncio.wait_for(task, 3)
    return st


_st_fake = asyncio.run(_pinger_test())
check("pinger ne REPLY nahi bheji (0 naya message)", len(_st_fake.texts) == 0,
      f"replies={len(_st_fake.texts)}")
check("pinger ne edits kiye (10s/16s.. wali bheed khatam)", len(_st_fake.edits) >= 2,
      f"edits={len(_st_fake.edits)}")


async def _pinger_deleted():
    st = _FakeMsg()
    await st.delete()
    stop = asyncio.Event()
    task = asyncio.create_task(B._progress_pinger(
        _FakeMsg(), lambda el: "x", every=0.02, stop=stop, max_pings=6, edit_msg=st))
    await asyncio.sleep(0.12)
    stop.set()
    await asyncio.wait_for(task, 3)
    return st


_d = asyncio.run(_pinger_deleted())
check("status card delete ho jaye to pinger crash/flood nahi karta",
      len(_d.texts) <= 1, f"replies={len(_d.texts)}")

# _st_edit: delete hue card par bhi jawab user tak pahunche
async def _st_edit_test():
    st = _FakeMsg()
    await st.delete()
    up = type("U", (), {"message": _FakeMsg()})()
    ok = await B._st_edit(st, up, "aapka jawab", parse_mode="HTML")
    return ok, up.message.texts


_ok_ed, _texts = asyncio.run(_st_edit_test())
check("_st_edit: edit fail hua to naya message bheja (crash-shield tak nahi gaya)",
      _ok_ed is False and len(_texts) == 1, str(_texts)[:60])
check("downloader block me kacha `await st.edit_text(` nahi bacha",
      "await st.edit_text(" not in _bsrc[_bsrc.index('res = await with_tool_timeout(download_video_async'):
      _bsrc.index('    if mode == "bgmi":')],
      "koi ek site bachi")

# ======================================================================
section("F. 🐘 intake wiring (bot.py) — 20MB gate ab config-driven")
# ======================================================================
_is = _bsrc.index("if kind and att is not None:")
_ie = _bsrc.index('await msg.reply_text(fail_msg("FILE ERROR"', _is)
_i = _bsrc[_is:_ie]
check("gate ab BF.cap_in_mb() se chalta hai (hardcode 20MB nahi)",
      "_cap_mb = BF.cap_in_mb()" in _i)
check("MTProto off par PURANA message waisa hi (copy nahi badli)",
      "The file is bigger than 20MB — that is the Telegram bot limit" in _i)
check("20MB se upar -> MTProto download (disk par)", "BF.download_to_path(msg" in _i)
check("badi file MappedFile se jaati hai (RAM safe)", "BF.MappedFile(_r[" in _i)
check("temp file finally me saaf hoti hai (disk full na ho)", "unlink()" in _i)
check("chhoti file ka purana raasta intact (get_file + download_to_memory)",
      "await tf.download_to_memory(buf)" in _i)
check("handle_new_tool_file ka signature nahi badla (doosre tools safe)",
      "async def handle_new_tool_file(update, context, uid, msg, mode, kind, data, mime=\"\"):" in _bsrc)

# tools jo MappedFile le sakte hain
from modules import desi_tools as DT                         # noqa: E402
_fd, _vp = tempfile.mkstemp(suffix=".mp4")
with os.fdopen(_fd, "wb") as fh:
    fh.write(b"M" * 2_000_000)
_mf2 = BF.MappedFile(_vp, 2_000_000)
_fd2, _op = tempfile.mkstemp(suffix=".mp4")
os.close(_fd2)
check("desi_tools._write_media MappedFile ko DISK se copy karta hai",
      DT._write_media(_op, _mf2) == 2_000_000 and os.path.getsize(_op) == 2_000_000)
check("desi_tools._write_media plain bytes bhi sambhalta hai",
      DT._write_media(_op, b"abc") == 3)
check("_as_bytes ab MappedFile bhi nibhta hai (getvalue)",
      DT._as_bytes(_mf2) == b"M" * 2_000_000)
_mf2.unlink()
for _p in (_vp, _op):
    try:
        os.remove(_p)
    except OSError:
        pass
check("cyber_studio/bulk jaisi byte-only tools bytes par hi chalti rahengi",
      callable(getattr(__import__("modules.cyber_studio", fromlist=["x"]),
                       "_load_photo", None)))

# ======================================================================
section("G. ⚡ Speed non-regression (v78 ka DB fix ab bhi zinda)")
# ======================================================================
import database as db                                        # noqa: E402
_conn = {"n": 0}
_real = db._vault_connect


def _counting(path, *a, **kw):
    _conn["n"] += 1
    return _real(path, *a, **kw)


db._vault_connect = _counting
try:
    db.reset_conns()
    _conn["n"] = 0
    for _ in range(60):
        with db.db() as c:
            c.execute("SELECT 1")
    check("60 DB calls me 1 connect (v78 reuse intact)", _conn["n"] <= 1, f"={_conn['n']}")
finally:
    db._vault_connect = _real
check("core/limiter.py safeconf.env_int use karta hai (boot crash fix zinda)",
      "from .safeconf import env_int" in open(os.path.join(_ROOT, "modules", "core",
                                                            "limiter.py"), encoding="utf-8").read())
_src_lim = open(os.path.join(_ROOT, "modules", "core", "limiter.py"), encoding="utf-8").read()
check("core/limiter.py me raw int(os.environ...) wapas nahi aaya",
      'int(os.environ.get("RATE_LIMIT' not in _src_lim)
_src_pr = open(os.path.join(_ROOT, "modules", "core", "proengine.py"), encoding="utf-8").read()
check("core/proengine.py me bhi raw int(os.environ...) nahi",
      'int(os.environ.get("PRO_' not in _src_pr)


# ---------------------------------------------------------------
# v80.2: 🐘 MTProto WARM-UP — boot par handshake, /health par ON
# ---------------------------------------------------------------
import asyncio as _aio_w                                        # noqa: E402
import inspect as _insp_w                                       # noqa: E402
check("bigfile.warm() maujood + async hai",
      hasattr(BF, "warm") and _insp_w.iscoroutinefunction(BF.warm))
_wsrc = _insp_w.getsource(BF.warm)
check("warm() asli login (_started) ko call karta hai", "await _started()" in _wsrc)
check("warm() kabhi exception nahi fenkta (try/except se lipta)",
      "except Exception" in _wsrc and "return False" in _wsrc)


def _warm_without_creds():
    """Creds na hone par warm() False deta hai — na crash, na hang."""
    _orig_ready, _orig_client = BF._client_ready, BF._client
    BF._client, BF._client_ready = None, (lambda: None)
    try:
        return _aio_w.run(BF.warm())
    finally:
        BF._client_ready, BF._client = _orig_ready, _orig_client


check("creds na ho to warm() False (safe deploy ab bhi intact)",
      _warm_without_creds() is False)
_post_w = _bsrc.split("async def _post_init")[1].split("\nasync def ")[0] \
    if "async def _post_init" in _bsrc else ""
# comment lines hata ke ginte hain — varna hamari hi explanation comment count me aa jaati
_post_wn = re.sub(r"(?m)^\s*#.*$", "", _post_w)
check("_post_init BF.warm() ko BACKGROUND task me daalta hai (startup block nahi)",
      "asyncio.create_task(BF.warm())" in _post_wn and _post_wn.count("BF.warm()") == 1)
check("warm call bhi try/except me hai (boot kabhi na ruke)",
      "except Exception as _we" in _post_w)
check("warm-up BIGFILE_WARM knob se off ho sakta hai (memory trade-off user ke haath)",
      '_env_bool("BIGFILE_WARM", True)' in _post_w and "warm-up OFF" in _post_w)
_src_bf = open(os.path.join(_ROOT, "modules", "core", "bigfile.py"), encoding="utf-8").read()
check("warm-off par bhi feature nahi marta (caps creds se hi chalte hain)",
      "def cap_in_mb" in _src_bf and "def cap_out_mb" in _src_bf)

print("\n" + "=" * 62)
print(f"  v89 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
if FAILS:
    print("-" * 62)
    for _f in FAILS[:30]:
        print("   ❌ " + _f)
print("=" * 62)
sys.exit(1 if FAIL else 0)
