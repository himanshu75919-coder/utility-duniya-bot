# -*- coding: utf-8 -*-
"""
v76 SELFTEST — 🎓 STUDENT STUDIO (v72.1)
=========================================
User ka order (7 Oct 2026): "Students Pack" — teen tools:
  1. 🎯 GK Quiz Challenge (roz 5 sawal, score + streak)
  2. 🏛️ Yojana Checker (profile → kaunsi sarkari yojana milegi)
  3. 📊 Marks Calculator (% + grade + division, aur "kitne chahiye")

Rules (bot ke standing orders):
  • 100% FREE (premium count 37 hi rahega)
  • Poora OFFLINE — koi website/API nahi (kabhi fail nahi hoga)
  • Cards: box title + patli lines, koi moti line (━) nahi
  • Crash-proof: galat input par saaf message, khaali card kabhi nahi

Sab kuch 100% OFFLINE test hota hai (nakli Telegram par poora flow).
"""
import os
import sys
import tempfile
import time
import warnings

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv76_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V76"
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


print("=" * 62)
print("  v76 SELFTEST — 🎓 STUDENT STUDIO (GK Quiz + Yojana + Marks)")
print("=" * 62)

import bot                                                        # noqa: E402
from modules import student_hub as SH                             # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()

# =====================================================================
section("1) GK Quiz — sawal bank ki safai (91 sawal)")
check("questions 80+ hain (bada bank)", len(SH.QUESTIONS) >= 80, str(len(SH.QUESTIONS)))
_bad = [i for i, q in enumerate(SH.QUESTIONS)
        if len(q[1]) != 4 or not (0 <= q[2] <= 3) or not str(q[0]).strip()]
check("har sawal: 4 option + sahi index + sawal text (koi kharab nahi)", not _bad, str(_bad[:5]))
check("har sawal me chhota fact bhi hai (gyaan ke saath)",
      all(str(q[3]).strip() for q in SH.QUESTIONS))
_opts_bad = [i for i, q in enumerate(SH.QUESTIONS) if len(set(q[1])) != 4]
check("kisi sawal me option repeat nahi", not _opts_bad, str(_opts_bad[:5]))
# Bihar + India + Science + Sports coverage
_all = " ".join(str(q[0]) + " " + " ".join(str(o) for o in q[1]) + " " + str(q[3])
               for q in SH.QUESTIONS).lower()
check("Bihar GK coverage hai (Patna/Nalanda/Bodh Gaya...)", "bihar" in _all and "nalanda" in _all)
check("India GK coverage hai (rashtrapita/railway...)", "bharat" in _all or "india" in _all)
check("Science coverage hai (photosynthesis/gravity...)", "photosynthesis" in _all or "gravity" in _all)

check("daily_set deterministic (same uid+date = same set)",
      SH.daily_set(12345, "2026-10-07") == SH.daily_set(12345, "2026-10-07"))
check("alag user = alag set", SH.daily_set(12345, "2026-10-07") != SH.daily_set(99999, "2026-10-07"))
check("alag din = (aksar) alag set", SH.daily_set(12345, "2026-10-07") != SH.daily_set(12345, "2026-10-08"))
_s = SH.daily_set(12345, "2026-10-07")
check("daily set me 5 alag sawal", len(_s) == 5 and len(set(_s)) == 5, str(_s))
check("q_at bounds-safe (kharab index par crash nahi)", SH.q_at(99999) is not None)

# =====================================================================
section("2) Marks Calculator — teeno mode + error handling")
_r = SH.parse_marks("350/500")
check("mode ratio: 350/500 → 70%", _r.get("ok") and abs(_r["pct"] - 70.0) < 0.01, str(_r))
check("ratio: grade B2 nikla", _r.get("grade") == "B2", str(_r.get("grade")))
check("ratio: division First 🥇", "First" in str(_r.get("division")))
_r2 = SH.parse_marks("80 75 90 66")
check("mode subjects: 4 subject → total 400", _r2.get("ok") and _r2.get("total") == 400.0, str(_r2))
check("subjects: 311/400 = 77.75%", abs(_r2.get("pct", 0) - 77.75) < 0.01, str(_r2.get("pct")))
_r3 = SH.parse_marks("chahiye 33 500 350")
check("mode need: pass target already done → passed=True",
      _r3.get("ok") and _r3.get("passed") is True, str(_r3))
_r4 = SH.parse_marks("chahiye 60 500 200")
check("mode need: 60% chahiye, 200 hai → 100 aur chahiye",
      _r4.get("ok") and abs(_r4.get("left", 0) - 100.0) < 0.01, str(_r4))
_r5 = SH.parse_marks("990/1000")
check("99% → grade A1", _r5.get("grade") == "A1", str(_r5.get("grade")))
_r6 = SH.parse_marks("25/100")
check("25% → Fail division + grade E", "Fail" in str(_r6.get("division")) and _r6.get("grade") == "E")
_r7 = SH.parse_marks("xyz")
check("bakwas input: ok=False + SAFA error (crash nahi)",
      _r7.get("ok") is False and bool(_r7.get("error")), str(_r7))
_r8 = SH.parse_marks("42")
check("akela number: saaf error", _r8.get("ok") is False and bool(_r8.get("error")))
check("grades table 8 step ka hai", len(SH.GRADES) == 8, str(len(SH.GRADES)))

# =====================================================================
section("3) Yojana Checker — eligibility logic")
check("schemes 25+ hain (Central + Bihar)", len(SH.SCHEMES) >= 25, str(len(SH.SCHEMES)))
_f = SH.match_schemes("farmer", "male", 100000)
_fn = [s["n"] for s in _f]
check("kisan ko PM Kisan milta hai", any("PM Kisan" in n for n in _fn), str(_fn[:4]))
check("kisan ko PMFBY (fasal bima) milta hai", any("PMFBY" in n for n in _fn))
_st = [s["n"] for s in SH.match_schemes("student", "male", 150000)]
check("student ko scholarship milti hai",
      any("Scholarship" in n or "Credit Card" in n for n in _st), str(_st[:5]))
_st_rich = [s["n"] for s in SH.match_schemes("student", "male", 900000)]
check("8 lakh wale student ko income-cap scholarship NAHI milti",
      not any("Post Matric" in n for n in _st_rich), str(_st_rich[:5]))
_w = [s["n"] for s in SH.match_schemes("women", "female", 50000)]
check("mahila ko Ladli Behna / Sukanya jaisi schemes milti hain",
      any("Ladli Behna" in n or "Sukanya" in n for n in _w), str(_w[:5]))
_wm = [s["n"] for s in SH.match_schemes("women", "male", 50000)]
check("purush ko mahila-ONLY scheme NAHI milti (Ladli Behna/Widow/Matru)",
      not any(("Ladli Behna" in n) or ("Widow" in n) or ("Matru" in n) for n in _wm),
      str(_wm[:5]))
_old = [s["n"] for s in SH.match_schemes("old", "", 50000)]
check("60+ ko pension schemes milti hain",
      any("Pension" in n for n in _old), str(_old[:4]))
_all = SH.match_schemes("all", "", 1e12)
check("'all + no income limit' par bhi list khali nahi", len(_all) >= 5, str(len(_all)))
check("result me 8 se zyada par card limit lagata hai (query fine)",
      len(SH.match_schemes("farmer", "male", 0)) >= 1)
check("match crash-proof: bakwas input par bhi list",
      isinstance(SH.match_schemes("xyz", "abc", 0), list))

# =====================================================================
section("4) Cards — box + patli lines + safety")
_c1 = bot.gkq_next_card(0, 0)
check("quiz card boxed title", _c1.startswith("┏") and "┗" in _c1)
check("quiz card me 4 option (A-D)", all(f"{x})" in _c1 for x in "ABCD"))
check("quiz card me moti line nahi", "━" not in _c1)
_c2 = bot.gkq_after_card(0, 1, False)
check("feedback card: sahi jawab par ✅", "✅" in _c2)
_c3 = bot.gkq_after_card(0, 0, False)
check("feedback card: galat par ❌ + sahi jawab dikhata", "❌" in _c3 and "Sahi jawab" in _c3)
_c4 = bot.gkq_result_card(777001, 4, 5)
check("result card: score 4/5 dikhta", "4/5" in _c4)
check("result card: streak/best save hoke dikhta", "Streak" in _c4 and "Best" in _c4)
_c5 = bot.gkq_result_card(777002, 5, 5, practice=True)
check("practice card me streak NAHI likhti", "Streak" not in _c5 and "practice" in _c5.lower())
_c5b = bot.gkq_result_card(777002, 5, 5, practice=True)
check("practice se store nahi banta (dobara same result)",
      "Streak" not in _c5b)
_mk = bot.marks_card(SH.parse_marks("350/500"))
check("marks card: percentage + grade + division dikhta",
      "70.00%" in _mk and "B2" in _mk and "First" in _mk)
_mk2 = bot.marks_card(SH.parse_marks("chahiye 60 500 200"))
check("marks card (need mode): 'Aur chahiye' dikhta", "Aur chahiye" in _mk2)
_yj = bot.yoj_card("farmer", "male", "100000", SH.match_schemes("farmer", "male", 100000))
check("yojana card: schemes list dikhti", "fit lagte ho" in _yj)
check("yojana card: imaandar disclaimer hai (final office par)",
      "office/CSC" in _yj)
check("sab card me moti line (━) nahi",
      all("━" not in x for x in (_c1, _c2, _c3, _c4, _mk, _mk2, _yj)))
check("khaali match par bhi khaali card nahi",
      len(bot.yoj_card("xyz", "", "100000", [])) > 100)

# =====================================================================
section("5) Wiring — keyboard, mode, free, prompts")
_kb = [bot.unbold(b) for r in bot.KB_BTNS for b in r]
check("keyboard me STUDENT STUDIO button", any("STUDENT STUDIO" in x.upper() for x in _kb))
check("BTN_MODE_MAP: STUDENT STUDIO → stud", bot.BTN_MODE_MAP.get("STUDENT STUDIO") == "stud")
check("BTN_MODE_MAP: GK QUIZ → gkq_start", bot.BTN_MODE_MAP.get("GK QUIZ") == "gkq_start")
check("BTN_MODE_MAP: YOJANA CHECKER → yoj_open", bot.BTN_MODE_MAP.get("YOJANA CHECKER") == "yoj_open")
check("BTN_MODE_MAP: MARKS CALCULATOR → stud_marks", bot.BTN_MODE_MAP.get("MARKS CALCULATOR") == "stud_marks")
check("FREE hai — PREMIUM_TOOLS me nahi aur count 37",
      "stud" not in bot.PREMIUM_TOOLS and len(bot.PREMIUM_TOOLS) == 37,
      str(len(bot.PREMIUM_TOOLS)))
check("stud_marks ka rate-limit entry hai", bot.TOOL_RATE_LIMITS.get("stud_marks") is not None)
check("VIP wall par bhi khulta hai (gkq/yoj/stud prefixes)",
      bot.vip_free_cb("gkq_start") and bot.vip_free_cb("yoj_open") and bot.vip_free_cb("stud_open"))
check("PROMPT_DATA me stud_marks hai", "stud_marks" in bot.PROMPT_DATA)
_p = bot.tool_prompt("stud_marks")
check("marks prompt boxed + 🔗 line + 1 example",
      _p.startswith("┏") and "🔗" in _p and "350/500" in _p)
check("prompt me Tip/gyaan nahi (user ka order)",
      "Tip" not in _p and "💡" not in _p)
check("on_text me stud_marks handler hai", 'if mode == "stud_marks":' in BOT_SRC)
check("callbacks sab wired",
      all(x in BOT_SRC for x in ('"stud_open"', '"gkq_start"', '"gkq_prac"',
                                 'startswith("gkq_ans:")', 'startswith("yoj_g:")',
                                 'startswith("yoj_w:")', 'startswith("yoj_i:")',
                                 '"yoj_back_w"', '"stud_marks"')))
check("import hai", "from modules import student_hub as SH" in BOT_SRC)

# =====================================================================
section("6) E2E — nakli Telegram par poora quiz + marks (offline)")
import asyncio                                                    # noqa: E402


class _QMsg:
    def __init__(self):
        self.chat = type("C", (), {"id": 55})()
        self.out = []

    async def edit_text(self, txt, **kw):
        self.out.append(txt)
        return self

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        return self


class _Q:
    def __init__(self, data, uid):
        self.data = data
        self.from_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.message = _QMsg()

    async def answer(self, text=None, show_alert=False):
        pass


class _Upd:
    def __init__(self, q):
        self.callback_query = q
        self.effective_user = q.from_user
        self.effective_chat = q.from_user


class _Ctx:
    def __init__(self):
        self.user_data = {}
        self.bot = object()


async def _flow():
    uid = 808080
    c = _Ctx()
    # -- STUDENT STUDIO open --
    q0 = _Q("stud_open", uid)
    await bot.on_cb(_Upd(q0), c)
    _t0 = q0.message.out[-1]
    check("E2E: intro me teeno tools dikhte hain",
          "GK Quiz" in bot.unbold(_t0) and "Yojana" in _t0 and "Marks" in _t0)

    # -- quiz start --
    q1 = _Q("gkq_start", uid)
    await bot.on_cb(_Upd(q1), c)
    _t1 = q1.message.out[-1]
    check("E2E: quiz shuru hua (Sawal 1)", "Sawal 1" in _t1)
    idxs = list(c.user_data.get("gkq_idx") or [])
    check("E2E: 5 sawal ka set bana", len(idxs) == 5, str(idxs))

    # -- saare 5 sahi jawab do --
    last = None
    for step in range(5):
        qi = idxs[step]
        ans = SH.q_at(qi)[2]
        qa = _Q(f"gkq_ans:{qi}:{ans}", uid)
        await bot.on_cb(_Upd(qa), c)
        last = qa.message.out[-1]
    check("E2E: 5/5 sahi par result card", "5/5" in last and "QUIZ POORA" in bot.unbold(last))
    check("E2E: streak 1 din dikha", "Streak" in last and "1 din" in last)
    check("E2E: session saaf ho gaya (dobara quiz fresh)",
          c.user_data.get("gkq_idx") is None)

    # -- galat jawab wala flow bhi --
    q3 = _Q("gkq_start", uid)
    await bot.on_cb(_Upd(q3), c)
    _idx2 = list(c.user_data.get("gkq_idx") or [])
    qi2 = _idx2[0]
    wrong = (SH.q_at(qi2)[2] + 1) % 4
    qw = _Q(f"gkq_ans:{qi2}:{wrong}", uid)
    await bot.on_cb(_Upd(qw), c)
    _tw = qw.message.out[-1]
    check("E2E: galat jawab par sahi jawab dikhaya", "❌" in _tw and "Sahi jawab" in _tw)
    check("E2E: agla sawal aa gaya", "Sawal" in bot.unbold(_tw))
    # chhod do
    qs = _Q("stud_open", uid)
    await bot.on_cb(_Upd(qs), c)
    check("E2E: beech me chhodna bhi safe", "STUDENT STUDIO" in bot.unbold(qs.message.out[-1]).upper())

    # -- yojana flow --
    qy1 = _Q("yoj_open", uid)
    await bot.on_cb(_Upd(qy1), c)
    check("E2E: yojana sawal 1 (gender)", "purush" in bot.unbold(qy1.message.out[-1]).lower())
    qy2 = _Q("yoj_g:male", uid)
    await bot.on_cb(_Upd(qy2), c)
    check("E2E: yojana sawal 2 (kaam)", "karte hain" in bot.unbold(qy2.message.out[-1]).lower())
    qy3 = _Q("yoj_w:farmer", uid)
    await bot.on_cb(_Upd(qy3), c)
    check("E2E: yojana sawal 3 (aay)", "saalana" in bot.unbold(qy3.message.out[-1]).lower())
    qy4 = _Q("yoj_i:100000", uid)
    await bot.on_cb(_Upd(qy4), c)
    _ty = qy4.message.out[-1]
    check("E2E: yojana result card (kisan ke liye)",
          "fit lagte ho" in _ty and "PM Kisan" in _ty)
    qy5 = _Q("yoj_back_w", uid)
    await bot.on_cb(_Upd(qy5), c)
    check("E2E: wapas jaane par crash nahi", "karte hain" in bot.unbold(qy5.message.out[-1]).lower())


asyncio.run(_flow())


# -- marks via on_text (asli handler) --
class _MsgT:
    def __init__(self, text):
        self.text = text
        self.out = []

    async def reply_text(self, txt, **kw):
        self.out.append(txt)
        return self


class _UpdT:
    def __init__(self, text, uid):
        self.effective_user = type("U", (), {"id": uid, "first_name": "T", "username": "t"})()
        self.effective_chat = self.effective_user
        self.message = _MsgT(text)
        self.callback_query = None


async def _marks_flow():
    uid = 707070
    c = _Ctx()
    um = _UpdT("350/500", uid)
    c.user_data["mode"] = "stud_marks"
    await bot.on_text(um, c)
    _tm = um.message.out[-1]
    check("E2E marks: 350/500 → card aaya (70%)", "70.00%" in _tm)
    check("E2E marks: mode saaf ho gaya", c.user_data.get("mode") is None)
    um2 = _UpdT("bukwaas", uid)
    c.user_data["mode"] = "stud_marks"
    await bot.on_text(um2, c)
    _tm2 = um2.message.out[-1]
    check("E2E marks: galat input par saaf error (crash nahi)", "❌" in _tm2 and "Example" in _tm2)


asyncio.run(_marks_flow())

print(f"\n{'=' * 62}")
print(f"  v76 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
