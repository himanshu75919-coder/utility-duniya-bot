#!/usr/bin/env python3
# =====================================================================
# v105.1 SELFTEST — 🔐 FORCE-JOIN WALL: CHANNEL REPLACE (@CypherGrid → osint_xpert)
#
# User order (11 Oct): naya channel id -1004393596502, link
# https://t.me/osint_xpert — purana channel replace karo. Owner id
# 8607774564 (pehle se ADMIN_ID setup me).
#
# Behavior:
#   · Render env me FORCE_CHANNEL/FORCE_CHANNEL_LINK set ho → Wahi chalega
#     (user ko dashboard se in 2 values ko naye channel par update/delete
#     karne ka instruction diya gaya).
#   · Env key HI missing ho → code-default: osint_xpert (wall on).
#   · Env explicitly "" set ho → wall OFF (backward compat, test-locked).
#
# Run: python3 tests/test_v1051_wall.py
# =====================================================================
import os
import re
import sys
import logging

logging.disable(logging.CRITICAL)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
FAIL = []


def ok(name, cond, extra=""):
    print(("  ✅ " if cond else "  ❌ ") + name + (("  " + str(extra)) if not cond and extra else ""))
    if not cond:
        FAIL.append(name)


import modules.core.joinwall as JW                                # noqa: E402

BOT_SRC = open(os.path.join(_ROOT, "bot.py"), encoding="utf-8").read()


def _env(**kw):
    for k, v in kw.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = str(v)


print("\n== 1) Key MISSING → code-default = osint_xpert ==")
_env(FORCE_CHANNEL=None, FORCE_CHANNEL_LINK=None, FORCE_JOIN=None)
JW.reset()
ok("channel() numeric id -1004393596502 deta hai", JW.channel() == -1004393596502, JW.channel())
ok("link() = https://t.me/osint_xpert", JW.link() == "https://t.me/osint_xpert", JW.link())
ok("enabled() True (default wall ON)", JW.enabled() is True)
_t = JW.wall_text()
ok("wall_text me naya channel clickable", "t.me/osint_xpert" in _t and "channel" in _t)
ok("wall_text me PURANA @CypherGrid kahin nahi", "CypherGrid" not in _t)
ok("DEFAULT_CHANNEL constant sahi", JW.DEFAULT_CHANNEL == "-1004393596502")
ok("DEFAULT_LINK constant sahi", JW.DEFAULT_LINK == "https://t.me/osint_xpert")

print("\n== 2) Explicit '' = wall OFF (backward compat) ==")
_env(FORCE_CHANNEL="", FORCE_CHANNEL_LINK=None, FORCE_JOIN=None)
JW.reset()
ok("channel() khaali", JW.channel() == "", JW.channel())
ok("enabled() False", JW.enabled() is False)

print("\n== 3) Explicit env jeetta hai (purana/new override) ==")
_env(FORCE_CHANNEL="@kuch_aur", FORCE_CHANNEL_LINK=None, FORCE_JOIN="on")
JW.reset()
ok("diya hua @name respect hota hai", JW.channel() == "@kuch_aur", JW.channel())
ok("link us @name se derive", JW.link() == "https://t.me/kuch_aur", JW.link())
_env(FORCE_CHANNEL="-1004393596502", FORCE_CHANNEL_LINK="https://t.me/osint_xpert", FORCE_JOIN="on")
JW.reset()
ok("env me numeric+link set ho → wahi dono",
   JW.channel() == -1004393596502 and JW.link() == "https://t.me/osint_xpert")
_env(FORCE_CHANNEL=None, FORCE_CHANNEL_LINK=None, FORCE_JOIN=None)
JW.reset()

print("\n== 4) bot.py defaults + version ==")
ok("bot.py FORCE_CHANNEL default osint id",
   'FORCE_CHANNEL = os.getenv("FORCE_CHANNEL", "-1004393596502").strip()' in BOT_SRC)
ok("bot.py FORCE_CHANNEL_LINK default",
   'FORCE_CHANNEL_LINK = os.getenv("FORCE_CHANNEL_LINK", "https://t.me/osint_xpert").strip()' in BOT_SRC)
ok("v105.1 WALL-OSINT history retained under v105.2",
   re.search(r'BOT_VERSION\s*=\s*\(?\s*"v105\.2 RAM-SAVER', BOT_SRC) is not None
   and 'v105.1 WALL-OSINT' in BOT_SRC)
ok("owner-exempt design intact (ADMIN_ID/ADMINS/FORCE_JOIN_EXEMPT)",
   "FORCE_JOIN_EXEMPT" in open(os.path.join(_ROOT, "modules", "core",
                                            "joinwall.py"), encoding="utf-8").read())

print("\n" + ("🎉 v105.1 SELFTEST: SAB PASSED" if not FAIL else "❌ FAILURES: " + "; ".join(FAIL)))
sys.exit(1 if FAIL else 0)
