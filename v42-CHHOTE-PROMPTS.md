# ✂️ v42 — CHHOTE PROMPTS (har tool me kam instructions)

**Aapne bola:** koi bhi tool khole to **lambi instructions nahi** honi chahiye — jaise reference bot me hai —
bas **kya bhejna hai + ek example**. Detail samajhne ke liye har tool ke neeche 🎬 tutorial video already hai.

Isliye **saare 25 tools ke prompts** naye style me likh diye:

```
TITLE (emoji + naam)
1 line: kya milega / kya bhejna hai
📌 Example: <asli example>
👉 Now send ...:
```

Koi bullet list nahi, koi ━━━ separator nahi, koi "kaise use karein" paragraph nahi.

## Pehle vs ab (asli example)

**📱 NUMBER INFO — pehle (7 line):**
```
📱 NUMBER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━
Send a 10 digit mobile number.
✅ You get: operator, circle (region), number type + 6 useful links
(WhatsApp, Telegram, Truecaller, Google, spam report, 1930 cyber helpline).
<i>After MNP the operator can change. For legal use only.</i>
━━━━━━━━━━━━━━━━━━━━━━
🔢 Now send the 10 digit number (example 9876543210):
```

**📱 NUMBER INFO — ab (4 line):**
```
📱 NUMBER INFO
Operator, circle (region), number type + 6 useful links.
📌 Example: 9876543210
🔢 Now send the 10 digit mobile number:
```

**🚗 VEHICLE (pehle 10 line ki poori list) → ab:**
```
🚗 VEHICLE INFO + CHALLAN
Full RC record + all challans (pending/paid, amount, offence).
📌 Example: BR30AR0802
🔢 Now send the number plate:
```

**⚡ TERABOX (aapne khaas bola: ad-free likhna hai) → ab:**
```
⚡ TERABOX & CLOUD
✅ Ad-free download + stream (Terabox, Mediafire, Drive, Mega)
⚠️ Server rejects sometimes — just send the link again.
📌 Example: https://terabox.com/s/xxxxx
🔗 Now send your link:
```

## Har tool me ab example set hai (users turant samajh jaye)

| Tool | Example jo dikhta hai |
|---|---|
| 📱 NUMBER INFO | `9876543210` |
| 📲 IMEI / PHONE | `353010111111110` + `*#06#` ka tarika |
| 🚗 VEHICLE | `BR30AR0802` |
| 🏦 IFSC | `SBIN0000001` |
| 📮 PINCODE | `800001` / `Rajendra Nagar` |
| 🌐 IP/DOMAIN | `8.8.8.8` / `google.com` |
| 🔗 URL SHORT | `https://example.com/very/long/path?x=1` |
| 🔍 LINK CHECK | `http://sbi-kyc-verify.xyz` |
| 📦 APP FINDER | `instagram` |
| 🖼️ SCREENSHOT | `github.com` / `flipkart.com` |
| 📷 QR | `https://t.me/utility_duniya_bot` |
| 📸 PASSPORT PHOTO | photo + `Rahul Kumar` + `02-10-2026` |
| 📄 IMAGE→PDF | 3 photos, phir **A4 PDF** |
| 🖨️ 8-IN-1 | koi passport photo |
| 🖼️ QR WiFi / Contact | `JioFiber_Home` / `Himanshu Kumar` |
| 📄 BANK PDF→EXCEL | SBI/HDFC/PNB statement PDF |
| 📥 VIDEO DOWNLOADER | Instagram reel link |

## Aur kya chhota kiya

- **KAGAZ SUITE menu:** 9 line → **4 line** (documents ki list ab buttons me hi hai).
- **MEDIA STUDIO menu:** 8 line → **4 line**.
- Premium tools par **`(1 use of this tool = 1 credit)` line hata di** — ab sirf chhoti credits line
  (`⚡ Credits: 25 / 25`) dikhti hai. Baaki sab waisa hi.
- Prompt ke aakhir me `Tap /cancel any time to stop.` rehti hai (ek line — user atak na jaye).

## Jo nahi chhua (jaan-boojh kar)

- **Result cards** (vehicle report, IMEI spec sheet, IFSC result...) — wahi value hai, wo poore hi rahenge.
- 🏛️ SARKARI PORTALS aur 🎓 EXAM HUB — wo **link list** hain, links hi content hai.
- 🎬 Tutorial video ka button har tool ke neeche **waisa hi** hai (30 sec, HIMANSHU).

## Test

Naya test file: **`_selftest_prompts_v42.py`** — check karta hai ki har prompt
≤ 5 line / ≤ 320 char ho, me 📌 Example ho, aakhir me "Now send…" ho, koi bullet/separator na ho.
Baaki poora batch bhi green: 12/0 · tools_v31 ✅ · v34 48/0 · v35 46/0 · v32 51/0 · v37 87/0 · v38 80/0 ·
admin 54/0 · cloner ✅ · vehicle 78/0 · imei 70/0 · live_check **102/102** · audit 69/0.
