# 🚗 v40 — VEHICLE INFO + CHALLAN REPORT (setup guide)

**Kya hai:** number plate bhejo → bot **poora RC record + saare challan** dikhata hai — exactly jaise aapne example me dikhaya
(vehicle details, RC papers, insurance, PUC, finance, aur challan: pending / paid / court, amount, date, offence).

---

## 1️⃣ Sabse pehle: API lagao (2 minute)

Render → apni service → **Environment** tab → ye 4 variable daalo → **Save** → **Manual Deploy (Clear build cache)**.

| Variable | Kya daalna hai | Example |
|---|---|---|
| `VEHICLE_API_URL` | API ka poora endpoint | `https://api.proportalx.com/rc` |
| `VEHICLE_API_KEY` | API key / token | `xxxx-xxxx` |
| `VEHICLE_API_PARAM` | plate kis field me jaata hai | `vehicle_number` (default) |
| `VEHICLE_API_METHOD` | `GET` (default) ya `POST` | `GET` |
| `VEHICLE_API_KEYNAME` | key ka naam (kuch API `api_key` maangti hain) | `key` (default) |

> **Bas.** Phir Telegram me admin se **`/vehstatus`** bhejo → bot live test karke dikha dega (RC fields + challan count). Set na ho to wo hi bata dega ki kya missing hai.

**API ka response jaisa hona chahiye (jo aapne bheja):**
```json
{ "API_Developer": "...", "Today_Used": 7,
  "result": { "vehicle_number": "BR30AR0802",
              "data": { "Registration Authority": "...", "Maker Name": "HONDA", "Model Name": "SHINE", ... },
              "challan": { "challan_details": [ { "challan_number": "...", "amount": "1000", "status": "PENDING", ... } ] } } }
```
Parser **flexible** hai — key ke naam thode alag hon (jaise `challan_list`, `challans`, `violation_details`),
ya RC flat ho, to bhi pakad leta hai. Challan ka status padhkar bot **⏳ PENDING / ✅ PAID / 🏛️ IN COURT** kar deta hai.

---

## 2️⃣ User ko kya dikhta hai

```
🚘 VEHICLE REPORT — BR30AR0802
━━━━━━━━━━━━━━━━━━━━━━
🚗 VEHICLE INFORMATION
• Number: BR30AR0802
• Maker / Model: HONDA SHINE
• Class: M-CYCLE/SCOOTER (Private)
• Fuel: PETROL • 99 cc
• Colour: BLACK+GREY STRIPES
• Body: FULL BODY • seats 2
• Emission: BHARAT STAGE VI
• Chassis: ME4HC1******849      ← masked
• Engine No: HC15EG******174    ← masked
━━━━━━━━━━━━━━━━━━━━━━
📋 RC / PAPERS
• RTO Office: BIHAR Sitamrahi BR-30
• Registration: 29-08-2025  →  valid till 28-08-2040
• Manufacture Year: 2025
• RC Status: ✅ ...
• Insurance: GO DIGIT GENERAL INSURANCE LTD (till 27-07-2030)
• PUC: ✅ till 28-08-2026
• Tax: LTT
• Finance / Bank: CREDIT WISE CAPITAL PVT LTD
• Owner Mobile: ••••••8422       ← masked
━━━━━━━━━━━━━━━━━━━━━━
🚨 CHALLANS — 2 found
• ⏳ Pending: 1 (₹1,000)
• ✅ Paid / disposed: 1
• 💰 Total amount (all): ₹1,500

🔹 #BR250023260716183506
   👤 Accused: R****T K***R
   💰 Amount: ₹1,000
   📅 Date: 16 Jul 2026
   ❌ Status: ⏳ PENDING
   🛑 Offence: DRIVING WITHOUT HELMET
━━━━━━━━━━━━━━━━━━━━━━
📶 Live data — ...   <i>Confirm once on the official Parivahan / e-Challan site before paying anything.</i>
```
Saath me 2 button: **🚨 e-Challan par check/pay (official)** aur **📄 VAHAN RC status**, aur **🔄 Check again**.

---

## 3️⃣ Credits & rules

| Cheez | Detail |
|---|---|
| Kitna credit | **1 credit** per successful live report (premium tool #8) |
| VIP / Owner | **unlimited** (credits nahi katte) |
| 0 credits | block + **free part** (RTO office, district + 5 official links) bhi milta hai |
| API down | free card + saaf reason ("live report not available") — user khaali haath nahi jaata |
| API set nahi | tool purane **RTO district + official links** wale kaam me chal jaata hai (crash nahi) |

**Privacy (default ON):**
- Owner ka mobile **mask** (`••••••8422`)
- Chassis / engine **mask** (`ME4HC1******849`)
- Challan me naam **mask** (`R****T K***R`)
- Poora dikhana ho to env: `VEHICLE_SHOW_MOBILE=1` aur `VEHICLE_SHOW_IDS=1` (aapki marzi — DPDP Act ke hisaab se default masked rakha hai).

---

## 4️⃣ Aapke sawaal ka jawaab (jo aapne kaha tha)

> "agar aisa esi types me nahi hoga to add nahi karna, aur API chahiye to main dunga"

- **Tool ban gaya hai — aapke diye hue exact sample JSON par test kiya gaya** (mock API se, 15/15 checks PASS).
- API **aapko hi lagni hai** — env me daalte hi live chalu, **bina code change**.
- Aapki API ka format thoda alag ho to bhi chalega (flexible parser) — agar bilkul hi alag ho to bata dena,
  1 line change karke theek kar dunga.

---

## 5️⃣ Test kese kiya (proof)

```bash
python3 _selftest_vehicle.py     # 15 checks: engine + card + bot flow + credits + VIP + fallback
```
- Mock API ne **aapka hi sample JSON** diya (HONDA SHINE, insurance, PUC, 2 challans: 1 PENDING + 1 PAID).
- Bot flow: prompt → plate → live report → 1 credit kata → "Check again" → 0 credits par block → VIP par unlimited → API band par fallback.
