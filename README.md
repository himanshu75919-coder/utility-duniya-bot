# ⚡ Utility Duniya Super-Bot — **v50 Premium Pro**

**Ek hi bot me 32+ kaam:** video download, channel auto-forward, photo/document banane wale tools,
sarkari kagaz, bank statement → Excel, media studio (MP3 / status video / karaoke), info tools
(IMEI / vehicle / number / IFSC / pincode / ID / IP), **weather + EMI/vyaaj calculator**, QR,
link safety, aur VIP + payment system.

Poora bot ka **text Hinglish** me hai — short prompt + example ke saath, taaki naya user bhi bina
padhe samajh jaye.

---

## 🆕 v50 me kya badla (Premium Pro)

### ➕ 2 NAYE FREE TOOLS
| Tool | Kya karta hai |
|---|---|
| 🌦️ **WEATHER / MAUSAM** | Shehar ka naam bhejo (Gaya, Patna, Pune…) → abhi ka mausam + aage 3 din ka forecast, hawa, humidity, baarish ki sambhavna, sunrise/sunset. 100% free (Open-Meteo, koi API key nahi) |
| 🧮 **EMI / INTEREST CALC** | 🧮 Bank EMI calculator (amount + rate% + months → monthly EMI, total interest, balance milestones) + 🪔 Gaon-wala **chakravritti vyaaj** hisaab (₹100 par ₹X mahina, poora month-by-month). PURANA INTEREST CALC ka badla — ab poora kaam karta hai |

### 🐛 BUG FIXES (real problems)
| Kya | Problem |
|---|---|
| 🆔 **ID Finder forward** | Forward karne par ID nahi milti thi (help text aa jata tha) — ab forward sabse pehle process hota hai |
| 🖨️ **8-in-1 sheet** | Photos 1.17×1.5" chhoti print hoti thi — ab **EXACT 3.5×4.5cm** (413×532px @300DPI) |
| 📸 **Passport photo size** | Kabhi 20KB se chhoti file banti thi (portals reject karte hain) — ab 20-50KB window pakka |
| 📱 **Toll-free numbers** | 1800-… (11 digit) US country code ban jata tha — ab +91 India |
| 🛠️ **Admin tutorial button** | Button par crash (galat HTML tag) — ab kaam karta hai + link dikhata hai |
| 🖼️ **Image→PDF** | "10 photo tak" likha tha par limit nahi thi — ab 10 par rukta hai + Clear button |
| 📢 **Broadcast** | `<` jaise character par poora broadcast fail hota — ab plain-text fallback |
| 🗄️ **Database** | "database is locked" crash ka risk — `busy_timeout` laga |
| 🧹 **Dead code** | 70 lines duplicate admin code delete kiya |

### ⚡ SPEED + PRO UPGRADES
| Kya | Kya badla |
|---|---|
| 🔗 **URL Shortener** | Ab 6 providers **PARALLEL** chalte hain — 10-45s ki jagah **~1 second** |
| 🆔 **ID/Username Finder** | 5 platform checks **parallel** — ~60s ki jagah **~5-10s** |
| 🔍 **Link Check** | NAYA **domain-age** signal (free RDAP) — 30 din se naya domain = automatic risk +20. Phishing feed scan bhi ab instant |
| 🏦 **Bank PDF** | Password wale PDF par pehle **khud common passwords try** karta hai — aksar user ko matlaagne ki zaroorat hi nahi |
| 👤 **Error handling** | Koi ghatna ho to user ko saaf message milta hai (pehle chup-chaap fail hota) |

✅ **Test suite:** `_selftest_v50.py` = **99 checks** (2 naye tools, 9 bug fixes, live API checks, DB/credits)

---

## 🆕 v49 me kya badla

| Kya | Detail |
|---|---|
| 🗑️ **3 faaltu tools hate** | 🎬 CLIP MAKER · 🔓 LINK BYPASS · 📈 INTEREST CALC — menu, code, video, tutorial: sab se gayab |
| 🗣️ **Poora bot Hinglish** | Har prompt ab short Hinglish + `📌 Jaise:` example. Lambi English instructions hata di gayi |
| 📲 **IMEI tool fix** | Hub ka naya TAC endpoint + phone ki photo + poori spec sheet + `.json` file. Privacy: sirf pehle 8 digit dikhte hain |
| 🔌 **Hub URLs sahi** | Bot ab `osint-api-hub.onrender.com/api` (naya hub) use karta hai — purane dead host nahi |
| 🧹 **Saaf-safai** | 9 bekaar tutorial videos, 14 purane dev-note files aur 2 dead module (`clip_maker`, `ai_brain`) delete |
| ✅ **Test suite** | `_verify_v49.py` = **93 checks** (3-tool removal, 29 menu buttons, Hinglish texts, 26 live API checks, DB/credits) |

---

## 🚀 Deploy (Render) — 4 step

1. GitHub par push karo.
2. Render → apni service → **Manual Deploy** → **Clear build cache & deploy**.
3. Environment tab me ye 4 cheezein zaroor honi chahiye:
```
BOT_TOKEN=BotFather se mila token
ADMIN_ID=aapki Telegram user ID      (owner — unlimited, free)
UPI_ID=aapka@upi                     (VIP payment ke liye)
UPI_NAME=Utility Duniya
```
4. Telegram me `/start` bhejo → menu aa jayega. `/premium` → VIP plans. `/admin` → admin panel.

> 🚨 **Deploy ke baad ek baar `/refresh` (ya `/newmenu`) bhejo** — isse sab users ko naya
> keyboard mil jata hai (purane hataye gaye tools ke buttons hat jayenge).

---

## 💎 Credits + VIP ka hisaab

| Cheez | Kitna |
|---|---|
| Naya user | **25 credits free** (one time — roz nahi milte) |
| Premium tools | **1 use = 1 credit** |
| Baaki saare tools | **FREE** (koi credit nahi) |
| VIP (paid) / Owner | **Unlimited** — premium tools bhi free |

**Premium tools:** 📥 Video Downloader · 📱 Number Info · 🔄 Channel Cloner · 🔒 Private Channel Setup ·
🏦 Bank Statement PDF→Excel · 📜 Document Suite · ⚡ Media Studio · 🚗 Vehicle Info + Challan · 📲 IMEI / Phone Details.

VIP lene ka tarika: `/premium` → plan chuno → QR se paisa → **Step 2**: UTR bhejo (12 digit) →
**Step 3**: screenshot bhejo → admin verify karke activate kar dega. Status: `/mypay`.
**Direct VIP (bina payment):** `/admin` → plan select → `/activate <user_id>`.

---

## 🧰 Poori tool list (v49)

**Download / forward**
📥 Video Downloader (Instagram, YouTube, FB, X, TikTok, Pinterest… 20+ sites) · ⚡ Terabox/Mediafire/GDrive resolver ·
🔄 Channel Cloner — manual + **full-auto** (source → target, caption/watermark/thumbnail) · 🔒 Private Channel Setup

**Photo / document**
📸 Govt Exam Passport Photo (naam + DOP stamp) · 🖨️ 8-in-1 Print Sheet · 📄 Doc/Marksheet PDF Compress (100KB-500KB) ·
🖼️ Image → Multi-page PDF · 🏦 **Bank Statement PDF → Excel** · 📜 **Document Suite**
(kirayanama, affidavit, notice 138, bayana/pakki rasid, rin shodh, naam sudhar + **registry total cost** + **bigha/kattha converter**)

**Media studio**
⚡ YouTube→MP3 · 🎬 Status Video (9:16) · 🎧 Ringtone cutter · 🎤 Karaoke · 🔊 8D · 💥 Bass boost ·
🗣️ Voice change (kid / heavy / robot / ghost / gadget / echo) · ✂️ Trim · 🗜️ Compress · 🎼 Video→MP3

**Info**
🚗 Vehicle Info + Challan · 📲 IMEI / Phone Details (device + poori spec sheet + .json) · 📱 Number Info
(operator/circle/type + links) · 🏦 IFSC branch · 📮 Pincode + post offices (area ke naam se bhi) ·
🆔 ID & Username Finder · 🌐 IP/Domain · 📦 App Finder (8 trust stores)

**Chhote tools**
📷 QR (link/text, WiFi, contact) · 🔗 URL Short · 🔍 Link Check (scam detector) ·
🖼️ Website Screenshot (HD + full page) · 🏛️ Sarkari Seva Portals · 👤 My Account ·
❓ Help/Tutorial · 💎 VIP · 🎁 Refer & Earn (5 refer = 30 din VIP)

---

## 📖 Tutorial

- Bot ke andar: har tool ke neeche **🎬 video button** (30 sec video) + ❓ **Help/Tutorial** me saare video.
- Text tutorial: **`TUTORIAL.md`** (aur bot ka telegra.ph page — `/tutrefresh` se refresh).
- Admin commands: `/admin` (dashboard), `/payments` (pending list), `/activate <id> [days]`,
  `/credits <id> [n]`, `/refresh` (sabko naya keyboard), `/tutrefresh`, `/imeistatus`.

---

## 🗂️ Files

```
bot.py              — main bot (handlers, menus, credits, VIP, admin, kagaz flow, media studio flow)
database.py         — SQLite (users, credits, payments, VIP, referrals, cloner config)
modules/
  channel_cloner.py — cloner engine (auto-forward, branding, albums, floodwait retry)
  cloud_tools.py    — terabox / mediafire / gdrive direct-link resolvers
  cyber_studio.py   — passport photo, print sheet, PDF compress (grayscale/A4)
  desi_tools.py     — bank statement parser, kagaz PDFs, registry cost, land units, media studio (ffmpeg)
  general_tools.py  — QR, vCard, WiFi QR, image→PDF, screenshot, app store links
  media_downloader.py — yt-dlp / hub engine (20+ sites) + YouTube 1080p
  osint_tools.py    — IFSC, pincode, phone info, IP, username finder
  api_hub.py        — aapke OSINT API hub ke saare endpoints ka wrapper
  imei_lookup.py    — IMEI → brand/model/spec sheet (TAC privacy included)
  vehicle_challan.py— live vehicle RC + challan report
  render_health.py  — Render keepalive / health + webhook URL helper
  payguard.py       — payment proof check (UTR + duplicate + screenshot analysis)
  sarkari_hub.py    — government portals ke direct links
  tutorial_hub.py   — tutorial page (telegra.ph) + video links
  vip_payment.py    — VIP plans, UPI QR, payment flow
requirements.txt    — saare packages
TUTORIAL.md         — text tutorial (bot ke andar se bhi link milta hai)
1-PADHO-PEHLE.md    — sabse pehle ye padho (setup + zaroori baatein)
RENDER-ME-KYA-DALNA-HAI.md — Render me kaun-kaun se env var dalne hain
tutorial_videos/    — har tool ka 30 second video (CDN se serve hota hai)
```

---

## 🧪 Khud test karo

```bash
python3 _verify_v49.py        # 93 checks: menu, Hinglish text, live API, DB/credits
python3 _selftest_v45.py      # hub integration (61 checks)
python3 _selftest_v48.py      # video size / truncated-file checks
python3 _selftest_imei.py     # IMEI flow (70 checks)
python3 _selftest_vehicle.py  # vehicle + challan (78 checks)
python3 -m pytest tests/ -q   # privacy tests
```

---

## ⚠️ Zaroori baatein

- **Koi AI tool nahi** — sab deterministic (Render 512MB me aaram se chalega).
- **Legal:** Number info = live carrier/type + links (kisi ki niji jaankari nahi). Kuch hub endpoints
  owner ki marzi se off hain — bot us case me saaf Hinglish message deta hai, credit nahi katta.
- **Vehicle/challan** hub par disabled ho to bot graceful message + official portal link deta hai.
- **Copyright:** downloader sirf public links ke liye — kisi ka paid content dobara bechna galat hai.
- Payment proof sakhti se check hota hai: UTR format + duplicate + screenshot asli hai ya photo.
