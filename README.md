# ⚡ Utility Duniya Super-Bot (v34 — QUICK ACTIVATE + TUTORIAL PAGE EDITION)

An All-in-One Super Automation & Utility Engine for Telegram — **25+ tools**, **Full-Auto Channel Cloner (3-step wizard + private-channel support)**, **Universal Video Downloader (20+ platforms)**, **Real Link Safety Scanner**, **Cyber Cafe Studio**, **Terabox Multi-Engine Resolver**, **Voice Studio (24 real + 30 lab voices)**, **OSINT Info Suite (RTO / Phone / IFSC / Pincode / IP / Username)** and **Automated VIP / UPI Engine**.

---

## 🆕 v34 — Quick VIP Activate (`/activate`) + Tutorial ab link par

### 🎁 1. Seedha VIP (bina payment) — `/activate`
Dost ya koi user seedha aapke number/UPI par paisa bhej de, ya aap kisi ko free me VIP dena chaho:
1. `/admin` → **🎁 VIP Activate** button → plan chuno (30/60/90/120 din ya Lifetime)
2. Phir likho: `/activate <user_id>` → us user ko wahi plan
   - `/activate 123456789 90` → alag din chahiye to
   - `/activate @username` → username se bhi chalta hai
- User ko turant "Mubarak ho, VIP mil gayi + valid till" message jata hai
- Poora record **📜 Manual VIP Log** me (kaun, kab, kitne din, kis admin ne)
- `meta` table + `vip_grants` table naye; stats me "Aaj manual VIP diye" count

### 📖 2. Tutorial ab bot me nahi — ek page par (link)
- Tool ke andar wale "💡 Kaise use karein" línes hata di gayi → ab har tool me sirf kaam + neeche **tutorial link**
- Poora tutorial (saare tools ka tareeka + har tool ki detail) ek page par embed:
  - Bot **khud** telegra.ph par page banata/update karta hai (startup par, background me)
  - `TUTORIAL_URL` env se apna link bhi laga sakte ho (jaise channel post)
  - Fallback: repo ka `TUTORIAL.md`
- `/tutorial`, `/help`, keyboard ka ❓ MADAD/TUTORIAL, Voice Studio aur Cloner ke guide buttons — sab isi link par le jaate hain
- Admin panel me **📖 Tutorial Page** button (turant refresh) + `/tutrefresh` command

---

## 🆕 v33 — Admin Panel + Strict Payment Verification

### 🛠️ 1. Naya Admin Panel (`/admin`)
- Live dashboard: users, active today, uses, VIP count, **pending payments**, revenue, approved/rejected totals.
- Buttons: Pending Payments · Payment History · Recent Users · **User Search (VIP do/hatao/ban/unban)** · Broadcast · Ban/Unban · Command list.
- `/payments` = sirf pending list (tap → poora verification card + approve/reject).
- `/grant`, `/revoke`, `/broadcast`, `/ban`, `/unban` — sab pehle jaise, plus **double-admin support** (`ADMINS=id1,id2`).

### 👑 2. Owner ko ab koi premium/limit nahi
- `ADMIN_ID` wali ID = **OWNER** → na daily limit, na "Buy VIP" message.
- `/premium` par owner ko dikhta hai: *"Aap owner ho — sab unlimited"* + pending payments shortcut.
- Keyboard me naya **👑 OWNER MODE** button. (Purana bug: owner bhi free-limit me fas jata tha.)

### 🧾 3. Payment proof ab STRICTLY verify hota hai (`modules/payguard.py`)
- **Layer 1 — UTR format:** 12-digit UPI UTR ya 16-22 char bank ref. Mobile number / random text / 15-digit = ❌ wajah ke saath reject. (`/premium` → "❓ UTR kahan milega?" helper bhi)
- **Layer 2 — UTR duplicate:** ek UTR se sirf ek baar VIP (DB check).
- **Layer 3 — Screenshot check (bina internet, fast):** flat-block + UI-line + text-sharpness metrics se score 0-100 → 🟢/🟡/🔴. Photo/selfie/meme = ❌ reject (3 try tak, phir flag ke saath admin ko).
- **Layer 4 — Screenshot duplicate:** same image (Telegram `file_unique_id`) dobara = ❌ reject.
- Extra: per-user pending limit (3), sare admins ko card, `pytesseract` ho to OCR keyword check bhi.

### ✅ 4. Premium Activate button ka BUG FIX
- **Root cause:** text-message wale proof par `edit_caption` chalta tha → Telegram error → handler chup-chaap marta tha → VIP lagta nahi tha.
- Ab `edit_caption → edit_text → reply` fallback chain hai, `q.answer()` bhi hota hai, aur approve **idempotent** hai (dobara click = "pehle hi approve").
- Approve/reject/"dobara maango" — teeno par user ko automatic message jata hai.

---

## 🆕 v32 PHASE-3 — Har tool check + professional upgrade

### 🎙️ 1. Voice Studio → **24 ASLI alag awaazein** (pehle "sab ek jaise" the)
- 24 actor/character presets — har ek **alag real neural voice**: Don (hi-IN-Madhur), South Mass Hero (te-IN-Mohan), Rowdy (mr-IN-Manohar), Shayar (ur-IN-Salman), Sweet Girlfriend (hi-IN-Swara), Hollywood Trailer (en-US-Christopher), UK Documentary (en-GB-Ryan), Spooky Demon (en-US-Eric), Anime Girl (ja-JP-Nanami), Robot AI (en-US-Steffan), Arabic (ar-SA-Hamed), French, Spanish, Russian + 11 Indian languages.
- **🧪 Voice Lab:** 30 voices × 4 speeds (🐢 −25% · ▶️ 0 · ⚡ +25% · 🚀 +50%).
- Hindi (Devanagari) text + English voice = engine kuch nahi deta tha → ab bot **khud sahi voice par switch** karta hai aur caption me note bhi likhta hai.
- Generation me 3 retries + size-verify; audio na bane to saaf error.

### 🔄 2. Auto-Forwarding → **source-first 3-step wizard** + private channel flow
- Pehle **SOURCE** poochhega → phir **TARGET** → phir **🤖 FULL AUTO ON** (button) → bas.
- **🔒 Private channel:** koi login/password nahi — bot ko private channel me **admin** banao aur us channel ki **koi post bot ko forward** karo → bot khud chat-ID pakad kar Source/Target set karne ke **buttons** de deta hai.
- **📘 Kaise Use Karein?** (poora guide), **🧪 Test Forward** (bot admin hai ya nahi + target me test post), **📊 Meri Setting Dekho** (summary card).
- Video / PDF / Doc / Audio / Voice / GIF / Sticker / Album (2–10) — sab auto-forward hota hai.

### 📈 3. Vyaaj → **sirf CHAKRAVRIDDHI (compound)**, gaon-kasbe wali bhasha me
- Input: paisa → *"₹100 par kitne rupaye mahina?"* → kitne mahine.
- Output: pehle mahine ka byaaj, kul byaaj, **wapas dena hoga kitna**, mahine-dar-mahine table, milestones (6/12/24/36 mahine), aur "agar har mahine sirf byaaj dete raho to kitna lagta" wala comparison. Simple interest **hata diya**.
- Money ab **Indian format** me: ₹1,00,000 (1 lakh), ₹1.25 crore.

### 🧮 4. EMI → ab **"kitne din me poora chukega"**
- EMI, kul byaaj, kul payment, **pehli EMI ki date, aakhri EMI ki date**, aur `24 mahine = 731 din me` — simple bhasha me.

### 📱 5. Number Info → **carrier info + 🧾 Public Records (button)**
- Operator, circle/region, number type, country, timezone + **6 real check links** (WhatsApp chat, Telegram, Truecaller, Google, **Chakshu spam-report (TRAI)**, **Cyber Crime 1930**).
- **🧾 Public Records button:** owner ke diye hue API (`osint-apis-hub.onrender.com/api/num-info`) se naam / pita ka naam / pata / linked number dikhata hai (5 records tak) + misuse warning + 1930/Chakshu report buttons.
- ⚠️ Ye leaked/personal data hai — misuse **crime** (IT Act + DPDP Act) aur Telegram/host ban ka risk. Isliye **owner-controlled on/off switch**: `NUM_LEAK_ENABLED=off` karte hi button gayab.

### 🆔 6. ID & Username Finder → **asli existence check** (pehle sirf links the)
- GitHub · Telegram · YouTube · TikTok · Steam par **200/404-styled real check** → ✅ account MILA / ❌ account nahi hai / ❔ check nahi hua.
- Baaki 9 platforms (Instagram, X, Reddit, Pinterest, Snapchat, Facebook, Spotify, Twitch, Threads) = **direct open links** (inka server-side check honestly possible nahi — jhooth nahi bolte).
- Telegram heuristic: real/deactivated/bot page se naam nikalta hai, fake/generic page ko sahi se reject karta hai (7/7 verified).

### 🧰 7. Roz ke tools ka upgrade
| Tool | Kya naya |
|---|---|
| 📷 QR | 4 type — Link/Text · 💰 UPI (fixed amount ke saath) · 📶 WiFi share · 👤 Contact card |
| 🔐 Password | 4 mode — Naam wala · 🧠 Easy words (passphrase) · 🎲 Random strong · 🔢 6-digit PIN (strength meter ke saath) |
| 📄 Doc PDF Compress | 100/200/300/500 KB choose karo + ⚫ Black & White mode + multi-photo → ek PDF |
| 🖼️ Image→PDF | Normal + **A4 Print PDF** (printer par kuch kat nahi aata) |
| 📸 Screenshot | HD + **📜 Full Page** (3-engine chain: thum.io → thum.io full → microlink backup) |
| 📮 Pincode | Pincode se post offices **ya area ke naam se pincode** (bade buttons, copy-friendly) |
| 🚗 RTO | 36 state codes + ~45 RTO districts + **5 official links** (VAHAN, e-Challan, IIB insurance, Sarathi DL, mParivahan) |
| 🏦 IFSC | MICR + contact + UPI/NEFT/RTGS/IMPS flags + Maps |
| 📖 **Tutorial Page (NAYA)** | Saare tools ka tareeka ek page par, bot me sirf link |
| 🎁 **Quick Activate (NAYA)** | `/activate` — dost/direct paisa wale ko bina proof VIP |
| 🛠️ **Admin Panel (NAYA)** | Dashboard + pending payments + user search + VIP/ban + broadcast |
| 🌐 **IP / Domain (NAYA)** | ip-api se ISP, org, geo, timezone + **VPN/Proxy & Datacenter flags** |
| 📱 **Public Records (optional)** | Naam/pita/pata/linked-number — env se on/off, warning + report buttons ke saath |
| 🔎 Web Search | **3-engine parallel** (DuckDuckGo Lite + DDG HTML + Bing) → merge + dedupe (pehle sirf DDG) |
| 📦 App Finder | 6 → **8 stores** (+ APKCombo, F-Droid) |
| ❓ **MADAD / TUTORIAL (NAYA)** | Bot ke andar har tool ka 1-line simple matlab + `/tutorial` command |
| 💬 Har tool ke andar | "Kaise use karein" mini-guide (users ko kuch poochhna hi na pade) |

### ❌ 8. Signature Cleaner **DELETE**
- Menu, code, handler aur module se poori tarah hata diya gaya (jaisa aapne kaha).

---

---

## 🆕 v31 PRO — Kya naya hai (What's New)

### 🔄 1. Channel Cloner → ab **100% FULL AUTO**
- **Source channel set karo → bot khud**, 2–5 second me har **nayi post** tumhare target channel me daal deta hai (caption, tag, watermark, replace/remove words, thumbnail — sab branding ke saath).
- **Manual forward mode** bhi pehle jaisa kaam karta hai (`🚀 Manual Forward Mode`).
- Video / Document / Audio / Voice / GIF / Sticker / Video-Note **sab support** (pehle sirf text + photo chalta tha).
- **Album (2–10 photos/videos)** ek saath album ban kar jata hai.
- FloodWait (Telegram rate-limit) par khud wait; galat caption HTML ya thumbnail par automatic fallback — bot crash nahi hota.
- Source == Target par **loop-protection**; target/source set karte waqt bot **khud admin-check** karta hai.

### 📥 2. Video Downloader → ab **UNIVERSAL (20+ platforms)**
- Instagram (Reels / Posts / Carousels / Stories) + **YouTube, Shorts, Facebook, X (Twitter), TikTok, Snapchat, Pinterest, Reddit, Vimeo, Dailymotion, Threads** aur bahut kuch.
- **3-engine chain:** `parth-dl` → `yt-dlp` → `og:video` scrape (jo chale wahi), plus optional cookie support (`IG_COOKIE`) se 100% reliable.
- 48 MB se bada file ho to bot **clean direct download link** de deta hai (kaam rukta nahi).
- Bundled FFmpeg (`imageio-ffmpeg`) — YouTube ke DASH streams ko 360p+audio merge karke bhejta hai.

### 🛡️ 3. LINK CHECK → ab **REAL multi-signal scanner** (pehle sirf 8 keyword match tha)
- Redirect-chain unpacking, IP-host / punycode / `@`-trick detection, suspicious TLDs, brand-impersonation detection, lure words, free-hosting scam patterns, unusual ports, non-HTTPS.
- **OpenPhish LIVE phishing feed** + **urlscan.io** reputation lookup.
- Result: Verdict (SAFE / LOW RISK / SUSPICIOUS / DANGEROUS) + Risk score 0–100 + "Aap kya karein".

### 📈 4. INTEREST CALCULATOR — **FIXED** (ye tool pehle completely toota hua tha)
- 3-step flow: Principal → Rate (%) → Time (months/saal) → **Simple + Compound (monthly/quarterly/half-yearly/yearly)** poora breakdown.

### 🧮 5. EMI CALC → ab **flexible input**
- `100000` · `5,00,000 9% 24m` · `3 lakh 8.5% 5 saal` — sab chalega; Total Interest + Total Payment + 6 mahine ka breakdown.

### 🔗 6. URL SHORT + LINK BYPASS → upgraded
- **6 shortener providers** (da.gd, spoo.me, cleanuri, clck.ru, tinyurl, is.gd) — jo chale wahi (pehle wala is.gd dead tha).
- LINK BYPASS ab **asli redirect chain** kholta hai + **tracking parameters (utm, fbclid, si, igshid…)** saaf karta hai.

### ☁️ 7. Terabox / Cloud → **6-layer engine chain** (2026 reality handled)
- Public workers → Guest listing → **NDUS cookie mode** (`TERABOX_COOKIE` env) → apna custom provider (`TERABOX_API_BASE`) → **trusted web-downloader fallback buttons**.
- Mediafire: naya `data-scrambled-url` (base64) decode; Google Drive: large-file **confirm-token** handling + filename/size.

### 🔍 8. Baaki sab **waise hi kaam kar raha hai** (regression-tested)
- QR, Password, Age, Pincode, IFSC, RTO, Number Info, ID Finder, IMAGE→PDF, Cyber Cafe Studio (Passport photo / Signature / Print sheet / PDF compress), Web Search, App Finder, Site Screenshot, Sarkari & Exam Hub, VIP/UPI, Voice Studio, ID… — sab pehle jaisa, aur 44 live checks me se 43 PASS.

---

# ⚡ Utility Duniya Super-Bot (v31 PRO Edition)

An All-in-One Super Automation & Utility Engine built for Telegram with **25+ High-Power Tools**, **Sarkari & Student Portals**, **AI Cyber Cafe Studio**, **Terabox Multi-Cloud Downloader**, **Channel Cloner & Auto-Forwarder**, **AI Voiceover Studio**, and **Automated VIP Subscription & UPI Dynamic QR Engine**.

---

## 🔥 Features Overview

### 1. ⚡ Terabox & Multi-Cloud Direct Downloader
- **Ad-Free Bypass:** Extracts direct high-speed download links and web stream links for **Terabox**, **Mediafire**, and **Google Drive**.

### 2. 🔄 Channel Cloner & Auto-Forwarder with Custom Branding
- **Auto-Forward / Batch Clone:** Clone posts from public channels or batch forward media.
- **Custom Branding:** Automatically replaces captions, removes old links, and appends custom channel watermarks.

### 3. 🎙️ AI Voice Clone & Celebrity Voiceover Studio
- Powered by high-speed neural TTS engines:
  - 🎙️ *Modi Ji / Deep Indian Male Voice*
  - 🌸 *Sweet Hindi Female (Swara)*
  - ⚡ *Viral Deep Alpha Male (Hormozi / Sigma Style)*
  - 🏏 *Aggressive Sports Commentary*
  - 🎭 *Anime Cute Girl Voice*
  - 🇮🇳 *Indian & British English Accents*

### 4. 🏛️ Official Government Services & Student Exam Hub
- **100% Direct Official Portals:**
  - 💳 **Aadhaar:** e-Aadhaar Download, PVC Card Order, Mobile Link & Lock
  - 🪪 **PAN Card:** 10-Minute Free Instant e-PAN, Link Status & Corrections
  - 🍚 **Ration & Ayushman:** NFSA State Portals, ABHA Health ID Download
  - 🎓 **APAAR ID:** One Nation One Student ID Portal
  - 🚗 **Parivahan:** Driving License, Learner Apply, RC & e-Challan
  - 📜 **State Certificates:** Bihar RTPS, UP e-District, Jharsewa
  - 💼 **EPFO / PF:** UAN Passbook & Online Claim
- **Student Exam Hub:** SSC, Railway RRB, UPSC, Defence Agniveer, State Police, Banking IBPS/SBI, CTET Admit Cards & Official Answer Keys.

### 5. 📸 AI Cyber Cafe Document Studio
- **Candidate Name & DOP Stamp:** Auto creates standard 3.5cm x 4.5cm passport photo with official white bottom box, uppercase name & date, compressed to exact 20KB-50KB.
- **Printable 8-in-1 Sheet:** Creates 4x6 inch (1200x1800 @ 300 DPI) sheet with crop lines for ₹5-10 photo lab printing.
- **Signature Cleaner & Enhancer:** Converts camera photos into high-contrast black ink on pure white background, compressed to 10KB-20KB.
- **Document / Marksheet PDF Compressor:** Compresses marksheet photos into crisp PDFs under 250KB for Govt portal compliance.

### 6. 🕵️ Smart OSINT & Digital Investigation Hub
- 🚗 **Vehicle RTO Lookup:** Parses number plates, state, district RTO, and parivahan links.
- 📱 **Phone Carrier & Circle:** Telecom circle, carrier, and one-tap WhatsApp link.
- 🏦 **IFSC Bank Branch Lookup:** Real-time bank branch details + Google Maps location.
- 📮 **Pincode Lookup:** Postal circle, district, and post offices list.
- 🌐 **IP / Domain WHOIS:** Host, ISP, region, city, and ASN details.
- 👤 **Social Media Username Checker:** Checks availability across 30+ platforms.

### 7. 🛠️ Classic High-Speed Utilities
- 📷 HD QR Code Generator (WiFi, UPI, URL, Text)
- 🖼️ Multi-Page Image to PDF Converter
- 🔗 URL Shortener (is.gd & tinyurl)
- 🧮 Loan EMI & Amortization Schedule
- 🎂 Age, Zodiac & Next Birthday Countdown
- 🔐 Strong Password Generator
- 🔎 Web Search & Play Store App Finder
- 🖼️ Full HD Website Screenshot

### 8. 💎 Automated VIP Subscription & Earning System
- Dynamic UPI QR Code generation with plan amounts (₹19, ₹49, ₹99).
- Payment proof submission with 1-click Admin Approval / Rejection buttons.
- Referral system: Invite 5 friends = 30 Days Free VIP.

---

## 🚀 Deployment Instructions

### 1. Environment Variables (`.env`)
```env
BOT_TOKEN=your_telegram_bot_token_from_botfather
ADMIN_ID=your_telegram_user_id
FORCE_CHANNEL=@YourChannelUsername
FORCE_CHANNEL_LINK=https://t.me/YourChannelUsername
UPI_ID=yourname@upi
UPI_NAME=UtilityDuniya
FREE_LIMIT=20
REFER_NEED=5
```

### 2. Run Locally
```bash
pip install -r requirements.txt
python bot.py
```

### 3. Deploy to Render / Koyeb / VPS
The repository includes `render.yaml` and a built-in background keepalive web server on port `8080` for 24/7 uninterrupted uptime.
