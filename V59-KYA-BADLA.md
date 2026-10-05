# 🆕 v59.0 me kya badla — "UPI GAYA + DEEP CLEAN + FAST YOUTUBE"

> Aapke 5 naye orders par kaam. **Saara kaam GitHub par push ho chuka hai.**
> Deploy check karne ke liye: **`AB-KYA-KARNA-HAI.md`**

---

## 1️⃣ 🏦 UPI VERIFY — POORI TARAH DELETE

Aapne kaha: *"phle upi verify tools delete karo and uska code"*.
Isliye v58 me jo bhi UPI ka kaam hua tha, sab hata diya:

| Kya hataya | Detail |
|---|---|
| Tool handler | `if mode == "upi":` — poora boxed card block (100+ line) |
| Tool prompt | `PROMPT_DATA` se `upi` key gayi + `PROMPTS` entry |
| Keyboard button | `🏦 UPI VERIFY` button gaya — uski jagah ab `📮 PINCODE INFO` |
| Dono callbacks | `upi_to_num` + `upi_to_vpa` (inline buttons + handlers) |
| Rate limit | `TOOL_RATE_LIMITS` se `upi` entry |
| Premium list | `PREMIUM_TOOLS` / `PREMIUM_TOOL_NAMES` se `upi` |
| Tool-name map | `BTN_MODE_MAP` / help text se UPI ka zikr |
| Verification code | `modules/osint_tools.py` se `upi_verify()` + `UPI_BANK_HANDLES` **(84 line)** |
| Naam-API module | `modules/upi_provider.py` **poori file delete** |
| Admin command | `/upiapi` command + uska handler |
| Env vars | `render.yaml` + `.env.example` se `UPI_VERIFY_*` (6 line) |
| Docs | `UPI-NAAM-API-SETUP.md` **delete** |

**Matlab:** keyboard, prompt, handler, callback, premium list, rate-limit,
admin command, module file, env var, doc — UPI ka **koi nishaan nahi bacha**.
Purane buttons (jo kisi purane message me reh gaye ho) dabaane par
ab kuch nahi hota — crash bhi nahi.

---

## 2️⃣ 🔒 PRIVACY TEXT — SAARE TOOLS SE GAYI

Aapne kaha: *"jaha jahan privacy code hai, privacy text ya card...
saare codes and text hatao"*. Isliye ab **kisi bhi tool me** privacy
lecture nahi aata:

| Kahan tha | Ab |
|---|---|
| BGMI card ka 🔒 privacy note | ❌ Gaya |
| FF UID card ka 🔒 privacy note | ❌ Gaya |
| Number Info ka "leaked data" lecture | ❌ Gaya |
| UPI card ka "Privacy (zaroori baat)" | ❌ Gaya (tool hi delete) |
| Number Info hub error me "leaked personal records" | ❌ Gaya → saaf message |
| `.env.example` ka `NUM_LEAK_ENABLED` + dara wala comment | ❌ Gaya |

**Tool ab bina lecture ke seedha apna kaam karta hai.**

---

## 3️⃣ 📱 NUMBER INFO — SIRF AAPKE DIYE FORMAT ME

Purana card (National / Line Type / Country / Timezone / boxed title) **poori tarah delete** —
ab **sirf ek hi layout** hai (neeche wala). API na ho to bhi *wahi* layout dikhta hai
(bas owner ki 6 line nahi aati + chhota setup hint).
Ab 10-digit number bhejne par **aapka format** aata hai:

```
👤 Name: Sanjay Sah
👨 Father: Ram Akwal Sah
📱 Phones/Alt: 7305190526
🌐 Region: BIHAR JIO
🆔 Govt ID: 401635555849
🏠 Address(es):
   └ S/O  Ram Akwal Sah, ward 02, ...
──────────────────────────────
📞 Number: +91 98765 43210
🏢 Operator: Jio  •  📍 Bihar
📡 Source: 🟢 LIVE — aapki API se (240ms)
⚡ Response: 240ms
──────────────────────────────
🔥 Powered by …
```

**Kaam kaise karta hai:**

- Data **sirf aapki API** se aata hai (`NUMINFO_PROVIDER_URL` + `NUMINFO_PROVIDER_KEY`
  — Render → Environment me daalna hai). Bot khud kahin se personal record
  **nahi** uthata.
- **Aapki API jo fields bhejegi, wahi dikhega.** Missing fields ki line
  apne aap gayab ho jaati hai (khaali dikhane se accha hai na dikhe).
- Address ek se zyada ho to `|` (ya array) se bhejo → `└` bullet list
  (max 4 lines, har line 300 char tak — Telegram limit se safe).
- **API na lagi ho to bhi tool chalta hai** — operator/circle/type offline
  database se aata hai + card me API setup hint (`/numapi`).
- Pehle jaisa privacy lecture nahi — bas kaam.

**Setup guide:** `NUMBER-INFO-API-SETUP.md` · **Status check:** `/numapi`

---

## 4️⃣ ⚡ YOUTUBE DOWNLOAD — LATE RESPONSE FIX

**Problem:** YouTube link bhejte hi bot 5–20 second chup ho jaata tha,
phir quality buttons dikhate the. Wajah: buttons se pehle **poora metadata
fetch** hota tha (`yt_available_qualities`) — 1080p jaisa bada video ho to
20 second tak lag jaate the.

**Fix (2 layer):**

1. **Instant buttons** — cache me qualities ho to **turant** wo dikhte hain,
   warna standard options (1080 / 720 / 480 / 360) **0 second** me dikhte hain.
   Peeche-peeche background thread me asli qualities nikaal kar 6 ghante ke
   cache me daal deta hai — agli baar wahi link instant.
2. **Tez download** — pehle `bestvideo+bestaudio` merge hota tha (video
   download → audio download → ffmpeg merge = 3 kaam). Ab **progressive
   format** (`18` / `22`) pehle try hota hai — ek hi file me video+audio,
   merge ka time bach jaata hai (≈3x tez). Saath me:
   - `socket_timeout = 15` (lat-fehta connection par ghanton nahi latakta)
   - `concurrent_fragment_downloads = 4` (parallel chunks)

---

## 5️⃣ 📲 IMEI — FIX + THODA AUR MAZBOOT

- **Naam / model code dono se search** chalu (`Redmi Note 10 Pro`,
  `M2101K6P`, `862407054987700`).
- **Photo** aata hai (nanoreview se) — model code se aaye **galat device ka
  photo** guard bhi hai.
- v59 me render path bhi faster: photo URL seedha banata hai, extra page
  fetch nahi karta.

---

## 6️⃣ 🐛 EK CHHUPA HUA BUG BHI PAKDA GAYA (important)

Patch (code badalne wala script) UPI ka purana block kaat raha tha, aur
usi block me **`/version` command bhi udtа chala gaya** (function gayab,
par handler registration reh gaya = Render par startup par crash ho jaata).

**Fix:** `/version` wapas lagaya (v59 wali detail ke saath) + test suite me
**regression lock** daala — ab koi script galti se ise udaaye to test turant
FAIL kar dega.

---

## 7️⃣ 🛡️ HARDCORE CRASH-PROOF CORE (v59.3) — "pehli baar hi crash"

Aapne kaha: *"hardcore proof built core rakhiye ki crash na ho"*. Ab ye 4 layer hain:

| Layer | Kya karta hai |
|---|---|
| 🩺 **Boot self-check** | Logs me saaf report: `version` + `commit` + `modules: sab OK` + API `set / not set`. Ab ek nazar me pata chal jaata hai kaunsa code chal raha hai |
| 🔁 **Self-heal supervisor** | `main()` crash ho to bot **khud restart** ho jaata hai (pehle process mar jaata tha = Render 502) |
| 🧯 **Loop guard** | Background task me error aaye to sirf log hota hai — poora bot nahi girta |
| 📊 **Crash counter** | `/health` par `self-heal: crashes=N` — sach dikhta hai, chhupaya nahi jaata |

**Live proof (test me):** `main()` ko 2 baar jaan-boojh kar crash karaya → bot **3rd try par khud chalu** ho gaya, counter me `crashes=2` — process zinda raha ✅

**Saath me 2 asli bug fix (jo "pehli baar" me hi dikhte the):**
1. **Owner-only API** — agar aapki API sirf naam/pata bheje (operator/circle ke bina) to bot
   pehle *"format match nahi hua"* bolta tha. **Ab chalti hai** ✅
2. **POST wali API** — pehle sirf GET chalta tha. Ab `NUMINFO_PROVIDER_METHOD=POST` laga do
   to number+key body me chale jaate hain ✅

📖 Render me key/value exactly kya likhna hai → **`DEMO-API-SETUP.md`**

---

## 8️⃣ 🧪 SAMPLE PREVIEW — "kaisa dikhega" bina API dekh lo (v59.5)

| Tarika | Kaise |
|---|---|
| ⚡ **Command** | Telegram me **`/numdemo`** (admin) → wahi card, SAMPLE (nakli) data ke saath |
| 🧪 **Poora flow** | Render me `NUMINFO_DEMO=on` → 📱 Number Info me koi bhi number → card aayega, Source line par `🧪 DEMO SAMPLE` likha hoga |
| 🔎 **Apni API ka response** | **`/numtest {"carrier":"Jio", ...}`** — apni API ke docs wala sample JSON paste karo → bot dikha dega card kaisa banega + kaunsi field map hui (koi API call nahi, koi credit nahi) |

- Card ka layout **ek hi renderer** (`numinfo_card()`) se banta hai — jo aap
  `/numdemo` me dekhte ho, **bilkul wahi** asli API lagne par aayega.
- Demo data me har line par **(SAMPLE)** likha hota hai — koi asli vyakti ka data nahi.
- **Aur ek zaroori baat:** naam me "leak" wali APIs (jaise
  `x-trace-...-leak-num-api`) bot me **kabhi nahi lagayi jayengi** — wo chori ka
  data hai (DPDP ₹250 cr + Telegram ban + 2 din me band hone wala trap).
  Poori baat: **`DEMO-API-SETUP.md`** ⛔ section.

---

## 9️⃣ 💬 SUPPORT CLICKABLE — tap karo, seedha owner se baat (v59.7)

Aapka username **@Supermannn_x** ab har jagah **clickable** hai:

| Kahan | Kya hota hai |
|---|---|
| Har card ka footer — `🔥 Powered by @Supermannn_x` | Tap → aapki chat khulti hai → user **Start** dabata hai → apni baat likh sakta hai |
| **Har tool ke prompt** me button `📩 Support — seedha message karo @Supermannn_x` | Tap → wahi — bina username type kiye |
| `/support` command (naya) | Poora madad card + bada "📩 Message karo" button |
| Ban message / help / payment screens / error message | Wo bhi clickable |

**Username badalna ho?** Render → Environment → `OWNER_USERNAME` = naya username
(`@` ke bina bhi chalega) → Save. **Poore bot me apne aap badal jaayega** — code chhune ki zaroorat nahi.

---

## 📊 Test status

| File | Kya check karta hai |
|---|---|
| `tests/test_v59.py` | **naya** — UPI delete, lecture text gone, naya Number Info card, YT speed, IMEI, /version lock, **crash-proof core (self-heal live test)** |
| `tests/test_v58.py` | prompt system + guard + `/version` (v59 ke hisaab se update) |
| `tests/test_v57/v56/v55/v53/v541/v50_core` | purane sab tests update — UPI wale assertions ab "UPI gaya" verify karte hain |

---

## 🎯 Ek line me

**UPI poora gaya · privacy text gaya · Number Info aapke format me ·
YouTube instant + tez · IMEI theek · ek chhupa crash bug bhi fix.**
Bas Render deploy + `/version` bhejo (v59 dikhna chahiye).

---

## 10. v59.9 — 🌐 AUTO-WEBHOOK (asli "kyun nahi chal raha" ka jawab)

Aapne poocha: *"naye versions me ye kyun nahi chal raha"* — Render logs me jawab tha:

| Jo logs me dikha | Matlab |
|---|---|
| `MODE = POLLING (safe default)` | Bot purane mode me tha |
| 2 baar `STARTING POLLING ... only ONE instance must run` | Deploy ke waqt **do** instance saath chal rahe the |
| Dono `getUpdates` maangte hain | Telegram: **"Conflict: terminated by other getUpdates request"** → us waqt bot late / no reply |

**Fix (v59.9):** ab **webhook mode apne aap ON** hota hai. Webhook me Telegram khud
update bhejta hai, `getUpdates` hota hi nahi → **Conflict kabhi nahi**.

| Kaam | Detail |
|---|---|
| `WEBHOOK_MODE=auto` (default) | `RENDER_EXTERNAL_URL` mila → webhook ON |
| Safety 1 — DNS check | URL kaam ka nahi to chup-chaap POLLING (crash nahi) |
| Safety 2 — Telegram preflight | `setWebhook` ek baar try; fail = POLLING (bot rukta nahi) |
| `WEBHOOK_URL` me galat value | **v59.9.3:** sirf asli `http(s)` URL maani jaati hai — `on`/`yes`/`1` likha ho to Render ka apna URL use hota hai |
| Puran `WEBHOOK_MODE=polling` | **v59.9.1:** ab auto maana jaata hai (dashboard ki purani value webhook band nahi karti) |
| Zabardasti polling | `WEBHOOK_MODE=off` (bas yahi ek rasta) |
| Polling par switch | purani webhook delete hoti hai (warna `getUpdates` band) |

### /version aur /health me ab ASLI proof

* `/version` → 🔖 **Code commit** + 🌐 **Mode** + ⏱️ uptime + 🩺 crashes + 🌐 webhook check
  + 3-step "naya version live hai ya nahi" guide.
* `/health` (browser) → version, **commit**, branch, **mode**, uptime, keepalive, crashes
  aur webhook ki **asli wajah** (`mode_env`, `url_env`, `decision`, `why`).
  *Webhook mode me pehle sirf chhota JSON aata tha — isliye aapko version/commit
  dikh hi nahi raha tha.*

### Live proof (05-10-2026)

```
version: v59.9 Auto-Webhook (Conflict-Free) + Live Version Proof + Support Clickable
commit: 83a16a7 | branch: main | mode: WEBHOOK | up: 0m
self-heal: crashes=0 (koi crash nahi)
webhook: mode_env=(not set) | url_env=set | render_url=set | decision=WEBHOOK
         | why: Telegram ne URL maan liya ✅
```

**Aap khud kaise check karo:** Telegram me `/version` bhejo → commit `83a16a7` aur
`Mode: WEBHOOK` dikhna chahiye. Browser me `/health` kholo → `mode: WEBHOOK`.
