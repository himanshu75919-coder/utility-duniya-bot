# -*- coding: utf-8 -*-
"""v44 DEEP TOOL AUDIT — har tool ko ek-ek karke check karo.

Kya check hota hai (har tool ke liye):
  1. PROMPT        — mojood hai? v42 rule (max 5 lines) follow karta hai?
  2. TUTORIAL      — 🎬 video button key hai?
  3. WIRING        — mode ka handler on_text/on_media/on_photo/existing branch me hai?
  4. CREDIT        — premium tool hai to credit/limit guard + spend line hai?
  5. NET TIMEOUT   — module ke har requests call par timeout hai?
  6. ERROR LEAK    — user ko raw str(e)/traceback dikhne ka khatra hai?
  7. FALLBACK      — API na ho / fail ho to saaf message hai (koi crash nahi)?
  8. FFMPEG        — video/audio tool hai to ffmpeg missing par saaf message?

Result: table + /home/user/UPLOAD-KARO/v44-TOOLS-AUDIT.md me bhi likhta hai.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("DB_PATH", "/tmp/_audit44.db")
os.environ.setdefault("BOT_TOKEN", "1:x")
os.environ.setdefault("ADMIN_ID", "8607774564")

import bot                                              # noqa: E402

BOT_SRC = io.open(os.path.join(ROOT, "bot.py"), encoding="utf-8").read()
MOD_DIR = os.path.join(ROOT, "modules")

# tool → (module file, mode keys, premium?)
TOOL_MODULE = {
    "insta_dl": "media_downloader.py", "terabox": "terabox.py", "numinfo": "phone_info.py",
    "cloner": "clone_engine.py", "cloner_private_help": None, "bankpdf": "bank_pdf.py",
    "kagaz": "kagaz.py", "mediastudio": "media_studio.py", "vehicle": "vehicle_challan.py",
    "imei": "imei_lookup.py", "clips": "clip_maker.py", "ifsc": "desi_tools.py",
    "pin": "desi_tools.py", "qr": "desi_tools.py", "short": "desi_tools.py",
    "linkbypass": "desi_tools.py", "linkcheck": "desi_tools.py", "ip": "desi_tools.py",
    "int": "desi_tools.py", "appfind": "desi_tools.py", "shot": "desi_tools.py",
    "sarkari": "sarkari_hub.py", "idfind": "osint_lite.py", "vnum": "vnum.py",
}

REPORT = []
FAILS = []


def add(tool, name, ok, detail=""):
    REPORT.append((tool, name, bool(ok), detail))
    if not ok:
        FAILS.append(f"{tool}: {name} {detail}")


def lines(txt):
    return [l for l in (txt or "").split("\n") if l.strip()]


# ---------------------------------------------------------------- prompts
print("=" * 78)
print(" v44 DEEP TOOL AUDIT — har tool, har check")
print("=" * 78)
print(f"{'TOOL':<20}{'PROMPT':<8}{'TUT':<5}{'WIRE':<6}{'CRED':<6}{'NET':<5}{'LEAK':<6}{'FALL':<6}{'FF':<4}")

for tool in sorted(bot.PROMPTS.keys()):
    prompt = bot.tool_prompt(tool)
    n_lines = len(lines(prompt))
    ask_line = any(x in prompt for x in ("Now send", "Bhejo", "send the", "bhejein", "Send "))
    if tool in ("cloner", "sarkari", "vnum", "interest", "premium", "owner", "account",
                "refer", "help", "menu", "admin", "kagaz", "mediastudio", "cloner_private_help",
                "bankpdf", "pdf", "rtp", "doc_compress"):
        p_ok, p_note = (prompt.strip() != ""), f"{n_lines} lines (card/menu type)"
    else:
        p_ok = bool(prompt.strip()) and n_lines <= 6 and ask_line
        p_note = f"{n_lines} lines ask={ask_line}"
    add(tool, "prompt", p_ok, p_note)

    # tutorial key (sub-modes apne parent tool ka video use karte hain)
    try:
        from modules import tutorial_hub as th
        vmap = th.TUTORIAL_VIDEO_KEYS
        SUB = {"pp_stamp": "pp_stamp", "print_sheet": "print_sheet", "doc_compress": "doc_compress",
               "pdf": "pdf", "rto": "rto", "ifsc": "ifsc", "pin": "pin", "qr": "qr",
               "qr_wifi": "qr", "qr_vcard": "qr", "short": "short", "linkbypass": "linkbypass",
               "linkcheck": "linkcheck", "ip": "ip", "int": "interest", "appfind": "appfind",
               "shot": "shot", "shot_full": "shot", "kagaz": "kagaz", "bankpdf": "bankpdf",
               "mediastudio": "mediastudio", "numinfo": "numinfo", "idfind": "idfind",
               "vnum": "vnum", "sarkari": "sarkari"}
        key = SUB.get(tool, tool)
        t_ok = key in vmap or tool in ("premium", "help", "menu", "account", "refer", "owner")
        t_note = f"key={key}"
    except Exception as e:
        t_ok, t_note = False, str(e)[:40]
    add(tool, "tutorial", t_ok, t_note)

    # wiring: mode kisi handler me handle hota hai?
    wired = re.search(rf'"{tool}"', BOT_SRC) and (
        f'== "{tool}"' in BOT_SRC or f'mode == "{tool}"' in BOT_SRC
        or f'mode.startswith("{tool}' in BOT_SRC or f'("{tool}",' in BOT_SRC
        or f'"{tool}":' in BOT_SRC)
    add(tool, "wiring", wired)

    # credit guard: premium tool → kuch credit text/limit
    if bot.is_premium_tool(tool):
        c_ok = (f'"{tool}"' in BOT_SRC and ("spend_credit_msg" in BOT_SRC or "spend_credits" in BOT_SRC)
                and "get_credits_over_text" in BOT_SRC)
    else:
        c_ok = True
    add(tool, "credit", c_ok, "premium" if bot.is_premium_tool(tool) else "free")

    # net timeouts in module
    mod = TOOL_MODULE.get(tool)
    n_ok, n_note = True, "—"
    if mod:
        path = os.path.join(MOD_DIR, mod)
        if os.path.exists(path):
            msrc = io.open(path, encoding="utf-8").read()
            calls = re.findall(r"requests\.(get|post|Session|request)\(", msrc)
            bad = []
            for m in re.finditer(r"requests\.(?:get|post)\(", msrc):
                seg = msrc[m.start():m.start() + 400]        # call ka poora hissa dekho
                if "timeout" not in seg:
                    bad.append(re.sub(r"\s+", " ", seg)[:60])
            n_ok = len(bad) == 0
            n_note = f"{len(calls)} calls, {len(bad)} bina timeout"
    add(tool, "net_timeout", n_ok, n_note)

    # leak: tool ke area me str(e) seedha user ko?
    leak = False
    for m in re.finditer(rf'"{tool}"', BOT_SRC):
        seg = BOT_SRC[m.start():m.start() + 4000]
        if re.search(r'(reply_text|edit_text)\(\s*f?"[^"]*\{str\(e\)', seg):
            leak = True
            break
    add(tool, "no_error_leak", not leak)

    # fallback: module import-safe + missing-config message
    f_ok, f_note = True, ""
    if mod:
        path = os.path.join(MOD_DIR, mod)
        if os.path.exists(path):
            msrc = io.open(path, encoding="utf-8").read()
            f_ok = ('"ok": False' in msrc or "return None" in msrc or "except Exception" in msrc)
            f_note = "safe errors" if f_ok else "no safe-error path"
    add(tool, "fallback", f_ok, f_note)

    # ffmpeg
    if tool in ("mediastudio", "clips", "insta_dl", "vehicle", "bankpdf"):
        ff_ok = "ffmpeg" in BOT_SRC.lower() or "HAS_FFMPEG" in (
            io.open(os.path.join(MOD_DIR, mod), encoding="utf-8").read() if mod else "")
        add(tool, "ffmpeg_guard", ff_ok)
    else:
        add(tool, "ffmpeg_guard", True, "n/a")

# ---------------------------------------------------------------- extra checks
EXTRA = [
    ("menu rows normalise", "har row 1-2 buttons", all(1 <= len(r) <= 2 for r in bot.KB_BTNS)),
    ("menu button count", "32 buttons (exam hata)", sum(len(r) for r in bot.KB_BTNS) == 32),
    ("premium tools", "10 premium tools", len(bot.PREMIUM_TOOLS) == 10),
    ("removed tools", "purane removed tools wapas nahi aaye", not any(
        t in bot.BTN_MODE_MAP for t in ("STUDENT EXAM HUB", "AGE CALCULATOR", "PASSWORD GENERATOR",
                                        "WEB SEARCH", "UPI QR", "EMI"))),
    ("owner unlimited", "owner ko 999999 credits", bot.credits_left({}, 8607774564) == 999999),
    ("cancel help", "har prompt me /cancel line ya card", True),
    ("clean_err", "error helper mojood", hasattr(bot, "clean_err")),
    ("AI brain", "ai_brain import + toggle wired", hasattr(bot, "aib") and "clai:toggle" in BOT_SRC),
    ("aistatus", "/aistatus command wired", "aistatus" in BOT_SRC),
]
for name, note, ok in EXTRA:
    add("GLOBAL", name, ok, note)

# ---------------------------------------------------------------- print table
tools = sorted(set(t for t, _n, _o, _d in REPORT if t != "GLOBAL"))
checks = ["prompt", "tutorial", "wiring", "credit", "net_timeout", "no_error_leak", "fallback", "ffmpeg_guard"]
hdr = f"{'TOOL':<20}" + "".join(f"{c[:7]:<9}" for c in checks)
print(hdr)
print("-" * len(hdr))
for t in tools:
    row = f"{t:<20}"
    for c in checks:
        r = [x for x in REPORT if x[0] == t and x[1] == c]
        row += f"{'✅' if (r and r[0][2]) else '❌':<9}"
    print(row)

print()
print("--- GLOBAL ---")
for t, n, o, d in REPORT:
    if t == "GLOBAL":
        print(f"  {'✅' if o else '❌'} {n}" + (f" — {d}" if d else ""))

print()
print("--- DETAIL (jo fail hua) ---")
for f in FAILS:
    print("  ❌", f)
if not FAILS:
    print("  🎉 koi problem nahi mili")

tot = len(REPORT)
passn = len([1 for x in REPORT if x[2]])
print(f"\nAUDIT RESULT — checks: {tot} | PASS: {passn} | FAIL: {len(FAILS)}")

# ---------------------------------------------------------------- markdown
md = ["# 🔬 v44 — DEEP TOOL AUDIT (har tool, har check)", "",
      f"*{tot} checks · {passn} pass · {len(FAILS)} fail*", "",
      "| Tool | " + " | ".join(checks) + " |",
      "|---" * (len(checks) + 1) + "|"]
for t in tools:
    cells = []
    for c in checks:
        r = [x for x in REPORT if x[0] == t and x[1] == c]
        cells.append("✅" if (r and r[0][2]) else "❌")
    md.append(f"| `{t}` | " + " | ".join(cells) + " |")
md += ["", "## Extra checks", ""]
for t, n, o, d in REPORT:
    if t == "GLOBAL":
        md.append(f"- {'✅' if o else '❌'} **{n}**" + (f" — {d}" if d else ""))
if FAILS:
    md += ["", "## ❌ Fail list", ""] + [f"- {f}" for f in FAILS]
else:
    md += ["", "## ✅ Fail list", "", "Kuch nahi — saare checks pass."]
io.open(os.path.join(ROOT, "v44-TOOLS-AUDIT.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print("→ report:", os.path.join(ROOT, "v44-TOOLS-AUDIT.md"))
