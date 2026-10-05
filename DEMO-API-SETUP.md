# 🔑 RENDER ENVIRONMENT — kya bharna hai (Number Info API)

> Aapke paas API ka **key** hai. Par Render ko **do cheezein** chahiye:
> **1) URL** (kahan bhejna hai) aur **2) KEY** (jo aapke paas hai).
> Sirf key se kaam nahi chalega — URL zaroori hai. Dono neeche diye hain.

---

## STEP 1 — Render me kahan daalna hai

1. Kholo 👉 **dashboard.render.com** → **`utility-duniya-bot`**
2. Left side me **`Environment`** tab dabao
3. **`Add Environment Variable`** dabao
4. Neeche wale table se **Key** aur **Value** ek-ek karke daalo
5. **`Save Changes`** → Render khud restart karega (1–2 minute)

---

## STEP 2 — Key & Value (yahi likhna hai)

| # | Key (left box) | Value (right box) | Kyun zaroori |
|---|---|---|---|
| 1 | `NUMINFO_PROVIDER_URL` | aapki API ka **poora URL** (neeche 3 example) | **zaroori** — iske bina data nahi aayega |
| 2 | `NUMINFO_PROVIDER_KEY` | aapki **demo API key** (dhundhla rahega) | zaroori (agar API key maangti hai) |
| 3 | `NUMINFO_PROVIDER_PARAM` | `number` | mobile number jis naam se jaata hai |
| 4 | `NUMINFO_PROVIDER_AUTH` | `query` | key URL me jaati hai (`?key=...`) |
| 5 | `NUMINFO_PROVIDER_KEY_PARAM` | `key` | key ka param naam |
| 6 | `NUMINFO_PROVIDER_METHOD` | `GET` ya `POST` | *(aapki API POST maange to `POST`)* |
| 7 | `NUMINFO_PROVIDER_TIMEOUT` | `12` | dheemi API ho to `25` |

> **3, 4, 5 chhod bhi sakte ho** — inke default yahi hote hain.
> Sirf **1 aur 2** daalo to bhi 90% API chalti hai ✅
> **POST wali API** ho to bas ek extra line: `NUMINFO_PROVIDER_METHOD` = `POST`
> (number + key apne aap body me chale jaate hain — GET wali API ke liye kuch nahi karna).

---

## STEP 3 — `NUMINFO_PROVIDER_URL` me kya likhein? (APNI API ke hisaab se)

Aapki API ka URL jaisa hai, waisa hi daalo — bas number ki jagah `{number}` likh do:

| Aapki API ka format | Value me ye daalo |
|---|---|
| `https://api.site.com/lookup?number=9876543210&key=ABC` | `https://api.site.com/lookup?number={number}` *(aur key alag se `NUMINFO_PROVIDER_KEY` me)* |
| `https://api.site.com/v1/phone/9876543210` | `https://api.site.com/v1/phone/{number}` |
| **POST** wali API (`/api/search`) | URL: `https://api.site.com/api/search` **aur** ek extra line: `NUMINFO_PROVIDER_METHOD` = `POST` |

**Kaise pata chalega sahi hai?** Telegram me:
```
/numapi 9876543210
```
→ `✅ API CHAL RAHI HAI` aaya to bilkul sahi ✅
→ fail hua to jo error aaye wo mujhe bhejo, main 1 line me theek kar dunga.

---

## STEP 4 — Aapki API ka response kaisa hona chahiye

Bot aapke response me se **in fields** ko dhoondhta hai (jo milega wahi dikhega):

```json
{
  "name": "Sanjay Sah",
  "fatherName": "Ram Akwal Sah",
  "altMobile": "7305190526",
  "region": "BIHAR JIO",
  "govtId": "401635555849",
  "address": "S/O Ram Akwal Sah, ward 02, B Machhpakauni, Bela Khurd Parihar, Sitamarhi, Bihar, 843324",
  "operator": "Jio",
  "circle": "Bihar"
}
```

**Naam alag ho to koi baat nahi** — bot ye sab bhi samajh leta hai:

| Cheez | Ye-naam bhi chalta hai |
|---|---|
| Naam | `ownerName`, `subscriberName`, `customerName`, `fullName`, `holderName`, `name` |
| Pita | `father`, `fathersName`, `guardian`, `sonOf`, `so` |
| Extra number | `alt`, `alternate`, `phones`, `otherNumbers`, `linkedNumbers` |
| Region | `region`, `state`, `circle`, `telecomCircle`, `area` |
| Govt ID | `govtId`, `idNumber`, `aadhaar`, `uid`, `documentId` |
| Pata | `address`, `addresses`, `fullAddress`, `permanentAddress`, `addr` |
| **Do se zyada pate** | `addresses` me **list** bhejo: `["pata1", "pata2"]` → card me `└` bullet ban jaayenge |

**Deep (nested) JSON bhi chalta hai** — `{"data": {"name": ...}}` ya `{"result": {...}}` —
bot khud andar chala jaata hai.

---

## STEP 5 — Test karne ka tarika

| Telegram me bhejo | Kya hoga |
|---|---|
| `/numapi` | API lagi hai ya nahi + 6 env var ka status (key kabhi print nahi hoti) |
| `/numapi 9876543210` | **Live test** — aapki API se asli data maangta hai |
| 📱 **Number Info** daba ke `9876543210` | 10-digit number → aapke format ka card |

> ⚠️ **`/numapi` ek private command hai** — sirf aap (admin) chala sakte ho.

---

## 🧯 Kuch atak gaya to (turant fix)

| Log/message me kya dikhe | Matlab | Fix |
|---|---|---|
| `URL set nahi hai` | pehli line hi nahi daali | `NUMINFO_PROVIDER_URL` daalo |
| `HTTP 401 / 403` | key galat hai ya bhejne ka tarika galat | `NUMINFO_PROVIDER_AUTH=header` + `NUMINFO_PROVIDER_HEADER` try karo |
| `HTTP 429` | API ka daily limit khatam | provider ka plan/limit dekho |
| `format match nahi hua` | response me naam ke fields alag hain | mujhe response ka 1 sample bhejo — main map kar dunga |
| `timeout` | API 12 second me jawab nahi deti | `NUMINFO_PROVIDER_TIMEOUT=25` daalo |
| `format match nahi hua` | API ka jawab samajh nahi aaya | mujhe 1 sample response bhejo — main 1 min me map kar dunga |

---

## 🔐 Security (zaroori)

- Key **sirf Render → Environment** me rakho — chat me, screenshot me, GitHub me **kabhi nahi**.
- Bot key ko **kabhi print nahi karta** — log me, message me, `/numapi` me sirf
  **`🟢 set` / `⚪ not set`** dikhta hai.
- `/health` page par bhi key nahi dikhti.
- Key galti se kahin chali jaye to provider ke dashboard se **regenerate** kar lo —
  Render me nayi value daal dena, bas.
