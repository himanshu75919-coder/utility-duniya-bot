# 📲 v41 — IMEI / PHONE DETAILS + VEHICLE (asli API hub se)

**Is version me 2 kaam hue:**

1. 🚗 **VEHICLE INFO + CHALLAN** ab aapke diye **asli API hub** se chalta hai — ek hi plate bhejo,
   teen endpoint se data aata hai aur sab **merge** ho jaata hai:
   - `/api/vehicle-rc` → RC record (dates, insurance, PUC, owner, RTO, vehicle details)
   - `/api/vehicle-challan` → challan list (number, amount, date, offence, place, court)
   - `/api/vehicle-challan-v4` → summary (total challan + total amount)
2. 📲 **NAYA TOOL — IMEI / PHONE DETAILS**: 15 digit IMEI bhejo → **brand, model, device photo +
   poori spec sheet** (display, chipset, RAM/storage, camera, battery, network) + ek **`.json` copy file**
   (Telegram me "COPY CODE" style) — bilkul jaisa aapne screenshot me dikhaya.

---

## 1️⃣ Sabse pehle: key lagao (1 minute ka kaam)

Daata abhi **demo key** `Demo` par chal raha hai (public demo key). Ye kaam karegi, par:

> ⚠️ **Demo key par kisi bhi time limit / band ho sakti hai.** Apna key le lo:
> hub wale se apni key maango (ya hub ke hisaab se apna account banwa lo) → uske baad Render me daal do.

Render → service → **Environment** → ye daalo → **Save** → **Manual Deploy (Clear build cache)**:

| Variable | Kya daalna hai | Default (agar khaali chhodo) |
|---|---|---|
| `VEHICLE_API_BASE` | hub ka base URL | `https://osint-apis-hub.onrender.com/api` |
| `VEHICLE_API_KEY` | aapki key | `Demo` |
| `IMEI_API_BASE` | IMEI wali API ka base | `VEHICLE_API_BASE` / default hub |
| `IMEI_API_KEY` | IMEI key | `VEHICLE_API_KEY` / `Demo` |
| `VEHICLE_TIMEOUT` / `IMEI_TIMEOUT` | seconds | `25` |

> **Note:** kuch purane `VEHICLE_API_URL` (single endpoint) wale variable bhi kaam karte hain — agar wahi set ho
> aur `VEHICLE_API_BASE` khaali ho, to bot usi host ka `/api` nikaal leta hai. Kuch bhi toota nahi hai.

### Test kaise karo (Telegram me, admin se)
- **`/vehstatus`** → vehicle API live test (sample plate par RC + challan count + report ki jhalak)
- **`/imeistatus`** → IMEI API live test (device naam, spec sections, JSON file size, photo ✅/❌)

Dono commands **sirf admin** ke liye hain. Kuch galat ho to bot khud bata dega ki kaun sa variable missing hai.

---

## 2️⃣ 📲 IMEI tool — user ko kya milta hai

User **📲 IMEI / PHONE DETAILS** button dabata hai → bot aisa maangta hai:

```
📲 IMEI / PHONE DETAILS
━━━━━━━━━━━━━━━━━━━━━━
Send the 15 digit IMEI of any phone or tablet.
📍 Where to find it: dial *#06# on that phone — the IMEI shows on the screen
(it is also printed on the box or the bill).
✅ You get: brand, model, device photo + full spec sheet (display, chipset, RAM/storage,
camera, battery, network) + a .json copy file.
⚠️ Use it only for your own device or a phone you are buying.
━━━━━━━━━━━━━━━━━━━━━━
🔢 Now send the 15 digit IMEI (example 353010111111110):
```

IMEI bhejne par **3 cheezein** aati hain:

1. **Photo** — device ki image + caption:
   `📲 Apple iPhone 12 mini` + Brand + IMEI + top spec jhalak
2. **Poora spec card** — section-wise: Basic Info, Dimensions, Display, Network, Battery, Camera…
3. **`.json` file** — `Apple_iPhone_12_mini_specs.json` (Telegram me **COPY CODE** button) — register/shop
   log, WhatsApp, kisi bhi jagah paste karne ke liye ready.

**Safety / rules jo bot khud lagata hai:**
- 15 digit + **Luhn check** — galat IMEI par ek bhi API call nahi jaati ("IMEI must be exactly 15 digits"
  / "This IMEI is not valid (check digit failed)").
- Device na mile → saaf message + **official imei.info link** — **credit nahi katta**.
- Koi API/network problem → "plz try later" card — **credit nahi katta**.
- 1 successful check = **1 credit**, VIP/owner = unlimited (jaise baaki premium tools).
- `.gif` photo URLs Telegram par fail hote hain → bot us case me sirf text card bhejta hai (crash nahi).

**IMEI kahan se milega:** phone me `*#06#` dial karo, ya box / bill / phone settings (About) me likha hota hai.

---

## 3️⃣ 🚗 Vehicle tool me kya badla (v40 → v41)

| Pehle (v40) | Ab (v41) |
|---|---|
| Ek hi custom endpoint (`VEHICLE_API_URL`) | **3 hub endpoint**: `vehicle-rc` + `vehicle-challan` + `vehicle-challan-v4` (parallel me, phir merge) |
| Challan list | Challan list **+ v4 summary** (total challan, total amount — portal wala number) |
| — | Purana custom endpoint ab bhi optional hai (jo khaali ho, custom se bhar jaata hai) |
| — | **Khaali jawab par credit nahi katta:** hub kuch numbers par sirf RTO office info deta hai (RC/challan nahi) → bot purana **free RTO card** dikhata hai, 1 credit bhi nahi katta |
| — | Card me API ka text **HTML-safe** hai (`&`, `<` par Telegram error nahi aata) |
| — | 5 minute ka cache (same plate dobara → API call bachti hai) |

**Sample (asli API, HR26EV0001):** TOYOTA KIRLOSKAR… FORTUNER LEGENDER (AT), DIESEL, 124.6 CC,
Owner `E****H Y***V` (masked), RTO Haryana Head Office CHD, challan **20 found — ⏳ Pending 20 — ₹45,500**.

Privacy default wahi hai: owner naam masked, chassis/engine/PUC/insurance number masked, accused naam masked.
Poora dikhana ho: `VEHICLE_SHOW_MOBILE=1` · `VEHICLE_SHOW_IDS=1` · `VEHICLE_SHOW_OWNER=1`.

---

## 4️⃣ Tutorial video (zaroori)

IMEI tool ka 🎬 video button **abhi Number Info wali video** par point karta hai (bot me caption sahi
"📲 IMEI / PHONE DETAILS — TUTORIAL" dikhta hai). Jab aap **`imei.mp4`** banakar repo ke
`tutorial_videos/` folder me daal dena, tab `modules/tutorial_hub.py` me ek line badalni hai:

```python
# "imei": "numinfo",     ← ye hata kar
"imei": "imei",           ← ye kar dena (video file imei.mp4)
```

---

## 5️⃣ Kabhi kuch na chale to 👍

1. `/vehstatus` ya `/imeistatus` chalao — dono batate hain API live hai ya nahi.
2. API band ho to bot **crash nahi karta** — vehicle me purana free RTO card, IMEI me help card + imei.info link.
3. Credits ka hisaab: sirf **saflik report** par 1 credit. Fail / na-mila / API-down = **0 credit**.
4. Docs ke baaki files: `README.md` (setup) · `1-PADHO-PEHLE.md` (5 minute) · `TUTORIAL.md` (user ke liye).
