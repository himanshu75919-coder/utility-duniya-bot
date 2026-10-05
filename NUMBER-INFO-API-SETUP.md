# 📱 NUMBER INFO — Apni API Render me kaise lagayein

> **Ye guide aapke liye hai (Himanshu bhai)** — koi coding nahi chahiye, sirf copy-paste.
> API key **sirf Render me** daalni hai — bot me, GitHub me, ya kisi chat me **kabhi nahi**.

---

## ❓ Pehle samjho: ye kya karta hai?

Abhi aapka **📱 Number Info** tool kaam kar raha hai, par data **offline database** se aata hai:

```
🏢 Operator: Airtel
📍 Circle / Region: ⚪ live API set nahi (sirf country pata hai)
📡 Data Source: ⚪ OFFLINE — phonenumbers public database se
```

API lagane ke baad:

```
🏢 Operator: Airtel
📍 Circle / Region: Bihar
🔎 Live Line Type: 📱 Mobile
📡 Data Source: 🟢 LIVE — aapki API se (312ms)
```

**Fayda:** asli circle/region, live operator, MNP (number port) status, aur exact line type.

---

## 🎯 STEP 1 — Free API lo (2 minute, koi card nahi chahiye)

### Option A: numverify (⭐ Sabse aasan — recommended)

1. Kholo 👉 **https://numverify.com**
2. **"Sign Up FREE"** dabao (email + password)
3. Email verify karo
4. Dashboard me **"Your API Access Key"** dikhega — wo lamba code **copy** karo
   *(aisa dikhta hai: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)*
5. **Free plan:** 100 lookups/month — bilkul free, credit card nahi chahiye

> ⚠️ 100/month kam lage to **Doosra free account** bana lo (dusri email se) — key badal ke
> use kar sakte ho. Ya STEP 6 me paid options dekho.

### Option B: abstractapi (bhi free)

1. Kholo 👉 **https://www.abstractapi.com/api/phone-validation-api**
2. Free signup → Dashboard → **API Key** copy karo
3. Free plan: 250 lookups/month

---

## 🎯 STEP 2 — Render me Environment Variables daalo

1. Kholo 👉 **https://dashboard.render.com**
2. **utility-duniya-bot** service par click karo (left side me)
3. Left menu me **`Environment`** par click karo
4. **`+ Add Environment Variable`** dabao
5. Ye **4 lines** ek-ek karke add karo 👇

### ⭐ numverify use kar rahe ho to — yahi 4 lines daalo:

| Key | Value |
|---|---|
| `NUMINFO_PROVIDER_URL` | `https://apilayer.net/api/validate` |
| `NUMINFO_PROVIDER_KEY` | *[apni copied key paste karo]* |
| `NUMINFO_PROVIDER_KEY_PARAM` | `access_key` |
| `NUMINFO_PROVIDER_PARAM` | `number` |

### ⭐ abstractapi use kar rahe ho to — yahi 4 lines daalo:

| Key | Value |
|---|---|
| `NUMINFO_PROVIDER_URL` | `https://phonevalidation.abstractapi.com/v1/` |
| `NUMINFO_PROVIDER_KEY` | *[apni copied key paste karo]* |
| `NUMINFO_PROVIDER_KEY_PARAM` | `api_key` |
| `NUMINFO_PROVIDER_PARAM` | `phone` |

6. **Save Changes** dabao
7. Render khud service restart karega — **1-2 minute** lagenge

---

## 🎯 STEP 3 — Telegram se hi check karo (1 second me pata chal jayega)

Bot me ye command bhejo (sirf **aap**, admin):

```
/numapi
```

**Agar lagi hai to aisa dikhega:**
```
📱 NUMBER INFO — PROVIDER
━━━━━━━━━━━━━━━━━━━━━━
🔌 Status: ✅ SET HAI
• URL: https://apilayer.net/api/validate
• Number param: number
• Key: ✅ set (chhupi hui)   • Auth: query
• Timeout: 12s   • Cache: 6 ghante
```

**Ab live test karo:**
```
/numapi 9876543210
```

**Sab theek ho to:**
```
✅ API CHAL RAHI HAI!
━━━━━━━━━━━━━━━━━━━━━━
🏢 Operator: Airtel
📍 Circle: Bihar
🔎 Line Type: 📱 Mobile
🌍 Country: India
⚡ Latency: 312ms
```

Bas! 🎉 Ab **📱 Number Info** tool aapki API se live data dega.

---

## 🚑 PROBLEM AAYE TO — 4 cheezein check karo

`/numapi 9876543210` fail ho to bot **khud batayega** kya galat hai. Ye table dekho:

| Message | Matlab | Kya karo |
|---|---|---|
| `HTTP 401` / `key reject` | Key galat hai | Render me key dobara paste karo (aage-peeche space na ho) |
| `HTTP 404` / `URL galat` | Endpoint galat hai | STEP 2 ki URL table se **exactly** copy karo |
| `JSON nahi bheja` | API JSON nahi de rahi | URL ke end me `/` laga ke dekho (jaise abstractapi me `/v1/`) |
| `carrier data nahi diya` | Response ka format match nahi hua | `NUMINFO_PROVIDER_PARAM` galat ho sakta hai — numverify: `number`, abstractapi: `phone` |
| `HTTP 429` | API ki monthly limit khatam | Agle mahine tak wait, ya dusra free account, ya STEP 6 dekho |
| `connect nahi hua` | Render se internet nahi | 2 minute baad dobara `/numapi` bhejo (Render restart ho raha ho sakta hai) |

> 💡 **API fail hui to bot band nahi hota** — Number Info purane offline database se
> chalta rehta hai. Bas card me `⚪ OFFLINE` likha aayega. **Kuch bhi crash nahi hota.**

---

## 🔒 STEP 4 — SAFETY (bahut zaroori)

| ✅ KARO | ❌ NA KARO |
|---|---|
| Key sirf Render → Environment me daalo | Key kisi chat me na bhejo (mere saath bhi nahi) |
| Screen recording me Environment tab na dikhao | Screenshot me key na dikhe |
| Kisi ko Render account ka access na do | GitHub me kabhi na commit karo |

**Agar key kabhi leak ho jaye:** provider ke dashboard me jaake **key regenerate** karo,
phir Render me nayi key daal do. Bas.

---

## ⚙️ STEP 5 — Advanced options (zaroorat pade to)

| Key | Kaam | Default |
|---|---|---|
| `NUMINFO_PROVIDER_AUTH` | Key kaise bheje — `query` / `header` / `bearer` / `none` | `query` |
| `NUMINFO_PROVIDER_HEADER` | `auth=header` par header ka naam | `X-Api-Key` |
| `NUMINFO_PROVIDER_TIMEOUT` | Kitne second wait (4-30) | `12` |
| `NUMINFO_PROVIDER_URL` me `{number}` | Number URL me hi jaaye | — |

### Misal 1 — Key header me jaati hai (Twilio jaisa):

```
NUMINFO_PROVIDER_URL   = https://api.example.com/lookup
NUMINFO_PROVIDER_KEY   = xxxxx
NUMINFO_PROVIDER_AUTH  = header
NUMINFO_PROVIDER_HEADER= X-Api-Key
NUMINFO_PROVIDER_PARAM = phone
```

### Misal 2 — Number URL me hi ho:

```
NUMINFO_PROVIDER_URL   = https://api.example.com/lookup/{number}?full=1
NUMINFO_PROVIDER_KEY   = xxxxx
NUMINFO_PROVIDER_AUTH  = bearer
```
*(URL me `{number}` ho to `NUMINFO_PROVIDER_PARAM` ki zaroorat nahi.)*

---

## 💰 STEP 6 — Zyada lookups chahiye to (paid, optional)

| Provider | Free | Paid | Kya special |
|---|---|---|---|
| **numverify** | 100/month | ~$10/1000 | Sabse sasta, reliable |
| **abstractapi** | 250/month | ~$9/mo (unlimited-ish) | Zyada free lookups |
| **Veriphone** | 100/month | ~$10/5000 | Bada volume |
| **Twilio Lookup** | trial | ~$0.008/lookup | Sabse accurate (MNP data) |

> **Suggestion:** 2-3 free accounts bana lo (dusri email se) = 300-500 lookups/month
> bilkul free. Aapke bot ke liye kaafi hai.

---

## 📊 Ye API kya NAHI de sakti (honesty)

| Kya | Milega? | Kyun nahi |
|---|---|---|
| Operator / Circle / Type | ✅ Haan | Public carrier metadata hai |
| MNP (ported) status | ✅ Haan (kuch APIs) | Public info |
| **Number ka naam / owner** | ❌ **Nahi** | Ye **private** data hai — koi legal API nahi deti |
| **Address / Aadhaar** | ❌ **Nahi** | Illegal — hum ye kabhi nahi karenge |
| **Live location** | ❌ **Nahi** | Sirf police/telecom ke paas hota hai |

> ⚠️ Number Info me naam/pata **sirf aapki apni API** ke jawab se dikhta hai —
> bot khud kahin se personal record nahi uthata.
> IT Act + DPDP Act ke khilaaf hai. Aapka bot **saaf aur legal** rahega. 🙏

---

## 🧾 Ek nazar me (cheat sheet)

```
STEP 1: numverify.com  →  Sign Up Free  →  API key copy
STEP 2: Render → utility-duniya-bot → Environment → 4 lines daalo → Save
STEP 3: Telegram → /numapi       (status dekho)
                → /numapi 9876543210   (live test)
STEP 4: Key kabhi kisi ko na do, screenshot me na dikhao
```

**Ho gaya!** Ab 📱 Number Info live data dega. 🎉

---

## 🔧 Technical detail (developer ke liye)

`modules/numinfo_provider.py` — ye module:
- **Kabhi raise nahi karta** — hamesha dict deta hai
- **Response shape auto-detect** karta hai (nested / flat / prefixed keys)
- **6 ghante cache** — same number dobara poochho to instant (API quota bachta hai)
- **Provider + hub PARALLEL** chalte hain (`asyncio.gather`) — 2x tez
- **Fallback chain:** provider → hub → offline phonenumbers (kabhi band nahi hota)
- **Key kabhi log/print nahi hoti** — `/numapi` me sirf "set / not set" dikhta hai

Test:
```bash
python3 tests/test_v57.py
```
