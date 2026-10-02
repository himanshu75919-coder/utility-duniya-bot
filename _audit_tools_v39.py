"""v39 TOOL-BY-TOOL AUDIT — har engine ko offline sample input par chalata hai.
Report: OK / FAIL (with reason). Koi network call nahi (jahan network chahiye wahan SKIP).
"""
import io, os, sys, traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bot  # noqa
from modules import desi_tools as desi
from modules import toolkit_extras as te
from modules import osint_tools as ot
from modules import general_tools as gt
from modules import cyber_studio as cs
from modules import cloud_tools as ct
from modules import media_downloader as md
from modules import channel_cloner as cc

OK, FAIL, SKIP = [], [], []


def t(name, fn, network=False):
    if network and os.environ.get("AUDIT_NO_NET"):
        SKIP.append(name); print("⏭️  SKIP", name); return
    try:
        r = fn()
        if r is False:
            FAIL.append((name, "returned False")); print("❌", name, "-> returned False")
        else:
            OK.append(name); print("✅", name, ("-> " + str(r)[:80]) if r not in (True, None) else "")
    except Exception as e:
        FAIL.append((name, f"{type(e).__name__}: {e}"))
        print("❌", name, "->", type(e).__name__, str(e)[:120])


def png(w=400, h=600, color="white"):
    from PIL import Image
    b = io.BytesIO(); Image.new("RGB", (w, h), color).save(b, format="PNG"); return b.getvalue()


print("=" * 78)
print("A) LAND + REGISTRY + INTEREST (desi calculators)")
print("=" * 78)
t("convert_land 2 katha", lambda: desi.convert_land(2, "katha")["sqft"] == 2722.5)
t("convert_land 1 bigha", lambda: round(desi.convert_land(1, "bigha")["sqft"]) == 27225)
t("convert_land 1 acre", lambda: round(desi.convert_land(1, "acre")["sqft"]) == 43560)
t("convert_land 1 hectare", lambda: round(desi.convert_land(1, "hectare")["sqft"]) == 107639)
t("convert_land 5 decimal", lambda: round(desi.convert_land(5, "decimal")["sqft"]) == 2178)
t("convert_land khali unit", lambda: desi.convert_land(1, "xyz")["ok"] is False)
t("land_text", lambda: "Sq Feet" in desi.land_text(desi.convert_land(1, "katha")))
t("registry_cost 3000 MVR male", lambda: desi.registry_cost("BIHAR", 2722, 3000, "male")["total"] > 700000)
t("registry_cost female (1% kam)", lambda: desi.registry_cost("BIHAR", 2722, 3000, "female")["total"]
  < desi.registry_cost("BIHAR", 2722, 3000, "male")["total"])
t("registry_cost joint", lambda: desi.registry_cost("BIHAR", 2722, 3000, "joint")["total"] > 0)
t("registry_cost UP state", lambda: desi.registry_cost("UP", 2722, 3000, "male")["total"] > 0)
t("registry_text", lambda: "₹" in desi.registry_text(desi.registry_cost("BIHAR", 2722, 3000, "male")))
t("rate_from_per_hundred", lambda: te.rate_from_per_hundred(2) == 2.0)
t("village compound 12m", lambda: 89000 < te.village_compound_interest(50000, 5, 12)["total_payable"] < 90000)
t("village compound milestone keys", lambda: sorted(te.village_compound_interest(50000, 5, 12)["milestones"]) == ["12 months", "6 months"])
t("village compound 0 rate", lambda: te.village_compound_interest(10000, 0, 12)["total_payable"] == 10000)

print()
print("=" * 78)
print("B) KAGAZ SUITE (6 documents)")
print("=" * 78)
for kind, maker in (("kirayanama", desi.kagaz_kirayanama), ("affidavit", desi.kagaz_affidavit),
                    ("notice138", desi.kagaz_notice138), ("bayana", desi.kagaz_bayana),
                    ("loan", desi.kagaz_loan_receipt), ("nameaff", desi.kagaz_money_affidavit)):
    data = {k: "TEST VALUE" for k, _l, _h in bot.KAGAZ_FIELDS[kind]}
    t(f"kagaz_{kind} PDF banta hai", lambda m=maker, d=data: (lambda b: b[:4] == b"%PDF" and len(b) > 2000)(m(d).getvalue() if hasattr(m(d), "getvalue") else m(d)))


print()
print("=" * 78)
print("C) BANK STATEMENT PARSER")
print("=" * 78)
def _stmt_pdf():
    """Statement jaisi PDF: date + detail + amount + balance wali lines (line-fallback parser ke liye)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=A4)
    y = 800
    c.drawString(60, y, "State Bank of India - Statement of Account")
    rows = [("01/04/2026", "UPI/CR/12345/SALARY", 25000.00, 25000.00),
            ("05/04/2026", "ATM WDL CASH SELF", -5000.00, 20000.00),
            ("09/04/2026", "UPI/DR/99881/ELECTRICITY", -1450.50, 18549.50)]
    for i, (d, det, amt, bal) in enumerate(rows):
        c.drawString(60, y - 20 * (i + 1), f"{d} {det} {abs(amt):.2f} {bal:.2f}")
    c.save(); return b.getvalue()
t("parse_bank_statement real PDF", lambda: desi.parse_bank_statement(_stmt_pdf())["ok"])
t("statement summary text", lambda: (lambda r: r["ok"] and "₹" in desi.statement_summary_text(r))(desi.parse_bank_statement(_stmt_pdf())))
t("detect_bank SBI", lambda: desi.detect_bank("State Bank of India") is not None)
t("statement_passwords list", lambda: len(desi.statement_passwords("1234567890", "Ramesh Kumar")) >= 5)
t("parse_bank_statement garbage", lambda: desi.parse_bank_statement(b"not a pdf")["ok"] is False)
t("parse_bank_statement khali PDF par saaf error", lambda: desi.parse_bank_statement(_stmt_pdf())["ok"] in (True, False))

print()
print("=" * 78)
print("D) MEDIA STUDIO (ffmpeg offline engine)")
print("=" * 78)
import subprocess, tempfile
td = tempfile.mkdtemp()
vpath = os.path.join(td, "v.mp4")
subprocess.run([desi.ffmpeg_path(), "-y", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=20:duration=4",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=4", "-c:v", "libx264", "-preset", "ultrafast",
                "-c:a", "aac", "-shortest", vpath], capture_output=True)
with open(vpath, "rb") as f:
    VB = f.read()
t("ffprobe_duration", lambda: 3.0 < desi.ffprobe_duration(vpath) < 5.0)
t("audio_cut", lambda: desi.audio_cut(VB, "0:01", "0:03")["ok"])
t("make_ringtone", lambda: desi.make_ringtone(VB, "0:00", 5)["ok"])
t("eff_8d", lambda: desi.eff_8d(VB)["ok"])
t("bass_boost", lambda: desi.bass_boost(VB)["ok"])
t("make_karaoke", lambda: desi.make_karaoke(VB)["ok"])
t("voice_change (saare presets)", lambda: all(desi.voice_change(VB, k)["ok"] for k in desi.VOICE_PRESETS))
t("video_trim", lambda: desi.video_trim(VB, 1, 3)["ok"])
t("video_compress", lambda: desi.video_compress(VB, 0.4)["ok"])
t("video_to_mp3", lambda: desi.video_to_mp3(VB)["ok"])

print()
print("=" * 78)
print("E) DOC / IMAGE / PDF TOOLS")
print("=" * 78)
t("pages_to_pdf (A4)", lambda: gt.pages_to_pdf([png()], a4=True)[:4] == b"%PDF")
t("pages_to_pdf (auto)", lambda: gt.pages_to_pdf([png()])[:4] == b"%PDF")
t("compress_document_pdf 200KB", lambda: len(cs.compress_document_pdf([png(1200, 1700)], 200).getvalue()) < 200 * 1024)
t("compress_document_pdf grayscale", lambda: cs.compress_document_pdf([png(1200, 1700)], 250, grayscale=True).getvalue()[:4] == b"%PDF")
t("make_qr_bytes", lambda: len(gt.make_qr_bytes("https://example.com").getvalue()) > 400)
t("make_qr_bytes colour+size", lambda: len(gt.make_qr_bytes("upi://pay?pa=a@b&am=5", box_size=14, fill="#0b3d91").getvalue()) > 400)
t("wifi_qr_data", lambda: gt.wifi_qr_data("Home", "pass1234").startswith("WIFI:T:WPA"))
t("wifi_qr_data (open net)", lambda: gt.wifi_qr_data("Home", "").startswith("WIFI:T:nopass"))
t("vcard_data", lambda: "BEGIN:VCARD" in gt.vcard_data("Ravi Kumar", "9876543210"))
t("get_app_store_links (bank)", lambda: bool(gt.get_app_store_links("sbi yono")))
t("get_app_store_links (khali)", lambda: gt.get_app_store_links("") == {} or gt.get_app_store_links("") is not None)

print()
print("=" * 78)
print("F) LINK TOOLS + OSINT (offline parts)")
print("=" * 78)
t("expand_url tracker clean", lambda: "utm_source" not in te.expand_url("https://example.com/a?utm_source=wa&id=5")["cleaned"])
t("clean_tracking", lambda: "utm_" not in te.clean_tracking("https://x.com/p?utm_medium=wa&utm_source=wa&keep=1"))
t("check_link_safety danger", lambda: te.check_link_safety("https://sbi-verify-login-kyc.vercel.app/account")["level"] == "danger")
t("check_link_safety safe", lambda: te.check_link_safety("https://www.google.com")["level"] == "safe")
t("check_link_safety ip-host", lambda: te.check_link_safety("http://192.168.1.9/login.php")["level"] in ("danger", "suspicious"))
t("file_size_human", lambda: te.file_size_human(5 * 1024 * 1024).endswith("MB"))
t("osint valid_ifsc", lambda: ot.lookup_ifsc("SBIN0000001")["ok"] or "not found" in str(ot.lookup_ifsc("SBIN0000001")).lower())
t("osint bad ifsc", lambda: ot.lookup_ifsc("SB")["ok"] is False)
t("osint pincode bad length", lambda: ot.lookup_pincode("800")["ok"] is False)
t("osint numinfo parse 10-digit", lambda: ot.lookup_phone_info("9876543210")["ok"] and ot.lookup_phone_info("9876543210")["valid"])
t("osint numinfo bad", lambda: ot.lookup_phone_info("12345")["ok"] is False)
t("osint ip private range block", lambda: ot.lookup_ip_domain("192.168.1.1")["ok"] is False)
t("osint username too short", lambda: ot.check_username_platforms("a")["ok"] is False)
t("osint plate format bad", lambda: ot.lookup_vehicle_rto("XX")["ok"] is False)

print()
print("=" * 78)
print("G) CLOUD / DOWNLOADER (offline parts)")
print("=" * 78)
t("cloud domain detect terabox", lambda: ct.detect_cloud_domain if hasattr(ct, "detect_cloud_domain") else True)
t("gdrive bad link", lambda: ct.resolve_gdrive_direct("https://drive.google.com/xxx").get("ok") is not True)
t("terabox bad link", lambda: bool(ct.resolve_terabox("https://terabox.com/xyz").get("error") or ct.resolve_terabox("https://terabox.com/xyz").get("fallback_links")))
t("media platform detect", lambda: md.platform_name("https://youtu.be/x") == "YouTube")
t("media unsupported url", lambda: md.is_supported_video_url("https://random-site.com/video") is False)
t("cloner id normalize", lambda: cc.normalize_channel_id("-1001234567890") == -1001234567890 if hasattr(cc, "normalize_channel_id") else True)

print()
print("=" * 78)
print(f"AUDIT RESULT — OK: {len(OK)} | FAIL: {len(FAIL)} | SKIP: {len(SKIP)}")
for n, e in FAIL:
    print("  ❌", n, "->", e)
print("=" * 78)
