# 🚗 RC + CHALLAN — RAPIDAPI SE API LENE KA POORA TARIKA (step by step)

> **Kitna paisa?** ₹0. RapidAPI par is API ka **BASIC plan $0.00/month** hai —
> **card, UPI, kuch bhi nahi lagta.** Login ke liye bas Google/Gmail chahiye.
> **Kitna time?** ~10 minute.
> **Baad me kya?** Bot me `BR30AR0802` bhejo → poora VEHICLE INFO REPORT card bhara aayega.

---

# ✅ v71.5 UPDATE — API CHALU HO GAYI (ye hamesha yaad rakhna)

**Is API ka asli endpoint — ROOT par hai (koi `/path` nahi):**

```
POST https://vehicle-rc-information.p.rapidapi.com/
Body: {"VehicleNumber": "PB65AM0008"}
Headers: X-RapidAPI-Key: <aapki key>
         X-RapidAPI-Host: vehicle-rc-information.p.rapidapi.com
```

- **Basic endpoint** = yahi root URL, body me `VehicleNumber` (capital V, capital N)
- **v2 [Advance]** = alag endpoint (body `vehicle_number`) — abhi Basic chalu hai
- **Bot ko kuch samjhane ki zaroorat nahi** 🔥 — v71.5 se bot khud:
  1. **root URL pehle** try karta hai (1 second me jawab aata hai), phir baaki path candidates
  2. Ghalat body key khud adjust karta hai
  3. Jo URL chala wo **yaad** rakhta hai

**Render me bas 2 line (bas itna hi):**

```
VEHICLE_PROVIDER_URL = https://vehicle-rc-information.p.rapidapi.com
VEHICLE_PROVIDER_KEY = <aapki RapidAPI key>
```

> 💡 Tip: URL me `/VehicleInformation` **na lagao** — ye API root par chalti hai.
> Sirf host daalo, bacha hua kaam bot karega (2026-10-07 ko verified: `PB65AM0008` → 1.0s me poora card ✅)

---

> ⚠️ **Agar bot bole "Is gaadi ka record sarkari database me nahi mila"** — matlab aapka
> setup **bilkul theek hai**, bas wo number API ke database me nahi hai (jaise demo number
> `BR30AR0802`). Asli registered gaadi ka number try karo — turant data aayega.

---

# 📋 Step 1 — RapidAPI par jao aur Google se sign up karo

👉 **https://rapidapi.com/auth/sign-up**

- **"Sign up with Google"** / **"Continue with Google"** dabao
- Apna Gmail chuno → bas, ho gaya (koi card, koi OTP nahi)

*(Pehle se account ho to seedha login: https://rapidapi.com/auth/sign-in)*

---

# 📋 Step 2 — Yehi API kholo (Vehicle RC Information)

👉 **https://rapidapi.com/fatehbrar92/api/vehicle-rc-information**

Ye page khulega: **"Vehicle RC Information"** — 3866+ log ise use kar rahe hain.

---

# 📋 Step 3 — FREE plan le lo ("Subscribe to Test")

Us page par:

1. **Right side** me ya page ke upar **`Subscribe to Test`** / **`Pricing`** button dabao
2. Plan list aayegi — **`BASIC`** wala chuno jisme **$0.00 / month** likha hai
3. **`Subscribe`** / **`Subscribe to Test`** dabao
4. Kuch poochhe to **`Continue`** / **`OK`** dabao

✅ Bas — ab aapki API **free me chalu** ho gayi (mahine me kuch hundred calls milti hain).

> ⚠️ **Paise wale plan (PRO / ULTRA) kabhi na dabao** — unme card maangta hai. BASIC hi kaafi hai.

---

# 📋 Step 4 — Endpoint ka URL (aapke screenshot ke hisaab se)

Aap playground me **`POST Vehicle Information [Basic]`** par ho — us page par:

1. **`Endpoints`** (left side) me do option hain:
   - `POST Vehicle Information [Basic]` ← **yehi free wala hai** ✅
   - `POST Vehicle Information v2 [Advance]` ← screenshot 2 wala (isme bhi `vehicle_number` body hai)
2. Playground me **neeche `Request` tab** dabao (Code snippet / Request / Response ke beech)
3. Wahan **poora URL** dikhega — aisa:
   ```
   https://vehicle-rc-information.p.rapidapi.com/VehicleInformation
   ```
   → **copy** kar lo

**✅ Achhi khabar (v71.4):** ab aap chaaho to **sirf host** bhi daal sakte ho —
```
VEHICLE_PROVIDER_URL = https://vehicle-rc-information.p.rapidapi.com
```
Bot **khud** sahi path (`/VehicleInformation`) dhoondh leta hai aur yaad rakh leta hai.
Aur **body ka key naam** bhi bot khud handle karta hai:
- Basic endpoint maangta hai: `{"VehicleNumber": "..."}` (capital V, capital N)
- v2 endpoint maangta hai: `{"vehicle_number": "..."}`
→ **dono** bot apne aap try karta hai. Aapko iski chinta nahi.

---

# 📋 Step 4-B (purana tarika) — Apna Endpoint URL copy karo ⭐

Usi page par upar **`Endpoints`** tab dabao:

1. Wahan 1-2 endpoint dikhenge (jaise **POST** ``/vehicle/rc`` ya ``/rc`` — jo bhi likha ho)
2. Us endpoint par **click** karo
3. Right side me **poora URL** dikhega — aisa:
   ```
   https://vehicle-rc-information.p.rapidapi.com/vehicle/rc
   ```
   (aapke page par jo bhi path ho, **wahi poora URL copy karo** — usme `/vehicle/rc` ya
   jo bhi ho, wo hissa zaroori hai)
4. Ye URL phone ke **Notes** me paste kar do — Step 6 me chahiye

💡 *Tip: isi page par right side me `Test Endpoint` button hota hai — usse aap wahi ek
number (`BR01AB1234` — demo) bhej kar dekh sakte ho ki API jawab deti hai ya nahi. Wo
test free hai aur key lagne se pehle hi pata chal jayega.*

---

# 📋 Step 5 — Apni KEY copy karo (aapke screenshot 3 se)

Aap `rapidapi.com/developer/apps` par ho — bilkul sahi jagah! Wahan:

1. Table me **`default-application_12176190`** par click karo (blue link — App Name wala)
   *(ya left sidebar me neeche `default-application_12176190` par click karo)*
2. App page khulega → **`Security`** tab dabao
   *(aapke screenshot me table ki aakhri column me 🛡️ **Authorization** icon bhi hai —
   wahi bhi yahi kholta hai)*
3. Wahan **`Application Key`** dikhegi — lambi line, aisi:
   `a1b2c3d4e5f6...` → **`copy`** dabao
4. Iske saath **`Application Id`** bhi likha hoga — uski zaroorat NAHI hai, sirf **Key** chahiye

**Sabse aasan tarika (aapke screenshot 1 se):** playground me hi, **`X-RapidAPI-Key`**
likha hota hai (upar ya `Authorization` tab me) — wahi copy kar lo. Wo bhi same key hai.

---

# 📋 Step 5-B (purana) — KEY kahan milti hai

**Tarika A (sabse aasan):** Endpoints tab me hi, **`X-RapidAPI-Key`** likha hota hai
(pata nahi chale to `Show` / 👁️ dabao) → **copy** kar lo. Ye lambi line hai, aisi:
`a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6`

**Tarika B:** kholo 👉 **https://rapidapi.com/developer/apps**
→ **My Apps** → **Default Application** → **Security** → **Application Key** → copy.

Ye key phone ke **Notes** me paste kar do.

> 🔒 **Ye key kisi ko na do, screenshot me na dikhao, GitHub par kabhi na daalo.**
> Kaam khatam hone ke baad chaaho to **Security** tab se rotate kar sakte ho.

---

# 📋 Step 6 — Render me 2 line daalo (kaam 2 minute ka)

1. Kholo 👉 **https://dashboard.render.com**
2. Apne bot **`utility-duniya-bot`** par click karo
3. Left me **`Environment`** tab dabao
4. **`Add Environment Variable`** dabao — **do baar**, aur ye daalo:

| Key (naam) | Value (jo aapne copy kiya) |
|---|---|
| `VEHICLE_PROVIDER_URL` | `https://vehicle-rc-information.p.rapidapi.com/vehicle/rc` ← *(Step 4 wala apna poora URL)* |
| `VEHICLE_PROVIDER_KEY` | `aapki X-RapidAPI-Key` ← *(Step 5 wali lambi line)* |

5. **`Save Changes`** dabao
6. Upar **`Manual Deploy`** → **`Clear build cache & deploy`** → 2-4 minute ruko

**Bas ho gaya!** 🎉 Baaki sab bot khud karta hai — headers, GET/POST, sab.

---

# 📋 Step 7 — Test karo

1. Telegram me bot ko likho: **`/rcsetup`** → wahan **`Provider status: ✅ LAGI HUI HAI`** aana chahiye
2. Phir bhejo: **`BR30AR0802`** (ya koi bhi number plate)
3. Poora card bhara aayega:

```
╔════════════════════════════╗
🚘 𝐕𝐄𝐇𝐈𝐂𝐋𝐄 𝐈𝐍𝐅𝐎 𝐑𝐄𝐏𝐎𝐑𝐓
╚════════════════════════════╝

🔢 Number: BR30AR0802
├ 👤 Owner: ...
├ 🚘 Model: HONDA SHINE
├ ⛽ Fuel: PETROL
├ 🏙️ City: Sitamarhi
📞 Phone: 9199xxxxxx
📍 RTO: BIHAR Sitamarhi BR-30
├ 🎨 Color : BLACK+GREY STRIPES
├ ⚙️ Engine : 99.0 CC
├ 📅 Reg Date : 29-08-2025
├ 🛡️ Insurance : GO DIGIT · 27-07-2030
├ 🌫️ PUC : 28-08-2026
└ 🏦 Finance : CREDIT WISE CAPITAL PVT LTD
```

---

# 🆘 KUCH GALAT HO TO (troubleshooting)

| Bot kya kehta hai | Matlab | Kya karo |
|---|---|---|
| `Provider ne 404 diya (endpoint ka pata galat hai)` | URL me path galat/missing | Step 4 dobara — **Endpoints tab se poora URL** copy karo |
| `Provider ne key nahi maani (401/403)` | Key galat ya adhoori copy hui | Step 5 — poori key dobara copy (aakhir tak) |
| `Provider ka limit khatam (429)` | Free quota is mahine khatam | Agle mahine apne aap reset, ya koi doosri free API (neeche) |
| `Provider tak baat nahi pahunchi` | Internet/Render issue | 2 minute baad dobara try karo |
| Card me `⚠️ N/A` hi aa raha | Key lag hi nahi paayi | Render → Environment me naam **bilkul** same hai? (`VEHICLE_PROVIDER_URL`, `VEHICLE_PROVIDER_KEY`) |

---

# 🆓 AGAR YE API KAAM NA KARE (doosri free) 

RapidAPI par hi search karo 👉 **https://rapidapi.com/search/vehicle%20rc**

Filters: **Pricing → Free** (left side). Koi bhi API khol kar wahi Step 3-5 karo —
bot **kisi bhi** provider ke JSON ko khud samajh leta hai, URL/key badalne se kaam ho jayega.

---

# ℹ️ Ek zaroori baat (jhooth nahi)

- Free plan me **mahine me seemit calls** milti hain (kuch hundred). Isliye bot ka
  jawab **15 minute tak yaad rakhta hai** — ek hi gaadi dobara poochi to API call nahi hoti
  (quota bachta hai).
- Ye API **VAHAN ka licensed data** deti hai, isliye **legal** hai — captcha todne wale
  jugaad (jo bot band karwa dete hain) ki zaroorat nahi.
- Hub (osint-api-hub) me bhi lagana ho to wahi 2 line **hub ke** Render → Environment me
  daal do — phir hub ke saare users ko bhi live data milega.
