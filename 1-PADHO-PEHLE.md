---
## 🆕 v45 — Aapka apna OSINT HUB jud gaya (Number / Vehicle / Aadhaar Family)

| Tool | Kya badla |
|---|---|
| 📱 **Number Info** | Ab naam, father, address, linked numbers, ID — **ek hi card** me (apne hub se) |
| 🚗 **Vehicle + Challan** | Ab **ek hi API call** `/api/vehicle-report` — RC + insurance + PUC + challan (~1-4s) |
| 🆔 **Aadhaar Family** | **NAYA TOOL** — 12 digit Aadhaar se family card (members, district, masked) |

- Admin: `/hubstatus` — teeno API ka live test
- **Credit sirf tab katta hai jab record mile** (nahi to free)
- Poora detail: **[v45-OSINT-HUB.md](v45-OSINT-HUB.md)**

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

## 0️⃣ (purana) v42 — CHHOTE PROMPTS (kam instructions)

Har tool khulne par ab sirf ye dikhta hai: **TITLE → 1 line → 📌 Example → "Now send …"**.
Lambi bullet list hata di (tutorial video har tool ke neeche hai). Terabox par **ad-free** likha hai +
"server reject kare to link dobara bhejo". Number Info me example `9876543210` set hai.
Poora before/after: **`v42-CHHOTE-PROMPTS.md`**.

## 0️⃣ (purana) v41 — IMEI / PHONE DETAILS + asli VEHICLE hub

**📲 IMEI / PHONE DETAILS:** 15 digit IMEI bhejo (phone me `*#06#`) → brand, model, **device photo** +
poori **spec sheet** (display, chipset, camera, battery, network) + **`.json` copy file**.
Galat IMEI / na mila / API band = **credit nahi katta**. Guide: **`v41-API-HUB.md`**.

**🚗 VEHICLE INFO + CHALLAN:** ab aapke **asli API hub** se — `vehicle-rc` + `vehicle-challan` + `vehicle-challan-v4`
teeno merge hote hain (challan list + total amount summary). Khaali plate par credit nahi katta.
Key Render me daalni hai (`VEHICLE_API_KEY` / `IMEI_API_KEY`) — **default abhi `Demo` hai**.

## 0️⃣ (purana) v40 — VEHICLE INFO + CHALLAN

Number plate bhejo → poora **RC record + saare challan** (pending/paid, amount, date, offence) — jaise aapne example dikhaya.
- **API lagani hai:** Render → Environment me `VEHICLE_API_URL` + `VEHICLE_API_KEY` (+ `VEHICLE_API_PARAM` agar naam alag ho) →
  phir `/vehstatus` se test karo. Poora guide: **`v40-VEHICLE-CHALLAN.md`**.
- **1 credit** per report · VIP = unlimited · API band ho to purana free RTO card chalta rehta hai.
- Owner mobile / chassis / engine **masked** (privacy) — chaho to env se poora on kar sakte ho.

---

## 1️⃣ v39 me kya badla

| Kaam | Detail |
|---|---|
| **8 tools poore hata diye** | 🎙️ Actors Voice Studio · 🧮 EMI Calc · 🎂 Age Calculator · 🔐 Password Generator · 🔎 Web Search · 💰 UPI QR · 🕵️ Photo Info + Fake Detect · 🪔 Rahu Kaal/Panchang — **menu, button, code, tutorial: sab se gayab** |
| **Text simple English** | Pehle Hindi me tha ("Ab number bhejein", "CREDITS KHATAM") — ab **simple English** ("Now send the number:", "ALL CREDITS USED"). Lambe instructions bhi chhote kar diye |
| **v40 tool** | 🚗 Vehicle Info + Challan (RC + challan report, live API) — premium tool #8 |
| **v41 naya tool** | 📲 IMEI / Phone Details (device + full spec sheet + .json) — premium tool #9 · vehicle ab asli hub API par |
| **v42** | ✂️ Chhote prompts — har tool me TITLE + 1 line + 📌 Example + "Now send…" |
| **v43 naya tool** | 🎬 Clip Maker (video → 4-7 clips) — premium tool #10 |
| **Bug fix** | tutorial me "voice" video ka button (tool hi nahi tha) · admin plan select par double line · purane imports |
| **Test** | sab suites green: 51/51 flows, 54/54 admin, 46/46 video, 81/81 credits, 80/80 naye tools, 93/93 live checks, 68 engines audit |

📌 Poora changelog: **`v39-KYA-BADLA.md`**

---

## 2️⃣ Deploy (Render) — 4 step

1. **Push karo:**
   ```bash
   GITHUB_TOKEN=ghp_xxxxxxx bash /home/user/push_v39_ready.sh
   ```
   (Token GitHub → Settings → Developer settings → Tokens me banao; **ek token sirf ek baar** — jo purane use ho chuke hain unhe **revoke** kar dena.)
2. **Render → apni service → Manual Deploy → "Clear build cache & deploy"** dabao.
3. 2-3 minute ruko. Log me `Bot running...` dikhe to chalu ho gaya.
4. Telegram me `/start` → naya menu. `/premium` → VIP plans. `/admin` → admin panel.

**Render par ye Environment Variables** (Environment tab):
```
BOT_TOKEN   = BotFather ka token
ADMIN_ID    = tumhari Telegram user ID (owner — unlimited)
UPI_ID      = tumhara@upi
UPI_NAME    = Utility Duniya
```
(Baaki optional: `FORCE_CHANNEL`, `FORCE_CHANNEL_LINK`, `REFER_NEED=5`, `FREE_CREDITS=25`, `TUTORIAL_URL`, `NUM_LEAK_ENABLED=off`.)

---

## 3️⃣ Test (5 minute)

Telegram me ye 6 cheezein check karo:

| # | Karo | Kya hona chahiye |
|---|---|---|
| 1 | `/start` | Menu aaye — **EMI/Age/Password/Web Search/UPI QR/Voice/Panchang ke button NAHI** |
| 2 | 📱 NUMBER INFO kholo | Prompt **English** me: "Now send the 10 digit number" + credits line |
| 3 | 🏦 BANK STATEMENT PDF → EXCEL | PDF bhejo → Excel/CSV file + summary (English) |
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
3. **Legal line:** sarkar ka public data ✅ · kisi ki niji jaankari ❌ (public-records feature `NUM_LEAK_ENABLED=off` se band).
