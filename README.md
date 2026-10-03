---
## 🔒 Privacy-safe lookup status

| Tool | Abhi kya available hai |
|---|---|
| 📱 **Number Info** | Local carrier/type/circle/validity metadata + official safety links; naam, family, address ya ID lookup disabled hai. |
| 🚗 **Vehicle + Challan** | Free RTO/state parsing + official VAHAN/e-Challan links; live owner/RC/challan data tabhi jab authorized provider set ho. |
| 🆔 **Aadhaar Official Portals** | Aadhaar ko bot/hub me bhejne ke bajay UIDAI/NFSA ke official, consent-based portals use karein. |

- Admin `/hubstatus` sirf hub health check karta hai; koi phone, plate ya Aadhaar test nahi hota.
- IMEI input locally validate hota hai; network par sirf pehle 8-digit TAC bheja jata hai.
- Poora privacy/setup detail: **[v41-API-HUB.md](v41-API-HUB.md)**

# ⚡ Utility Duniya Super-Bot — **v44**

**Ek bot me 30 kaam:** video download, channel auto-forward, photo/document, sarkari kagaz, bank statement → Excel,
media studio (MP3/status/karaoke), info tools (IFSC/pincode/ID/IP/RTO), QR, link safety, VIP + payment system.

> **Naya (v44):** 🧠 **AI Brain Clip Maker me** — Gemini/Groq key lagate hi AI khud video dekh kar
> best moments (hasi, cheer, action, shor) chunta hai + har clip ko AI ka title milta hai.
> Saath me: 🎓 STUDENT EXAM HUB **hata diya**, 3 crash fix (passport photo, bade video ka timeout,
> YouTube ka gandha error), menu dobara sajaya, aur **26 tools ka deep audit**. Guide: **`v44-AI-CLIPS.md`** ·
> Audit report: **`v44-TOOLS-AUDIT.md`**.
> **v43:** 🎬 CLIP MAKER (`v43-CLIP-MAKER.md`).
> **v42:** ✂️ chhote prompts · **v41:** 📲 IMEI TAC-only device hint + 🚗 safe RTO/official links; private lookup disabled.
>
> **v39:** 8 tools **poori tarah hata diye** (Actors Voice Studio, EMI Calc, Age Calculator, Password Generator,
> Web Search, UPI QR, Photo Info + Fake Detect, Rahu Kaal/Panchang) aur **saara bot text ab SIMPLE ENGLISH** me hai.
> Poora detail: **`v39-KYA-BADLA.md`**. Naye earning tools ki list: **`EARNING-TOOLS-V39.md`**.

---

## 🚀 Deploy (Render) — 4 step

1. GitHub par push karo (`push_v39_ready.sh` chalao, `GITHUB_TOKEN` env ke saath).
2. Render → apni service → **Manual Deploy** → **Clear build cache & deploy**.
3. Environment tab me ye 4 cheezein zaroor honi chahiye:
```
BOT_TOKEN=BotFather se mila token
ADMIN_ID=tumhari Telegram user ID   (owner — unlimited, free)
UPI_ID=tumhara@upi                  (VIP payment ke liye)
UPI_NAME=Utility Duniya
```
4. Telegram me `/start` bhejo → menu aa jayega. `/premium` → VIP plans. `/admin` → admin panel.

---

## 💎 Credits + VIP ka hisaab (v37 se, v39 me wahi)

| Cheez | Kitna |
|---|---|
| Naya user | **25 credits free** (one time — roz nahi milte) |
| Premium tools (7) | **1 use = 1 credit** |
| Baaki **saare tools** | **FREE** (koi credit nahi) |
| VIP (paid) / Owner | **Unlimited** — premium tools bhi free, koi credit nahi |

**Premium tools (8):** 📥 Video Downloader · 📱 Number Info · 🔄 Channel Cloner · 🔒 Private Channel Setup ·
🏦 Bank Statement PDF→Excel · 📜 Document Suite · ⚡ Media Studio · 🚗 Vehicle Info + Challan · 📲 IMEI / Phone Details · 🎬 Clip Maker.

VIP buy: `/premium` → plan chuno → QR se paisa → **Step 2**: UTR bhejo (12 digit) → **Step 3**: screenshot bhejo →
admin verify karke activate kar dega. **Direct VIP (bina payment):** `/admin` → plan select → `/activate <user_id>`.

---

## 🧰 Poori tool list (v39)

**Download / forward**
📥 Video Downloader (Instagram, YouTube, FB, X, TikTok, Pinterest… 20+ sites) · ⚡ Terabox/Mediafire/GDrive resolver ·
🔄 Channel Cloner — manual + **full-auto** (source → target, caption/watermark/thumbnail) · 🔒 Private Channel Setup

**Photo / document**
📸 Govt Exam Passport Photo (naam + DOP stamp, 20-50KB) · 🖨️ 8-in-1 Print Sheet · 📄 Doc/Marksheet PDF Compress (100KB-500KB) ·
🖼️ Image → Multi-page PDF · 🏦 **Bank Statement PDF → Excel** (locked PDF bhi) · 📜 **Document Suite**
(kirayanama, affidavit, notice 138, bayana/pakki rasid, rin shodh, naam sudhar + **registry total cost** + **bigha/kattha converter**)

**Media studio**
⚡ YouTube→MP3 · 🎬 Status Video (9:16) · 🎧 Ringtone cutter · 🎤 Karaoke · 🔊 8D · 💥 Bass boost ·
🗣️ Voice change (kid / heavy / robot / ghost / gadget / echo) · ✂️ Trim · 🗜️ Compress · 🎼 Video→MP3

**Info**
🚗 Vehicle Info + Challan (RTO details + official VAHAN/e-Challan links; live report ke liye authorized provider zaroori) · 📲 IMEI / Device Model (TAC match; catalog me available specs + .json) · 📱 Number Info (sirf operator/circle/type + safety links; personal records nahi) · 🏦 IFSC branch · 📮 Pincode + post offices (area se bhi) ·
🆔 ID & Username Finder (me / forward / @username → 5 platforms + 9 links) · 🌐 IP/Domain · 🚗 RTO vehicle info ·
📦 App Finder (8 trust stores)

**Chhote tools**
📷 QR (link/text, WiFi, contact) · 🔗 URL Short · 🔓 Link Bypass (tracking clean) · 🔍 Link Check (scam detector) ·
📈 Interest Calc (chakravriddhi — gaon wala byaaj) · 🖼️ Website Screenshot (HD + full page) ·
🏛️ Sarkari Seva Portals · 🎓 Student Exam Hub · 👤 My Account · ❓ Help/Tutorial · 💎 VIP · 🎁 Refer & Earn (5 refer = 30 din VIP)

---

## 📖 Tutorial

- Bot me: har tool ke **neeche 🎬 video button** (30 sec video) — aur ❓ **Help/Tutorial** me saare video.
- Text tutorial: `TUTORIAL.md` (aur bot ka telegra.ph page — `/tutrefresh` se refresh).
- Admin: `/admin` (dashboard: users, revenue, pending payments), `/payments` (pending list), `/activate <id> [days]`,
  `/credits <id> [n]`, `/tutrefresh`.

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
  media_downloader.py — yt-dlp/parth engine (20+ sites)
  osint_tools.py    — RTO (plate parse), phone info, IFSC, pincode, IP, username finder
  vehicle_challan.py— legacy RC/challan parser; live lookup default me disabled
  payguard.py       — payment proof check (UTR format + duplicate + screenshot analysis)
  sarkari_hub.py    — government portals + student exam hub
  toolkit_extras.py — URL shortener, link bypass, link safety scanner, interest engine
  tutorial_hub.py   — tutorial page (telegra.ph) + video links
  vip_payment.py    — VIP plans, UPI QR, payment flow
requirements.txt    — saare packages
v39-KYA-BADLA.md    — v39 me kya badla (2 minute read)
v44-AI-CLIPS.md — 🧠 AI brain (Gemini/Groq) + crash fixes + STUNDET EXAM HUB removal
v44-TOOLS-AUDIT.md — 26 tools ka deep audit (217 checks, sab pass)
v43-CLIP-MAKER.md — clip maker (video → 4-7 clips) setup, limits, best-moment logic
v42-CHHOTE-PROMPTS.md — chhote prompts (pehle vs ab, har tool ka example)
v41-API-HUB.md — TAC-only IMEI setup + authorized vehicle-provider safety notes
v40-VEHICLE-CHALLAN.md — purana single-endpoint vehicle setup (optional) + privacy notes
EARNING-TOOLS-V39.md— 12 naye earning-tool ideas (no AI)
TUTORIAL.md         — text tutorial (fallback link)
_audit_tools_v39.py — tool-by-tool audit script (68 engines — chala kar dekh lo)
```

---

## 🧪 Khud test karo

```bash
python3 _audit_tools_v39.py     # 68 engines: PDF, ffmpeg, QR, link safety, land, kagaz — sab
```

Aur bot me: `/start` → menu → tool kholo → prompt Hinglish (Hindi Latin script) me aayega.
Admin commands: **`/vehstatus`** (safe config check; real plate query nahi) · `/hubstatus` (sirf health check) · `/activate <id> [days]` · `/credits <id> [n]` · `/tutrefresh`.

---

## ⚠️ Zaroori baatein

- **Koi AI tool nahi** — sab kuch offline/deterministic (server pe koi AI model nahi, Render 512MB me aaram se chalega).
- **Privacy:** Number Info sirf carrier/type/circle jaise safe metadata dikhata hai. Leaked personal records — naam, family/linked numbers, address, government-ID — retrieve nahi hote; `NUM_LEAK_ENABLED` hamesha off hai.
- **IMEI privacy:** full IMEI locally validate hota hai; API ko sirf pehle 8-digit TAC bheja jata hai. Serial/owner/blacklist lookup nahi hota.
- **Vehicle:** live RC/challan sirf authorized provider se; default me official Parivahan/e-Challan links hi dikhte hain.
- **Copyright:** downloader sirf public links ke liye — kisi ka paid content dobara bechna galat hai.
- Payment proof sakhti se check hota hai: UTR format + duplicate + screenshot asli hai ya photo.
