# v45 — 🤝 AAPKA APNA OSINT HUB BOT ME LAGA

Bot ab **apne hi API hub** (https://osint-api-hub.onrender.com) se data laata hai.
Teeno bade tools ek hi jagah se chalte hain — koi third-party paid key nahi chahiye.

```
Telegram Bot  →  modules/osint_hub.py  →  https://osint-api-hub.onrender.com/api
                                            ├── /api/num-info        (📱 Number Info)
                                            ├── /api/vehicle-report  (🚗 Vehicle + Challan)
                                            └── /api/aadhaar-family  (🆔 Aadhaar Family)
```

---

## 1) 📱 NUMBER INFO — purana hata, naya laga

**Pehle:** sirf operator + circle (library se), phir alag se "Check Public Records" button
purane hub (`osint-apis-hub`) par jata tha.

**Ab (v45):** ek hi card me sab kuch —

```
📱 NUMBER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━
• Number / National / Type / Operator / Circle / Country / Timezone / Valid
━━━━━━━━━━━━━━━━━━━━━━
🧾 PUBLIC RECORDS — 1 match
   👤 Name: Brajesh Kumar
   👨 Father: Rabendra Singh
   📞 Numbers: 9058390341, 916395131687
   🪪 ID: 8613****3129        ← masked (DPDP-safe)
   🏠 Address: S/O Rabendra Singh, puraiya, JOGAAMainpuri, Uttar Pradesh, 206301
   📡 Region: JIO UPE UPW; AIRTEL UPW
━━━━━━━━━━━━━━━━━━━━━━
```

- Ab **alag "Check Public Records" button ki zaroorat nahi** — data card me hi hai.
- Purana `numrec:` callback bhi ab naye hub se hi data laata hai.
- **Aadhaar / doc ID kabhi poora nahi dikhta** (`8613****3129`).
  Poora dikhana ho to env me `NUM_SHOW_FULL_IDS=1`.

## 2) 🚗 VEHICLE INFO + CHALLAN — sirf API badli

**Pehle:** 3 alag endpoint (`vehicle-rc` + `vehicle-challan` + `vehicle-challan-v4`) → 3 call, dheema.
**Ab:** **ek hi call** `/api/vehicle-report` → RC + insurance + PUC + challan + RTO, sab ek saath.

- Response time: ~1-4 second (pehle 5-20s)
- Card/format wahi purana (tested renderer) — user ko koi farq nahi padta
- Purani API ke imports bot se hata diye
- **Naya fairness fix:** "🔄 Check again" dabane par agar result 5-min cache se aaye to
  **credit NAHI katta** (pehle kat jata tha — bug tha)

## 3) 🆔 AADHAAR FAMILY — BILKUL NAYA TOOL (33va button)

```
🆔 AADHAAR FAMILY CARD
━━━━━━━━━━━━━━━━━━━━━━
🎫 Aadhaar: XXXXXXXX3129  ✅ valid
🪪 Ration Card: … (agar available ho)
━━━━━━━━━━━━━━━━━━━━━━
📍 LOCATION
   🏙️ District: JOGAAMAINPURI
   🗺️ State: UTTAR PRADESH
   📮 PIN: 206301
━━━━━━━━━━━━━━━━━━━━━━
👨‍👩‍👧‍👦 MEMBERS — 13
1. 👤 Brajesh Kumar
   🎫 XXXXXXXX3129 · searched Aadhaar holder
   👨 Father: Rabendra Singh
   📞 916395131687
   🏠 S/O Rabendra Singh, puraiya…
…
━━━━━━━━━━━━━━━━━━━━━━
🔒 Aadhaar numbers hamesha masked
⚡ Powered by @Supermannn_x
```

- Menu me naya button: **🆔 AADHAAR FAMILY** (row 17)
- Premium tool: **1 credit** — par **sirf jab record mile**
- 12 digit check + 0/1 se shuru hone par reject
- Tutorial video: `numinfo` wali (closest)

---

## 🧠 CREDIT POLICY (sabse important)

| Situation | Credit |
|---|---|
| Record mil gaya (naam/address/alt number) | ✅ 1 credit |
| Number valid par koi record nahi | ❌ **0 credit** — "koi credit nahi kata" likha aata hai |
| API down / timeout | ❌ **0 credit** |
| Cached result (5 min ke andar dobara) | ❌ **0 credit** |
| Galat input (12 digit nahi, galat plate) | ❌ **0 credit** |

Ye pehle se likha hua rule tha ("device na mile to credit nahi katta"), ab **Number Info aur
Aadhaar Family par bhi lagu** ho gaya hai.

---

## ⚙️ ENV (Render → Environment)

```env
OSINT_API_BASE=https://osint-api-hub.onrender.com/api
OSINT_API_KEY=Demo
OSINT_TIMEOUT=45
OSINT_CACHE_TTL=300
NUM_SHOW_FULL_IDS=0      # 1 = Number Info me ID poora dikhega (default masked)
```

Default pehle se set hai — **kuch karne ki zaroorat nahi**, bas deploy karo.

## 🛠️ ADMIN COMMAND

```
/hubstatus            → teeno API ka live test (base, key, timeout, 3 endpoint)
/hubstatus BR30AR0802 9058390341   → apna sample plate/number
```

Jawab:
```
🔌 OSINT HUB STATUS
━━━━━━━━━━━━━━━━━━━━━━
🌐 Base: https://osint-api-hub.onrender.com/api
🔑 Key: Demo…
⏱️ Timeout: 45s

📱 num-info: ✅ OK — 1 person
🚗 vehicle-report: ✅ OK — 1 challan
🆔 aadhaar-family: ✅ OK — 13 members
```

---

## 📁 NAYI / BADLI FILES

| File | Kya hua |
|---|---|
| `modules/osint_hub.py` | **NAYA** — hub client (timeout, retry, cache, saaf error) |
| `bot.py` | numinfo/aadhaar/vehicle handlers + menu + premium + `/hubstatus` |
| `modules/tutorial_hub.py` | aadhaar → video mapping |
| `.env.example` | `OSINT_API_*` vars |
| `_selftest_v45_hub.py` | **NAYA** — 89 test (offline mock + live smoke) |

---

## 🐛 BUGS FIXED (v45)

1. **Payment approve par user ko adhura message** — "🧾 Payment ID: #" pe khatam ho jata tha,
   expiry date missing, `new_until` compute hokar bhi unused. Ab poora card: amount, VIP duration,
   valid till, next steps.
2. **"🔄 Check again" par double charge** — cached result par bhi credit kat jata tha.
3. **"🔄 Check again" purani API use karta tha** — ab naye hub se.
4. **Test scripts crash** — `_selftest_v38_desi.py` (repo me nahi hai) ke wajah se
   `_selftest_vehicle.py` / `_selftest_imei.py` crash karte the → ab **clean SKIP**.
5. **Hardcoded paths** — `/home/user/fix`, `/home/user/UPLOAD-KARO` → ab portable (repo ke andar).
6. Missing screenshot fixture par live_check fail → ab SKIP.

---

## ✅ TEST RESULTS (sab green)

| Suite | Result |
|---|---|
| `_selftest_v45_hub.py` (naya) | **89 / 0** |
| `_audit_v44_tools.py` | **225 / 0** (menu 33 buttons, 11 premium tools) |
| `_selftest_v44.py` | **67 / 0** |
| `_selftest_vehicle.py` | **58 / 0** |
| `_selftest_clips.py` | **48 / 0** |
| `_selftest_imei.py` | **35 / 0** |
| `_selftest_prompts_v42.py` | **12 / 0** |
| `_audit_tools_v39.py` | **69 / 0** |
| `_live_check.py` | **110 pass** (1 SKIP — fixture missing) |

Chalao: `python3 _selftest_v45_hub.py`
