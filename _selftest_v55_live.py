# -*- coding: utf-8 -*-
"""
_selftest_v55_live.py — v55 AUDIT: har engine ko ASLI inputs par chalao
=====================================================================
Ye suite static tests ke alawa LIVE network calls karta hai (jaise v53 audit
me ki gayi thi). Isse pata chalta hai ki tool sach me chalta hai ya nahi.

Chalane ka tarika:
    python3 _selftest_v55_live.py

Har check: (name, callable, expect_ok_callable)
"""
from __future__ import annotations

import sys
import time
import traceback

PASS, FAIL = [], []


def check(name: str, fn, expect=None):
    """fn chalao. expect(result) True hone par PASS."""
    t0 = time.perf_counter()
    try:
        res = fn()
    except Exception as e:
        FAIL.append((name, f"EXCEPTION {type(e).__name__}: {str(e)[:140]}"))
        print(f"  ❌ {name}: EXCEPTION {type(e).__name__}: {str(e)[:120]}")
        return None
    ms = (time.perf_counter() - t0) * 1000
    ok = True
    why = ""
    if expect is not None:
        try:
            ok, why = expect(res)
        except Exception as e:
            ok, why = False, f"expect-crash: {e}"
    if ok:
        PASS.append((name, round(ms)))
        print(f"  ✅ {name} ({ms:.0f}ms)")
    else:
        FAIL.append((name, f"{why} | result={str(res)[:200]}"))
        print(f"  ❌ {name} ({ms:.0f}ms): {why} | {str(res)[:160]}")
    return res


def section(t: str):
    print(f"\n━━━ {t} ━━━")


# ============================================================ offline first
def main():
    # ---------------------------------------------------------------- QR
    section("📷 QR CODE")
    from modules.general_tools import (make_qr_bytes, make_branded_qr,
                                       wifi_qr_data, vcard_data, build_upi_link)
    check("make_qr_bytes basic", lambda: make_qr_bytes("hello").read(4),
          lambda r: (r[:4] == b"\x89PNG", "not png"))
    check("make_branded_qr+label",
          lambda: make_branded_qr("upi://pay?pa=x@y", label="Scan & Pay").read(4),
          lambda r: (r[:4] == b"\x89PNG", "not png"))
    w = wifi_qr_data("My;Net,work", "p:a\\ss")
    check("wifi_qr_data escaping",
          lambda: w,
          lambda r: ("My\\;Net\\,work" in r and "p\\:a\\\\ss" in r, f"bad escape: {r}"))
    v = vcard_data("Rahul Kumar", "9876543210,9812345670", org="Acme",
                   email="r@x.com", title="Dev", url="https://x.com",
                   address="Patna", note="hi")
    check("vcard_data", lambda: v,
          lambda r: ("BEGIN:VCARD" in r and "TEL;TYPE=CELL:9876543210" in r
                     and "TEL;TYPE=VOICE:9812345670" in r, f"bad vcard: {r[:80]}"))
    check("build_upi_link", lambda: build_upi_link("himanshu@upi", "Utility", amt=49, note="VIP-1-30"),
          lambda r: (r.startswith("upi://pay?pa=himanshu@upi") and "am=49.00" in r, f"bad: {r}"))
    try:
        build_upi_link("bad upi id", "x")
        check("build_upi_link rejects bad", lambda: "no-raise", lambda r: (False, "should raise"))
    except ValueError:
        check("build_upi_link rejects bad", lambda: "raised", lambda r: (True, ""))

    # ---------------------------------------------------------------- IMEI (offline)
    section("📲 IMEI validation")
    from modules.imei_lookup import validate_imei, luhn_ok, clean_imei
    check("clean_imei strips", lambda: clean_imei("IMEI: 35-301011-1111110"),
          lambda r: (r == "353010111111110", f"got {r}"))
    check("luhn valid", lambda: luhn_ok("353010111111110"), lambda r: (r is True, "not ok"))
    check("luhn invalid", lambda: luhn_ok("353010111111111"), lambda r: (r is False, "should fail"))
    ok, c, err = validate_imei("35-301011-1111110")
    check("validate_imei ok", lambda: (ok, c), lambda r: (r[0] and r[1] == "353010111111110", f"{r} {err}"))

    # ---------------------------------------------------------------- desi offline
    section("🧮 DESI TOOLS (offline)")
    from modules.desi_tools import convert_land, registry_cost, statement_passwords, detect_bank, _norm_date
    r = convert_land(1, "bigha", "bihar")
    check("convert_land bigha→sqft", lambda: r.get("sqft"),
          lambda v: (v and abs(v - 27225) < 1, f"got {v}"))
    check("registry_cost", lambda: registry_cost("bihar", 1000, 500)["total"] if isinstance(registry_cost("bihar", 1000, 500), dict) else None,
          lambda v: (v is not None, "no total"))
    check("statement_passwords", lambda: len(statement_passwords("hdfc", "01011990", "RAHUL KUMAR")) >= 3,
          lambda v: (v, "too few passwords"))
    check("detect_bank", lambda: detect_bank("HDFC BANK STATEMENT\nxxxx"),
          lambda v: (bool(v), f"got {v}"))

    # ---------------------------------------------------------------- payguard offline
    section("🛡️ PAYGUARD (offline)")
    from modules.payguard import validate_utr, shot_verdict_line
    check("validate_utr 12-digit", lambda: validate_utr("123456789012"),
          lambda r: (bool(r.get("ok") if isinstance(r, dict) else r), f"got {r}"))
    check("validate_utr rejects short", lambda: validate_utr("123"),
          lambda r: (not (r.get("ok") if isinstance(r, dict) else r), f"got {r}"))

    # ---------------------------------------------------------------- cyber studio
    section("📄 CYBER STUDIO (offline)")
    from modules.cyber_studio import compress_document_pdf
    try:
        import io as _io
        from PIL import Image
        _im = Image.new("RGB", (800, 1000), (255, 255, 255))
        _b = _io.BytesIO(); _im.save(_b, format="JPEG"); pdf_bytes = _b.getvalue()
        # v55 fix verify: single bytes bhejne par bhi crash nahi hona chahiye
        out = compress_document_pdf(pdf_bytes)
        check("compress_document_pdf single-bytes (v55 fix)",
              lambda: out.read(4) == b"%PDF", lambda r: (r, f"got {type(out)}"))
        out2 = compress_document_pdf([pdf_bytes, pdf_bytes])
        check("compress_document_pdf list input",
              lambda: out2.read(4) == b"%PDF", lambda r: (r, "not pdf"))
    except Exception as e:
        check("compress_document_pdf", lambda: (_ for _ in ()).throw(e), lambda r: (False, "setup fail"))

    # ---------------------------------------------------------------- toolkit extras
    section("🔗 TOOLKIT EXTRAS (offline)")
    from modules.toolkit_extras import clean_tracking, file_size_human
    check("clean_tracking strips utm", lambda: clean_tracking("https://x.com/a?utm_source=ig&b=1"),
          lambda r: ("utm_source" not in r and "b=1" in r, f"got {r}"))
    check("file_size_human", lambda: file_size_human(1536),
          lambda r: ("1.5" in str(r) and ("KB" in str(r) or "K" in str(r)), f"got {r}"))

    # ---------------------------------------------------------------- gaming offline
    section("🎮 GAMING (offline)")
    from modules.gaming_tools import parse_region, strip_region, bgmi_availability
    check("parse_region", lambda: parse_region("12345 (IND)"),
          lambda r: (bool(r), f"got {r}"))
    check("strip_region", lambda: strip_region("12345 (IND)"),
          lambda r: ("12345" in str(r) and "IND" not in str(r), f"got {r}"))
    av = bgmi_availability()
    check("bgmi_availability shape", lambda: sorted(av.keys()) if isinstance(av, dict) else None,
          lambda r: ("ok" in r, f"keys={r}"))

    # ---------------------------------------------------------------- pinterest offline
    section("📌 PINTEREST (offline)")
    from modules. import extract_pin_id
    for url, want in [("https://www.pinterest.com/pin/1234567890/", "1234567890"),
                      ("https:/abc123", None),
                      ("https://in.pinterest.com/pin/987654321/", "987654321")]:
        check(f"extract_pin_id {url[:40]}", lambda u=url: extract_pin_id(u),
              lambda r, w=want: ((r == w) if w else (r is None or isinstance(r, str)),
                                 f"got {r} want {w}"))

    # ============================================================ LIVE
    section("🌐 LIVE: WEB / OSINT")

    from modules.osint_tools import lookup_ifsc, lookup_pincode, lookup_ip_domain, upi_verify
    check("IFSC SBIN0000309", lambda: lookup_ifsc("SBIN0000309"),
          lambda r: (isinstance(r, dict) and r.get("ok"), f"got {str(r)[:150]}"))
    check("IFSC bad format", lambda: lookup_ifsc("XXX"),
          lambda r: (not (r.get("ok") if isinstance(r, dict) else True), f"got {str(r)[:100]}"))
    check("PINCODE 826001 (Dhanbad)", lambda: lookup_pincode("826001"),
          lambda r: (isinstance(r, dict) and (r.get("ok") or r.get("post_offices")), f"got {str(r)[:150]}"))
    check("IP/DOMAIN google.com", lambda: lookup_ip_domain("google.com"),
          lambda r: (isinstance(r, dict) and r.get("ok"), f"got {str(r)[:150]}"))

    section("🌐 LIVE: APP FINDER")
    from modules.general_tools import app_lookup
    check("app_lookup whatsapp", lambda: app_lookup("whatsapp", use_cache=False),
          lambda r: (isinstance(r, dict) and r.get("found"), f"got {str(r)[:200]}"))
    check("app_lookup fake app", lambda: app_lookup("xyzabc123fakenonexistentapp", use_cache=False),
          lambda r: (isinstance(r, dict) and not r.get("found"), f"got {str(r)[:200]}"))

    section("🌐 LIVE: WEB SCRAPER")
    from modules.web_tools import scrape_public_text, extract_readable, reading_time_min
    # v55: example.com sirf 25-word ka page hai (readable-article threshold se
    # neeche) — asli article page se test karo.
    check("scrape wikipedia article", lambda: scrape_public_text("https://en.wikipedia.org/wiki/India", use_cache=False),
          lambda r: (isinstance(r, dict) and r.get("ok") and len(str(r.get("text") or "")) > 200,
                     f"got {str(r)[:200]}"))
    check("extract_readable html", lambda: extract_readable(
        "<html><body><article><h1>Title</h1><p>"
        + "This is a proper article paragraph with enough words to pass the readability threshold. " * 5
        + "</p></article></body></html>", "https://x.com"),
        lambda r: (isinstance(r, dict) and len(str(r.get("text") or "")) > 50 and r.get("words", 0) > 20,
                   f"got {str(r)[:150]}"))
    check("reading_time_min", lambda: reading_time_min(400),
          lambda v: (isinstance(v, int) and v >= 1, f"got {v}"))

    section("🌐 LIVE: TEMP MAIL")
    from modules.temp_mail import tm_domains, extract_codes
    doms = tm_domains()
    check("tm_domains", lambda: len(doms), lambda n: (n > 0, f"got {n} domains"))
    codes = extract_codes("Your OTP 482913", "", "Do not share. Your verification code is 482913.")
    check("extract_codes OTP", lambda: [c["code"] for c in codes],
          lambda r: ("482913" in r, f"got {r}"))

    section("🌐 LIVE: LINK TOOLS")
    from modules.toolkit_extras import analyze_link
    check("analyze_link example.com", lambda: analyze_link("https://example.com"),
          lambda r: (isinstance(r, dict) and r.get("ok"), f"got {str(r)[:200]}"))

    section("🌐 LIVE: CLOUD TOOLS")
    from modules.cloud_tools import is_gdrive_url, is_terabox_url, resolve_gdrive_direct
    check("is_gdrive_url", lambda: is_gdrive_url("https://drive.google.com/file/d/ABC/view"),
          lambda r: (r is True, f"got {r}"))
    check("is_terabox_url", lambda: is_terabox_url("https://terabox.com/s/1abc"),
          lambda r: (r is True, f"got {r}"))

    section("🌐 LIVE: MEDIA DOWNLOADER")
    from modules.media_downloader import platform_name, is_supported_video_url
    check("platform_name youtube", lambda: platform_name("https://youtube.com/watch?v=x"),
          lambda r: (bool(r), f"got {r}"))
    check("is_supported_video_url yt", lambda: is_supported_video_url("https://youtu.be/x"),
          lambda r: (r is True, f"got {r}"))

    section("🌐 LIVE: API HUB")
    from modules import api_hub
    st = api_hub.status_card()
    check("api_hub.status_card", lambda: isinstance(st, str) and len(st) > 10,
          lambda r: (r, f"got {str(st)[:100]}"))
    lt = api_hub.live_test()
    check("api_hub.live_test chalta hai", lambda: isinstance(lt, dict) and "ok" in lt,
          lambda r: (r, f"keys={list(lt.keys()) if isinstance(lt, dict) else lt}"))

    section("🌐 LIVE: OSINT TOOLS")
    from modules.osint_tools import upi_verify, tg_user_public, domain_osint, lookup_phone_info
    check("upi_verify valid format", lambda: upi_verify("himanshu@upi"),
          lambda r: (isinstance(r, dict) and "ok" in r, f"got {str(r)[:150]}"))
    check("upi_verify garbage", lambda: upi_verify("not-a-upi"),
          lambda r: (isinstance(r, dict) and not r.get("ok"), f"got {str(r)[:150]}"))
    check("tg_user_public", lambda: tg_user_public("Supermannn_x"),
          lambda r: (isinstance(r, dict), f"got {str(r)[:150]}"))
    check("domain_osint google.com", lambda: domain_osint("google.com"),
          lambda r: (isinstance(r, dict), f"got {str(r)[:200]}"))
    check("lookup_phone_info", lambda: lookup_phone_info("9876543210"),
          lambda r: (isinstance(r, dict), f"got {str(r)[:150]}"))

    section("🌐 LIVE: PINTEREST SEARCH")
    from modules. import pinterest_search
    check("pinterest_search", lambda: pinterest_search("couple dp", use_cache=False),
          lambda r: (isinstance(r, dict) and r.get("ok"), f"got {str(r)[:200]}"))

    section("🌐 LIVE: GAMING ENGINES")
    from modules.gaming_tools import ff_service_status, bgmi_availability, ff_regions
    check("ff_service_status", lambda: ff_service_status(force=True),
          lambda r: (isinstance(r, dict) and "ok" in r, f"got {str(r)[:150]}"))
    check("ff_regions", lambda: ff_regions(),
          lambda r: (isinstance(r, (list, dict)) and len(r) > 0, f"got {str(r)[:100]}"))

    section("🌐 LIVE: MEDIA / TTS")
    from modules.desi_tools import hindi_tts
    import asyncio as _asyncio
    def _tts():
        return _asyncio.run(hindi_tts("namaste doston, kaise ho", voice="male"))
    check("hindi_tts", _tts,
          lambda r: (isinstance(r, dict) and r.get("ok") and r.get("bytes"),
                     f"got {str(r)[:150]}"))

    section("🌐 LIVE: YT QUALITIES")
    from modules.media_downloader import yt_available_qualities
    check("yt_available_qualities", lambda: yt_available_qualities("https://www.youtube.com/watch?v=aqz-KE-bpKQ"),
          lambda r: (isinstance(r, list), f"got {str(r)[:150]}"))

    section("🌐 LIVE: IMEI (hub)")
    from modules.imei_lookup import fetch_imei_details, render_report
    _im = fetch_imei_details("353010111111110", use_cache=False)
    check("fetch_imei_details", lambda: isinstance(_im, dict) and "ok" in _im,
          lambda r: (r, f"got {str(_im)[:200]}"))
    if _im.get("ok"):
        check("render_report", lambda: len(render_report(_im)) > 20,
              lambda r: (r, "report khaali"))

    section("🌐 LIVE: OSINT HUB")
    from modules.osint_hub import num_info_report, hub_status
    check("osint_hub.num_info_report", lambda: num_info_report("9876543210"),
          lambda r: (isinstance(r, dict), f"got {str(r)[:150]}"))
    check("osint_hub.hub_status", lambda: len(hub_status()) > 10,
          lambda r: (r, "status khaali"))

    section("🌐 LIVE: CLOUD RESOLVER")
    from modules.cloud_tools import resolve_cloud_url
    check("resolve_cloud_url gdrive", lambda: resolve_cloud_url(
        "https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9I0J/view"),
        lambda r: (isinstance(r, dict), f"got {str(r)[:200]}"))

    # ---------------------------------------------------------------- summary
    print("\n" + "=" * 60)
    print(f"  v55 LIVE AUDIT — PASS: {len(PASS)} | FAIL: {len(FAIL)}")
    print("=" * 60)
    if FAIL:
        print("\n🚨 FAILURES:")
        for n, w in FAIL:
            print(f"  • {n}: {w}")
    slow = sorted(PASS, key=lambda x: -x[1])[:5]
    print("\n🐢 Slowest:", ", ".join(f"{n} {ms}ms" for n, ms in slow))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
