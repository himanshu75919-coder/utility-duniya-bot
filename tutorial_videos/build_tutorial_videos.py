"""
build_tutorial_videos.py — Utility Duniya Bot ke har tool ka tutorial video banata hai.
=====================================================================================
Har video: 1080x1920 (vertical) • ~30-40 sec • Hindi voiceover (AI) •
character: 16-saal aesthetic ladka, hoodie par "HIMANSHU" bold capitals • purple theme.

Ek video banane ke liye:   python3 build_tutorial_videos.py video_dl
Sab banane ke liye:        python3 build_tutorial_videos.py --all
Ek saath N parallel:       python3 build_tutorial_videos.py --all --jobs 4
Sirf script check:         python3 build_tutorial_videos.py video_dl --dry
"""
import argparse
import asyncio
import math
import os
import random
import subprocess
import time

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
OUT_DIR = os.path.join(ROOT, "videos")
CACHE = os.path.join(ROOT, "cache")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 24

# ---------------- fonts ----------------
F_TITLE = os.path.join(ASSETS, "Anton.ttf")                  # bade English title
F_BODY = os.path.join(ASSETS, "Poppins-ExtraBold.ttf")       # English body
F_HINDI = os.path.join(ASSETS, "NotoSansDevanagari-Bold.ttf")  # Hindi text
F_NUM = os.path.join(ASSETS, "ArchivoBlack.ttf")

F_EMOJI = os.path.join(ASSETS, "TwemojiMozilla.ttf")
_font_cache = {}

import re as _re
_EMOJI_RE = _re.compile(
    "(?:[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2190-\u21FF\u203C\u2049\u2122\u2139\u25AA-\u25FE\u2705\u274C\u2714\u2757\u2753\u2764\u2B50]"
    "|[0-9#*]\uFE0F?\u20E3)"
    "(?:[\uFE0F\u200D]?(?:[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u203C\u2049\u2122\u2139\u25AA-\u25FE\u2705\u274C\u2714\u2757\u2753\u2764\u2B50]|[0-9#*]\uFE0F?\u20E3))*")


def text_runs(text):
    """Text ko (is_emoji, chunk) runs me todta hai."""
    runs, pos = [], 0
    for m in _EMOJI_RE.finditer(text):
        if m.start() > pos:
            runs.append((False, text[pos:m.start()]))
        chunk = m.group(0)
        # zWJ/variation selectors ko alag na karo — emoji font sambhal lega
        runs.append((True, chunk))
        pos = m.end()
    if pos < len(text):
        runs.append((False, text[pos:]))
    return [(e, c) for e, c in runs if c and c not in ("\ufe0f",)]


def measure(d, text, f, esize=None):
    """Mixed text ki width (emoji ke saath)."""
    total = 0
    ef = font(F_EMOJI, esize or int(f.size * 1.0))
    for is_e, chunk in text_runs(text):
        if is_e:
            try:
                total += d.textlength(chunk, font=ef, embedded_color=True)
            except Exception:
                total += f.size * 0.9 * len(chunk)
        else:
            total += d.textlength(chunk, font=f)
    return total


def draw_mixed(d, xy, text, f, fill, esize=None):
    """Emoji + text dono sahi render karta hai (emoji color me aate hain)."""
    x, y = xy
    ef = font(F_EMOJI, esize or int(f.size * 1.0))
    for is_e, chunk in text_runs(text):
        if is_e:
            chunk = chunk.replace("\ufe0f", "").replace("\u200d", "")  # variation selector se tofu box aata hai
            try:
                # Pillow quirk: akela emoji render nahi hota — trailing space zaroori hai
                d.text((x, y - int(f.size * 0.10)), chunk + " ", font=ef, embedded_color=True, fill=fill)
                x += d.textlength(chunk, font=ef, embedded_color=True)
            except Exception:
                x += f.size * 0.95 * len(chunk)
        else:
            d.text((x, y), chunk, font=f, fill=fill)
            x += d.textlength(chunk, font=f)
    return x


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        f = ImageFont.truetype(path, size)
        try:
            if "Devanagari" in path:
                f.set_variation_by_axes([100])
        except Exception:
            pass
        _font_cache[key] = f
    return _font_cache[key]


# ---------------- colors (Telegram dark + purple) ----------------
BG_TOP = (11, 7, 20)
BG_BOT = (18, 10, 33)
PURPLE = (140, 106, 255)
PURPLE_D = (94, 66, 200)
GOLD = (255, 196, 61)
WHITE = (245, 244, 255)
GRAY = (168, 160, 195)
BUBBLE_ME = (124, 92, 255)
BUBBLE_BOT = (24, 33, 46)
CARD = (13, 20, 30)
GREEN = (74, 222, 128)


# ======================================================================
#  TOOL SPECS  (har tool ka tutorial video ka data)
# ======================================================================
def T(key, title, hindi_title, emoji, pose, steps, narration, outro, cta="BOT START KARO"):
    return dict(key=key, title=title, hi=hindi_title, emoji=emoji, pose=pose,
                steps=steps, narration=narration, outro=outro, cta=cta)


TOOLS = [
    T("video_dl", "VIDEO DOWNLOADER", "वीडियो डाउनलोडर", "📥", "char_phone",
      steps=[
          ("1️⃣ मेनू से टूल खोलो", [("me", "📥 VIDEO DOWNLOADER"), ("bot", "🔗 Video ka link bhejo\n(Instagram • YouTube • Facebook • TikTok)")]),
          ("2️⃣ Share → Copy Link", [("bot", "Video kholo → Share → Copy Link"), ("me", "https://www.instagram.com/reel/Dc9Wj49z_IC/")]),
          ("3️⃣ लिंक बॉट में भेजो", [("bot", "⏳ Video nikal raha hoon..."), ("bot", "🎬 Video ready! 12.4 MB ✅")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! वीडियो डाउनलोडर टूल। स्टेप एक, नीचे मेनू से ये टूल खोलो। स्टेप दो, इंस्टाग्राम, यूट्यूब, फेसबुक या टिकटॉक का पब्लिक वीडियो खोलो और शेयर से कॉपी लिंक करो। स्टेप तीन, वो लिंक बॉट में भेज दो। बस, कुछ सेकंड में वीडियो डाउनलोड! धन्यवाद दोस्तों!",
      outro="48MB तक वीडियो सीधे बॉट में आता है"),
    T("terabox", "TERABOX DOWNLOADER", "टेराबॉक्स डाउनलोडर", "⚡", "char_phone",
      steps=[
          ("1️⃣ मेनू से टूल खोलो", [("me", "⚡ TERABOX DOWNLOADER"), ("bot", "🔗 Terabox / Mediafire / GDrive link bhejo")]),
          ("2️⃣ Share → Copy Link", [("bot", "File kholo → Share → Copy Link"), ("me", "https://terabox.com/s/1BmIr01rHN7K")]),
          ("3️⃣ डायरेक्ट लिंक मिलेगा", [("bot", "⏳ Link nikal raha hoon..."), ("bot", "✅ Direct link ready!\n📥 Bina ad, bina speed-limit")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! टेराबॉक्स डाउनलोडर। स्टेप एक, मेनू से टेराबॉक्स डाउनलोडर खोलो। स्टेप दो, टेराबॉक्स, मीडियाफायर या गूगल ड्राइव की फाइल का कॉपी लिंक करो। स्टेप तीन, लिंक बॉट में पेस्ट करके भेज दो। बिना एड, बिना स्पीड लिमिट डायरेक्ट लिंक मिलेगा! धन्यवाद दोस्तों!",
      outro="Bina ad • Bina speed-limit • Browser player"),
    T("cloner", "CHANNEL CLONER", "ऑटो फॉरवर्ड सेटअप", "🔄", "char_point",
      steps=[
          ("1️⃣ SOURCE चुनो", [("me", "🔄 CHANNEL CLONER"), ("bot", "Step 1: Source channel ka link/username bhejo\n(ya private channel ki post forward karo)")]),
          ("2️⃣ TARGET चुनो", [("me", "@mychannel"), ("bot", "✅ Source set!\nAb Target channel bhejo (bot wahan admin ho)")]),
          ("3️⃣ FULL AUTO ON", [("bot", "🚀 FULL AUTO ON!\nAb source ki posts khud target me jayengi")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! चैनल क्लोनर यानी ऑटो फॉरवर्ड। स्टेप एक, सोर्स चैनल का लिंक भेजो। प्राइवेट चैनल हो तो उसकी कोई पोस्ट बॉट को फॉरवर्ड कर दो। स्टेप दो, टारगेट चैनल भेजो, बॉट वहाँ एडमिन होना चाहिए। स्टेप तीन, फुल ऑटो ऑन कर दो। बस, हर पोस्ट खुद चली जाएगी! धन्यवाद दोस्तों!",
      outro="Source की हर post खुद target में जाएगी"),
    T("voice", "ACTORS VOICE STUDIO", "आवाज़ स्टूडियो", "🎙️", "char_phone",
      steps=[
          ("1️⃣ टूल खोलो", [("me", "🎙️ ACTORS VOICE STUDIO"), ("bot", "🎭 Actor Voices (24)\n🧪 Voice Lab (30 + speed)")]),
          ("2️⃣ आवाज़ चुनो + टेक्स्ट", [("me", "Don — रुको ज़रा, सबर करो!"), ("bot", "⏳ Awaaz ban rahi hai...")]),
          ("3️⃣ ऑडियो तैयार", [("bot", "🎧 Voice ready!\nSuno aur download karo")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! एक्टर्स वॉइस स्टूडियो। यहाँ टेक्स्ट लिखकर असली जैसी आवाज़ बनती है। स्टेप एक, मेनू से ये टूल खोलो। स्टेप दो, चौबीस एक्टर वॉइस या तीस वॉइस लैब में से कोई आवाज़ चुनो, स्पीड भी सेट करो। स्टेप तीन, अपना टेक्स्ट भेज दो। ऑडियो तैयार! धन्यवाद दोस्तों!",
      outro="24 actor + 30 lab voices • 4 speeds"),
    T("pp_stamp", "PASSPORT PHOTO", "पासपोर्ट फोटो", "📸", "char_point",
      steps=[
          ("1️⃣ फोटो भेजो", [("me", "📸 PASSPORT PHOTO"), ("bot", "Photo bhejo (saamne se, clear)")]),
          ("2️⃣ नाम + डेट लिखो", [("me", "Himanshu Kumar\n02-10-2026"), ("bot", "⏳ Photo ban rahi hai...")]),
          ("3️⃣ तैयार फोटो", [("bot", "✅ 3.5 x 4.5 cm photo ready!\nNaam + date stamp ke saath")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! पासपोर्ट फोटो टूल। स्टेप एक, मेनू से पासपोर्ट फोटो खोलो और सामने से खिंची साफ फोटो भेजो। स्टेप दो, अपना नाम लिखो और फोटो की डेट भेजो। बस, तीन पॉइंट पाँच गुना चार पॉइंट पाँच सेंटीमीटर की फोटो तैयार, नाम और डेट स्टैम्प के साथ। धन्यवाद दोस्तों!",
      outro="SSC • Railway • BPSC form ke liye perfect"),
    T("print_sheet", "8-IN-1 PRINT SHEET", "8 फोटो शीट", "🖨️", "char_thumb",
      steps=[
          ("1️⃣ एक फोटो भेजो", [("me", "🖨️ 8-IN-1 PRINT SHEET"), ("bot", "Ek passport photo bhejo")]),
          ("2️⃣ बॉट शीट बनाएगा", [("bot", "⏳ 8 copies laga raha hoon...")]),
          ("3️⃣ शीट तैयार", [("bot", "✅ 8-in-1 sheet ready!\nStudio se ₹10-20 me print karwao")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! आठ इन वन प्रिंट शीट। स्टेप एक, मेनू से ये टूल खोलो और एक पासपोर्ट फोटो भेजो। बॉट खुद आठ कॉपी एक शीट पर लगा देगा। फिर ये शीट किसी फोटो स्टूडियो से दस से बीस रुपये में प्रिंट करवा लो। धन्यवाद दोस्तों!",
      outro="Ek photo → 8 copies → ₹10-20 me print"),
    T("doc_compress", "DOCUMENT PDF COMPRESS", "डॉक्युमेंट कंप्रेस", "📄", "char_phone",
      steps=[
          ("1️⃣ मार्कशीट की फोटो", [("me", "📄 DOCUMENT PDF COMPRESS"), ("bot", "Marksheet / certificate ki photo bhejo (2-3 bhi chalengi)")]),
          ("2️⃣ साइज़ चुनो", [("me", "📸 [photo]"), ("bot", "📉 100KB • 200KB • 500KB\nSize chuno 👇")]),
          ("3️⃣ PDF तैयार", [("bot", "✅ Sharp PDF ready — 198KB\n(Online form me upload karo)")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! डॉक्युमेंट पीडीएफ कंप्रेस। स्टेप एक, मेनू से ये टूल खोलो और मार्कशीट या सर्टिफिकेट की फोटो भेजो। स्टेप दो, बॉट साइज़ के बटन दिखाएगा, अपना साइज़ चुनो। शार्प पीडीएफ तैयार, ऑनलाइन फॉर्म में सीधे अपलोड करो। धन्यवाद दोस्तों!",
      outro="100KB se 500KB tak — upload ke liye ready"),
    T("pdf", "IMAGE TO PDF", "फोटो से PDF", "🖼️", "char_point",
      steps=[
          ("1️⃣ फोटो भेजो (10 तक)", [("me", "🖼️ IMAGE→PDF"), ("bot", "Ek-ek karke 10 photo tak bhejo")]),
          ("2️⃣ PDF बनाओ दबाओ", [("me", "📸 [3 photos]"), ("bot", "📄 Normal PDF (jaisa hai waisa)\n🖨️ A4 PDF (print ke liye)")]),
          ("3️⃣ PDF तैयार", [("bot", "✅ 3-page PDF ready!")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! इमेज टू पीडीएफ। स्टेप एक, मेनू से ये टूल खोलो और एक एक करके दस फोटो तक भेजो। स्टेप दो, नीचे से नॉर्मल पीडीएफ या ए फोर पीडीएफ चुनो। ए फोर प्रिंट के लिए सही साइज़ देता है। बस, आपकी पीडीएफ तैयार! धन्यवाद दोस्तों!",
      outro="10 photo tak • Normal ya A4 print"),
    T("shot", "SITE SCREENSHOT", "वेबसाइट स्क्रीनशॉट", "🖼️", "char_phone",
      steps=[
          ("1️⃣ टूल खोलो", [("me", "🖼️ SITE SCREENSHOT"), ("bot", "Website ka URL bhejo")]),
          ("2️⃣ HD या Full Page", [("me", "github.com"), ("bot", "🖼️ HD Screenshot\n📜 Full Page (upar se neeche tak)")]),
          ("3️⃣ स्क्रीनशॉट तैयार", [("bot", "✅ Screenshot ready! 📸")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! साइट स्क्रीनशॉट। स्टेप एक, मेनू से साइट स्क्रीनशॉट खोलो और वेबसाइट का यूआरएल भेजो। स्टेप दो, एचडी स्क्रीनशॉट या फुल पेज चुनो। फुल पेज में पूरी वेबसाइट ऊपर से नीचे तक आती है। धन्यवाद दोस्तों!",
      outro="HD ya poora lamba page — dono मिलेंगे"),
    T("rto", "RTO VEHICLE INFO", "गाड़ी की जानकारी", "🚗", "char_point",
      steps=[
          ("1️⃣ नंबर प्लेट भेजो", [("me", "🚗 RTO VEHICLE INFO"), ("bot", "Number plate bhejo (BR01AB1234)")]),
          ("2️⃣ जानकारी तैयार", [("me", "BR01AB1234"), ("bot", "✅ Bihar • Patna RTO\n+ VAHAN, e-Challan, Insurance links")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! आरटीओ व्हीकल इन्फो। स्टेप एक, मेनू से ये टूल खोलो। स्टेप दो, गाड़ी का नंबर प्लेट भेजो, जैसे बीआर शून्य एक ए बी एक दो तीन चार। बॉट बताएगा राज्य, आरटीओ ऑफिस और ज़िला, साथ में वाहन और ई चालान के ऑफिशियल लिंक। धन्यवाद दोस्तों!",
      outro="VAHAN • e-Challan • Insurance — sab links"),
    T("numinfo", "NUMBER INFO", "नंबर की जानकारी", "📱", "char_phone",
      steps=[
          ("1️⃣ 10 अंकों का नंबर", [("me", "📱 NUMBER INFO"), ("bot", "10 digit mobile number bhejo")]),
          ("2️⃣ जानकारी + लिंक", [("me", "9973700984"), ("bot", "✅ Airtel • Bihar\n+ WhatsApp, Truecaller, Cyber helpline")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! नंबर इन्फो टूल। स्टेप एक, मेनू से नंबर इन्फो खोलो। स्टेप दो, दस अंकों का मोबाइल नंबर भेजो। बॉट बताएगा ऑपरेटर, सर्कल और नंबर का टाइप, साथ में व्हाट्सएप और ट्रूकॉलर जैसे छह लिंक। धन्यवाद दोस्तों!",
      outro="Operator • Circle • 6 kaam ke links"),
    T("ifsc", "IFSC INFO", "IFSC बैंक जानकारी", "🏦", "char_point",
      steps=[
          ("1️⃣ IFSC कोड भेजो", [("me", "🏦 IFSC INFO"), ("bot", "Passbook / cheque par IFSC likha hota hai")]),
          ("2️⃣ पूरी डिटेल", [("me", "SBIN0000001"), ("bot", "✅ State Bank of India\nBranch • Address • MICR")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! आईएफएससी इन्फो। पैसा भेजने से पहले ब्रांच चेक करना ज़रूरी है। स्टेप एक, मेनू से आईएफएससी इन्फो खोलो। स्टेप दो, पासबुक या चेक पर लिखा आईएफएससी कोड भेजो। बैंक, ब्रांच, एड्रेस और एमआईसीआर कोड मिल जाएगा। धन्यवाद दोस्तों!",
      outro="Bank • Branch • MICR — paisa bhejne se pehle check"),
    T("pin", "PINCODE INFO", "पिनकोड जानकारी", "📮", "char_phone",
      steps=[
          ("1️⃣ पिनकोड या इलाका", [("me", "📮 PINCODE INFO"), ("bot", "6-digit pincode bhejo, ya area ka naam")]),
          ("2️⃣ पोस्ट ऑफिस लिस्ट", [("me", "800001"), ("bot", "✅ Patna GPO • Bihar\n+ saare post offices")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! पिनकोड इन्फो। स्टेप एक, मेनू से पिनकोड इन्फो खोलो। स्टेप दो, छह अंकों का पिनकोड भेजो, या इलाके का नाम लिखो। बॉट बताएगा ज़िला, राज्य और उस पिनकोड के सारे पोस्ट ऑफिस। धन्यवाद दोस्तों!",
      outro="Pincode se area • Area se pincode"),
    T("idfind", "ID FINDER", "आईडी और यूज़रनेम", "🆔", "char_phone",
      steps=[
          ("1️⃣ तीन तरीके", [("me", "🆔 ID & USERNAME FINDER"), ("bot", "1️⃣ me  → apni ID\n2️⃣ Message forward → uski ID\n3️⃣ @username → asli check")]),
          ("2️⃣ चेक हो गया", [("me", "@telegram"), ("bot", "✅ Telegram • GitHub • YouTube\n❌ Instagram • Snapchat")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! आईडी फाइंडर। तीन तरीके हैं। एक, मी लिखकर भेजो, अपनी टेलीग्राम आईडी मिलेगी। दो, किसी का मैसेज बॉट को फॉरवर्ड करो, उसकी आईडी मिलेगी। तीन, एट यूज़रनेम भेजो, बॉट बताएगा वो अकाउंट असली है या नहीं। धन्यवाद दोस्तों!",
      outro="me • forward • @username — teen tareeke"),
    T("ip", "IP / DOMAIN INFO", "आईपी और वेबसाइट", "🌐", "char_point",
      steps=[
          ("1️⃣ IP या वेबसाइट", [("me", "🌐 IP / DOMAIN INFO"), ("bot", "IP bhejo (8.8.8.8) ya website ka naam")]),
          ("2️⃣ लोकेशन + ISP", [("me", "google.com"), ("bot", "✅ Location • ISP\nVPN/Proxy check bhi")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! आईपी और डोमेन इन्फो। स्टेप एक, मेनू से ये टूल खोलो। स्टेप दो, आईपी भेजो जैसे आठ आठ आठ आठ, या वेबसाइट का नाम लिखो। बॉट बताएगा वो कहाँ है, कौन सी कंपनी है, और वीपीएन या प्रॉक्सी है या नहीं। धन्यवाद दोस्तों!",
      outro="Kahan hai • Kaunsi company • VPN ya nahi"),
    T("qr", "QR CODE", "क्यूआर कोड", "📷", "char_thumb",
      steps=[
          ("1️⃣ क्या चाहिए?", [("me", "📷 QR CODE"), ("bot", "🔗 Text/Link • 💰 UPI QR\n📶 WiFi • 👤 Contact card")]),
          ("2️⃣ QR तैयार", [("me", "https://youtube.com/@utilityduniya"), ("bot", "✅ HD QR ready!\nScan karke check karo")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! क्यूआर कोड जनरेटर। लिंक, यूपीआई, वाईफाई या कॉन्टैक्ट कार्ड का क्यूआर बनाओ। स्टेप एक, मेनू से क्यूआर कोड खोलो। स्टेप दो, जो बनाना है वो चुनो और उसका टेक्स्ट या लिंक भेजो। एचडी क्यूआर तैयार! धन्यवाद दोस्तों!",
      outro="Link • UPI • WiFi • Contact card"),
    T("upi", "UPI QR GENERATOR", "पेमेंट QR", "💰", "char_phone",
      steps=[
          ("1️⃣ अपनी UPI ID भेजो", [("me", "💰 UPI QR GENERATOR"), ("bot", "Apni UPI ID bhejo (9876543210@ybl)")]),
          ("2️⃣ रकम + QR", [("me", "9876543210@ybl"), ("bot", "✅ QR ready!\nCustomer scan karega, paisa seedha account me")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! यूपीआई क्यूआर जनरेटर। दुकान, ऑटो या ट्यूशन फीस के लिए अपना पेमेंट क्यूआर बनाओ। स्टेप एक, मेनू से ये टूल खोलो। स्टेप दो, अपनी यूपीआई आईडी भेजो। बॉट क्यूआर बना देगा, कस्टमर स्कैन करेगा और पैसा सीधे आपके अकाउंट में आएगा। धन्यवाद दोस्तों!",
      outro="Dukaan • Auto • Tuition fees ke liye"),
    T("pwd", "PASSWORD GENERATOR", "पासवर्ड बनाओ", "🔐", "char_thumb",
      steps=[
          ("1️⃣ मेनू से चुनो", [("me", "🔐 PASSWORD GENERATOR"), ("bot", "4 tareeke:\nNaam wala • Easy words • Random • PIN")]),
          ("2️⃣ पासवर्ड तैयार", [("me", "Himanshu"), ("bot", "🔐 Him@nshu#2026!\n💪 Strong + yaad rakhne me aasan")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! पासवर्ड जनरेटर। मज़बूत पासवर्ड बनाने के चार तरीके हैं — नाम वाला, ईज़ी वर्ड्स, रैंडम और पिन। स्टेप एक, मेनू से पासवर्ड जनरेटर खोलो और तरीका चुनो। स्टेप दो, नाम वाले में अपना नाम भेजो, बॉट मज़बूत पासवर्ड बना देगा। धन्यवाद दोस्तों!",
      outro="Naam wala • Easy words • Random • PIN"),
    T("short", "URL SHORT", "लिंक छोटा करो", "🔗", "char_point",
      steps=[
          ("1️⃣ लंबा लिंक भेजो", [("me", "🔗 URL SHORT"), ("bot", "Lamba link bhejo")]),
          ("2️⃣ छोटा लिंक तैयार", [("me", "https://example.com/very/long/path?x=1"), ("bot", "✅ Short link ready!\nWhatsApp/Telegram par share karo")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! यूआरएल शॉर्टनर। लंबे लिंक को छोटा करने के लिए। स्टेप एक, मेनू से यूआरएल शॉर्ट खोलो। स्टेप दो, अपना लंबा लिंक बॉट को भेजो। छोटा लिंक तैयार, कॉपी करो और व्हाट्सएप या टेलीग्राम पर शेयर कर दो। धन्यवाद दोस्तों!",
      outro="Lamba link → chhota link, ek second me"),
    T("linkbypass", "LINK BYPASS", "असली लिंक निकालो", "🔓", "char_point",
      steps=[
          ("1️⃣ ऐड वाला लिंक भेजो", [("me", "🔓 LINK BYPASS"), ("bot", "GPLinks / VPLinks / redirect link bhejo")]),
          ("2️⃣ असली लिंक", [("me", "https://gplinks.co/xyz123"), ("bot", "✅ Asli destination:\nhttps://realfile.com/file.zip")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! लिंक बायपास। ऐड वाले शॉर्ट लिंक के पीछे छिपा असली लिंक निकालने के लिए। स्टेप एक, मेनू से लिंक बायपास खोलो। स्टेप दो, ऐड वाला लिंक बॉट को भेजो। बॉट रीडायरेक्ट खोलकर असली डेस्टिनेशन निकाल देगा, बिना ऐड देखे। धन्यवाद दोस्तों!",
      outro="Ad-wale link ka asli destination"),
    T("linkcheck", "LINK CHECK", "लिंक सेफ्टी चेक", "🔍", "char_phone",
      steps=[
          ("1️⃣ लिंक भेजो", [("me", "🔍 LINK CHECK"), ("bot", "Link bhejo — kholne se pehle check karo")]),
          ("2️⃣ फैसला", [("me", "http://sbi-kyc-verify.xyz"), ("bot", "🔴 DANGEROUS!\nBank phishing link — mat kholo")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! लिंक चेक टूल। बैंक के नाम पर आने वाले फ़र्ज़ी लिंक पकड़ने के लिए, लिंक खोलने से पहले जाँचो। स्टेप एक, मेनू से लिंक चेक खोलो। स्टेप दो, शक वाला लिंक बॉट को भेजो। बॉट बताएगा लिंक सेफ है, शक वाला है या खतरनाक। धन्यवाद दोस्तों!",
      outro="Kholne se pehle check — scam se bacho"),
    T("emi", "EMI CALCULATOR", "ईएमआई कैलकुलेटर", "🧮", "char_phone",
      steps=[
          ("1️⃣ डिटेल भेजो", [("me", "🧮 EMI CALC"), ("bot", "Aise likho:\n500000 9% 24m\n(ya: 3 lakh 8.5% 5 saal)")]),
          ("2️⃣ EMI + कितने दिन", [("me", "5,00,000 9% 24m"), ("bot", "✅ EMI ₹22,845 / mahina\nLoan poori: 731 din me")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! ईएमआई कैलकुलेटर। लोन की ईएमआई और लोन कितने दिन में पूरा होगा, वो पता करने के लिए। स्टेप एक, मेनू से ईएमआई कैलक खोलो। स्टेप दो, रकम, ब्याज दर और समय लिखकर भेजो, जैसे पाँच लाख नौ परसेंट चौबीस महीने। हिंदी में भी चलेगा। धन्यवाद दोस्तों!",
      outro="EMI + kul byaaj + kitne din me poora"),
    T("interest", "INTEREST CALCULATOR", "ब्याज कैलकुलेटर", "📈", "char_point",
      steps=[
          ("1️⃣ रकम, दर, समय", [("me", "📈 INTEREST CALC"), ("bot", "Step 1/3: Kitni rakam?\n(jaise: 50000)")]),
          ("2️⃣ चक्रवृद्धि हिसाब", [("me", "50000 → 5 → 12 mahine"), ("bot", "✅ Chakravriddhi byaaj:\n₹8,289 • poori rakam ₹58,289")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! ब्याज कैलकुलेटर। गाँव के हिसाब से चक्रवृद्धि ब्याज निकालने के लिए। स्टेप एक, मेनू से इंटरेस्ट कैलक खोलो और रकम भेजो। स्टेप दो, ब्याज दर बताओ, जैसे सौ रुपये पर पाँच रुपये। स्टेप तीन, कितने महीने का हिसाब चाहिए वो भेजो। पूरा हिसाब तैयार! धन्यवाद दोस्तों!",
      outro="Chakravriddhi (जोड़कर) byaaj ka poora hisaab"),
    T("age", "AGE CALCULATOR", "उम्र कैलकुलेटर", "🎂", "char_thumb",
      steps=[
          ("1️⃣ जन्म तिथि भेजो", [("me", "🎂 AGE CALCULATOR"), ("bot", "Date bhejo (DD-MM-YYYY)")]),
          ("2️⃣ उम्र + राशि", [("me", "15-08-2005"), ("bot", "✅ 21 saal 1 mahine 17 din\nAgla birthday: 317 din baad")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! एज कैलकुलेटर। सरकारी फॉर्म में उम्र साल, महीने और दिन में लिखनी होती है, ये टूल वो बताता है। स्टेप एक, मेनू से एज कैलकुलेटर खोलो। स्टेप दो, अपनी जन्म तिथि भेजो। पूरी उम्र, अगला जन्मदिन और राशि मिल जाएगी। धन्यवाद दोस्तों!",
      outro="Exact umar • agla birthday • राशि"),
    T("search", "WEB SEARCH", "वेब सर्च", "🔎", "char_phone",
      steps=[
          ("1️⃣ कुछ भी पूछो", [("me", "🔎 WEB SEARCH"), ("bot", "Kya dhoondhna hai?")]),
          ("2️⃣ असली रिजल्ट", [("me", "Bihar board 12th result date"), ("bot", "✅ Top results\n(title + link + description)")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! वेब सर्च टूल। गूगल जैसा सर्च, बॉट के अंदर ही। स्टेप एक, मेनू से वेब सर्च खोलो। स्टेप दो, जो दूँढना है वो लिखकर भेजो। बॉट डकडकगो और बिंग दोनों से रिजल्ट दिखाएगा, टाइटल और लिंक के साथ। धन्यवाद दोस्तों!",
      outro="DuckDuckGo + Bing — ek saath results"),
    T("appfind", "APP FINDER", "ऐप डाउनलोड", "📦", "char_point",
      steps=[
          ("1️⃣ ऐप का नाम", [("me", "📦 APP FINDER"), ("bot", "App ka naam bhejo")]),
          ("2️⃣ 8 भरोसेमंद स्टोर", [("me", "instagram"), ("bot", "✅ Play Store • APKPure • APKCombo\nHappyMod • Uptodown • F-Droid")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! ऐप फाइंडर। किसी भी ऐप को डाउनलोड करने के लिए भरोसेमंद स्टोर के सीधे लिंक। स्टेप एक, मेनू से ऐप फाइंडर खोलो। स्टेप दो, ऐप का नाम भेजो। आठ अच्छे स्टोर के लिंक मिलेंगे। रैंडम साइट से ए पी के मत डाउनलोड करो, वायरस का खतरा होता है। धन्यवाद दोस्तों!",
      outro="Random site se APK nahi — safe stores se lo"),
    T("sarkari", "SARKARI PORTALS", "सरकारी पोर्टल", "🏛️", "char_point",
      steps=[
          ("1️⃣ टूल खोलो", [("me", "🏛️ SARKARI SEVA PORTALS"), ("bot", "Aadhaar, PAN, Ration, Ayushman...\nState wise bhi")]),
          ("2️⃣ सीधा लिंक", [("me", "Ayushman card"), ("bot", "✅ Official portal link\n(Direct — bina google)")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! सरकारी सेवा पोर्टल्स। आधार, पैन, राशन और आयुष्मान कार्ड जैसी सेवाओं के असली और सीधे लिंक। स्टेप एक, मेनू से ये टूल खोलो। स्टेप दो, जो सेवा चाहिए वो चुनो या नाम लिखो। राज्य वाइज़ पोर्टल भी मिलते हैं। धन्यवाद दोस्तों!",
      outro="Aadhaar • PAN • Ration • Ayushman"),

    T("exam", "STUDENT EXAM HUB", "एग्ज़ाम हब", "🎓", "char_thumb",
      steps=[
          ("1️⃣ टूल खोलो", [("me", "🎓 STUDENT EXAM HUB"), ("bot", "Result, Admit card, Syllabus,\nSarkari naukri — sab ek jagah")]),
          ("2️⃣ सीधा पोर्टल", [("me", "SSC result"), ("bot", "✅ Official links ready!")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! स्टूडेंट एग्ज़ाम हब। रिजल्ट, एडमिट कार्ड, सिलेबस और सरकारी नौकरी की जानकारी, सब एक जगह। स्टेप एक, मेनू से एग्ज़ाम हब खोलो। स्टेप दो, जो चाहिए वो सर्च करो या बटन दबाओ। ऑफिशियल लिंक तुरंत मिल जाएगा। धन्यवाद दोस्तों!",
      outro="Result • Admit card • Syllabus • Naukri"),
    T("premium", "VIP PREMIUM", "वीआईपी प्रीमियम", "💎", "char_phone",
      steps=[
          ("1️⃣ /premium भेजो", [("me", "/premium"), ("bot", "💎 Plan chuno:\n30 din ₹49 • 60 din ₹89\n90 din ₹129 • Lifetime ₹199")]),
          ("2️⃣ QR से पे करो", [("bot", "📲 QR scan karke pay karo\n(PhonePe / GPay / Paytm)")]),
          ("3️⃣ UTR + स्क्रीनशॉट", [("me", "448612394857\n📸 [payment screenshot]"), ("bot", "✅ Proof mil gaya!\nAdmin verify karke VIP on kar dega")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! वीआईपी प्रीमियम कैसे लेते हैं, सिखाता हूँ। वीआईपी में सब अनलिमिटेड। स्टेप एक, स्लैश प्रीमियम भेजो और प्लान चुनो। स्टेप दो, क्यूआर स्कैन करके फोनपे, जीपे या पेटीएम से पेमेंट करो। स्टेप तीन, पेमेंट का यूटीआर नंबर और हिस्ट्री का स्क्रीनशॉट भेजो। एडमिन वेरिफाई करके वीआईपी चालू कर देगा। धन्यवाद दोस्तों!",
      outro="Unlimited tools • Admin verify • Instant VIP"),
    T("refer", "REFER & EARN", "रेफर और कमाओ", "🎁", "char_thumb",
      steps=[
          ("1️⃣ अपना लिंक लो", [("me", "🎁 REFER & EARN"), ("bot", "🔗 Aapka link:\nt.me/bot?start=ref_8607774564")]),
          ("2️⃣ दोस्त जुड़े = VIP", [("bot", "✅ 5 dost jode → 30 din VIP FREE!")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! रेफर एंड अर्न। दोस्तों को बॉट शेयर करो और फ्री वीआईपी पाओ। स्टेप एक, मेनू से रेफर एंड अर्न खोलो, अपना पर्सनल लिंक मिल जाएगा। स्टेप दो, वो लिंक दोस्तों को भेजो। जितने दोस्त जुड़ेंगे, उतने दिन की फ्री वीआईपी मिलेगी। धन्यवाद दोस्तों!",
      outro="Dost jodo • Free VIP pao"),
    T("account", "MY ACCOUNT", "मेरा अकाउंट", "👤", "char_point",
      steps=[
          ("1️⃣ टूल खोलो", [("me", "👤 MY ACCOUNT"), ("bot", "Naam, ID, VIP status,\nuses today, referrals")]),
          ("2️⃣ VIP स्टेटस चेक", [("bot", "👑 VIP: ACTIVE\n📅 Valid till: 01-11-2026")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! माय अकाउंट। अपनी पूरी डिटेल देखने के लिए, नाम, टेलीग्राम आईडी, वीआईपी स्टेटस और आज के यूज़। स्टेप एक, मेनू से माय अकाउंट खोलो। वीआईपी एक्टिव है तो वैलिड डेट भी दिखेगी, और रेफरल काउंट भी। धन्यवाद दोस्तों!",
      outro="VIP status • uses today • referrals"),
    T("vnum", "VIRTUAL NUMBERS", "वर्चुअल नंबर", "🌐", "char_phone",
      steps=[
          ("1️⃣ टूल खोलो", [("me", "🌐 VIRTUAL NUMBERS"), ("bot", "OTP ke liye virtual numbers\nWhatsApp • Telegram")]),
          ("2️⃣ नंबर + OTP", [("me", "Telegram"), ("bot", "✅ Number ready!\nOTP aane par yahin dikh jayega")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! वर्चुअल नंबर टूल। बिना सिम, ओटीपी के लिए वर्चुअल नंबर। स्टेप एक, मेनू से वर्चुअल नंबर खोलो। स्टेप दो, किस प्लेटफॉर्म के लिए चाहिए वो चुनो। बटन दबाकर नंबर कॉपी करो और जहाँ चाहिए वहाँ लगाओ, ओटीपी बॉट में आ जाएगा। धन्यवाद दोस्तों!",
      outro="Bina SIM — OTP ke liye numbers"),
    T("tutorial", "HOW TO USE BOT", "बॉट कैसे चलाएँ", "❓", "char_wave",
      steps=[
          ("1️⃣ टूल चुनो", [("me", "📥 VIDEO DOWNLOADER"), ("bot", "Neeche keyboard se koi bhi tool chuno")]),
          ("2️⃣ टूल माँगे वो भेजो", [("bot", "Link / number / photo bhejo → kaam ho jayega")]),
          ("3️⃣ हर टूल का ट्यूटोरियल", [("bot", "🎬 Tutorial button dabao —\nus tool ka video dekh lo")]),
      ],
      narration="नमस्ते दोस्तों, मैं हिमांशु! बॉट चलाना बहुत आसान है। एक, नीचे कीबोर्ड से कोई भी टूल चुनो। दो, टूल जो माँगे वो भेज दो, लिंक, नंबर या फोटो। तीन, किसी टूल को चलाना न आए तो उसके नीचे ट्यूटोरियल बटन दबाओ, उस टूल का छोटा वीडियो मिल जाएगा। धन्यवाद दोस्तों!",
      outro="Har tool ke neeche uska tutorial video hai"),
]

TOOL_MAP = {t["key"]: t for t in TOOLS}


# ======================================================================
#  BACKGROUND (pre-rendered, animated)
# ======================================================================
_bg_layers = {}


def build_bg():
    if "base" in _bg_layers:
        return _bg_layers
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = (yy / H)
    base = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        base[:, :, i] = BG_TOP[i] * (1 - v) + BG_BOT[i] * v
    # purple radial glow (do jagah)
    for (cx, cy, rad, inten) in [(0.85 * W, 0.22 * H, 0.75 * W, 0.55), (0.10 * W, 0.80 * H, 0.60 * W, 0.30)]:
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / rad
        g = np.clip(1 - d, 0, 1) ** 2 * inten
        for i in range(3):
            base[:, :, i] += g * (PURPLE[i] if i else PURPLE[i] * 0.85)
    # faint grid
    step = 90
    grid = ((xx % step < 2) | (yy % step < 2)).astype(np.float32) * 6
    base += grid[:, :, None]
    # floating particles
    rnd = random.Random(7)
    parts = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(2, 6), rnd.uniform(10, 26), rnd.uniform(0, 6.28))
             for _ in range(70)]
    _bg_layers["base"] = np.clip(base, 0, 255).astype(np.uint8)
    _bg_layers["parts"] = parts
    return _bg_layers


def bg_frame(t):
    L = build_bg()
    img = Image.fromarray(L["base"].copy())
    dr = ImageDraw.Draw(img, "RGBA")
    for (x0, y0, r, spd, ph) in L["parts"]:
        y = (y0 - t * spd) % (H + 80) - 40
        a = 40 + 40 * math.sin(t * 1.4 + ph)
        dr.ellipse([x0 - r, y - r, x0 + r, y + r], fill=(190, 160, 255, int(max(12, a))))
    return img


# ======================================================================
#  UI HELPERS
# ======================================================================
def rrect(dr, box, r, fill, outline=None, wid=2):
    dr.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=wid)


def text_w(d, s, f):
    return d.textbbox((0, 0), s, font=f)[2]


def center_text(d, y, s, f, fill, x=W // 2, shadow=None):
    w = measure(d, s, f)
    x0 = x - w // 2
    if shadow:
        draw_mixed(d, (x0 + 3, y + 3), s, f, shadow)
    draw_mixed(d, (x0, y), s, f, fill)
    return w


def wrap(d, s, f, maxw):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if measure(d, trial, f) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def glow_text(base, xy, txt, f, color, glow=(120, 70, 255), strength=9):
    w = text_w(ImageDraw.Draw(base), txt, f)
    layer = Image.new("RGBA", (base.width, base.height), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, txt, font=f, fill=glow + (255,))
    layer = layer.filter(ImageFilter.GaussianBlur(14))
    for _ in range(strength):
        base.alpha_composite(layer)
    ImageDraw.Draw(base).text(xy, txt, font=f, fill=color + (255,))
    return w


def paste_logo(img, cx, cy, size=170, ring=True):
    logo = Image.open(os.path.join(ASSETS, "avatar_head.png")).convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 3, size * 3), 0)
    ImageDraw.Draw(mask).ellipse([size * 1.5] * 2 + [size * 3, size * 3], fill=255)
    # circular mask with soft edge
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size, size], fill=255)
    img.paste(logo, (cx - size // 2, cy - size // 2), m)
    if ring:
        ImageDraw.Draw(img).ellipse([cx - size // 2 - 6, cy - size // 2 - 6, cx + size // 2 + 6, cy + size // 2 + 6],
                                    outline=PURPLE + (210,), width=5)


def paste_char(img, pose, cx, cy, height, t=0.0, glow=True):
    path = os.path.join(ASSETS, f"{pose}.png")
    if not os.path.exists(path):
        path = os.path.join(ASSETS, "char_base.png")
    ch = Image.open(path).convert("RGBA")
    ratio = height / ch.height
    ch = ch.resize((int(ch.width * ratio), height), Image.LANCZOS)
    bob = int(math.sin(t * 1.1) * 14)
    x, y = cx - ch.width // 2, cy - ch.height // 2 + bob
    if glow:
        gl = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gl.paste(ch, (x, y), ch)
        gl = gl.filter(ImageFilter.GaussianBlur(38))
        img.alpha_composite(Image.blend(Image.new("RGBA", img.size, (0, 0, 0, 0)), gl, 0.85))
    img.alpha_composite(ch, (x, y))


def bubble(dr_img, side, text_lines, top, font_body, maxw=760, pad=26, x_offset=0, y_offset=0):
    """Telegram jaisa chat bubble. side: 'me' (right, purple) ya 'bot' (left, dark)."""
    d = ImageDraw.Draw(dr_img)
    lh = font_body.size + 12
    h = pad * 2 + lh * len(text_lines)
    w = max([text_w(d, t, font_body) for t in text_lines] + [120]) + pad * 2
    w = min(w, maxw)
    if side == "me":
        x1 = (dr_img.width - 40) + x_offset
        x0 = x1 - w
        fill = BUBBLE_ME + (255,)
    else:
        x0 = 24 + x_offset
        x1 = x0 + w
        fill = BUBBLE_BOT + (255,)
    rrect(d, [x0, top, x1, top + h], 26, fill)
    for i, ln in enumerate(text_lines):
        draw_mixed(d, (x0 + pad, top + pad + i * lh), ln, font_body, WHITE)
    return top + h


# ======================================================================
#  SCENE RENDER
# ======================================================================
def load_json_fonts():
    return {
        "title": font(F_TITLE, 84),
        "title_sm": font(F_TITLE, 62),
        "hi": font(F_HINDI, 54),
        "hi_sm": font(F_HINDI, 42),
        "body": font(F_BODY, 40),
        "body_sm": font(F_BODY, 34),
        "bubble": font(F_HINDI, 34),
        "bubble_en": font(F_BODY, 32),
        "chip": font(F_BODY, 30),
        "small": font(F_BODY, 26),
        "num": font(F_NUM, 46),
        "sub": font(F_HINDI, 44),
    }


def make_plate(scene, tool, f, t=0.0):
    """Static part (bg + header + title + chip + card + character + footer) — ek baar banake cache."""
    img = bg_frame(t).convert("RGBA")
    dr = ImageDraw.Draw(img)

    # header
    paste_logo(img, 84, 84, 110)
    dr.text((162, 52), "UTILITY DUNIYA", font=f["chip"], fill=WHITE)
    dr.text((162, 90), "TUTORIAL • HIMANSHU", font=f["small"], fill=PURPLE)
    dr.line([(56, 156), (W - 56, 156)], fill=(255, 255, 255, 34), width=3)

    # title
    ty = 172
    tsize = f["title"] if measure(dr, tool["title"], f["title"]) < W - 100 else f["title_sm"]
    glow_text(img, ((W - measure(dr, tool["title"], tsize)) // 2, ty), tool["title"], tsize, WHITE)
    hy = ty + 108
    center_text(dr, hy, f'{tool["emoji"]}  {tool["hi"]}  {tool["emoji"]}', f["hi_sm"], GOLD)

    # step chip
    if isinstance(scene, int):
        chip = f'STEP {scene + 1} / {len(tool["steps"])}'
        cw = measure(dr, chip, f["chip"]) + 60
        cy0 = 372
        rrect(dr, [W // 2 - cw // 2, cy0, W // 2 + cw // 2, cy0 + 62], 31, PURPLE + (255,))
        center_text(dr, cy0 + 12, chip, f["chip"], (12, 6, 24))

    # character
    pose = "char_thumb" if scene == "outro" else tool["pose"]
    paste_char(img, pose, int(W * 0.80), 1520, 1030, 0.0)

    # chat card frame
    cx0, cx1 = 50, int(W * 0.72)
    cy0 = 470
    card_h = 730
    rrect(dr, [cx0, cy0, cx1, cy0 + card_h], 34, CARD + (240,), outline=(96, 74, 168, 170), wid=3)
    dr.ellipse([cx0 + 24, cy0 + 20, cx0 + 78, cy0 + 74], fill=PURPLE_D + (255,))
    dr.text((cx0 + 40, cy0 + 30), "TV", font=f["small"], fill=WHITE)
    dr.text((cx0 + 92, cy0 + 24), "ToolVault", font=f["chip"], fill=WHITE)
    dr.text((cx0 + 92, cy0 + 58), "bot", font=f["small"], fill=GRAY)
    dr.line([(cx0, cy0 + 100), (cx1, cy0 + 100)], fill=(255, 255, 255, 28), width=3)
    _plate_meta["card"] = (cx0, cx1, cy0)

    # intro overlay (pehle 2.4 sec)
    if scene == "intro":
        big = font(F_EMOJI, 150)
        d2 = ImageDraw.Draw(img)
        d2.text((W // 2 - 95, 640), tool["emoji"] + " ", font=big, embedded_color=True, fill=WHITE)
        center_text(d2, 880, "30 SECOND ME SEEKHO", font(F_BODY, 52), WHITE)
        center_text(d2, 960, f'{tool["hi"]} — पूरा तरीका', font(F_HINDI, 46), GOLD)

    # footer
    pw = W - 160
    rrect(dr, [80, H - 150, 80 + pw, H - 132], 9, (255, 255, 255, 40))
    dr.text((80, H - 118), "UTILITY DUNIYA • HIMANSHU", font=f["small"], fill=GRAY)
    tw = measure(dr, "@Supermannn_x", f["small"])
    dr.text((W - 80 - tw, H - 118), "@Supermannn_x", font=f["small"], fill=GRAY)

    # outro overlay
    if scene == "outro":
        img.alpha_composite(Image.new("RGBA", img.size, (8, 4, 16, 208)))
        dr = ImageDraw.Draw(img)
        paste_logo(img, W // 2, 430, 230)
        glow_text(img, ((W - measure(dr, "HIMANSHU", f["title"])) // 2, 590), "HIMANSHU", f["title"], WHITE)
        center_text(dr, 726, "UTILITY DUNIYA • SUPER BOT", f["chip"], PURPLE)
        dr.line([(150, 800), (W - 150, 800)], fill=(255, 255, 255, 60), width=2)
        y = 860
        for ln in wrap(dr, tool["outro"], f["hi_sm"], W - 240):
            center_text(dr, y, ln, f["hi_sm"], WHITE)
            y += 62
        cta = "BOT START KARO"
        cw = measure(dr, cta, f["body"]) + 110
        rrect(dr, [W // 2 - cw // 2, y + 60, W // 2 + cw // 2, y + 170], 55, PURPLE + (255,))
        center_text(dr, y + 86, cta, f["body"], (10, 5, 20))
        paste_char(img, "char_thumb", int(W * 0.80), 1620, 740, 0.0, glow=False)
    return img


_plate_meta = {}
_plate_cache = {}


def get_plates(tool, f):
    """Har scene ka static plate (ek baar banao, phir cache)."""
    key = tool["key"]
    if key in _plate_cache:
        return _plate_cache[key]
    plates = {"intro": make_plate("intro", tool, f, 0.0), "outro": make_plate("outro", tool, f, 0.0)}
    for i in range(len(tool["steps"])):
        plates[i] = make_plate(i, tool, f, 0.0)
    _plate_cache[key] = plates
    return plates


def render_frame(t, dur, tool, f, phase, sub_line="", plates=None):
    """Har frame: cached plate + animated bubbles + subtitle + progress."""
    plates = plates or get_plates(tool, f)
    key = phase["step_idx"] if phase["step_idx"] is not None else phase["scene"]
    img = plates[key].copy()
    dr = ImageDraw.Draw(img)
    cx0, cx1, cy0 = _plate_meta.get("card", (50, int(W * 0.72), 560))

    # ---- animated chat bubbles ----
    if phase["step_idx"] is not None:
        msgs = tool["steps"][phase["step_idx"]][1]
        n = max(1, len(msgs))
        inner_top = cy0 + 130
        for i, (side, txt) in enumerate(msgs):
            appear_at = (i + 0.3) / n
            fnt = f["bubble"] if any("\u0900" <= c <= "\u097f" for c in txt) else f["bubble_en"]
            lines = wrap(ImageDraw.Draw(img), txt, fnt, 560)
            box_h = 40 + (fnt.size + 12) * len(lines)
            if phase["step_t"] >= appear_at:
                prog = min(1.0, (phase["step_t"] - appear_at) * 6)
                bx = int((1 - prog) * (46 if side == "bot" else -46))
                tmp = Image.new("RGBA", (cx1 - cx0, box_h + 20), (0, 0, 0, 0))
                bubble(tmp, side, lines, 0, fnt, maxw=600, x_offset=bx, y_offset=0)
                if prog < 1:
                    tmp.putalpha(tmp.getchannel("A").point(lambda p: int(p * min(1.0, prog))))
                img.alpha_composite(tmp, (cx0, inner_top))
            inner_top += box_h + 14

    # ---- subtitle ----
    if sub_line and phase["scene"] != "outro":
        slines = wrap(dr, sub_line, f["sub"], W - 150)
        y = 1246
        for ln in slines[:3]:
            w = measure(dr, ln, f["sub"])
            rrect(dr, [W // 2 - w // 2 - 26, y - 8, W // 2 + w // 2 + 26, y + 60], 18, (8, 4, 16, 195))
            center_text(dr, y, ln, f["sub"], WHITE)
            y += 68

    # ---- progress bar fill ----
    p = max(0.0, min(1.0, t / dur))
    pw = W - 160
    rrect(dr, [80, H - 150, 80 + int(pw * p), H - 132], 9, PURPLE + (255,))
    return img.convert("RGB")


# ======================================================================
#  VOICE
# ======================================================================
VOICES = [v.strip() for v in os.getenv("TUTORIAL_VOICES", "hi-IN-MadhurNeural,hi-IN-SwaraNeural,mr-IN-ManoharNeural").split(",")]


async def make_voice(text, out_mp3):
    """Hindi male voice (Madhur) → fail ho to fallback voices, 3 koshish tak."""
    import edge_tts
    last = None
    for attempt in range(3):
        for v in VOICES:
            try:
                try:
                    await edge_tts.Communicate(text, v, rate="+18%").save(out_mp3)
                except Exception:
                    await edge_tts.Communicate(text, v).save(out_mp3)
                if os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 4000:
                    return out_mp3
            except Exception as e:
                last = e
        await asyncio.sleep(2 + attempt * 2)
    raise RuntimeError(f"voice nahi bani: {last}")


def split_sentences(text):
    """Narration ko chhote hisson me todta hai (subtitle ke liye)."""
    import re as _r
    parts = _r.split(r"(?<=[।!?])\s+|(?<=\.)\s+", text.strip())
    out, cur = [], ""
    for p_ in parts:
        p_ = p_.strip()
        if not p_:
            continue
        if len(cur) + len(p_) <= 92:
            cur = (cur + " " + p_).strip()
        else:
            if cur:
                out.append(cur)
            cur = p_
    if cur:
        out.append(cur)
    return out or [text]


def make_music(dur, out_mp3):
    """Halka synth music bed (royalty-free, khud banaya) — voice ke neeche mix hoga."""
    sr = 22050
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    # chord progression: Am - F - C - G (loop har 8 sec)
    chords = [(110.0, 164.81, 220.0), (87.31, 130.81, 174.61), (130.81, 196.0, 261.63), (98.0, 146.83, 196.0)]
    sig = np.zeros(n, np.float32)
    for ci, ch in enumerate(chords):
        seg = (t // 8.0).astype(int) % len(chords) == ci
        for fq in ch:
            sig[seg] += 0.16 * np.sin(2 * np.pi * fq * t[seg])
    # pluck arpeggio
    for k in range(int(dur * 2)):
        st_ = k * (sr // 2)
        ln = sr // 5
        if st_ + ln >= n:
            break
        fq = chords[(k // 8) % len(chords)][k % 3] * 2
        env = np.exp(-np.linspace(0, 6, ln))
        sig[st_:st_ + ln] += 0.10 * np.sin(2 * np.pi * fq * t[:ln]) * env
    # halka kick (heartbeat)
    for k in range(int(dur)):
        st_ = k * sr
        ln = sr // 10
        if st_ + ln >= n:
            break
        env = np.exp(-np.linspace(0, 9, ln))
        sig[st_:st_ + ln] += 0.22 * np.sin(2 * np.pi * 55 * t[:ln]) * env
    sig = np.tanh(sig * 1.1) * 0.9
    pcm = (sig * 32767).astype("<i2").tobytes()
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1",
           "-i", "-", "-c:a", "libmp3lame", "-b:a", "96k", out_mp3]
    subprocess.run(cmd, input=pcm, check=True)
    return out_mp3


def media_duration(path):
    out = subprocess.run([FFMPEG, "-i", path], capture_output=True, text=True).stderr
    for line in out.splitlines():
        if "Duration:" in line:
            hm = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = hm.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 30.0


# ======================================================================
#  BUILD ONE VIDEO
# ======================================================================
def build(key, jobs_tag=""):
    tool = TOOL_MAP[key]
    t_start = time.time()
    mp3 = os.path.join(CACHE, f"{key}_hi.mp3")
    if not os.path.exists(mp3):
        asyncio.run(make_voice(tool["narration"], mp3))
    vdur = media_duration(mp3)
    intro_d, outro_d = 2.4, 3.2
    body = max(8.0, vdur + 1.0)          # narration ko poora time
    dur = intro_d + body + outro_d

    # steps timing (har step barabar, text length ke hisaab se thoda adjust)
    lens = [max(1.0, len(s[0]) + sum(len(m[1]) for m in s[1]) / 3) for s in tool["steps"]]
    tot = sum(lens)
    step_dur = [body * l / tot for l in lens]

    f = load_json_fonts()
    plates = get_plates(tool, f)
    out = os.path.join(OUT_DIR, f"{key}.mp4")
    tmp = os.path.join(OUT_DIR, f"__tmp_{key}.mp4")
    cmd = [FFMPEG, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", mp3, "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "128k", "-t", f"{dur:.2f}", tmp]
    # ---- subtitles (narration ke hisaab se timing) ----
    subs = split_sentences(tool["narration"])
    sub_total = sum(len(s_) for s_ in subs) or 1
    sub_bounds, acc2 = [], intro_d
    for s_ in subs:
        d_ = body * len(s_) / sub_total
        sub_bounds.append((acc2, acc2 + d_))
        acc2 += d_

    def sub_at(t_):
        for a_, b_, s_ in [(a_, b_, subs[i]) for i, (a_, b_) in enumerate(sub_bounds)]:
            if a_ <= t_ < b_:
                return s_
        return ""

    # ---- music bed ----
    music = os.path.join(CACHE, f"music_{int(dur)}.mp3")
    if not os.path.exists(music):
        make_music(max(10.0, dur), music)

    # voice + music mix (voice ke baad silence, phir music neeche)
    mix = os.path.join(CACHE, f"{key}_mix.m4a")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", mp3, "-stream_loop", "-1", "-i", music,
                    "-filter_complex",
                    "[0:a]apad[a0];[1:a]volume=0.13[bg];[a0][bg]amix=inputs=2:duration=longest:dropout_transition=0[a]",
                    "-map", "[a]", "-c:a", "aac", "-b:a", "128k", "-t", f"{dur:.2f}", mix], check=True)
    cmd[cmd.index(mp3)] = mix  # voice ki jagah voice+music mix
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total_frames = int(dur * FPS)
    acc = intro_d
    step_bounds = []
    for i, sd in enumerate(step_dur):
        step_bounds.append((acc, acc + sd))
        acc += sd
    for fi in range(total_frames):
        t = fi / FPS
        if t < intro_d:
            phase = {"scene": "intro", "step_idx": None, "step_t": 0}
        elif t < dur - outro_d:
            bt = t - intro_d
            idx = next((i for i, (a, b) in enumerate(step_bounds) if a <= bt < b), len(step_bounds) - 1)
            a, b = step_bounds[idx]
            phase = {"scene": "body", "step_idx": idx, "step_t": bt - a, "step_dur": b - a}
        else:
            phase = {"scene": "outro", "step_idx": None, "step_t": 0}
        try:
            frame = render_frame(t, dur, tool, f, phase, sub_line=sub_at(t), plates=plates)
            proc.stdin.write(frame.tobytes())
        except BrokenPipeError:
            break
    proc.stdin.close()
    proc.wait()
    os.replace(tmp, out)
    size = os.path.getsize(out) / 1e6
    print(f"✅ {key}.mp4  ({dur:.1f}s, {size:.1f} MB)  [{time.time()-t_start:.0f}s]", flush=True)
    return out, dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tool", nargs="?", help="tool key (jaise video_dl) ya --all")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if a.dry:
        print(f"{len(TOOLS)} tools ke tutorial videos banenge:")
        for t in TOOLS:
            print(f"  • {t['key']:14} {t['emoji']} {t['title']:22} {t['hi']}   (~{len(t['narration'])} chars)")
        return
    if a.all:
        keys = [t["key"] for t in TOOLS]
        done = [k for k in keys if os.path.exists(os.path.join(OUT_DIR, k + ".mp4"))]
        keys = [k for k in keys if k not in done]
        print(f"banane hain: {len(keys)} (pehle se ready: {len(done)})", flush=True)
        if a.jobs <= 1:
            for k in keys:
                build(k)
        else:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=a.jobs) as ex:
                list(ex.map(build, keys))
    else:
        build(a.tool)


if __name__ == "__main__":
    main()
