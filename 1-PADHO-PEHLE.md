---
## 🔒 Privacy-safe lookup status

- **Number Info:** local carrier/type/circle/validity metadata aur official safety links hi; leaked naam, family, linked numbers, address ya government ID nahi.
- **Vehicle + Challan:** free RTO/state parsing aur official VAHAN/e-Challan links; live owner/RC/challan tabhi jab authorized provider configure ho.
- **Aadhaar:** bot/hub me number mat bhejein; apne records ke liye UIDAI/NFSA ke official, consent-based portal use karein.
- **IMEI:** full IMEI local validation ke baad network par sirf pehle 8-digit TAC jata hai.
- Admin `/hubstatus` sirf `/health` check karta hai; koi phone, plate, Aadhaar query nahi hota.
- Setup detail: **[v41-API-HUB.md](v41-API-HUB.md)**

# 📖 1-PADHO-PEHLE.md — v44 (5 minute me poora samajh)

Bhai, ye file **sabse pehle** padh lo. Isme sirf kaam ki baat hai:

1. **v39 me kya badla** (2 line me)
2. **Deploy kaise karna hai** (4 step)
3. **Test kaise karna hai** (5 minute)
4. **Credits/VIP ka hisaab**
5. **Aage kya banana hai** (earning tools ki list)

---

## 0️⃣ v44 (naya) — 🧠 AI + crash fixes + 🎓 EXAM HUB hata

**1) 🎓 STUDENT EXAM HUB poori tarah hata diya** — button, code aur tutorial se (aapka order).

**2) 3 crash fix (screenshot wale):**
- 📸 **PASSPORT PHOTO** — naam + date (DOP) bhejne par pehle bot menu par phenk deta tha (bug).
  Ab: photo → `SHWETA KUMARI 01-07-2011` → stamped photo ready ✅ (3.5×4.5 cm, 20-50KB).
- 📥 **VIDEO DOWNLOADER** — bada video bhejte waqt Telegram "Timed out" deta tha. Ab bot
  **timeout bade** kar deta hai, aur pehli koshish fail ho to **compressed version** khud bhej deta hai.
- 🎬 **YOUTUBE** — gandha error (`[youtube] ... github.com/yt-dlp ...`) hata diya. Ab saaf line
  + **credit nahi katta**.
- Saath me: galti se galat input bhejo to bot **us tool ka prompt dobara** dikhata hai (menu par nahi phenkta).

**3) 🧠 AI Clip Maker (asli AI):** Render → Environment me ek key daalo —
- `GEMINI_API_KEY` (free, aistudio.google.com/apikey) → AI **video ke frames + audio** dekh kar
  best moments chunta hai (hasi, cheer, shout, action, drama).
- ya `GROQ_API_KEY` (free, console.groq.com/keys) → **Whisper** transcript + loudness mila kar
  best windows + **AI se clip ke title**.
- Key na ho to bot apne purane **loud + scene** engine se chalta rahega (kuch tootega nahi).
- Card me naya button: `🧠 Smart AI` (ON/OFF). Admin: **/aistatus** se check karo.

**4) 🔬 26 tools ka deep audit** — `v44-TOOLS-AUDIT.md` (217 checks, sab pass): har tool ka prompt,
tutorial video, wiring, credit guard, network timeout, error leak, fallback.

---

## 0️⃣1️⃣ v43 — 🎬 CLIP MAKER

Video bhejo → **4-7 short clips (25-60 sec)**. Mode: 🎯 Best Moments (awaaz tez + action hisse) ya
⏱️ Equal Parts. Format: 🖥️ 16:9 ya 📱 9:16 (Shorts/status). Limit **15 min**, file 20MB, ya direct
`.mp4` link (YouTube optional — kabhi block hota hai). 1 credit, VIP unlimited.
Poora guide: **`v43-CLIP-MAKER.md`**.

## 🔒 Number, IMEI, Vehicle aur Aadhaar — abhi ka status

- **Number Info:** sirf local carrier/type/circle/validity metadata aur official safety links. Leaked naam, family links, alternate numbers, address ya government ID nahi dikhte.
- **IMEI:** full 15-digit input locally validate hota hai; API ko sirf pehle 8 digits ka TAC bheja jata hai. Catalog me brand/model hint mil sakta hai, lekin full specs/photo har model ke liye guaranteed nahi. Serial/owner/blacklist lookup nahi hota.
- **Vehicle + Challan:** default me live lookup disabled hai. Bot sirf RTO/state format info aur official VAHAN/e-Challan links deta hai. Provider ko tabhi configure karein jab use aur display ki written authorization ho.
- **Aadhaar:** Aadhaar number bot/hub me mat bhejein. Apne record ke liye UIDAI/NFSA ke official, consent-based portal use karein.
- `/vehstatus` real plate query nahi karta; `/hubstatus` sirf `/health` check karta hai. Setup detail: **`v41-API-HUB.md`**.

---

## 1️⃣ v39 me kya badla

| Kaam | Detail |
|---|---|
| **8 tools poore hata diye** | 🎙️ Actors Voice Studio · 🧮 EMI Calc · 🎂 Age Calculator · 🔐 Password Generator · 🔎 Web Search · 💰 UPI QR · 🕵️ Photo Info + Fake Detect · 🪔 Rahu Kaal/Panchang — **menu, button, code, tutorial: sab se gayab** |
| **Bot language** | User-facing prompts Hinglish (Hindi Latin script) me rakhe gaye hain. |
| **Number / Vehicle** | Number Info me sirf safe metadata; live owner/challan lookup default me disabled, official links available. |
| **IMEI** | Local validation ke baad sirf pehle 8 TAC digits API ko jaate hain; full specs ki guarantee nahi. |
| **v42** | ✂️ Chhote prompts ka historical update; current user-facing copy Hinglish me hai. |
| **v43 naya tool** | 🎬 Clip Maker (video → 4-7 clips) — premium tool #10 |
| **Bug fix** | tutorial me "voice" video ka button (tool hi nahi tha) · admin plan select par double line · purane imports |
| **Test** | sab suites green: 51/51 flows, 54/54 admin, 46/46 video, 81/81 credits, 80/80 naye tools, 93/93 live checks, 68 engines audit |

📌 Poora changelog: **`v39-KYA-BADLA.md`**

---

## 2️⃣ Deploy (Render) — safe steps

1. Sahi GitHub repo me code ka push authorized maintainer/agent karega. **GitHub token chat, README ya terminal me paste mat karein**; pehle share hue tokens ko revoke karein.
2. **Render → `utility-duniya-bot` service → Manual Deploy → `Clear build cache & deploy`** dabayein.
3. Deploy ke baad `/health` par JSON me `service: utility-duniya-bot` verify karein. Sirf static HTML ka HTTP 200 Telegram bot chalu hone ka proof nahi.
4. Telegram me `/start` aur actual bot feature test karein; live verify hone tak deploy ko complete na maanein.

**Render par ye Environment Variables** (Environment tab):
```
BOT_TOKEN   = BotFather ka token
ADMIN_ID    = tumhari Telegram user ID (owner — unlimited)
UPI_ID      = tumhara@upi
UPI_NAME    = Utility Duniya
```
(Baaki optional: `FORCE_CHANNEL`, `FORCE_CHANNEL_LINK`, `REFER_NEED=5`, `FREE_CREDITS=25`, `TUTORIAL_URL`. Personal leaked-record lookup permanently disabled hai; vehicle live lookup ke liye authorized provider flag alag se zaroori hai.)

---

## 3️⃣ Test (5 minute)

Telegram me ye 6 cheezein check karo:

| # | Karo | Kya hona chahiye |
|---|---|---|
| 1 | `/start` | Menu aaye — **EMI/Age/Password/Web Search/UPI QR/Voice/Panchang ke button NAHI** |
| 2 | 📱 NUMBER INFO kholo | Prompt Hinglish me aaye; sirf carrier/circle/type metadata dikhaye, personal records nahi |
| 3 | 🏦 BANK STATEMENT PDF → EXCEL | PDF bhejo → Excel/CSV file + summary aaye |
| 4 | ⚡ MEDIA STUDIO → 🎬 Status Video | photo → song → text → 9:16 video ban ke aaye |
| 5 | 📜 DOCUMENT SUITE → kirayanama | ek-ek field poochhe (**House owner name**, **Rent (₹ per month)** — English) → PDF |
| 6 | 💎 `/premium` | plan chuno → UTR maange → screenshot maange (3 step) |

Aur computer par (agar chahiye):
```bash
cd /home/user/UPLOAD-KARO && python3 _audit_tools_v39.py
```
→ 68 engines ka result: sab ✅ aana chahiye.

---

## 4️⃣ Credits + VIP

- Naya user: **25 credits free** (ek hi baar).
- **Premium (7):** Video Downloader · Number Info · Channel Cloner · Private Setup · Bank PDF→Excel · Document Suite · Media Studio — **1 use = 1 credit**.
- **Baaki 23 tools FREE** — koi credit nahi.
- **VIP / Owner = unlimited.**
- VIP bechne ka tarika: `/premium` → plan → QR → UTR + screenshot → `/admin` me **Approve**.
- Bina payment VIP: `/admin` → plan select → `/activate <user_id>` (ya `/activate <user_id> 90`).
- Refer: **5 log = 30 din free VIP**.

---

## 5️⃣ Aage kya (v40 ideas — `EARNING-TOOLS-V39.md` me poora)

Chhupe, earning wale tools (koi AI nahi, market me jaldi nahi milte):

| # | Tool | Kyun paisa aayega |
|---|---|---|
| 1 | 🧾 **Dukaan Bill Pack** (GST bill + quotation + cash memo + auto number) | har dukaan roz use karegi → VIP renewal |
| 2 | 📸 **Exam Form Photo Pack** (SSC/Railway/BPSC exact spec) | cyber cafe / CSC wale har form par kamate hain |
| 3 | 📒 **Udhaar Khata** + reminder | kirana/medical/tailor ka roz ka hisaab |
| 4 | 🏛️ **Court Case Finder** (CNR) | vakil ₹200-500 lete hain sirf "agli tareekh" ke liye |
| 5 | 🔧 **Repair Job Card** (mobile/laptop/AC) | repair shop ka parcha — ab PDF me |

Iske baad: 📊 Labour Wage Bill · 🏫 Coaching Pack · 🏦 Vehicle/Challan Guide · 🌾 Kisan Pack · 🧾 GSTIN/HSN.

---

## ⚠️ 3 baatein yaad rakho

1. **Koi AI tool nahi** — jo bhi bana hai, sab offline/deterministic hai (Render 512MB me chalega).
2. **Copyright:** downloader public links ke liye hai — kisi ka paid content bechna galat hai.
3. **Privacy:** number holder ka leaked naam, family, linked numbers, address ya ID search/return nahi hota; sirf safe phone metadata dikhte hain. Vehicle/live challan ke liye authorized source chahiye.
