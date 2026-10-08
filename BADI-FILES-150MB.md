# 🐘 BADI FILES — 20 MB की हद अब 150 MB (aapka 1 kaam)

## Problem kya thi (aapka screenshot)
Aapne **Chat X-Ray** me **66.5 MB** ka WhatsApp zip bheja → bot bola:
> ⚠️ The file is bigger than 20MB — that is the Telegram bot limit.

Ye **hamara code nahi, Telegram ka rule** hai:

| Kaam | Bot API (jo bot ab use karta hai) | MTProto (Telegram ka apna API) |
|---|---|---|
| File **len** (download) | **20 MB** tak | ~2 GB tak |
| File **bhej** (upload) | **50 MB** tak | ~2 GB tak |

## Solution (already code me hai — sirf 2 chhoti settings chahiye)
`modules/core/bigfile.py` same **bot token** se MTProto use karta hai. Koi naya
bot/account nahi chahiye. Ye 2 cheezein set karte hi 150 MB chalना शुरू:

### Step 1 — 2 minute, Telegram ka official page
1. Browser me kholo: **https://my.telegram.org**
2. Apna Telegram phone number login karo (code aapke Telegram app me aayega).
3. **"API development tools"** par jao → form me kuch bhi valid bhar do
   (App title: `ToolVault`, Short description: `utility`) → **Create application**.
4. Wahan 2 values dikhengi:
   - **Api_id** → ek number (jaise `1234567`)
   - **Api_hash** → 32 character ka code

### Step 2 — Render me 2 env vars (main kar dunga, aap bas values do)
Render → `utility-duniya-bot` → Environment → ye 2 add:

```
TG_API_ID   = <Api_id>
TG_API_HASH = <Api_hash>
```

(Aap mujhe ye 2 values de do, main Render API se daal kar deploy khud kar dunga —
ya khud dashboard me daal do, 30 second ka kaam hai.)

### Step 3 — bas. Verify
Bot restart ke baad: `https://utility-duniya-bot.onrender.com/health`
me ye line dikhegi:

```
bigfile: MTProto ON | in ≤150MB out ≤150MB | bot-api caps: in 20MB / out 48MB
```

`ready`/`ON` dikha = 150 MB files chalegi. `note: TG_API_ID/TG_API_HASH set nahi`
dikha = abhi purana 20 MB behaviour (bot theek chalta rahega, kuch tuta nahi).

---

## Isme kya-kya bana (technical, aapko padhne ki zaroorat nahi)
- **File RAM me nahi, DISK par utarti hai** (`mapped` mode). Render free plan par
  sirf **512 MB RAM** hai aur isi wajah se bot pehle OOM-crash hota tha — 150 MB
  file ko RAM me bhar dete to wahi crash phir aata. Isliye 45 MB se upar ka payload
  `mmap` (`MappedFile`) ke roop me tools ko jaata hai: Python ka RAM ~0 badhta hai.
- **Chat X-Ray ab disk se stream karta hai**: 66 MB zip ke andar ka `chat.txt`
  sirf zaroorat ke hisaab se (pehle `MAX_BYTES`, default 45 MB) padha jaata hai —
  `.zip` ke andar ki media/MACOSX files ignore, aur poora zip decompress nahi hota.
- **Video badi ho to (48–96 MB) bot use MTProto se bhejta hai**; MTProto off ho to
  pehle jaisa compressed version / direct link milta hai.
- **Limits env se tune hoti hain** (default theek hain, chhune ki zaroorat nahi):
  `MAX_FILE_MB` (lend = 150), `MAX_SEND_MB` (bhejna = 150), `MAX_TG_MB` (download
  cap 48 → 96 jab MTProto on), `CHAT_XRAY_MAX_BYTES`.
- **Safe by default**: `TG_API_ID`/`TG_API_HASH` na ho to `telethon` import bhi
  lazy hai aur behaviour bilkul vaise hi rehta hai — deploy ka koi risk nahi.
- **`requirements.txt` me `telethon` add kiya** (Deploy ke waqt install ho jaayega).

## Note on Telegram ka apna rule (jo hum change nahi kar sakte)
User jab bot ko file bhejta hai to Telegram **Bot API server** file ko 20 MB ke
baad rok deta hai — isliye 20 MB se badi file ke liye MTProto *zaroori* hai,
sirf code se ye limit nahi badhti. 150 MB ke upar bhi chalega (MTProto ~2 GB tak
hai) — bas Render ki disk/RAM ke hisaab se `MAX_FILE_MB` badha dena.
---

## ✅ STATUS (8 Oct 2026, shaam): DONE — ab aapko kuch nahi karna

`TG_API_ID` + `TG_API_HASH` Render ke Environment me **set ho chuke hain** (aapne my.telegram.org se diye, maine daale). Live proof — bot ka `/health`:

```
bigfile: MTProto ON | in ≤150MB out ≤150MB | bot-api caps: in 20MB / out 48MB
```

`MTProto ON` ka matlab bot ne **boot par hi** Telegram ke apne API se login kar liya (v80.2 ka warm-up) — yaani pehle user ko 5-8 second ka handshake wait nahi milega. 20 MB ki deewar ab **150 MB** hai (2000 tak `MAX_FILE_MB` se badhani ja sakti hai, par Render ke 512 MB RAM par 150 safe hai).

Verify kiya gaya: 26 MB ki file MTProto se upload + user chat me send (Bot API iski ijaazat nahi deta tha). **Aapki baari:** koi 30-100 MB ki video bhej ke dekho — "bigger than 20MB" wala message ab nahi aana chahiye.

## v80.2 ka naya knob

| knob | default | kaam |
|---|---|---|
| `BIGFILE_WARM` | **`off` (aapke Render env me)** | boot par hi MTProto login (pehle user ko 5-8s bachta hai, par ~60 MB extra RAM). **`off`** kar do agar RAM tight lage (Render free = 512 MB) — tab bhi 150 MB chalega, bas pehli badi file par 5-8 second extra lagenge |

> **Aapke instance par kyun `off` rakha hai:** live /health me dekha — warm ON karne se bot ka baseline RAM 286 MB se **358 MB** ho gayi, aur memory-throttle 378 MB par shuru hota hai (Render free = 512 MB). Yaani bheed me users ko jaldi "busy" milta. `off` par baseline ~290 MB rehti hai aur **150 MB ka raasta waisa hi chalta hai** — bas deploy ke baad *pehli* badi file par 5-8 second ka login lagta hai (uske baad process bhar session zinda rehta hai). Agar Render plan badlo (Starter/Standard, 2 GB) to `BIGFILE_WARM=on` kar dena — phir `/health` par hamesha `MTProto ON` dikhega.
