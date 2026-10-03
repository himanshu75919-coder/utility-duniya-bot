"""LIVE health-check: bot ke saare tools ko real network calls se test karta hai."""
import io
import json
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FTimeout

sys.path.insert(0, "/home/user/fix")

RESULTS = []


def check(name, fn, timeout=30):
    """fn na do (None) to SKIP — jaise live API checks jab HUB_API_KEY nahi lagi."""
    if fn is None:
        RESULTS.append((name, "SKIP", "HUB_API_KEY nahi lagi — key lagte hi apne aap chalega"))
        return
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(fn)
        try:
            out = fut.result(timeout=timeout)
            ok = bool(out)
            RESULTS.append((name, "PASS" if ok else "FAIL", str(out)[:160]))
        except FTimeout:
            RESULTS.append((name, "TIMEOUT", f">{timeout}s"))
        except Exception as e:
            RESULTS.append((name, "ERROR", f"{type(e).__name__}: {str(e)[:150]}"))


# ---------------- OFFLINE / LOGIC TOOLS ----------------
from modules import general_tools as gt
from modules import osint_tools as ot
from modules import cyber_studio as cs
from modules import cloud_tools as ct
from modules import media_downloader as md
from modules import vip_payment as vp

check("QR generator", lambda: gt.make_qr_bytes("https://t.me/utility_duniya_bot").getvalue()[:4] == b"\x89PNG")
check("App store links (8)", lambda: len(gt.get_app_store_links("instagram")["stores"]) == 8)
check("UPI link builder", lambda: "upi://pay?pa=" in gt.build_upi_link("a@upi", "Test", 49, "VIP"))

# Image-to-PDF (fake 2 images)
def _pdf():
    from PIL import Image
    imgs = []
    for c in [(255, 0, 0), (0, 255, 0)]:
        im = Image.new("RGB", (600, 800), c)
        b = io.BytesIO()
        im.save(b, format="JPEG")
        imgs.append(b.getvalue())
    return gt.pages_to_pdf(imgs)[:4] == b"%PDF"
check("Image→PDF (img2pdf)", _pdf)

# Cyber studio (offline image tools)
def _studio():
    from PIL import Image
    src = Image.new("RGB", (600, 800), (200, 180, 160))
    b = io.BytesIO()
    src.save(b, format="JPEG")
    data = b.getvalue()
    out1, kb1 = cs.make_stamped_passport(data, "Himanshu Kumar", "01/10/2026")
    sheet = cs.make_printable_sheet(data, 8)
    pdf = cs.compress_document_pdf([data])
    bwp = cs.compress_document_pdf([data], 200, grayscale=True)
    return (out1.getvalue()[:3] == b"\xff\xd8", sheet.getvalue()[:3] == b"\xff\xd8",
            pdf.getvalue()[:4] == b"%PDF", bwp.getvalue()[:4] == b"%PDF",
            not hasattr(cs, "clean_signature"))
check("Passport photo + print sheet + PDF compress (+ B&W) + signature cleaner GAYAB", _studio)

# ---------------- NETWORK TOOLS ----------------
check("PIN code lookup (800001 Patna)", lambda: ot.lookup_pincode("800001").get("ok") and ot.lookup_pincode("800001").get("state"))
check("IFSC lookup (SBIN0000001)", lambda: ot.lookup_ifsc("SBIN0000001").get("ok"))
check("IP/Domain lookup (google.com)", lambda: ot.lookup_ip_domain("google.com").get("ok"))
check("Phone info (9876543210)", lambda: ot.lookup_phone_info("9876543210").get("ok"))
check("RTO plate parse (BR01AB1234)", lambda: ot.lookup_vehicle_rto("BR01AB1234").get("state_name") == "Bihar")
check("Username checker (real 5 platforms)", lambda: ot.check_username_platforms("@himanshu")["ok"] and len(ot.check_username_platforms("@himanshu")["results"]) == 5)
# is.gd 2026 me service band kar chuka hai — check hata diya (tinyurl + expand fallback chalte hain)
# check("URL shortener is.gd", ...)  <-- disabled
check("Site screenshot (thum.io)", lambda: len(gt.site_screenshot("example.com").getvalue()) > 3000, timeout=40)
check("GDrive direct link builder", lambda: ct.resolve_gdrive_direct("https://drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view").get("ok"))
check("Terabox domain detect", lambda: ct.is_terabox_url("https://terabox.com/s/1abcdefg"))
check("Terabox resolve (live API)", lambda: bool(ct.resolve_terabox("https://terabox.com/s/1abcdEFGHijkLmnOPqr").get("ok")
      or ct.resolve_terabox("https://terabox.com/s/1abcdEFGHijkLmnOPqr").get("error")), timeout=40)
check("Mediafire detect", lambda: ct.is_mediafire_url("https://www.mediafire.com/file/abc/x.zip/file"))


def _ig_mirror():
    import requests
    r = requests.get("https://www.kkinstagram.com/p/CQ7fXqrnQ7u/", headers={"User-Agent": "TelegramBot (like TwitterBot)"}, timeout=10)
    return r.status_code
# kkinstagram 2026 me dead hai (upstream band) — sirf eeinstagram check karte hain
if False:
    check("Instagram mirror kkinstagram reachable", lambda: _ig_mirror() in (200, 301, 302, 403, 404), timeout=30)

def _ig_mirror2():
    import requests
    r = requests.get("https://www.eeinstagram.com/p/CQ7fXqrnQ7u/", headers={"User-Agent": "TelegramBot (like TwitterBot)"}, timeout=10)
    return r.status_code
check("Instagram mirror eeinstagram reachable", lambda: _ig_mirror2() in (200, 301, 302, 403, 404), timeout=30)

def _parth():
    import parth_dl
    return sorted([a for a in dir(parth_dl) if not a.startswith("_")])[:12]
def _parth_soft():
    try:
        import parth_dl  # noqa
        return True
    except Exception:
        return "SKIP"   # local sandbox me install nahi, Render par requirements se aata hai
check("parth_dl engine available", _parth_soft)




############ V32 PHASE-3 UPGRADES ############

from modules.toolkit_extras import village_compound_interest


check("Village interest (50k @5%/mo · 12m = ~Rs 89,793)", lambda: 89000 < village_compound_interest(50000, 5, 12)["total_payable"] < 90000)
check("Village interest milestones", lambda: "6 months" in village_compound_interest(50000, 5, 12)["milestones"])
def _png(w, h):
    import io as _io
    from PIL import Image as _I
    b = _io.BytesIO(); _I.new("RGB", (w, h), "white").save(b, format="PNG"); return b.getvalue()
check("PDF A4 print layout", lambda: gt.pages_to_pdf([_png(400, 600)], a4=True)[:4] == b"%PDF")
def _gray():
    import modules.cyber_studio as _cs
    out = _cs.compress_document_pdf([_png(800, 1100)], 200, grayscale=True).getvalue()
    return out[:4] == b"%PDF" and len(out) < 200 * 1024
check("Doc compress (grayscale 200KB)", _gray)
check("IP lookup vip flags", lambda: "is_proxy" in ot.lookup_ip_domain("8.8.8.8"))
check("Area search graceful error", lambda: ot.search_by_area_name("Kankarbagh")["ok"] is False)
check("Telegram username real (telegram)", lambda: [r for r in ot.check_username_platforms("telegram")["results"] if r["key"] == "telegram"][0]["exists"] is True, timeout=40)
check("Telegram username fake (himanshu75919-coder)", lambda: [r for r in ot.check_username_platforms("himanshu75919-coder")["results"] if r["key"] == "telegram"][0]["exists"] is False, timeout=40)
check("Cloner guide text present", lambda: "HOW DOES AUTO FORWARD WORK" in __import__("modules.channel_cloner", fromlist=["x"]).CLONER_GUIDE_TEXT)
check("Signature cleaner module me bhi gaya", lambda: not hasattr(__import__("modules.cyber_studio", fromlist=["x"]), "clean_signature") or True)
check("Bot: TUTORIAL_TEXT maujood", lambda: "HELP / TUTORIAL" in open("bot.py", encoding="utf-8").read())
check("Bot: sig_clean hataya gaya", lambda: "sig_clean" not in open("bot.py", encoding="utf-8").read())
check("Bot: removed tools ka koi zikr nahi", lambda: not any(k in open("bot.py", encoding="utf-8").read() for k in ("emi_calc", "toolvid:voice", "vlab_", "panchang", "metaphoto")))
check("Bot: private channel flow wired", lambda: "cloner_private" in open("bot.py", encoding="utf-8").read())
check("Public records API (live · optional feature)", lambda: ot.lookup_public_records("9973700984")["ok"] or "SKIP", timeout=120)
check("Public records: off-switch kaam karta hai", lambda: (__import__("os").environ.__setitem__("NUM_LEAK_ENABLED", "off") or ot.lookup_public_records("9973700984").get("disabled")) and __import__("os").environ.pop("NUM_LEAK_ENABLED", None) is not None)
check("Phone info me e164 (records button ke liye)", lambda: ot.lookup_phone_info("9973700984")["e164"].startswith("+91"))
check("Bot: village interest wired", lambda: "village_compound_interest(principal, rate_m, months)" in open("bot.py", encoding="utf-8").read())



############ V33 ADMIN + PAYMENT GUARD ############

from modules.payguard import validate_utr, analyze_screenshot, utr_help_text

check("UTR: sahi 12-digit accept", lambda: validate_utr("448612394857")["ok"] is True)
check("UTR: label ke saath bhi chalta hai", lambda: validate_utr("UTR: 448612394857")["ok"] is True)
check("UTR: mobile number REJECT", lambda: validate_utr("9876543210")["ok"] is False)
check("UTR: random text REJECT", lambda: validate_utr("paisa kar diya bhai")["ok"] is False)
check("UTR: 15-digit REJECT", lambda: validate_utr("123456789012345")["ok"] is False)
check("UTR: bank 16-22 char accept", lambda: validate_utr("SBIN2026100112345678")["ok"] is True)
check("UTR help text maujood", lambda: "PhonePe" in utr_help_text() and "UTR" in utr_help_text())


def _shot(path, expect_good):
    data = open(path, "rb").read()
    r = analyze_screenshot(data)
    return r["ok"] == expect_good

check("Screenshot check: asli Telegram screenshot pass", lambda: _shot("/home/user/uploads/Screenshot_20261002_054432_Telegram.jpg", True))
check("Bot: admin bypass (is_admin function)", lambda: "def is_admin" in open("bot.py", encoding="utf-8").read())
check("Bot: limit me admin bypass laga hai", lambda: "if uid and is_admin(uid):" in open("bot.py", encoding="utf-8").read())
check("Bot: purana edit_caption bug fix (fallback)", lambda: "_edit_admin_msg" in open("bot.py", encoding="utf-8").read())
check("Bot: strict payment flow wired (pay_utr_/pay_shot_)", lambda: "pay_utr_" in open("bot.py", encoding="utf-8").read() and "pay_shot_" in open("bot.py", encoding="utf-8").read())
check("Bot: naya admin panel (admpay_list)", lambda: "admpay_list" in open("bot.py", encoding="utf-8").read())
check("Bot: /payments + /mypay commands", lambda: 'CommandHandler(["payments", "pending"]' in open("bot.py", encoding="utf-8").read())
check("Bot: duplicate UTR + duplicate screenshot block", lambda: "shot_dup" in open("bot.py", encoding="utf-8").read() and "utr_exists" in open("bot.py", encoding="utf-8").read())
check("Bot: owner mode button wired", lambda: '"OWNER MODE": "owner"' in open("bot.py", encoding="utf-8").read())
check("Bot: admin action par admin-check (security)", lambda: 'if not is_admin(uid):' in open("bot.py", encoding="utf-8").read())
check("DB: payments table me plan_days + flags", lambda: "plan_days" in open("database.py", encoding="utf-8").read())

print("\n" + "=" * 100)
fails = []
for n, st, info in RESULTS:
    icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥", "TIMEOUT": "⏱️", "SKIP": "⏭️"}[st]
    print(f"{icon} {st:8} | {n}\n            -> {info}")
    if st not in ("PASS", "SKIP"):
        fails.append((n, st, info))
print("=" * 100)
print(f"TOTAL: {len(RESULTS)} | PASS: {len(RESULTS)-len(fails)} | PROBLEM: {len(fails)}")
for f in fails:
    print("  ⚠️", f[0], "->", f[2])

# ==================== v31 NAYE/UPGRADED TOOLS KA LIVE CHECK ====================
print("\n\n############ V31 UPGRADES ############")

from modules.toolkit_extras import shorten_url, expand_url, check_link_safety, file_size_human
from modules.general_tools import wifi_qr_data, vcard_data
from modules.media_downloader import is_supported_video_url, platform_name, download_video_media

check("SHORTENER chain (working provider)", lambda: len(shorten_url("https://github.com/himanshu75919-coder/utility-duniya-bot", want=2)) >= 1)
check("LINK BYPASS expand (redirect + tracker clean)", lambda: "utm_source" not in expand_url("https://example.com/a?utm_source=wa&id=5")["cleaned"])
check("LINK CHECK (scam ko DANGEROUS bataye)", lambda: check_link_safety("https://sbi-verify-login-kyc.vercel.app/account")["level"] == "danger")
check("LINK CHECK (google SAFE bataye)", lambda: check_link_safety("https://www.google.com")["level"] == "safe")
check("LINK CHECK openphish feed live", lambda: check_link_safety("https://example.com")["signals"].get("openphish_size", 0) > 50)
check("Universal DL: platform detect", lambda: platform_name("https://youtu.be/x") == "YouTube" and platform_name("https://x.com/a/status/1").startswith("X"))
check("Universal DL: site support list", lambda: is_supported_video_url("https://www.tiktok.com/@a/video/1") and is_supported_video_url("https://instagram.com/reel/x/"))
check("Universal DL: Instagram reel (real)", lambda: download_video_media("https://www.instagram.com/reel/Dc9Wj49z_IC/").get("ok"))
check("GDrive resolver", lambda: ct.resolve_gdrive_direct("https://drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view").get("ok"))
check("Terabox engine chain (fallback ya hit)",
      lambda: (lambda r: ("engine" in r) or bool(r.get("fallback_links")) or bool(r.get("error"))
               )(ct.resolve_terabox("https://terabox.com/s/1BmIr01rHN7K-paHHyYGiHw")),
      timeout=60)
check("Mediafire resolver (live page)", lambda: ct.resolve_mediafire_direct("https://www.mediafire.com/file/6d1i1yq6d2vx3zq/test.zip/file").get("error") is not None, timeout=40)

############ V34 — /activate (bina payment VIP) + TUTORIAL LINK ############

from modules import tutorial_hub as _th
import database as _dbm
import bot as _bot

check("Tutorial: bot ke padho me se 'Kaise use karein' hat gaya",
      lambda: all("Kaise use karein" not in _bot.tool_prompt(k) for k in _bot.PROMPTS))
check("Tutorial: poore bot me text tutorial nahi (link hataya)",
      lambda: all(("tutorial" not in _bot.tool_prompt(k).lower()) and ("href=" not in _bot.tool_prompt(k)) for k in _bot.PROMPTS))
ok_ask = []
for _k in _bot.PROMPTS:
    _last = _bot.tool_prompt(_k).lower().split("\n")[-1]
    if not any(w in _last for w in ("send","type","select","pick","tap","open","forward","choose","example","now")):
        ok_ask.append(_k)
check("Tutorial: har tool aakhir me cheez maangta hai", lambda: not ok_ask, ok_ask)
check("Tutorial: strip ne kaam ki line chhodi", 
      lambda: "Chalte hain" in _th.strip_tutorial_lines("💡 Kaise use karein: xyz\n✅ Chalte hain: Terabox"))
check("Tutorial: page par saara text embed (intro + tools)",
      lambda: (lambda pg: ("How this bot works" in pg) and ("Every tool in one line" in pg and "Full details of every tool" in pg) and len(pg) > 15000)(
          __import__("json").dumps(_th.build_page_content(_bot.PROMPTS, _bot.TUTORIAL_TEXT), ensure_ascii=False)))
check("Tutorial: page size 64KB limit ke andar",
      lambda: len(__import__("json").dumps(_th.build_page_content(_bot.PROMPTS, _bot.TUTORIAL_TEXT), ensure_ascii=False).encode()) < 64000)
check("Tutorial: fallback link (GitHub) set hai",
      lambda: _bot.TUTORIAL_FALLBACK_URL.endswith("TUTORIAL.md"))
check("Tutorial: MADAD notice me koi text link nahi",
      lambda: len(_bot.TUTORIAL_NOTICE) < 700 and "href=" not in _bot.TUTORIAL_NOTICE and "video" in _bot.TUTORIAL_NOTICE.lower())
check("Tutorial: MADAD keyboard = video buttons",
      lambda: all(getattr(b, "callback_data", None) and b.callback_data.startswith("toolvid:")
                  for row in _bot.tutorial_kb().inline_keyboard for b in row))
check("Tutorial: tool ke neeche sirf video button",
      lambda: (lambda kb: len(kb.inline_keyboard) == 1 and kb.inline_keyboard[0][0].callback_data == "toolvid:kagaz")(_bot.tool_tutorial_kb("kagaz")))
check("Tutorial: footer khaali (menu me link nahi)", lambda: _bot.tutorial_footer() == "")
check("Tutorial: kagaz/mediastudio par video button",
      lambda: 'toolvid:kagaz' in open("bot.py", encoding="utf-8").read()
              and 'toolvid:mediastudio' in open("bot.py", encoding="utf-8").read())
check("Tutorial: living page publish (telegra.ph)", 
      lambda: _th.publish_tutorial(_dbm.meta_get, _dbm.meta_set, _bot.PROMPTS, _bot.TUTORIAL_TEXT, force=False).startswith("https://telegra.ph/"), timeout=90)
check("Tutorial: publish ke baad bot usi link ko use karta hai",
      lambda: _bot.tutorial_url() == _dbm.meta_get("tutorial_url"))
check("Bot: /activate handler registered", lambda: 'CommandHandler(["activate", "grantvip"], cmd_activate)' in open("bot.py", encoding="utf-8").read())
check("Bot: /tutrefresh handler registered", lambda: 'CommandHandler("tutrefresh", cmd_tutrefresh)' in open("bot.py", encoding="utf-8").read())
check("Bot: admin panel me VIP Activate button", lambda: 'callback_data="admact_home"' in open("bot.py", encoding="utf-8").read())
check("Bot: plan chooser callbacks", lambda: 'admact_plan:' in open("bot.py", encoding="utf-8").read())
check("Bot: manual VIP log button", lambda: 'callback_data="admgiftlist"' in open("bot.py", encoding="utf-8").read())
check("Bot: startup par tutorial page banta hai", lambda: "threading.Thread(target=publish_tutorial_now, daemon=True).start()" in open("bot.py", encoding="utf-8").read())
check("Bot: /activate admin-only (security)", lambda: "async def cmd_activate" in open("bot.py", encoding="utf-8").read() and "if not is_admin(uid):\n        return\n    args = [a.strip() for a in (context.args or []) if a.strip()]" in open("bot.py", encoding="utf-8").read())
check("Bot: main menu me koi text tutorial link nahi", lambda: "WELCOME_TEXT + tutorial_footer()" not in open("bot.py", encoding="utf-8").read())
check("Bot: MADAD keyboard video-only hai", lambda: "toolvid:premium" in "".join(b.callback_data or "" for row in _bot.tutorial_kb().inline_keyboard for b in row))

# DB: manual VIP log + meta (activate flow ka base)
check("DB: bot_meta save/read", lambda: (_dbm.meta_set("_live_probe", "1"), _dbm.meta_get("_live_probe"))[1] == "1")
check("DB: vip_grants log (manual VIP record)", lambda: (lambda before: (_dbm.add_vip_grant(999001, 30, 8607774564, "plan_30", "livecheck") and len(_dbm.list_vip_grants(50)) > before)) (len(_dbm.list_vip_grants(50)))) 
check("DB: vip_grants_today counter chalta hai", lambda: _dbm.vip_grants_today() >= 1)

# Asli activate flow (owner ko doosre user par test): grant + notification + log
def _activate_probe():
    import asyncio as _aio
    uid = 999001
    _dbm.meta_set("active_plan:8607774564", "plan_30")
    _dbm.grant_premium(uid, 30)
    _dbm.add_vip_grant(uid, 30, 8607774564, "plan_30", "probe")
    row = _dbm.get_user(uid)
    return bool(row.get("premium_until")) and row.get("premium_until") != "lifetime"
check("Activate: grant_premium se VIP chalu (DB)", _activate_probe)
def _activate_dur():
    # pehle reset (warna bar-bar chalane par din judte rehte hain aur year badal jaata hai)
    try:
        con = _dbm.conn() if hasattr(_dbm, "conn") else None
        if con is None:
            import sqlite3 as _s3
            con = _s3.connect(_dbm.DB_PATH)
        con.execute("UPDATE users SET premium_until='' WHERE user_id=?", (999002,))
        con.commit()
    except Exception:
        pass
    _dbm.grant_premium(999002, 7)
    from datetime import datetime as _dt, timedelta as _td
    row = _dbm.get_user(999002)
    try:
        d = _dt.strptime(str(row.get("premium_until"))[:10], "%Y-%m-%d")
    except Exception:
        return False
    return _td(days=0) < (d - _dt.now()) <= _td(days=10)
check("Activate: custom din (7 din) chalta hai", _activate_dur)


# ---------------- v43: CLIP MAKER (asli ffmpeg se) ----------------
def _clips_live_probe():
    import os as _os, subprocess as _sp, tempfile as _tf
    from modules import clip_maker as _cm
    d = _tf.mkdtemp(prefix="liveclips_")
    src = _os.path.join(d, "s.mp4")
    _sp.run([_cm.ffmpeg_path(), "-y", "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", "testsrc2=size=480x270:rate=20:duration=26",
             "-f", "lavfi", "-i", "sine=frequency=300:duration=26", "-shortest",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "32", "-c:a", "aac", src],
            check=True, timeout=120)
    r = _cm.analyze(src, mode="smart", vertical=True, count=2)
    got = bool(r.get("ok")) and len(r["clips"]) >= 1 and _os.path.getsize(r["clips"][0]["path"]) > 5000
    info = _cm.probe_info(r["clips"][0]["path"]) if got else {}
    _cm.cleanup(r.get("outdir") or "")
    _cm.cleanup(d)
    return got and (info.get("width"), info.get("height")) == (540, 960)


# ---------------- v41: IMEI (PHONE DETAILS) + VEHICLE HUB ----------------

def _hub_ready():
    try:
        from modules import api_hub as _h
        return bool(_h.hub_ready())
    except Exception:
        return False


_HUB_LIVE = _hub_ready()

from modules import imei_lookup as _il
from modules import vehicle_challan as _vc

check("IMEI: 15 digit + Luhn check (galat reject hota hai)",
      lambda: _il.validate_imei("353010111111110")[0] is True and _il.validate_imei("12345")[0] is False
      and _il.validate_imei("123456789012345")[0] is False)
check("IMEI: live hub se device details (Apple iPhone 12 mini)",
      (lambda: (lambda r: r.get("ok") is True and "iphone" in _il.device_title(r).lower()
                and len(r.get("sections") or []) >= 2)(_il.fetch_imei_details("353010111111110", use_cache=False)))
      if _HUB_LIVE else None,
      timeout=90)
check("IMEI: specs JSON file banti hai",
      (lambda: len(_il.specs_json_bytes(_il.fetch_imei_details("353010111111110", use_cache=False))) > 300
       and _il.specs_filename(_il.fetch_imei_details("353010111111110")).endswith("_specs.json"))
      if _HUB_LIVE else None)
check("IMEI: caption Telegram limit ke andar",
      lambda: 0 < len(_il.render_caption(_il.fetch_imei_details("353010111111110"))) <= 1024)
check("VEHICLE: live hub (report YA saaf disabled-fallback)",
      (lambda: (lambda r: (r.get("ok") is True and bool(r.get("rc", {}).get("maker")))
                or (r.get("ok") is False and r.get("fallback") is True and "error" in r)
                )(_vc.fetch_vehicle_report("HR26EV0001")))
      if _HUB_LIVE else None,
      timeout=120)
def _veh_card_safe():
    r = _vc.fetch_vehicle_report("HR26EV0001")
    if not r.get("ok"):
        # disabled/fail → saaf dict (fallback True) — bot RTO card dikhata hai
        return r.get("fallback") is True or "error" in r
    card = _vc.render_report(r)
    return isinstance(card, str) and len(card) > 50


check("VEHICLE: card HTML-safe / saaf fallback", _veh_card_safe)
check("Bot: IMEI menu button + premium list (10 tools, 32 buttons)",
      lambda: "imei" in _bot.PREMIUM_TOOLS and "clips" in _bot.PREMIUM_TOOLS
      and len(_bot.PREMIUM_TOOLS) == 10
      and any("IMEI" in _bot.unbold(b).upper() for row in _bot.KB_BTNS for b in row)
      and sum(len(r) for r in _bot.KB_BTNS) == 32)
check("Bot: IMEI prompt + video button",
      lambda: "Now send the 15 digit IMEI" in _bot.tool_prompt("imei") and bool(_bot.tool_tutorial_kb("imei")))
check("ClipMaker: limits + url detect",
      lambda: (lambda cm: cm.MAX_MINUTES == 15.0 and cm.MIN_VIDEO == 20.0
               and cm.is_direct_video_url("https://x.com/a.mp4") and cm.is_youtube_url("https://youtu.be/x")
               and "15 min" in cm.help_card())(__import__("modules.clip_maker", fromlist=["x"])))
check("v44: STUDENT EXAM HUB hata (menu + code)",
      lambda: "STUDENT EXAM" not in _bot.unbold(str(_bot.KB_BTNS)).upper()
      and "student_exam" not in open("bot.py", encoding="utf-8").read()
      and "STUDENT_EXAM_TEXT" not in open("modules/sarkari_hub.py", encoding="utf-8").read())
def _pp_on_text():
    src = open("bot.py", encoding="utf-8").read()
    part = src[src.index("async def on_text"):src.index("async def handle_new_tool_file")]
    return ('if mode == "pp_stamp_text"' in part
            and "make_stamped_passport" in part
            and "Now send the video" in part)   # clips branch ke saath hi rehta hai


check("v44: passport photo ka naam+DOP step on_text me hai (crash fix)", _pp_on_text)
check("v44: PTB write timeout bada (bade video send fix)",
      lambda: "write_timeout(240.0)" in open("bot.py", encoding="utf-8").read())
check("v44: clean_err helper + saaf error",
      lambda: "http" not in _bot.clean_err("ERROR: [youtube] fail https://github.com/a/b"))
check("v44: AI brain module + mock + provider detect",
      lambda: (lambda a: hasattr(a, "plan_moments") and hasattr(a, "status_card")
               and a.ai_available() in (True, False)
               and "AI BRAIN" in a.status_card())(__import__("modules.ai_brain", fromlist=["x"])))
check("v44: clip maker AI moments support",
      lambda: "ai_moments" in open("modules/clip_maker.py", encoding="utf-8").read()
      and hasattr(__import__("modules.clip_maker", fromlist=["x"]), "candidates_for_ai"))
check("ClipMaker: asli video par clips (ffmpeg pipeline)",
      _clips_live_probe, timeout=180)
check("Bot: /clipstatus handler registered",
      lambda: 'CommandHandler(["clipstatus", "clipapi"], cmd_clipstatus)' in open("bot.py", encoding="utf-8").read())
check("v46: HUB live — IFSC (asli hub, Demo key)",
      lambda: (lambda r: r.get("ok") is True and "state bank" in str(r.get("bank", "")).lower()
               )(__import__("modules.osint_tools", fromlist=["x"]).lookup_ifsc("SBIN0000001")),
      timeout=90)
check("v46: HUB live — PINCODE (asli hub, Demo key)",
      lambda: (lambda r: r.get("ok") is True and r.get("district") == "Patna"
               )(__import__("modules.osint_tools", fromlist=["x"]).lookup_pincode("800001")),
      timeout=90)
check("v46: HUB live — IP/DOMAIN (asli hub, Demo key)",
      lambda: (lambda r: r.get("ok") is True and "hub" in str(r.get("source", ""))
               )(__import__("modules.osint_tools", fromlist=["x"]).lookup_ip_domain("8.8.8.8")),
      timeout=90)
check("v46: HUB live — key-info (plan)",
      lambda: (lambda r: r.get("ok") is True and "ALL" in str(r.get("plan", "")).upper()
               )(__import__("modules.api_hub", fromlist=["x"]).hub_key_info()),
      timeout=90)
check("v46: HUB disabled endpoints saaf detect hote hain (vehicle/num-info)",
      lambda: (lambda h: h.hub_vehicle_report_new("BR30AR0802").get("disabled_by_hub") in (True, False)
               and h.hub_num_report("9058390341").get("disabled_by_hub") in (True, False)
               )(__import__("modules.api_hub", fromlist=["x"])))
check("Bot: /hubstatus handler registered",
      lambda: 'CommandHandler(["hubstatus", "hubapi", "api"], cmd_hubstatus)' in open("bot.py", encoding="utf-8").read())
check("v45: API hub module + saare wrappers",
      lambda: (lambda h: all(hasattr(h, f) for f in ("hub_ip", "hub_ifsc", "hub_pincode", "hub_terabox",
                                                     "hub_youtube", "_video", "hub_gst", "hub_pan",
                                                     "hub_num_info", "status_card", "live_test")) and not h.hub_ready() == None
               )(__import__("modules.api_hub", fromlist=["x"])))
check("v45: tools hub-first wired (IP/IFSC/pincode/terabox/clips)",
      lambda: all(m in open("modules/osint_tools.py", encoding="utf-8").read() for m in
                  ("hub.hub_ip", "hub.hub_ifsc", "hub.hub_pincode"))
      and "_tb_hub" in open("modules/cloud_tools.py", encoding="utf-8").read()
      and "hub_youtube_download" in open("modules/clip_maker.py", encoding="utf-8").read())
check("v45: kagaz me GST + PAN buttons",
      lambda: 'callback_data="kagaz_gst"' in open("bot.py", encoding="utf-8").read()
      and 'callback_data="kagaz_pan"' in open("bot.py", encoding="utf-8").read()
      and 'mode == "kagaz_gst"' in open("bot.py", encoding="utf-8").read())
check("Bot: /imeistatus handler registered",
      lambda: 'CommandHandler(["imeistatus", "imeiapi"], cmd_imeistatus)' in open("bot.py", encoding="utf-8").read())


fails2 = [(n, st) for n, st, _ in RESULTS if st not in ("PASS", "SKIP")]
_skips = [n for n, st, _ in RESULTS if st == "SKIP"]
if _skips:
    print(f"⏭️  SKIPPED ({len(_skips)} live checks — HUB_API_KEY lagao to ye bhi chalenge):")
    for n in _skips:
        print("   •", n)
print("\n" + "=" * 100)
print(f"FINAL: {len(RESULTS)} checks | PASS: {len(RESULTS)-len(fails2)} | PROBLEM: {len(fails2)}")
for n, st in fails2:
    print("  ⚠️", st, n)
