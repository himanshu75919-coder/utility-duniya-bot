"""v43 TEST — 🎬 CLIP MAKER (asli ffmpeg se clips, Telegram mock).

Mock: 90 sec ka test video (3 hisse LOUD = "interesting", 3 hisse normal) + silent video.
Sab kuch offline — sirf ffmpeg chahiye.
"""
import asyncio
import os
import re
import subprocess
import sys
import unicodedata

os.environ["DB_PATH"] = "/tmp/_clips43.db"
os.environ["BOT_TOKEN"] = "123456789:AAHtesttoken_testtoken_testtoken_testtok"
os.environ["ADMIN_ID"] = "8607774564"
os.environ["CLIP_YTDLP"] = "0"          # test me YouTube off
sys.path.insert(0, "/home/user/fix")

from telegram import Chat, Update, User  # noqa: E402
from telegram.constants import ChatType  # noqa: E402

import bot  # noqa: E402
import database as dbm  # noqa: E402
from modules import clip_maker as cm  # noqa: E402

PASS, FAIL = [], []
OWNER = 8607774564
USER = 880000333
TMP = "/tmp/_clips43"
os.makedirs(TMP, exist_ok=True)
TEST_VIDEO = os.path.join(TMP, "test90.mp4")
SILENT = os.path.join(TMP, "silent40.mp4")


def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'✅' if cond else '❌'} {name}" + (f"  — {str(detail)[:220]}" if detail and not cond else ""))


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
def build_test_videos():
    print("\n--- 0) TEST VIDEO BANANA (ffmpeg) ---")
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
    if not os.path.exists(SILENT):
        subprocess.run([cm.ffmpeg_path(), "-y", "-hide_banner", "-loglevel", "error",
                        "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=25:duration=40",
                        "-an", "-c:v", "libx264", "-preset", "ultrafast", SILENT], check=True)
    ok("test video bana (90 sec, loud + normal hisse)", os.path.getsize(TEST_VIDEO) > 100000)


# ======================================================================
def test_engine():
    print("\n--- 1) ENGINE: ANALYSIS + SELECTION ---")
    info = cm.probe_info(TEST_VIDEO)
    ok("probe: 90 sec + 640x360 + audio", info["duration"] == 90.0 and info["width"] == 640
       and info["has_audio"] is True, info)
    rms = cm.audio_rms(TEST_VIDEO)
    ok("loudness windows mile (~180)", len(rms) > 120, len(rms))
    vals = [v for _t, v in rms]
    loud_first = [t for t, v in rms if v > (sum(vals) / len(vals)) + 4]
    ok("loud moments detect hue (15-30s wala hissa)", any(16 <= t <= 29 for t in loud_first),
       loud_first[:10])

    best = cm.pick_best(rms, cm.scene_times(TEST_VIDEO), 90.0, count=3, target_len=25)
    ok("3 best clips mile", len(best) == 3, best)
    ok("clips chronological order me", [c["idx"] for c in best] == [1, 2, 3], [c["idx"] for c in best])
    ok("koi overlap nahi", all(best[i]["start"] + best[i]["dur"] <= best[i + 1]["start"] + 0.05
                               for i in range(len(best) - 1)), best)
    loud_spots = [(0.5, 30), (30, 45), (45, 60), (60, 75), (75, 90)]
    loud_ranges = [(15, 30), (45, 60), (75, 90)]
    hit = sum(1 for c in best if any(c["start"] < b and a < c["start"] + c["dur"] for a, b in loud_ranges))
    ok("best clips loud hisso par gire (2+ out of 3)", hit >= 2, [c["start"] for c in best])
    ok("rank assign hua (1..3)", sorted(c["rank"] for c in best) == [1, 2, 3], best)

    eq = cm.equal_split(90.0, 3, cm.scene_times(TEST_VIDEO))
    ok("equal parts: 3 hisse barabar", len(eq) == 3
       and all(abs(c["dur"] - 30) <= 5 for c in eq), eq)

    r = cm.analyze(TEST_VIDEO, mode="smart", vertical=False, count=3)
    ok("analyze smart 16:9 chal gaya", r.get("ok") is True and len(r["clips"]) == 3, r.get("error"))
    c0 = r["clips"][0]
    ok("clip file bani + size bataayi", os.path.exists(c0["path"]) and c0["size_mb"] > 0.05, c0)
    p0 = cm.probe_info(c0["path"])
    ok("clip ka duration sahi (~25s)", abs(p0["duration"] - c0["dur"]) <= 1.5, p0)
    ok("clip me audio hai", p0["has_audio"] is True, p0)
    cm.cleanup(r["outdir"])

    r9 = cm.analyze(TEST_VIDEO, mode="smart", vertical=True, count=3)
    ok("analyze 9:16 chal gaya", r9.get("ok") is True and len(r9["clips"]) == 3, r9.get("error"))
    p9 = cm.probe_info(r9["clips"][0]["path"])
    ok("9:16 output = 540x960", (p9["width"], p9["height"]) == (540, 960), p9)
    ok("caption me 9:16 + clip number", "9:16" in cm.caption_for(r9["clips"][0], 3, True)
       and "Clip 1/3" in cm.caption_for(r9["clips"][0], 3, True), cm.caption_for(r9["clips"][0], 3, True))
    ok("best_of_best top 3 deta hai", len(cm.best_of_best(r9["clips"])) == min(3, len(r9["clips"])))
    cm.cleanup(r9["outdir"])

    rs = cm.analyze(SILENT, mode="smart", count=3)
    ok("silent video bhi chalta hai (scene/even se)", rs.get("ok") is True and len(rs["clips"]) >= 1,
       rs.get("error"))
    cm.cleanup(rs.get("outdir") or "")

    re_ = cm.analyze(TEST_VIDEO, mode="equal", vertical=True, count=3)
    ok("equal mode 9:16 chal gaya", re_.get("ok") is True and len(re_["clips"]) == 3, re_.get("error"))
    cm.cleanup(re_["outdir"])

    # limits
    import shutil
    short = os.path.join(TMP, "short15.mp4")
    if not os.path.exists(short):
        shutil.copy(os.path.join(TMP, "seg0.mp4"), short)
    rshort = cm.analyze(short, mode="smart", count=3)
    ok("15 sec video par saaf error", rshort.get("ok") is False
       and "at least" in str(rshort.get("error")).lower(), rshort)
    ok("URL detect: direct mp4", cm.is_direct_video_url("https://x.com/a.mp4?x=1")
       and not cm.is_direct_video_url("https://youtube.com/watch?v=1"))
    ok("URL detect: youtube", cm.is_youtube_url("https://youtu.be/abc") and cm.is_youtube_url("https://www.youtube.com/watch?v=1"))
    ok("help card me limit likha hai", "15 min" in cm.help_card(), cm.help_card())


# ======================================================================
class FakeSent:
    message_id = 1

    def __init__(self, owner=None):
        self.owner = owner
        self.chat = Chat(id=1, type=ChatType.PRIVATE)

    async def delete(self):
        return True

    async def edit_text(self, text, **kw):
        if self.owner:
            self.owner.replies.append(("edit", text, kw))
        return FakeSent(self.owner)


class FakeAtt:
    def __init__(self, path, size=None):
        self.file_name = os.path.basename(path)
        self.mime_type = "video/mp4"
        self.file_size = size if size is not None else os.path.getsize(path)
        self.file_id = "vid1"
        self.duration = 90
        self._path = path

    async def get_file(self):
        return self


class FakeMsg:
    def __init__(self, text="", uid=USER, video=None, document=None):
        self.text = text
        self.caption = None
        self.video = video
        self.document = document
        self.photo = None
        self.audio = self.voice = self.animation = self.video_note = None
        self.replies = []
        self.chat = Chat(id=uid, type=ChatType.PRIVATE)
        self.from_user = User(id=uid, first_name="Tester", is_bot=False)
        self.message_id = 7
        self.media_group_id = None
        self.forward_origin = None
        self.date = None

    async def _dl(self, buf, **kw):
        with open(self.document or self.video._path if False else self._p(), "rb") as f:
            buf.write(f.read())
        return buf

    def _p(self):
        return getattr(self, "_path", "")

    async def reply_text(self, text, **kw):
        self.replies.append(("text", text, kw))
        return FakeSent(self)

    async def edit_text(self, text, **kw):        # mode/orientation buttons dobara dikhane ke liye
        self.replies.append(("edit", text, kw))
        return FakeSent(self)

    async def reply_photo(self, photo=None, **kw):
        self.replies.append(("photo", kw.get("caption", ""), kw))
        return FakeSent(self)

    async def reply_document(self, document=None, **kw):
        self.replies.append(("document", kw.get("caption", ""), kw))
        return FakeSent(self)

    def all_text(self):
        parts = []
        for _k, t, kw in self.replies:
            parts.append(t if isinstance(t, str) else "")
            kb = (kw or {}).get("reply_markup")
            if kb is not None and getattr(kb, "inline_keyboard", None):
                for row in kb.inline_keyboard:
                    parts.append(" | ".join(b.text for b in row))
        return norm("\n".join(parts))

    def cb_data(self):
        out = []
        for _k, _t, kw in self.replies:
            kb = (kw or {}).get("reply_markup")
            if kb is not None and getattr(kb, "inline_keyboard", None):
                out += [b.callback_data for row in kb.inline_keyboard for b in row]
        return [c for c in out if c]


class FakeAttFile:
    """Telegram file object (download_to_memory)."""

    def __init__(self, path):
        self._path = path

    async def download_to_memory(self, buf, **kw):
        with open(self._path, "rb") as f:
            buf.write(f.read())
        return buf


class FakeVidAtt:
    def __init__(self, path):
        self.file_name = os.path.basename(path)
        self.mime_type = "video/mp4"
        self.file_size = os.path.getsize(path)
        self.file_id = "vid1"
        self.duration = 90
        self._path = path

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
        return FakeSent()

    async def send_video(self, chat_id=None, video=None, caption="", **kw):
        name = getattr(video, "name", "?")
        size = 0
        try:
            size = os.path.getsize(name) if isinstance(name, str) else 0
        except Exception:
            size = 0
        self.videos.append({"chat_id": chat_id, "caption": caption, "size": size, **kw})
        return FakeSent()


class Ctx:
    def __init__(self):
        self.user_data = {}
        self.args = []
        self.bot = FakeBotObj()


async def flows():
    print("\n--- 2) BOT FLOW ---")
    ok("menu me CLIP MAKER button", bool(kb_label("clips")), kb_label("clips"))
    ok("premium list me clips (#10)", "clips" in bot.PREMIUM_TOOLS and len(bot.PREMIUM_TOOLS) == 10,
       sorted(bot.PREMIUM_TOOLS))
    ok("prompt chhota + ask line", "Now send the video" in bot.tool_prompt("clips")
       and len([l for l in bot.tool_prompt("clips").split("\n") if l.strip()]) <= 5, bot.tool_prompt("clips"))
    ok("prompt me 15 min limit", "15 min" in bot.tool_prompt("clips"), bot.tool_prompt("clips"))

    # prompt kholna
    dbm.set_credits(USER, 5)
    dbm.get_user(USER, "Tester")
    ctx = Ctx()
    m = FakeMsg(kb_label("clips"), uid=USER)
    upd = Update(update_id=1, message=m)
    upd.message.from_user = User(id=USER, first_name="Tester", is_bot=False)
    await bot.on_text(upd, ctx)
    ok("tool prompt khulta hai", "CLIP MAKER" in m.all_text() and ctx.user_data.get("mode") == "clips",
       m.all_text()[:150])

    # video bhejna → mode buttons
    ctx = Ctx()
    ctx.user_data["mode"] = "clips"
    vid = FakeVidAtt(TEST_VIDEO)
    m2 = FakeMsg(uid=USER, video=vid)
    upd2 = Update(update_id=2, message=m2)
    upd2.message.from_user = User(id=USER, first_name="Tester", is_bot=False)
    await bot.on_media(upd2, ctx)
    t2 = m2.all_text()
    ok("video receive hui (duration + mode buttons)", "Video received" in t2, t2[:200])
    ok("mode buttons aaye", {"clmode:smart", "clmode:equal", "clorient:169", "clorient:916",
                            "clipgo"} <= set(m2.cb_data()), m2.cb_data())
    ok("src temp file bani", os.path.exists(ctx.user_data.get("clip_src") or ""), ctx.user_data.get("clip_src"))

    # mode + orientation choose → clipgo
    q = FakeQuery("clmode:smart", uid=USER)
    await bot.on_cb(Update(update_id=3, callback_query=q), ctx)
    ok("mode choose hua (Best Moments)", ctx.user_data.get("clip_mode") == "smart", ctx.user_data)
    q2 = FakeQuery("clorient:916", uid=USER)
    await bot.on_cb(Update(update_id=4, callback_query=q2), ctx)
    ok("orientation choose hui", ctx.user_data.get("clip_vert") is True, ctx.user_data)

    before = dbm.get_credits(USER)
    q3 = FakeQuery("clipgo", uid=USER)
    await bot.on_cb(Update(update_id=5, callback_query=q3), ctx)
    # job background task me chalta hai — complete hone tak ruko
    for _ in range(240):                       # peeche chal raha job pura hone tak ruko
        await asyncio.sleep(0.5)
        if dbm.get_credits(USER) == before - 1:
            break
    ok("3 clips bheji gayi (9:16)", len(ctx.bot.videos) >= 3, [v["caption"][:40] for v in ctx.bot.videos])
    if ctx.bot.videos:
        v0 = ctx.bot.videos[0]
        ok("clip caption me number + size", "Clip" in v0["caption"] and "MB" in v0["caption"], v0["caption"])
        ok("send_video me duration/width/height", v0.get("width") and v0.get("height") and v0.get("duration"),
           {k: v0.get(k) for k in ("width", "height", "duration")})
        ok("best of best mark hua kisi clip par", any("Best of best" in v["caption"] for v in ctx.bot.videos),
           [v["caption"][-30:] for v in ctx.bot.videos])
        ok("clip ki asli file 0 se badi", all(v["size"] > 1000 for v in ctx.bot.videos), [v["size"] for v in ctx.bot.videos])
    ok("1 credit kata", dbm.get_credits(USER) == before - 1, (before, dbm.get_credits(USER)))
    ok("credit message aaya", any("credit used" in (t or "").lower() for _c, t in ctx.bot.texts), ctx.bot.texts[-1:])

    # 0 credits → block
    dbm.set_credits(USER, 0)
    ctx2 = Ctx()
    m3 = FakeMsg(kb_label("clips"), uid=USER)
    upd3 = Update(update_id=6, message=m3)
    upd3.message.from_user = User(id=USER, first_name="Tester", is_bot=False)
    await bot.on_text(upd3, ctx2)
    ok("0 credits par block", "ALL CREDITS USED" in m3.all_text().upper(), m3.all_text()[:150])

    # 15 min se lamba video → saaf error (metadata se pata nahi chalta to skip)
    dbm.set_credits(USER, 5)
    ctx3 = Ctx()
    ctx3.user_data["mode"] = "clips"
    vid_long = FakeVidAtt(TEST_VIDEO)
    m4 = FakeMsg(uid=USER, video=vid_long)
    upd4 = Update(update_id=7, message=m4)
    upd4.message.from_user = User(id=USER, first_name="Tester", is_bot=False)
    await bot.on_media(upd4, ctx3)
    ok("dobara video par naya src mila", os.path.exists(ctx3.user_data.get("clip_src") or ""), ctx3.user_data.get("clip_src"))

    # YouTube link (yt-dlp off) → saaf message
    ctx4 = Ctx()
    ctx4.user_data["mode"] = "clips"
    m5 = FakeMsg("https://youtu.be/dQw4w9WgXcQ", uid=USER)
    upd5 = Update(update_id=8, message=m5)
    upd5.message.from_user = User(id=USER, first_name="Tester", is_bot=False)
    await bot.on_text(upd5, ctx4)
    ok("YouTube link par saaf message (yt-dlp off)", "not available" in m5.all_text().lower()
       or "video file" in m5.all_text().lower(), m5.all_text()[:200])
    ok("YouTube fail par credit nahi kata", dbm.get_credits(USER) == 5, dbm.get_credits(USER))

    # kachra text → help card
    ctx5 = Ctx()
    ctx5.user_data["mode"] = "clips"
    m6 = FakeMsg("hello bhai", uid=USER)
    upd6 = Update(update_id=9, message=m6)
    upd6.message.from_user = User(id=USER, first_name="Tester", is_bot=False)
    await bot.on_text(upd6, ctx5)
    ok("bekaar text par help card + dobara bhejo", "CLIP MAKER" in m6.all_text()
       and "Now send the video" in m6.all_text(), m6.all_text()[:160])

    # admin status
    ctxa = Ctx()
    ma = FakeMsg("", uid=OWNER)
    upda = Update(update_id=10, message=ma)
    upda.message.from_user = User(id=OWNER, first_name="Owner", is_bot=False)
    ctxa.args = []
    await bot.cmd_clipstatus(upda, ctxa)
    ok("/clipstatus admin ko status deta hai", "CLIP MAKER — status" in ma.all_text(), ma.all_text()[:160])
    ok("status me ffmpeg ✅", "ffmpeg" in ma.all_text() and "✅" in ma.all_text(), ma.all_text()[:200])


build_test_videos()
test_engine()
asyncio.run(flows())

print("\n" + "=" * 70)
print(f"V43 CLIP MAKER — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
for f in FAIL:
    print("  ❌", f)
print("=" * 70)
sys.exit(1 if FAIL else 0)
