# 🚀 v57.0 — "NUMBER INFO API + PREMIUM CARDS"

**Release date:** 5 Oct 2026
**Tests:** **720 checks — 0 fail** (14 + 97 + 208 + 67 + 63 + 131 + **140 naya v57**)

---

## 1️⃣ 📱 NUMBER INFO — ab AAPKI API lagegi (aapki main demand)

### Kyun ye kaam karna pada

Aapke docs me **v49.6 se** likha tha ki `NUMINFO_PROVIDER_URL` + `NUMINFO_PROVIDER_KEY`
Render me daal do — **par code me ye implement hi NAHI tha**. Ye sirf docs me tha,
bot padhta hi nahi tha. Isliye Number Info sirf offline data deta tha:

```
Abhi:  📍 Circle / Region: ⚪ live API set nahi (sirf country pata hai)
       📡 Data Source: ⚪ OFFLINE — phonenumbers public database se

Ab:    📍 Circle / Region: Bihar
       🔎 Live Line Type: 📱 Mobile
       📡 Data Source: 🟢 LIVE — aapki API se (312ms)
```

### Naya module: `modules/numinfo_provider.py`

| Feature | Detail |
|---|---|
| **6 env vars** | `URL` · `KEY` · `PARAM` · `KEY_PARAM` · `AUTH` · `TIMEOUT` |
| **Response shape auto-detect** | numverify · abstractapi · veriphone · Twilio · nested `data{}` — **sab chalta hai** |
| **6-ghante cache** | Same number dobara → instant, API quota bachta hai |
| **Parallel** | Provider + hub ek saath (`asyncio.gather`) — pehle serial tha, **2x tez** |
| **Fallback chain** | provider → hub → offline phonenumbers. **Tool kabhi band nahi hota** |
| **Key kabhi print nahi** | `/numapi` me sirf "set / not set" dikhta hai |
| **Kabhi crash nahi** | Har function `dict` deta hai, `raise` nahi karta |

### 🆕 `/numapi` command (Telegram se hi pata kar lo)

```
/numapi                    → API lagi hai ya nahi (poora status)
/numapi 9876543210         → live test → operator/circle/latency
```

Fail hone par bot **khud batata hai** kya galat hai (401/404/429/format) + 4-step fix.

### 📖 Poori guide: **`NUMBER-INFO-API-SETUP.md`**

Usme step-by-step hai:
1. **Free API lo** — numverify (100/month free, no card) ya abstractapi (250/month)
2. **Render me daalo** — exact 4 lines, copy-paste ready
3. **Telegram se check karo** — `/numapi`
4. **Safety** — key kisi ko na do, screenshot me na dikhao
5. **Advanced** — header auth, `{number}` placeholder, timeout
6. **Troubleshooting** — 6 errors ka table

> **Aapko kuch bhejne ki zaroorat nahi** — key sirf Render ke Environment me jaayegi.

---

## 2️⃣ 🚨 ASLI CRASH BUGS (4 naye mile + fix)

### Bug A: `BRAND_TAG` — NameError crash

`bot.py` me `BRAND_TAG` **kahi define hi nahi tha**, par Number Info card me use
ho raha tha (`f"🔥 Powered by {BRAND_TAG}"`). Ye line pehli baar chalti to
**NameError → crash**. (`render.yaml` me var tha, par bot.py padhta hi nahi tha.)
**Fix:** `BRAND_TAG = os.getenv("BRAND_TAG", "@Supermannn_x")`

### Bug B: User input → HTML injection (4 jagah) ⚠️ sabse khatarnak

Telegram me `<`, `>`, `&` special hain. Jab user ka data bina escape HTML
message me jaata hai, Telegram **pura message reject** kar deta hai
(`can't parse entities`) — user ko kuch nahi milta.

| # | Tool | Kya ho raha tha |
|---|---|---|
| 1 | 📥 **Video Downloader** | YouTube title `<b>{title}</b>` me seedha. Video ka naam `"Song <Official> Video"` ho to **crash** |
| 2 | 📥 Video Downloader (2 aur jagah) | Same title caption + link card me |
| 3 | 🔄 **Channel Cloner** | "Rename Tag set: `<b>{raw_text}</b>`" — tag me `<` daala to crash |
| 4 | 🔗 **URL Short** | `<code>{clean}</code>` — URL me `<`/`>` ho to crash |

**Fix:** sab jagah `hesc()`.

### Bug C: `hesc()` zyada ho gaya tha (ulti galti)

BGMI/FF ka help error **HTML formatted** hai (`📌 Game me: <b>Profile</b> → UID`),
par bot usko `hesc()` kar deta tha → user ko literally ye dikhta tha:

```
📌 Game me: &lt;b&gt;Profile&lt;/b&gt; → UID      ← bedhadak bug
```

**Fix — naya `safe_html_err()` helper:**
- Sirf **whitelist tags** pass hote hain (`<b>` `<i>` `<u>` `<code>` `<pre>` `<a href="https://...">`)
- **Baaki sab escape** (user data safe)
- **Aakhir me tag-balance check** — gadbad ho to poora escape (Telegram kabhi reject na kare)
- `<script>`, `<img onerror>`, `javascript:` links — sab escape ✅
- Orphan `</a>` — escape ✅ (warna Telegram reject)

---

## 3️⃣ 🖼️ PREMIUM CARDS — ek hi look, sab tools me

Pehle sirf 2 tool boxed the (UPI, Number Info), baaki plain text.

**Naye reusable helpers:**
- `pcard_title(icon, name)` → boxed header `┌─── │ 🏦 ɪꜰꜱᴄ ʀᴇᴘᴏʀᴛ │ └───`
- `pcard_foot(ms=, source=, note=)` → `📡 Source` + `⚡ Response` + `🔥 brand`
- `pcard_sep()` → consistent separator

**Upgrade hue cards (9):**

| Tool | Naya look |
|---|---|
| 🏦 **IFSC** | Boxed header + 📡 Source + ⚡ time |
| 📮 **PINCODE** | Boxed + sirf bhare hue fields (khali `: / N/A` gaye) + Post Office count |
| 📮 **AREA SEARCH** | Boxed + query + total + foot |
| 🎮 **BGMI** | Boxed + 📡 Source + ⚡ time |
| 🔥 **FF UID** | 📡 Source (Garena public) + ⚡ time |
| 📦 **APP FINDER** | Boxed + search query + 📡 Source + ⚡ time |
| 🛡️ **LINK CHECK** | Boxed + 📡 6-layer source + ⚡ time |
| 🔗 **URL SHORT** | Boxed + 📡 providers + ⚡ time (+ fail par saaf message) |
| 📱 **NUMBER INFO** | Boxed + LIVE/OFFLINE source + ⚡ time + privacy panel |

**Bonus:** PINCODE card se khali lines hata di (`📂 :  / ` jaisa adhoora text
dikh raha tha — India Post har pincode ka division/circle nahi deta).

---

## 4️⃣ ⚡ SPEED — event loop blocking fix

### Bug: `analyze_link()` async handler me seedha call ho raha tha

🔍 **LINK CHECK** handler me `chk = analyze_link(raw_text)` **blocking** tha —
meaning jab tak wo link check karta (6-layer: OpenPhish + urlscan + RDAP + DNS),
**poora bot ruk jaata tha**. Us waqt agar koi doosra user kuch bhejta, use wait
karna padta. Ab `asyncio.to_thread()` me hai → **bot sab users ke liye responsive**.

### Aur tez
- 📱 **Number Info:** provider + hub ab **parallel** (`asyncio.gather`)
- 🔗 **URL Short:** 6 providers parallel (pehle se tha) + response time dikhta hai

---

## 5️⃣ 📊 FULL TEST RESULT (v57)

```
tests/test_privacy_safe_lookup.py   14 tests   OK
tests/test_v50_core.py              PASS 97  | FAIL 0
tests/test_v53.py                   PASS 208 | FAIL 0
tests/test_v541.py                  PASS 67  | FAIL 0
tests/test_v55.py                   PASS 63  | FAIL 0
tests/test_v56.py                   PASS 131 | FAIL 0
tests/test_v57.py                   PASS 140 | FAIL 0   ← naya
---------------------------------------------------------
TOTAL                               720 checks — 0 fail
```

**Naya test_v57 (140 checks)** — ye aapki **permanent suraksha** hai:
- numinfo_provider ke 6 provider shapes parse hote hain
- `safe_html_err()` 14 tricky inputs par balanced output deta hai
- purane 4 injection bugs **wapas na aayein** (source scan)
- `BRAND_TAG` defined ho
- premium cards lage hon
- `/numapi` command wire ho
- guide + render.yaml me sahi keys hon
- koi deleted tool wapas na aaye

---

## 🎯 AAPKO AB KYA KARNA HAI

### Step 1 — Deploy (automatic)
Render khud deploy karega (autoDeploy ON). **2-3 minute** lagenge.
Deploy ke baad Telegram me `/refresh` dabao.

### Step 2 — Number Info API lagao (5 minute)

**Poori guide:** `NUMBER-INFO-API-SETUP.md` — chhota version:

1. Kholo 👉 **https://numverify.com** → Sign Up FREE → API key copy karo
2. Kholo 👉 **https://dashboard.render.com** → **utility-duniya-bot** → **Environment**
3. **4 lines** add karo:

| Key | Value |
|---|---|
| `NUMINFO_PROVIDER_URL` | `https://apilayer.net/api/validate` |
| `NUMINFO_PROVIDER_KEY` | *apni key paste karo* |
| `NUMINFO_PROVIDER_KEY_PARAM` | `access_key` |
| `NUMINFO_PROVIDER_PARAM` | `number` |

4. **Save Changes** → 1-2 min wait
5. Telegram me: **`/numapi`** → phir **`/numapi 9876543210`**

### Step 3 — Key kabhi kisi ko na do 🔒
Key sirf Render me rakho. Chat me, screenshot me, GitHub me — **kabhi nahi**.

---

## 📋 v57 ME KYA-KYA BADLA (ek line me har cheez)

- 📱 Number Info API support — **6 env vars**, pehle sirf docs me tha
- 🆕 `/numapi` command — status + live test + troubleshooting
- 📖 `NUMBER-INFO-API-SETUP.md` — 6-step guide (aapke liye)
- 🚨 `BRAND_TAG` NameError crash fix
- 🌐 **4 HTML injection crash bugs** fix (Video title, Cloner tag, URL clean)
- 🛡️ `safe_html_err()` — whitelist tags + balance check (naya helper)
- 🖼️ **9 premium boxed cards** + 3 reusable helpers
- ⚡ LINK CHECK ka blocking call → `to_thread` (event loop free)
- ⚡ Number Info: provider + hub parallel (2x fast)
- 🧹 PINCODE card se khali fields gaye
- 📄 `render.yaml` + `.env.example` me API vars ready
- 🧪 `tests/test_v57.py` — 140 checks (naya)
- 📈 Total: **720 checks, 0 fail** · `BOT_VERSION = v57.0`
