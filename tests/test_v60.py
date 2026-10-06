# -*- coding: utf-8 -*-
"""
v60 SELFTEST — FORTRESS (Premium Vault + Crash Shield)
======================================================
Ye test file PROVE karti hai ki:

  A. PREMIUM-SAFE MERGE  — galat/purane backup se bhi premium KAM nahi hota
  B. PREMIUM FLOOR GUARD — restore jo VIP ghatta hai, wo ABORT ho jata hai
  C. ENCRYPTION          — backup padha nahi ja sakta, galat key se kharab nahi hota
  D. TZ-SAFE PREMIUM     — timezone wali date se premium "gayab" nahi hota (asli bug)
  E. GRANT NEVER REDUCES — galti se bhi VIP chhota nahi ho sakta
  F. ATOMIC CREDITS      — ek saath 100 tool chalao, hisaab phir bhi sahi
  G. LEDGER              — /fixvip se premium wapas aa jata hai
  H. SAFESEND            — lamba/feela hua HTML message crash nahi karta
  I. SAFECONF            — galti se env value kharab ho to bot boot par crash nahi hota
  J. GUARD               — kisi bhi handler me bug ho to bot zinda rehta hai

Chalao:  python tests/test_v60.py
"""
import asyncio
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

_TMP = tempfile.mkdtemp(prefix="udv60_")
os.environ["DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN_FOR_V60"
os.environ["ADMIN_ID"] = "1"
os.environ["VAULT_ENABLED"] = "on"

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


print("=" * 62)
print("  v60 SELFTEST — FORTRESS (Premium Vault + Crash Shield)")
print("=" * 62)

# =====================================================================
print("\n[A] PREMIUM-SAFE MERGE — premium kabhi kam nahi hota")
# =====================================================================
import warnings
warnings.filterwarnings("ignore")

from modules.core.vault import (                                     # noqa: E402
    merge_users, merge_rows, premium_max, premium_rank, encrypt_blob,
    decrypt_blob, premium_floor_report, is_lifetime, Vault,
)

# --- case 1: remote me zyada premium
local = [{"user_id": 1, "premium_until": "2026-12-31T00:00:00", "credits": 5,
          "referrals": 1, "banned": 0, "name": "A", "last_date": "2026-10-01"}]
remote = [{"user_id": 1, "premium_until": "2027-12-31T00:00:00", "credits": 3,
           "referrals": 9, "banned": 1, "name": "A2", "last_date": "2026-10-05"}]
m, rep = merge_users(local, remote)
check("remote ka zyada premium jeeta", m[0]["premium_until"] == "2027-12-31T00:00:00",
      m[0]["premium_until"])
check("credits max hue (5 vs 3 -> 5)", m[0]["credits"] == 5, m[0]["credits"])
check("referrals max hue (1 vs 9 -> 9)", m[0]["referrals"] == 9, m[0]["referrals"])
check("ban kabhi nahi hatta", m[0]["banned"] == 1, m[0]["banned"])
check("naya last_date liya", m[0]["last_date"] == "2026-10-05", m[0]["last_date"])

# --- case 2: LIFETIME hamesha jeetta hai
local2 = [{"user_id": 2, "premium_until": "lifetime", "credits": 0, "referrals": 0,
           "banned": 0, "last_date": "2026-01-01"}]
remote2 = [{"user_id": 2, "premium_until": "2030-01-01T00:00:00", "credits": 0,
            "referrals": 0, "banned": 0, "last_date": "2026-09-01"}]
m2, _ = merge_users(local2, remote2)
check("lifetime > future date (priority)", m2[0]["premium_until"] == "lifetime",
      m2[0]["premium_until"])
m2b, _ = merge_users(remote2, local2)
check("lifetime jeeta chahe kisi bhi taraf ho", m2b[0]["premium_until"] == "lifetime",
      m2b[0]["premium_until"])

# --- case 3: khaali premium remote se khaali nahi hoga
local3 = [{"user_id": 3, "premium_until": "2027-06-01T00:00:00", "credits": 10,
           "referrals": 0, "banned": 0, "last_date": "2026-01-01"}]
remote3 = [{"user_id": 3, "premium_until": "", "credits": 0, "referrals": 0,
            "banned": 0, "last_date": "2026-01-01"}]
m3, _ = merge_users(local3, remote3)
check("khaali premium purane ko nahi girata", m3[0]["premium_until"] == "2027-06-01T00:00:00",
      m3[0]["premium_until"])

# --- case 4: backup me sirf purana data, local me naya — dono bachein
local4 = [{"user_id": 4, "premium_until": "2027-01-01T00:00:00", "credits": 0,
           "referrals": 0, "banned": 0, "last_date": "2026-10-01"}]
remote4 = [{"user_id": 4, "premium_until": "2026-02-01T00:00:00", "credits": 0,
            "referrals": 0, "banned": 0, "last_date": "2025-01-01"},
           {"user_id": 99, "premium_until": "2028-01-01T00:00:00", "credits": 0,
            "referrals": 0, "banned": 0, "last_date": "2026-09-01"}]
m4, rep4 = merge_users(local4, remote4)
u4 = {r["user_id"]: r for r in m4}
check("purana premium backup se nahi aaya (max liya)",
      u4[4]["premium_until"] == "2027-01-01T00:00:00", u4[4]["premium_until"])
check("backup ka chhupa hua VIP user wapas mila", 99 in u4 and
      u4[99]["premium_until"] == "2028-01-01T00:00:00")
check("report: only_remote=1", rep4["only_remote"] == 1, rep4)
check("report: total=2", rep4["total"] == 2, rep4)

# --- premium_rank / premium_max
check("premium_rank(lifetime) > premium_rank(2099)",
      premium_rank("lifetime") > premium_rank("2099-01-01"))
check("premium_max('','2027') -> 2027", premium_max("", "2027-01-01") == "2027-01-01")
check("premium_max('2027','') -> 2027", premium_max("2027-01-01", "") == "2027-01-01")
check("premium_max lifetime rule", premium_max("2027-01-01", "lifetime") == "lifetime")
check("is_lifetime variants", all(is_lifetime(x) for x in
                                 ("lifetime", "LIFETIME", "Life", "forever", "hamesha")))

# =====================================================================
print("\n[B] PREMIUM FLOOR GUARD — VIP ghattane wala restore BLOCK")
# =====================================================================
_DB = os.environ["DB_PATH"]
from database import db, grant_premium, get_user, get_credits, set_credits      # noqa: E402
from database import is_premium, premium_expiry, spend_credits                  # noqa: E402
from database import (ledger_all, ledger_for, premium_ledger_stats,             # noqa: E402
                      restore_premium_from_ledger, revoke_premium)

for i in (101, 102, 103):
    grant_premium(i, 30)
floor = premium_floor_report(_DB)
check("3 VIP grant ke baad floor=3", floor["total_premium"] == 3, floor)
grant_premium(104, 99999)
floor2 = premium_floor_report(_DB)
check("lifetime grant detect hua", floor2["lifetime"] == 1, floor2)

# ab ek "kharab" backup banate hain jisme VIP users nahi hain
bad_rows = {"users": [{"user_id": 101, "premium_until": "", "credits": 0,
                       "referrals": 0, "banned": 0, "last_date": "2026-01-01"}]}
merged_bad, _ = merge_rows({"users": [{"user_id": 101, "premium_until": "",
                                       "credits": 0, "referrals": 0, "banned": 0,
                                       "last_date": "2026-01-01"}]}, bad_rows)
after_bad = premium_floor_report(merged_bad.get("users", []))
check("kharab backup se premium ghatta (detect ho gaya)",
      after_bad["total_premium"] < floor2["total_premium"],
      f"{after_bad} vs {floor2}")

# lekin wahi backup asli data par merge karo to premium BACH jata hai
real_rows = {"users": [dict(r) for r in __import__("modules.core.vault",
             fromlist=["snapshot_rows"]).snapshot_rows(_DB).get("users", [])]}
safe_merge, _ = merge_rows(real_rows, bad_rows)
after_safe = premium_floor_report(safe_merge.get("users", []))
check("🛡️ ASLI data par merge karo to VIP SAFE rehta hai",
      after_safe["total_premium"] >= floor2["total_premium"],
      f"{after_safe} vs {floor2}")

# =====================================================================
print("\n[C] ENCRYPTION — backup safe hai")
# =====================================================================
secret = "test-secret-key-xyz"
data = b"SQLite format 3\x00" + os.urandom(2000)
blob = encrypt_blob(data, secret)
check("encrypt ka output alag hai", blob != data and len(blob) > len(data))
check("plaintext leak nahi hua", b"SQLite format 3" not in blob)
check("galat key se decrypt fail (None)", decrypt_blob(blob, "wrong-key") is None)
check("sahi key se round-trip OK", decrypt_blob(blob, secret) == data)
tampered = bytearray(blob)
tampered[len(tampered) // 2] ^= 0xFF
check("tampered backup detect hua", decrypt_blob(bytes(tampered), secret) is None)

# =====================================================================
print("\n[D] TZ-SAFE PREMIUM — timezone wali date (ASLI BUG ka fix)")
# =====================================================================
c = sqlite3.connect(_DB)
c.execute("UPDATE users SET premium_until='2027-01-01T00:00:00+00:00' WHERE user_id=101")
c.commit()
c.close()
u = get_user(101)
check("tz-aware (+00:00) premium sahi padha", is_premium(u) is True, u.get("premium_until"))
check("tz-aware expiry dikhti hai", premium_expiry(u) == "01-01-2027", premium_expiry(u))

for val, want in (("2027-01-01T00:00:00Z", True), ("2027-01-01 00:00:00", True),
                  ("2027-01-01", True), ("2020-01-01T00:00:00+05:30", False),
                  ("lifetime", True), ("LIFETIME", True), ("", False)):
    c = sqlite3.connect(_DB)
    c.execute("UPDATE users SET premium_until=? WHERE user_id=102", (val,))
    c.commit()
    c.close()
    got = is_premium(get_user(102))
    check(f"premium '{val}' -> {want}", got is want, f"mila {got}")

# =====================================================================
print("\n[E] GRANT NEVER REDUCES — galti se bhi VIP chhota nahi")
# =====================================================================
grant_premium(200, 365)
a = get_user(200)["premium_until"]
grant_premium(200, 0)
b = get_user(200)["premium_until"]
check("0 din grant se premium nahi ghata", a == b, f"{a} -> {b}")
grant_premium(200, -500)
c2 = get_user(200)["premium_until"]
check("negative days se premium nahi ghata", b == c2, f"{b} -> {c2}")
grant_premium(200, 99999)
check("99999 => lifetime", get_user(200)["premium_until"] == "lifetime")
grant_premium(200, 30)
check("lifetime ke baad bhi lifetime rehta hai",
      get_user(200)["premium_until"] == "lifetime")

# =====================================================================
print("\n[F] ATOMIC CREDITS — race condition fix")
# =====================================================================
set_credits(300, 10)
for _ in range(40):
    spend_credits(300, 1)
check("40 spend (1 thread) -> 0", get_credits(300) == 0, get_credits(300))

set_credits(301, 10)


def _spend_many():
    for _ in range(20):
        try:
            spend_credits(301, 1)
        except Exception:
            pass


ts = [threading.Thread(target=_spend_many) for _ in range(5)]
[t.start() for t in ts]
[t.join() for t in ts]
check("5 threads x 20 spend = 100 -> 0 (negative nahi, overflow nahi)",
      get_credits(301) == 0, get_credits(301))

set_credits(302, 5)
spend_credits(302, 999)
check("zyada spend karne par bhi 0 hi rehta hai (negative nahi)",
      get_credits(302) == 0, get_credits(302))

# =====================================================================
print("\n[G] PREMIUM LEDGER — /fixvip se premium wapas")
# =====================================================================
grant_premium(400, 90)
before_ledger = get_user(400)["premium_until"]
time.sleep(1.1)
c = sqlite3.connect(_DB)
c.execute("UPDATE users SET premium_until='' WHERE user_id=400")   # "accident"
c.commit()
c.close()
check("premium 'accidentally' gaya", is_premium(get_user(400)) is False)
stats_before = premium_ledger_stats()
check("ledger me grant record hai", stats_before["grant"] >= 1, stats_before)
back = restore_premium_from_ledger(400)
check("🛡️ /fixvip se premium WAPAS aa gaya", bool(back) and back == before_ledger,
      f"{back} vs {before_ledger}")
check("wapas aane ke baad is_premium True", is_premium(get_user(400)) is True)
check("ledger_for() itihaas deta hai", len(ledger_for(400, 10)) >= 1)
check("ledger_all() chalta hai", isinstance(ledger_all(10), list))

# =====================================================================
print("\n[H] SAFESEND — lamba / toota HTML crash nahi karta")
# =====================================================================
from modules.core.safesend import (split_html, repair_html,               # noqa: E402
                                   trim_callback_data, safe_send_text,
                                   safe_reply, SendResult)
from modules.core.html_safe import html_balanced                          # noqa: E402
from modules.core.safesend import TG_LIMIT                                # noqa: E402

long_txt = "".join(f"Line {i} <b>bold</b> <i>it</i> & more\n" for i in range(500))
parts = split_html(long_txt, TG_LIMIT)
check("lamba text tukdon me bata", len(parts) > 1, len(parts))
check("har tukda 4096 se chhota", all(len(p) <= TG_LIMIT for p in parts), 
      max(len(p) for p in parts))
check("har tukda HTML balanced", all(html_balanced(p) for p in parts))
check("kuch content khoya nahi",
      sum(p.count("Line ") for p in parts) == 500,
      sum(p.count("Line ") for p in parts))
check("unclosed <i> repair hua", repair_html("<b>hi <i>x") == "<b>hi <i>x</i></b>",
      repair_html("<b>hi <i>x"))
check("bare & escape hua", "&amp;" in repair_html("A & B"))
check("&amp; dobara escape nahi hua", "&amp;amp;" not in repair_html("A &amp; B"))
check("callback_data trim (64B limit)", len(trim_callback_data("x" * 200).encode()) <= 64)


# ---- fake bot classes
class _FakeBot:
    def __init__(self, mode="ok"):
        self.mode = mode
        self.sent = []

    async def send_message(self, chat_id, text, **kw):
        if self.mode == "entity" and kw.get("parse_mode"):
            from telegram.error import BadRequest
            raise BadRequest("Can't parse entities: can't find end tag "
                             "corresponding to start tag 'i'")
        if self.mode == "toolong" and len(text) > 3000:
            from telegram.error import BadRequest
            raise BadRequest("Message is too long")
        if self.mode == "blocked":
            from telegram.error import Forbidden
            raise Forbidden("Forbidden: bot was blocked by the user")
        if self.mode == "flood":
            if not getattr(self, "_flooded", False):
                self._flooded = True
                from telegram.error import RetryAfter
                raise RetryAfter(1)
        self.sent.append(text)
        return type("M", (), {"message_id": len(self.sent)})()


async def _send_tests():
    # normal
    r = await safe_send_text(_FakeBot(), 1, "hello <b>world</b>")
    check("normal send OK", r.ok is True, r)
    # entity error -> repair -> chalta hai
    b = _FakeBot("entity")
    r = await safe_send_text(b, 1, "<b>hi <i>there</b>")
    check("entity error ke baad bhi bhej diya (plain fallback)", r.ok is True, r)
    # too long -> split -> chalta hai
    b2 = _FakeBot("toolong")
    r = await safe_send_text(b2, 1, "x" * 9000)
    check("bahut lamba text bhi bhej diya", r.ok is True and r.sent_count >= 1, r)
    # blocked -> graceful fail (crash nahi)
    b3 = _FakeBot("blocked")
    r = await safe_send_text(b3, 1, "hi")
    check("blocked user par crash nahi (graceful False)", r.ok is False
          and "blocked" in r.reason.lower(), r)
    # flood -> retry
    b4 = _FakeBot("flood")
    r = await safe_send_text(b4, 1, "hi")
    check("flood-wait (429) ke baad dobara bheja", r.ok is True, r)
    # None bot -> crash nahi
    r = await safe_send_text(None, 1, "hi")
    check("bot None ho to bhi crash nahi", r.ok is False)
    # reply without message
    r = await safe_reply(None, "hi")
    check("safe_reply(None) crash nahi", r.ok is False)


asyncio.run(_send_tests())

# =====================================================================
print("\n[I] SAFECONF — galti se env kharab ho to boot crash nahi")
# =====================================================================
from modules.core.safeconf import env_int, env_bool, env_float, env_list    # noqa: E402

os.environ["_T_INT_BAD"] = "25       # naye user ko itne credits"
os.environ["_T_INT_TXT"] = "@myusername"
os.environ["_T_BOOL"] = '"on"'
os.environ["_T_FLOAT"] = "12.7 seconds"
check("inline comment wali value se crash nahi", env_int("_T_INT_BAD", 0) == 25,
      env_int("_T_INT_BAD", 0))
check("kachra value -> default (crash nahi)", env_int("_T_INT_TXT", 7) == 7)
check("quoted bool chalta hai", env_bool("_T_BOOL", False) is True)
check("float bhi nikal aaya", abs(env_float("_T_FLOAT", 0) - 12.7) < 0.01)
check("missing env -> default", env_int("_T_NOT_SET_XYZ", 42) == 42)
check("range clamp", env_int("_T_INT_BAD", 0, hi=10) == 10)
check("hinglish bool 'haan'", env_bool("_T_BOOL2", False) is False)   # not set -> default
os.environ["_T_BOOL2"] = "haan"
check("hinglish bool 'haan' = True", env_bool("_T_BOOL2", False) is True)
check("list parsing", env_list("_T_LIST", default="a, b, c") == ["a", "b", "c"])

# =====================================================================
print("\n[J] GUARD — handler me bug ho to bot zinda rehta hai")
# =====================================================================
from modules.core.guard import (guarded, guard_stats, heartbeat, HEART,     # noqa: E402
                                mem_mb, free_memory, safe_task, crash_state)

before = guard_stats()["handler"]


@guarded("test_boom", notify=False)
async def _boom_async():
    raise ValueError("jaan-boojh kar crash")


@guarded("test_boom_sync", notify=False)
def _boom_sync():
    raise RuntimeError("sync crash")


r = asyncio.run(_boom_async())
after = guard_stats()["handler"]
check("async handler crash sambhala gaya", after == before + 1, f"{before}->{after}")
check("crash ke baad None return (crash nahi)", r is None)
check("sync handler crash bhi sambhala gaya", _boom_sync() is None)

heartbeat()
check("heartbeat beat count badha", HEART["beats"] >= 1, HEART["beats"])
check("mem_mb() value deta hai", mem_mb() > 0, mem_mb())
fr = free_memory()
check("free_memory() dict deta hai", isinstance(fr, dict) and "freed_mb" in fr, fr)
cs = crash_state()
check("crash_state me recent list hai", isinstance(cs.get("recent"), list))


async def _ok_task():
    return 1


# =====================================================================
print("\n[K] BOOT SELF-CHECK + IMPORTS")
# =====================================================================
import bot                                                                  # noqa: E402
check("bot.py import ho gaya", bool(bot.BOT_VERSION), bot.BOT_VERSION)
check("BOT_VERSION v60 hai", "v60" in bot.BOT_VERSION or "FORTRESS" in bot.BOT_VERSION,
      bot.BOT_VERSION)
check("vault singleton ready", bot.vault is not None)
check("naye commands maujood hain",
      all(hasattr(bot, n) for n in ("cmd_vault", "cmd_backup", "cmd_restore",
                                    "cmd_vips", "cmd_fixvip", "cmd_ledger")))
check("grant_premium auto-backup wrapper laga", bot.grant_premium is not None)
check("health_html me vault info hai", "FORTRESS" in bot.health_html(), "vault block")
check("system_stats_text me vault block hai",
      "PREMIUM VAULT" in bot.system_stats_text())
check("DB path resolve hua", bool(bot.vault_db_path()))

# =====================================================================
print("\n[L] VAULT ROUND-TRIP — backup -> DB delete -> restore (asli test)")
# =====================================================================
v = Vault()
v.secret = "roundtrip-secret"
# ek VIP user aur banao
grant_premium(500, 120)
vip_500 = get_user(500)["premium_until"]
users_before = len(__import__("modules.core.vault", fromlist=["snapshot_rows"])
                   .snapshot_rows(_DB).get("users", []))
blob = v.dump_encrypted()
check("encrypted dump bana", bool(blob) and len(blob) > 100, len(blob or b""))
rows = v._plain_to_rows(decrypt_blob(blob, "roundtrip-secret"))
check("dump se rows wapas padhe gaye", bool(rows) and "users" in rows,
      list(rows.keys()) if rows else None)
if rows:
    got = {r["user_id"]: r for r in rows["users"]}
    check("VIP user 500 backup me hai", 500 in got, list(got)[:5])
    check("VIP expiry sahi hai", got.get(500, {}).get("premium_until") == vip_500,
          got.get(500, {}).get("premium_until"))

# ---- ab DB "wipe" karo (Render ke deploy jaisa) aur restore karo
shutil.copy2(_DB, _DB + ".keep")
try:
    os.remove(_DB)
    for ext in ("-wal", "-shm"):
        if os.path.exists(_DB + ext):
            os.remove(_DB + ext)
except Exception:
    pass
db()                                # nayi khaali DB ban jayegi
check("DB wipe ke baad VIP gayab", is_premium(get_user(500)) is False)

# local backup save karke restore karo
v._save_local(blob, "test0001")
res = v.restore_now(reason="selftest")
check("🛡️ RESTORE chal gaya", res.get("ok") is True, res.get("why"))
check("🛡️ WIPE ke baad VIP 500 WAPAS aa gaya", is_premium(get_user(500)) is True,
      get_user(500).get("premium_until"))
check("VIP expiry wahi hai", get_user(500)["premium_until"] == vip_500,
      f"{get_user(500)['premium_until']} vs {vip_500}")
check("premium_before/after report aayi",
      "premium_before" in res and "premium_after" in res, res.keys())
users_after = len(__import__("modules.core.vault", fromlist=["snapshot_rows"])
                  .snapshot_rows(_DB).get("users", []))
check("users count kam nahi hua", users_after >= users_before,
      f"{users_before} -> {users_after}")

# ---- v60.1 REGRESSION: GitHub backup PATH bug
# (candidate me poora path hona chahiye, sirf filename nahi — warna
#  fetch 404 deta hai aur restore chup-chaap fail ho jata tha)
import inspect as _insp                                                  # noqa: E402
_fetch_src = _insp.getsource(Vault._fetch)
check("_fetch poora PATH use karta hai (regression fix)",
      'cand.get("path")' in _fetch_src, _fetch_src[:200])
check("vault ka default branch 'main' NAHI hai (deploy loop se bachao)",
      Vault().gh_branch() != "main", Vault().gh_branch())
check("restore failure ka karan note hota hai",
      "skipped" in _insp.getsource(Vault.restore_now))

# =====================================================================
print("\n[M] VAULT STATUS CARD")
# =====================================================================
card = v.status_card()
check("status card bana", "PREMIUM VAULT" in card, card[:80])
check("card me VIP count dikhta hai", "VIP" in card)
plist = v.premium_list_rows()
check("premium_list_rows() kaam karta hai", isinstance(plist, list) and len(plist) >= 1,
      len(plist))
check("500 list me hai", any(r["user_id"] == 500 for r in plist),
      [r["user_id"] for r in plist][:8])

# =====================================================================
print("\n[N] 💼 BUSINESS STUDIO — 10 earning tools")
# =====================================================================
import modules.business_tools as bt                                          # noqa: E402

check("business_tools import ho gaya", bool(bt.__name__))
check("ScriptFont Latin+Devanagari dono alag karta hai",
      bt.ScriptFont.runs("नाम / Name") == [("नाम /", True), (" Name", False)],
      bt.ScriptFont.runs("नाम / Name"))
check("pure Latin ek hi run me", len(bt.ScriptFont.runs("SHARMA ELECTRONICS")) == 1)
check("pure Hindi ek hi run me", len(bt.ScriptFont.runs("हिमांशु कुमार")) == 1)
_md = bt.ScriptFont.runs("ब्याज · EMI")
check("middle-dot Latin run me (▯ se bachao)",
      any("·" in _t and not d for _t, d in _md), _md)
check("Hindi font detect hua", bt.FONT_INFO.get("hindi_ok") is True, bt.FONT_INFO)

# ---- money / amount_words
check("money() Indian format", bt.money(1234567) == "12,34,567", bt.money(1234567))
check("money() chhota", bt.money(999) == "999", bt.money(999))
check("money() decimal", bt.money(1047.4) == "1,047.40", bt.money(1047.4))
check("amount_words 1047", bt.amount_words(1047) == "One Thousand Forty Seven Rupees Only",
      bt.amount_words(1047))
check("amount_words lakh", "Lakh" in bt.amount_words(250000), bt.amount_words(250000))

# ---- EMI math (independent formula se milao)
b = bt.emi_breakup(500000, 9.5, 60)
mr = 9.5 / 12 / 100.0
_f = (1 + mr) ** 60
_exp = 500000 * mr * _f / (_f - 1)
check("EMI formula sahi", abs(b["emi"] - _exp) < 0.01, f"{b['emi']} vs {_exp}")
check("EMI rows = tenure", len(b["rows"]) == 60, len(b["rows"]))
check("schedule ke baad balance 0", b["rows"][-1]["balance"] == 0.0,
      b["rows"][-1]["balance"])
check("principal ka jod = loan",
      abs(sum(r["principal"] for r in b["rows"]) - 500000) < 1.0,
      sum(r["principal"] for r in b["rows"]))
check("zero rate EMI = P/n", abs(bt.emi_breakup(12000, 0, 12)["emi"] - 1000) < 0.01)
check("0 loan -> error (crash nahi)", "error" in bt.emi_breakup(0, 10, 12))

# ---- har tool ek baar chalao
_BIZ = [
    ("invoice", bt.invoice_image, {"shop": "Sharma Electronics", "buyer": "Ramesh",
                                   "items": [{"name": "LED", "qty": 4, "rate": 120, "gst": 18}],
                                   "upi": "s@upi"}),
    ("resume", bt.resume_image, {"name": "Himanshu Kumar", "role": "Developer",
                                 "skills": "Python, SQL", "languages": "Hindi"}),
    ("biodata", bt.biodata_image, {"name": "हिमांशु कुमार", "dob": "15-08-1998",
                                   "education": "B.Tech", "phone": "9876543210"}),
    ("certificate", bt.certificate_image, {"org": "ABC Institute", "name": "Anjali"}),
    ("idcard", bt.idcard_image, {"org": "ABC School",
                                 "students": [{"name": "A", "class": "X"}]}),
    ("vcard", bt.visiting_card_image, {"owner": "Himanshu", "shop": "Kumar Electronics",
                                       "phone": "9876543210"}),
    ("letter", bt.letter_image, {"type": "leave", "name": "Himanshu",
                                 "org": "ABC School", "reason": "wedding"}),
    ("upi", bt.upi_qr_image, {"upi": "kumar@upi", "shop": "Kumar Store"}),
    ("labels", bt.label_sheet_image, {"shop": "Store",
                                      "labels": [{"name": "Sugar", "price": 48, "mrp": 55}]}),
    ("emi", bt.emi_card_image, {"bank": "SBI", "loan_amount": 250000, "rate": 11.5,
                                "months": 36}),
]
for nm, fn, arg in _BIZ:
    r = fn(arg)
    check(f"tool {nm} bana", bool(r.get("ok")), r.get("error"))
    if r.get("ok"):
        check(f"tool {nm} me PNG bytes hain", len(r.get("png", b"")) > 2000,
              len(r.get("png", b"")))
        pdf = bt.to_pdf(r.get("pages") or [r["png"]])
        check(f"tool {nm} ka PDF bana", bool(pdf) and len(pdf) > 1000,
              len(pdf or b""))

# ---- galat input se crash nahi
check("invoice khaali input se crash nahi", bool(bt.invoice_image({}).get("ok")))
check("emi galat input se crash nahi", bt.emi_card_image({"loan_amount": "abc"})
      .get("ok") is False)
check("upi bina UPI id -> saaf error", bt.upi_qr_image({}).get("ok") is False)

# ---- bot.py integration
check("BIZ_MENU me 10 tools", len(bot.BIZ_MENU) == 10, len(bot.BIZ_MENU))
check("biz prompts maujood", all(k in bot.PROMPT_DATA for k in bot.BIZ_MENU),
      [k for k in bot.BIZ_MENU if k not in bot.PROMPT_DATA])
_kb_flat = [bot.unbold(x) for r in bot.KB_BTNS for x in r]
check("menu me BUSINESS STUDIO button",
      any("BUSINESS STUDIO" in bot.unbold(x).upper() for r in bot.KB_BTNS for x in r),
      [bot.unbold(x) for r in bot.KB_BTNS for x in r if "BUS" in bot.unbold(x).upper()])
check("BTN_MODE_MAP me bizstudio", bot.BTN_MODE_MAP.get("BUSINESS STUDIO") == "bizstudio")
check("EMI ab removed-tool nahi hai (wapas aa gaya)",
      bot.BTN_MODE_MAP.get("EMI CALC") == "biz_emi",
      bot.BTN_MODE_MAP.get("EMI CALC"))
check("biz_menu_kb bana", bot.biz_menu_kb() is not None)
check("biz_parse invoice", bot.biz_parse("biz_invoice", "A | B | X 2x100")["items"][0]["qty"] == 2)
check("biz_parse emi", bot.biz_parse("biz_emi", "100000 | 10 | 24")["months"] == 24)
check("biz_parse labels", len(bot.biz_parse("biz_labels", "S | a:10:12, b:20")["labels"]) == 2)
check("biz_build dispatch sahi", bot.biz_build("biz_emi", {"loan_amount": 1000, "rate": 10, "months": 12}).get("ok"))
check("_biz_kind mapping", bot._biz_kind("emi") == "biz_emi" and bot._biz_kind("cv") == "biz_resume")


# =====================================================================
print("\n[O] PURANI TEST FILES KE SAATH MEL (no regression)")
# =====================================================================
import inspect                                                              # noqa: E402
_src = inspect.getsource(__import__("database"))
check("database.py me WAL/vault connect use hua", "connect" in _src)
check("is_premium me parse_dt use hota hai", "parse_dt" in _src)

# =====================================================================
print()
print("=" * 62)
print(f"  v60 SELFTEST — PASS: {PASS} | FAIL: {FAIL}")
print("=" * 62)
if FAILS:
    print("\n  FAILURES:")
    for f in FAILS:
        print(f"   - {f}")
try:
    shutil.rmtree(_TMP, ignore_errors=True)
except Exception:
    pass
sys.exit(1 if FAIL else 0)
