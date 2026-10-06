# -*- coding: utf-8 -*-
"""
v72 SELFTEST — 🕵️ USERNAME HUNTER (public profiles only)
==========================================================
Boss ka order: "Username Hunter" tool banao — dikhne me spy-jaisa, kaam 100% legal:
  • Sirf PUBLIC profile pages check hoti hain (jaise browser me naam daalna)
  • Koi login / password / OTP / session NAHI
  • Site block kare to "⚪ check nahi ho paya" — kuch zabardasti nahi
  • Kabhi crash nahi karta
"""
import os
import re
import sys
import tempfile
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

warnings.filterwarnings("ignore")
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv72_")
os.environ["DB_PATH"] = os.path.join(_TMP, "t.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_V72"
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
print("  v72 SELFTEST — 🕵️ USERNAME HUNTER (sirf public profiles)")
print("=" * 62)

import bot                                                          # noqa: E402
from modules import username_hunter as UH                            # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()


def _clean(t):
    return re.sub(r"</?(?:b|code|i|blockquote|a[^>]*)>", "", str(t or ""))


# =====================================================================
section("[A] 🧩 MODULE — sites list + username validation")
# =====================================================================
check("module import ho gaya", UH is not None)
check("30+ sites hain", len(UH.SITES) >= 30, f"len={len(UH.SITES)}")
check("sab sites https hain", all(s[2].startswith("https://") for s in UH.SITES))
check("har site ke url me '{}' placeholder hai", all("{}" in s[2] for s in UH.SITES))
_cats = {s[1] for s in UH.SITES}
check("categories sahi hain",
      _cats <= {"dev", "social", "creative", "music", "video", "gaming", "other"},
      str(_cats))
check("koi duplicate site naam nahi",
      len({s[0] for s in UH.SITES}) == len(UH.SITES))

check("bahut chhota username reject hota hai",
      UH.hunt_username("ab").get("ok") is False)
check("space/emoji wala username reject hota hai",
      UH.hunt_username("ra hu😀l").get("ok") is False)
check("bahut lamba username reject hota hai",
      UH.hunt_username("a" * 40).get("ok") is False)
check("None/khali input par bhi SAFE jawab (crash nahi)",
      UH.hunt_username(None).get("ok") is False and UH.hunt_username("").get("ok") is False)
check("'@' laga ke bhejo to bhi saaf ho jata hai", UH._clean("@rahul_99") == "rahul_99")


# =====================================================================
section("[B] 🌐 ASLI CHECK (local mock sites — offline test)")
# =====================================================================
_MARK = "actual_persona_name"


class _MockSites(BaseHTTPRequestHandler):
    def log_message(self, *a):                                # noqa: ANN002
        pass

    def do_GET(self):
        p = self.path.rstrip("/")
        if p == "/found":
            self.send_response(200); self.end_headers(); self.wfile.write(b"<html>ok</html>")
        elif p == "/missing":
            self.send_response(404); self.end_headers(); self.wfile.write(b"nope")
        elif p == "/blocked":
            self.send_response(403); self.end_headers(); self.wfile.write(b"blocked")
        elif p == "/marker-ok":
            self.send_response(200); self.end_headers()
            self.wfile.write(f"<html>{_MARK}</html>".encode())
        elif p == "/marker-gone":
            self.send_response(200); self.end_headers()
            self.wfile.write(b"<html>profile not found</html>")
        elif p == "/bad-marker":
            self.send_response(200); self.end_headers()
            self.wfile.write(b"<html>User not found</html>")
        elif p == "/marker-sub":
            self.send_response(200); self.end_headers()
            self.wfile.write(b"<html>rahul_99 - Twitch</html>")
        else:
            self.send_response(500); self.end_headers(); self.wfile.write(b"err")


_srv = ThreadingHTTPServer(("127.0.0.1", 0), _MockSites)
_port = _srv.server_address[1]
threading.Thread(target=_srv.serve_forever, daemon=True).start()
_B = f"http://127.0.0.1:{_port}"

_orig_sites = UH.SITES
UH.SITES = (
    ("FoundSite", "dev", _B + "/found"),
    ("MissingSite", "social", _B + "/missing"),
    ("BlockSite", "other", _B + "/blocked"),
    ("MarkerOk", "gaming", _B + "/marker-ok", _MARK),
    ("MarkerGone", "music", _B + "/marker-gone", _MARK),
    ("BadMarker", "dev", _B + "/bad-marker", None, "User not found"),
    ("MarkerSub", "video", _B + "/marker-sub", "{} - Twitch"),
)
UH._CACHE.clear()
_r = UH.hunt_username("rahul_99", timeout=5, workers=5)
_found_names = [f["site"] for f in _r.get("found") or []]
check("200 wali site 'mila' me aati hai", "FoundSite" in _found_names, str(_found_names))
check("marker wali site (200 + marker) bhi 'mila' me",
      "MarkerOk" in _found_names, str(_found_names))
check("404 wali site 'nahi mila' me ginti me jaati hai", _r.get("not_found") == 3,
      str(_r.get("not_found")))
check("403 (blocked) site '⚪ check nahi ho paya' me jaati hai",
      _r.get("unknown") == ["BlockSite"], str(_r.get("unknown")))
check("200 par bhi marker na mile to 'nahi mila' (soft-404 pakda gaya)",
      "MarkerGone" not in _found_names and _r.get("not_found") == 3)
check("bad-marker wali site (200 + 'User not found') jhooti positive nahi banti",
      "BadMarker" not in _found_names)
check("marker me {} ki jagah username lagta hai (Twitch jaisa)",
      "MarkerSub" in _found_names, str(_found_names))
check("checked count sahi", _r.get("checked") == 7, str(_r.get("checked")))
check("response time record hota hai (ms > 0)", float(_r.get("ms") or 0) > 0)
check("mila wale me url bhi aata hai (public profile ka pata)",
      all(f.get("url", "").startswith("http") for f in _r.get("found") or []))

_r2 = UH.hunt_username("rahul_99", timeout=5, workers=5)
check("dobara maangne par CACHE se jawab (site dobara nahi khujli)",
      _r2.get("cached") is True, str(_r2.get("cached"))[:60])

_r3 = UH.hunt_username("kisi_aur_ka_naam", timeout=5, workers=5)
check("naya username par taaza check hota hai (cache alag)",
      _r3.get("ok") is True and not _r3.get("cached"))

UH.SITES = (("DeadSite1", "dev", "http://127.0.0.1:1/x"), ("DeadSite2", "dev", "http://127.0.0.1:1/y"))
UH._CACHE.clear()
_r4 = UH.hunt_username("koi_naam", timeout=2, workers=2)
check("saari sites dead ho to bhi CRASH nahi (ok=True, found khali)",
      _r4.get("ok") is True and _r4.get("found") == [], str(_r4)[:120])
check("dead sites 'unknown' me ginti me aati hain", len(_r4.get("unknown") or []) == 2)
_srv.shutdown()
UH.SITES = _orig_sites


# =====================================================================
section("[C] 🖼️ CARD — premium look, saaf numbers, moti line nahi")
# =====================================================================
_card = _clean(bot.uhunt_card({
    "username": "rahul_99",
    "found": [{"site": "GitHub", "cat": "dev", "url": "https://github.com/rahul_99"},
              {"site": "Reddit", "cat": "social", "url": "https://www.reddit.com/user/rahul_99"}],
    "not_found": 30, "unknown": ["Instagram", "YouTube"], "checked": 36, "ms": 4210.0}))
check("card me username dikhta hai", "rahul_99" in _card)
check("mila wali sites + unke public URLs dikhte hain",
      "GitHub" in _card and "github.com/rahul_99" in _card and "Reddit" in _card)
check("'Mila — 2 jagah' count sahi", "Mila — 2 jagah" in _card)
check("nahi mila + check nahi ho paya dono dikhte hain",
      "Nahi mila: 30" in _card and "Check nahi ho paya: 2" in _card)
check("time + sites count dikhta hai", "36 sites" in _card and "4.2s" in _card)
check("brand line end me hai", "Powered by @Supermannn_x" in _card)
check("card me moti safed line (━) bilkul nahi", "━" not in _card)
_c2 = _clean(bot.uhunt_card({"username": "ghost_user", "found": [], "not_found": 36,
                             "unknown": [], "checked": 36, "ms": 3900.0}))
check("kuch na mile to saaf line aati hai",
      "nahi mila" in _c2.lower() and "Mila —" not in _c2)
_c3 = _clean(bot.uhunt_card({}))
check("khali/None data par card crash nahi karta", isinstance(_c3, str) and len(_c3) > 0)


# =====================================================================
section("[D] 🔌 WIRING — button, mode, prompt, premium, legacy guard")
# =====================================================================
check("premium registry me 'uhunt' hai", "uhunt" in bot.PREMIUM_TOOLS)
check("premium naam registry me hai", bot.PREMIUM_TOOL_NAMES.get("uhunt") == "🕵️ Username Hunter")
check("button 'USERNAME HUNTER' mode 'uhunt' kholta hai",
      bot.BTN_MODE_MAP.get("USERNAME HUNTER") == "uhunt")
check("keyboard me naya button juda", any(
    "USERNAME HUNTER" in bot.unbold(x) for row in bot.KB_BTNS for x in row))
check("handler me 'uhunt' branch hai", 'if mode == "uhunt"' in BOT_SRC)
check("handler card builder use karta hai", "uhunt_card(" in BOT_SRC)
check("credits line lagni hai (spend_credit_msg uhunt)",
      'spend_credit_msg(uid, "uhunt")' in BOT_SRC)
check("rate-limit entry hai (10 per hour window)",
      bot.TOOL_RATE_LIMITS.get("uhunt") is not None, str(bot.TOOL_RATE_LIMITS.get("uhunt")))

_p = bot.PROMPTS.get("uhunt", "")
check("prompt boxed hai (┏ ┓)", _p.startswith("┏") and "┗" in _p)
check("prompt me 🔗 'kya bhejein' line hai", "🔗" in _p)
check("prompt me 1 asli example hai", "rahul_99" in _p)
check("prompt me koi Tip/gyaan nahi (user ka order)",
      "Tip" not in _p and "💡" not in _p and "kya aayega" not in _p.lower())
check("prompt ki aakhri line example hi hai",
      _clean(_p).strip().endswith("rahul_99"))

_rm = BOT_SRC.split("_removed_keys = {", 1)[1].split("}", 1)[0]
check("purana deleted 'USERNAME FINDER' hi guard me rehta hai (jo delete hua tha)",
      "USERNAME FINDER" in _rm)
check("naya 'USERNAME HUNTER' removed-list me NAHI hai (galat guard nahi lagega)",
      "USERNAME HUNTER" not in _rm)
check("module me legal boundary likha hai (sirf public profiles)",
      "public" in UH.__doc__.lower() and "login" in UH.__doc__.lower())


print(f"\n{'=' * 62}")
print(f"  v72 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print(f"{'=' * 62}")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS[:30]:
        print("  •", f)
sys.exit(1 if FAIL else 0)
