"""v44 TEST — STUDENT EXAM HUB removal + crash fixes + 🧠 AI Brain (mock AI, asli ffmpeg).

Sab offline chalta hai:
  • AI_MOCK=1 → AI layer ka poora rasta (plan_moments → analyze → clips) bina internet.
  • Asli 90 sec test video (ffmpeg) se clips.
  • Telegram mock: Timed out error, passport photo text flow, fallback re-prompt.
"""
import asyncio
import io
import os
import re
import subprocess
import sys
import unicodedata

os.environ["DB_PATH"] = "/tmp/_v44.db"
os.environ["BOT_TOKEN"] = "123456789:AAHtesttoken_testtoken_testtoken_testtok"
os.environ["ADMIN_ID"] = "8607774564"
os.environ["CLIP_YTDLP"] = "0"
os.environ["AI_MOCK"] = "1"                 # AI layer test (koi internet nahi)
sys.path.insert(0, "/home/user/fix")

for f in ("/tmp/_v44.db",):
    if os.path.exists(f):
        os.remove(f)

from telegram import Chat, Update, User             # noqa: E402
from telegram.constants import ChatType             # noqa: E402
from telegram.error import TimedOut                 # noqa: E402

import bot                                          # noqa: E402
import database as dbm                              # noqa: E402
from modules import clip_maker as cm                # noqa: E402
from modules import ai_brain as aib                 # noqa: E402

PASS, FAIL = [], []
OWNER = 8607774564
USER = 880000444
TMP = "/tmp/_v44"
os.makedirs(TMP, exist_ok=True)
TEST_VIDEO = os.path.join(TMP, "test90.mp4")


def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'✅' if cond else '❌'} {name}" + (f"  — {str(detail)[:230]}" if detail and not cond else ""))


def norm(t):
    return unicodedata.normalize("NFKC", t or "")


def clean_key(text):
    n = bot.unbold(text).strip().upper()
    return re.sub(r"^[^\w\s]+\s*", "", n).strip()


def kb_label(action):
    for row in bot.KB_BTNS:
        for b in row:
            if bot.BTN_MODE_MAP.get(clean_key(b)) == action:
                return b
    return ""


# ======================================================================
def build_video():
    segs = []
    for i, vol in enumerate([0.08, 0.5, 0.06, 0.6, 0.05, 0.55]):
        p = os.path.join(TMP, f"seg{i}.mp4")
        if not os.path.exists(p):
            subprocess.run([cm.ffmpeg_path(), "-y", "-hide_banner", "-loglevel", "error",
                            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=25:duration=15",
                            "-f", "lavfi", "-i", f"sine=frequency={220 + i * 60}:duration=15",
                            "-af", f"volume={vol}", "-c:v", "libx264", "-preset", "ultrafast",
                            "-crf", "30", "-c:a", "aac", p], check=True)
        segs.append(p)
    lst = os.path.join(TMP, "list.txt")
    with open(lst, "w") as f:
        for p in segs:
            f.write(f"file '{p}'\n")
    subprocess.run([cm.ffmpeg_path(), "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", TEST_VIDEO], check=True)
    ok("test video bana (90 sec)", os.path.getsize(TEST_VIDEO) > 100000)


# ======================================================================
def test_exam_removed():
    print("\n--- 1) 🎓 STUDENT EXAM HUB REMOVAL ---")
    kb_txt = norm(str(bot.KB_BTNS))
    ok("menu me STUDENT EXAM button nahi", "STUDENT EXAM" not in kb_txt.upper(), kb_txt[:120])
    ok("BTN_MODE_MAP me exam nahi", "exam" not in bot.BTN_MODE_MAP.values(), bot.BTN_MODE_MAP.get("STUDENT EXAM HUB"))
    src = io.open("/home/user/fix/bot.py", encoding="utf-8").read()
    ok("bot.py me student_exam callback nahi", "student_exam" not in src)
    ok("bot.py me /exam command nahi", 'CommandHandler("exam"' not in src)
    ok("sarkari_hub se STUDENT_EXAM_TEXT hata", "STUDENT_EXAM_TEXT" not in
       io.open("/home/user/fix/modules/sarkari_hub.py", encoding="utf-8").read())
    ok("tutorial_hub me exam key nahi", '"exam"' not in
       io.open("/home/user/fix/modules/tutorial_hub.py", encoding="utf-8").read())
    rows = bot.KB_BTNS
    ok("har menu row 2 buttons (aakhri row bhi)", all(1 <= len(r) <= 2 for r in rows), [len(r) for r in rows])
    ok("menu rows 16", len(rows) == 16, len(rows))
    ok("buttons 32", sum(len(r) for r in rows) == 32, sum(len(r) for r in rows))
    ok("numinfo/ifsc wali row bani (exam ki jagah)", any("NUMBER INFO" in norm(str(r)).upper()
                                                         and "IFSC" in norm(str(r)).upper() for r in rows))


# ======================================================================
class FakeAttFile:
    def __init__(self, path):
        self._path = path

    async def download_to_memory(self, buf, **kw):
        with open(self._path, "rb") as fh:
            buf.write(fh.read())
        return buf

    async def download_as_bytearray(self, **kw):
        with open(self._path, "rb") as fh:
            return bytearray(fh.read())


class FakePhotoSize:
    def __init__(self, path):
        self.file_id = "ph1"
        self.file_size = os.path.getsize(path)
        self.width = self.height = 600
        self._path = path

    async def get_file(self):
        return FakeAttFile(self._path)


class FakeSent:
    """Status message ka mock — jo edit hota hai wahi parent ki list me jata hai."""
    def __init__(self, owner=None, bucket=None):
        self.owner = owner
        self.bucket = bucket if bucket is not None else []

    async def edit_text(self, text, **kw):
        self.bucket.append(text)
        if kw.get("reply_markup"):
            self.owner.kbs.append(kw["reply_markup"])
        return self

    async def delete(self):
        return True


class FakeMsg:
    def __init__(self, text="", uid=USER, photo=None, video=None):
        self.text = text
        self.caption = None
        self.uid = uid
        self.photo = [FakePhotoSize(photo)] if photo else None
        self.video = video
        self.document = None
        self.audio = self.voice = self.animation = None
        self.sent = []
        self.edits = []
        self.kbs = []
        self._send_fail_times = 0
        self.chat = Chat(id=uid, type=ChatType.PRIVATE)
        self.chat_id = uid

    def all_text(self):
        return "\n".join([self.text or ""] + [s for s in self.sent] + [e for e in self.edits])

    def replies_text(self):
        """Sirf bot ke jawab (user ka bheja hua text nahi)."""
        return "\n".join([s for s in self.sent] + [e for e in self.edits])

    def U(self):
        """bold-unicode hata kar uppercase — comparison ke liye."""
        return norm(bot.unbold(self.replies_text())).upper()

    def cb_data(self):
        out = []
        for kb in self.kbs:
            try:
                rows = kb.inline_keyboard
            except Exception:
                continue
            for r in rows:
                for b in r:
                    out.append(getattr(b, "callback_data", "") or getattr(b, "url", "") or b.text)
        return out

    async def reply_text(self, text, **kw):
        self.sent.append(text)
        if kw.get("reply_markup"):
            self.kbs.append(kw["reply_markup"])
        return FakeSent(self, self.edits)

    async def reply_photo(self, photo=None, caption="", **kw):
        self.sent.append(caption or "")
        if kw.get("reply_markup"):
            self.kbs.append(kw["reply_markup"])
        return FakeSent(self, self.edits)

    async def reply_video(self, video=None, caption="", **kw):
        if self._send_fail_times > 0:
            self._send_fail_times -= 1
            raise TimedOut()
        self.sent.append(caption or "")
        self.videos_sent = getattr(self, "videos_sent", []) + [caption or ""]
        return FakeSent(self, self.edits)

    async def reply_document(self, document=None, caption="", **kw):
        self.sent.append(caption or "")
        return FakeSent()

    async def reply_media_group(self, media=None, **kw):
        self.sent.append("media_group")
        return [FakeSent()]

    async def edit_text(self, text, **kw):
        self.edits.append(text)
        if kw.get("reply_markup"):
            self.kbs.append(kw["reply_markup"])
        return FakeSent(self, self.edits)


class FakeVidAtt(FakeAttFile):
    def __init__(self, path):
        super().__init__(path)
        self.file_name = os.path.basename(path)
        self.mime_type = "video/mp4"
        self.file_size = os.path.getsize(path)
        self.file_id = "vid1"
        self.duration = 90

    async def get_file(self):
        return FakeAttFile(self._path)


class FakeQuery:
    def __init__(self, data, uid=USER):
        self.data = data
        self.from_user = User(id=uid, first_name="Tester", is_bot=False)
        self.message = FakeMsg("", uid=uid)
        self.answers = []

    async def answer(self, text=None, show_alert=False):
        self.answers.append(text)


class FakeBotObj:
    def __init__(self):
        self.id = 999
        self.videos = []
        self.texts = []

    async def send_message(self, chat_id=None, text=None, **kw):
        self.texts.append((chat_id, text))
        return FakeSent(self, self.texts)

    async def send_video(self, chat_id=None, video=None, caption="", **kw):
        name = getattr(video, "name", "")
        size = os.path.getsize(name) if isinstance(name, str) and os.path.exists(name) else 0
        self.videos.append({"caption": caption, "size": size, **kw})
        return FakeSent()


class Ctx:
    def __init__(self):
        self.user_data = {}
        self.args = []
        self.bot = FakeBotObj()


def mk_update(msg, uid=USER, upid=1):
    u = Update(update_id=upid, message=msg)
    u.message.from_user = User(id=uid, first_name="Tester", is_bot=False)
    return u


# ======================================================================
async def test_passport_photo():
    print("\n--- 2) 📸 PASSPORT PHOTO (crash fix) ---")
    dbm.set_credits(USER, 5)
    dbm.get_user(USER, "Tester")
    ctx = Ctx()
    ctx.user_data["mode"] = "pp_stamp"
    m = FakeMsg(uid=USER, photo="/tmp/_v44/face.jpg")
    await bot.on_photo(mk_update(m, upid=20), ctx)
    ok("photo liya gaya + naam maanga", ctx.user_data.get("mode") == "pp_stamp_text"
       and "NAME" in m.all_text().upper(), (ctx.user_data.get("mode"), m.all_text()[:120]))

    # 🐞 asli bug: text aane par pehle menu par phenk deta tha
    m2 = FakeMsg("SHWETA KUMARI 01-07-2011", uid=USER)
    before = dbm.get_credits(USER)
    await bot.on_text(mk_update(m2, upid=21), ctx)
    ok("naam+DOP par stamped photo bana (menu par nahi gira)",
       "PHOTO READY" in m2.U(), m2.replies_text()[:200])
    ok("caption me naam + DOP sahi", "SHWETA KUMARI" in m2.U() and "01-07-2011" in m2.replies_text(),
       m2.replies_text()[:200])
    ok("PASSPORT PHOTO free tool hai (credit nahi katta)", dbm.get_credits(USER) == before
       and not bot.is_premium_tool("pp_stamp"), (before, dbm.get_credits(USER)))
    ok("mode saaf hua", ctx.user_data.get("mode") is None, ctx.user_data.get("mode"))

    # date ke bina → aaj ki date + warning
    ctx2 = Ctx()
    ctx2.user_data["mode"] = "pp_stamp"
    m3 = FakeMsg(uid=USER, photo="/tmp/_v44/face.jpg")
    await bot.on_photo(mk_update(m3, upid=22), ctx2)
    m4 = FakeMsg("RAHUL KUMAR", uid=USER)
    await bot.on_text(mk_update(m4, upid=23), ctx2)
    ok("date na dene par bhi photo bani + warning", "PHOTO READY" in m4.U()
       and "DATE" in m4.U(), m4.replies_text()[:220])

    # bekaar naam → dobara maango (crash nahi)
    ctx3 = Ctx()
    ctx3.user_data["mode"] = "pp_stamp_text"
    ctx3.user_data["raw_photo"] = io.open("/tmp/_v44/face.jpg", "rb").read()
    m5 = FakeMsg("123 456", uid=USER)
    await bot.on_text(mk_update(m5, upid=24), ctx3)
    ok("bekaar naam par dobara maanga (crash nahi)", "NAME" in m5.U(), m5.replies_text()[:160])

    # photo ke bina text → seedha message
    ctx4 = Ctx()
    ctx4.user_data["mode"] = "pp_stamp_text"
    m6 = FakeMsg("RAHUL KUMAR 01-01-2026", uid=USER)
    await bot.on_text(mk_update(m6, upid=25), ctx4)
    ok("photo ke bina saaf message", "PASSPORT PHOTO" in m6.U(), m6.replies_text()[:160])


# ======================================================================
async def test_insta_timeout():
    print("\n--- 3) 📥 VIDEO DOWNLOADER (Timed out fix) ---")
    dbm.set_credits(USER, 5)
    big = b"\x00" * (7 * 1048576)

    async def fake_dl(url, max_mb=None, **kw):
        return {"ok": True, "type": "video", "bytes": big, "duration": 30, "size_mb": 7.0,
                "engine": "test", "title": "Test Reel"}

    orig_dl, orig_comp = bot.download_video_async, bot.desi.video_compress
    bot.download_video_async = fake_dl
    bot.desi.video_compress = lambda data, target_mb=18.0, ext=".mp4", max_seconds=150.0: {
        "ok": True, "bytes": b"y" * (3 * 1048576), "size_mb": 3.0}
    try:
        ctx = Ctx()
        ctx.user_data["mode"] = "insta_dl"
        m = FakeMsg("https://www.instagram.com/reel/ABC123xyz/", uid=USER)
        m._send_fail_times = 1                      # pehla send → Timed out
        before = dbm.get_credits(USER)
        await bot.on_text(mk_update(m, upid=30), ctx)
        ok("timeout ke baad compressed video bhej di", any("compressed" in s.lower()
                                                          for s in getattr(m, "videos_sent", [])),
           m.all_text()[:200])
        ok("user ko raw error/heap nahi dikha", "Traceback" not in m.replies_text()
           and "https://" not in m.replies_text(), m.replies_text()[:200])
        ok("success par 1 credit kata", dbm.get_credits(USER) == before - 1,
           (before, dbm.get_credits(USER)))
    finally:
        bot.download_video_async, bot.desi.video_compress = orig_dl, orig_comp

    # retry bhi fail → saaf message + credit nahi kata
    async def fake_dl2(url, max_mb=None, **kw):
        return {"ok": True, "type": "video", "bytes": b"z" * 1024, "duration": 10, "size_mb": 0.001,
                "engine": "test", "title": "T"}

    bot.download_video_async = fake_dl2
    try:
        ctx2 = Ctx()
        ctx2.user_data["mode"] = "insta_dl"
        m2 = FakeMsg("https://www.instagram.com/reel/ABC123xyz/", uid=USER)
        m2._send_fail_times = 5
        before2 = dbm.get_credits(USER)
        await bot.on_text(mk_update(m2, upid=31), ctx2)
        ok("fail par saaf SEND FAILED message", "SEND FAILED" in m2.U(), m2.replies_text()[:220])
        _junk = ("traceback", "github.com", "yt-dlp", "player response")
        ok("raw error/link kachra message me nahi", not any(j in m2.replies_text().lower() for j in _junk),
           m2.replies_text()[:220])
        ok("fail par credit nahi kata", dbm.get_credits(USER) == before2, (before2, dbm.get_credits(USER)))
    finally:
        bot.download_video_async = orig_dl


# ======================================================================
async def test_fallback():
    print("\n--- 4) 🧭 MAGIC FALLBACK (menu par nahi, wahi tool) ---")
    ctx = Ctx()
    ctx.user_data["mode"] = "mediastudio"
    m = FakeMsg("hello bhai kya haal", uid=USER)
    await bot.on_text(mk_update(m, upid=40), ctx)
    ok("mode chalu ho to menu par nahi girta", "Pick a tool from the grid menu" not in m.all_text(),
       m.all_text()[:200])
    ok("wahi tool dobara maanga (samajh nahi aaya)", "Samajh nahi aaya" in m.all_text(), m.all_text()[:200])

    ctx2 = Ctx()
    ctx2.user_data["mode"] = "pp_stamp_text"
    m2 = FakeMsg("hello", uid=USER)
    await bot.on_text(mk_update(m2, upid=41), ctx2)
    ok("special mode par naam batakar guide kiya", "PASSPORT PHOTO" in m2.all_text().upper(),
       m2.all_text()[:200])


# ======================================================================
async def test_ai_brain():
    print("\n--- 5) 🧠 AI BRAIN (mock) ---")
    ok("AI mock mode me available", aib.ai_available() is True, aib.provider_name())
    ok("label mock dikhata hai", "mock" in aib.ai_label().lower(), aib.ai_label())
    card = aib.status_card()
    ok("status card AI batata hai", "AI BRAIN" in card and "MOCK" in card.upper(), card[:120])

    info = cm.probe_info(TEST_VIDEO)
    cands = cm.candidates_for_ai(TEST_VIDEO, count=8)
    ok("candidates_for_ai windows deta hai", len(cands) >= 4 and all(c["end"] > c["start"] for c in cands),
       len(cands))
    ok("candidate me loud/cuts info hai", all(k in cands[0] for k in ("score", "loud", "scenes")), cands[0] if cands else None)

    plan = aib.plan_moments(TEST_VIDEO, info["duration"], count=3, min_len=15.0, target_len=25.0, candidates=cands)
    ok("plan_moments ok (mock AI)", plan.get("ok") is True and len(plan["moments"]) == 3, plan)
    ok("moments me title hai", all(m.get("title") for m in plan["moments"]), plan["moments"][0])

    # overlap/clamp cleaning
    dirty = [{"start": 5, "end": 25, "score": 9, "title": "A"},
             {"start": 10, "end": 30, "score": 8, "title": "overlap"},
             {"start": 80, "end": 200, "score": 7, "title": "bahar"},
             {"start": 40, "end": 41, "score": 6, "title": "chhota"}]
    clean = aib._clean_moments(dirty, 90.0, 6, 15.0)
    ok("overlap wala hata diya", all(not (clean[i]["end"] > clean[i + 1]["start"]) for i in range(len(clean) - 1)),
       clean)
    ok("video ke bahar wala clamp hua", all(c["end"] <= 90.0 for c in clean), clean)
    ok("bahut chhota moment bada kiya (ya video ke aakhir tak)",
       all(c["end"] - c["start"] >= 15 or c["end"] >= 89.5 for c in clean), clean)

    # AI moments → asli clips
    r = cm.analyze(TEST_VIDEO, mode="smart", vertical=True, count=3,
                   ai_moments=plan["moments"], ai_engine="AI · mock")
    ok("AI moments se asli clips bane", r.get("ok") is True and len(r["clips"]) == 3, r.get("error"))
    c0 = r["clips"][0]
    ok("clip par AI title chipka", bool(c0.get("title")), c0)
    ok("AI engine ka naam result me", r.get("ai_engine") == "AI · mock", r.get("ai_engine"))
    cap = cm.caption_for(c0, 3, True)
    ok("caption me 🤖 + title", "🤖" in cap and c0["title"][:6] in cap, cap)
    ok("clip ki asli file bani", os.path.exists(c0["path"]) and c0["size_mb"] > 0.05, c0)
    cm.cleanup(r["outdir"])

    # AI ke bina → classic engine (kabhi fail nahi)
    r2 = cm.analyze(TEST_VIDEO, mode="smart", vertical=False, count=3)
    ok("AI off par classic engine chalta hai", r2.get("ok") is True and len(r2["clips"]) == 3, r2.get("error"))
    ok("classic clip par title nahi", not r2["clips"][0].get("title"), r2["clips"][0].get("title"))
    cm.cleanup(r2["outdir"])


# ======================================================================
async def test_ai_bot_flow():
    print("\n--- 6) 🤖 BOT FLOW: AI ON (mock) ---")
    dbm.set_credits(USER, 5)
    ok("menu me CLIP MAKER hai", bool(kb_label("clips")))
    ctx = Ctx()
    ctx.user_data["mode"] = "clips"
    m = FakeMsg(uid=USER, video=FakeVidAtt(TEST_VIDEO))
    await bot.on_media(mk_update(m, upid=50), ctx)
    ok("video receive hui", "Video received" in m.all_text(), m.all_text()[:150])
    ok("card me Smart AI button", "clai:toggle" in m.cb_data(), m.cb_data())
    ok("card me AI ON likha", "Smart AI" in m.all_text(), m.all_text()[:220])

    q = FakeQuery("clmode:smart", uid=USER)
    await bot.on_cb(Update(update_id=51, callback_query=q), ctx)
    q2 = FakeQuery("clorient:169", uid=USER)
    await bot.on_cb(Update(update_id=52, callback_query=q2), ctx)
    ctx.user_data["clip_ai"] = True

    before = dbm.get_credits(USER)
    q3 = FakeQuery("clipgo", uid=USER)
    await bot.on_cb(Update(update_id=53, callback_query=q3), ctx)
    for _ in range(240):
        await asyncio.sleep(0.5)
        if dbm.get_credits(USER) == before - 1:
            break
    ok("AI ON me clips bheji gayi", len(ctx.bot.videos) >= 3, [v["caption"][:50] for v in ctx.bot.videos])
    ok("sent clip caption me 🤖 title", any("🤖" in v["caption"] for v in ctx.bot.videos),
       [v["caption"][:80] for v in ctx.bot.videos])
    _txts = [t for t in ctx.bot.texts if isinstance(t, str)] + \
            [t[1] for t in ctx.bot.texts if isinstance(t, tuple)]
    ok("AI note bhi bheja (status me)", any("AI" in t for t in _txts), [t[:70] for t in _txts][:4])
    ok("1 credit kata", dbm.get_credits(USER) == before - 1, (before, dbm.get_credits(USER)))

    # AI OFF → classic
    ctx2 = Ctx()
    ctx2.user_data["clip_ai"] = False
    ctx2.user_data["mode"] = "clips"
    m2 = FakeMsg(uid=USER, video=FakeVidAtt(TEST_VIDEO))
    await bot.on_media(mk_update(m2, upid=60), ctx2)
    ok("AI OFF par card OFF dikhata hai", "SMART AI: <B>OFF" in m2.U().replace("\n", " "),
       m2.replies_text()[:220])

    # toggle callback
    q4 = FakeQuery("clai:toggle", uid=USER)
    await bot.on_cb(Update(update_id=61, callback_query=q4), ctx2)
    ok("toggle se AI ON ho gaya", ctx2.user_data.get("clip_ai") is True, ctx2.user_data.get("clip_ai"))
    q5 = FakeQuery("clai:toggle", uid=USER)
    await bot.on_cb(Update(update_id=62, callback_query=q5), ctx2)
    ok("dobara toggle se OFF", ctx2.user_data.get("clip_ai") is False, ctx2.user_data.get("clip_ai"))

    # admin /aistatus
    ctxa = Ctx()
    ma = FakeMsg("", uid=OWNER)
    upda = mk_update(ma, uid=OWNER, upid=70)
    ctxa.args = []
    await bot.cmd_aistatus(upda, ctxa)
    ok("/aistatus status deta hai", "AI BRAIN" in ma.all_text(), ma.all_text()[:160])
    ok("/aistatus live test pass (mock)", "working" in ma.all_text().lower(), ma.all_text()[:220])

    ctxc = Ctx()
    mc = FakeMsg("", uid=OWNER)
    await bot.cmd_clipstatus(mk_update(mc, uid=OWNER, upid=71), ctxc)
    ok("/clipstatus me AI line", "AI Brain" in mc.all_text(), mc.all_text()[:200])


# ======================================================================
def test_no_key_fallback():
    print("\n--- 7) AI KEY NA HO TO (offline safety) ---")
    old_mock, old_g, old_gr = os.environ.pop("AI_MOCK", None), os.environ.get("GEMINI_API_KEY"), os.environ.get("GROQ_API_KEY")
    os.environ.pop("GEMINI_API_KEY", None)
    os.environ.pop("GROQ_API_KEY", None)
    try:
        ok("key na hone par ai_available False", aib.ai_available() is False, aib.provider_name())
        res = aib.plan_moments(TEST_VIDEO, 90.0, count=3)
        ok("plan_moments saaf error deta hai (crash nahi)", res.get("ok") is False and res.get("error"), res)
        card = aib.status_card()
        ok("status card key add karne ka tarika batata hai", "GEMINI_API_KEY" in card and "GROQ_API_KEY" in card)
        ok("live_test bhi saaf fail", aib.live_test().get("ok") is False)
    finally:
        if old_mock is not None:
            os.environ["AI_MOCK"] = old_mock
        if old_g:
            os.environ["GEMINI_API_KEY"] = old_g
        if old_gr:
            os.environ["GROQ_API_KEY"] = old_gr


# ======================================================================
def test_helpers():
    print("\n--- 8) 🧹 HELPERS ---")
    ok("clean_err link hatata hai", "http" not in bot.clean_err("ERROR: [youtube] failed https://github.com/x/y see"))
    ok("clean_err trim karta hai", len(bot.clean_err("x" * 500)) <= 210, len(bot.clean_err("x" * 500)))
    ok("clean_err khaali par default deta hai", bot.clean_err("") != "", bot.clean_err(""))
    _src = io.open("/home/user/fix/bot.py", encoding="utf-8").read()
    ok("PTB timeouts bade set hain (240s+)", "write_timeout(240.0)" in _src
       and "media_write_timeout(300.0)" in _src and "read_timeout(60.0)" in _src)


# ======================================================================
def make_face():
    from PIL import Image, ImageDraw
    p = os.path.join(TMP, "face.jpg")
    im = Image.new("RGB", (600, 800), (210, 225, 240))
    d = ImageDraw.Draw(im)
    d.ellipse((180, 120, 420, 380), fill=(240, 200, 170))
    d.rectangle((120, 400, 480, 800), fill=(200, 60, 60))
    im.save(p, quality=90)
    return p


make_face()
build_video()
test_exam_removed()
asyncio.run(test_passport_photo())
asyncio.run(test_insta_timeout())
asyncio.run(test_fallback())
asyncio.run(test_ai_brain())
asyncio.run(test_ai_bot_flow())
test_no_key_fallback()
test_helpers()

print("\n" + "=" * 70)
print(f"V44 — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
for f in FAIL:
    print("  ❌", f)
print("=" * 70)
sys.exit(1 if FAIL else 0)
