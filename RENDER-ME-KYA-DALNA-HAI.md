# 🔑 RENDER ME KYA ADD KARNA HAI — 2 minute ka kaam

Aapke Render → Environment page me abhi ye hain:
`ADMIN_ID`, `BOT_TOKEN`, `FORCE_CHANNEL`, `FORCE_CHANNEL_LINK`, `UPI_ID`, `UPI_NAME`, `WEBHOOK_URL`
— **ye sab theek hai, inhe chhedna nahi hai.**

---

## ✅ Sirf ye ek line add karni hai — API HUB

```
KEY   = HUB_API_KEY
VALUE = Demo
```

Bas. Is ek key se ye sab aapke hub (`osint-api-hub.onrender.com/api`) se chalne lagte hain:

🌐 IP/Domain · 🏦 IFSC · 📮 Pincode · ⚡ TeraBox · 📥 Video Downloader (YouTube/X) ·
🆔 ID Finder · 📜 Kagaz (GST + PAN check) · 🚗 Vehicle · 📲 IMEI · 📱 Number Info

> Wahi `HUB_API_KEY` wala khaana jo screenshot me khaali tha — **usme `Demo` likho**, blank mat chhodo.
> (`Demo` aapke hub par lifetime ALL-ENDPOINTS plan hai — abhi active hai.)

---

## 🚫 Ye keys add karne ki zaroorat NAHI

| Key | Kyun nahi |
|---|---|
| `HUB_API_BASE`, `OSINT_API_BASE` | default me hi `https://osint-api-hub.onrender.com/api` set hai |
| `IMEI_API_KEY`, `VEHICLE_API_KEY` | khaali chhodo — apne aap `HUB_API_KEY` use karte hain |
| `NUM_INFO_API_KEY` | default `Demo` sahi hai |
| `VEHICLE_API_URL`, `VEHICLE_API_PARAM` | naya bot hub ke 3 endpoint use karta hai — purane custom provider ke liye hi chahiye |
| `YTDLP_COOKIES_FILE` | sirf tab jab YouTube cookies file ho |
| `CLIP_*`, `GEMINI_*`, `GROQ_*`, `AI_*` | ❌ **ab inka koi kaam nahi** (CLIP MAKER tool v49 me hata diya gaya) — ye vars bot padhta hi nahi |

---

## ✅ Deploy ke baad 3 check

1. Telegram me `/start` → menu aaye.
2. `/refresh` bhejo — sabko naya keyboard mil jaye.
3. `/imeistatus` bhejo — hub base + key ki live status dikhe.

---

## 🔒 Safety (zaroori)

- `BOT_TOKEN` aur `HUB_API_KEY` **password jaise** hain — kisi ko chat me na bhejo,
  screenshot me na dikhao, GitHub par commit na karo.
- Sirf Render ke Environment tab me daalo.
- Galti se leak ho jaye to: BotFather se bot token **Revoke** karo, aur hub dashboard se nayi key banao.

---

## 🔑 v49.6 — Aapki API (vehicle + number info) kahan lagani hai

**Sabse aasan tarika:** API/key **hub** par lagao, bot ko chhedne ki zarurat nahi.

1. Render → **osint-api-hub** service → **Environment** → Add Environment Variable:
   - `VEHICLE_PROVIDER_URL` = aapki vehicle API ka endpoint
   - `VEHICLE_PROVIDER_KEY` = us API ki key
   - `NUMINFO_PROVIDER_URL` = aapki number/carrier API ka endpoint
   - `NUMINFO_PROVIDER_KEY` = us API ki key
2. Save → service khud restart hogi (~1 minute).
3. Bot me 🚗 **VEHICLE INFO + CHALLAN** aur 📱 **NUMBER INFO** kholo — **live data** aayega.

> Provider ka JSON ka shape kuch bhi ho — hub khud samajh leta hai
> (`reg_no`, `registration_number`, `rc_number`, `vehicle_number`… sab chalta hai).

**Bot par direct lagana ho** (hub ke bajaye): usi service ke Environment me
`VEHICLE_PROVIDER_URL/KEY` + `NUMINFO_PROVIDER_URL/KEY` daal do — bas.

---

## 💰 v49.7 — ZERO BUDGET setup (koi paisa nahi chahiye)

| Cheez | Free kaise |
|---|---|
| **Bot + Hub 24/7 ON** | Ab bot aur hub **ek dusre ko ping karte hain** (`KEEPALIVE_PEERS`) — Render free plan par bhi dono jaagte rehte hain. Koi UptimeRobot zaroori nahi (chaaho to backup ke liye laga lo) |
| **Live GST data** | `gstinapi.in` — **100 free lookups/month, no credit card** → hub me `GST_PROVIDER_KEY` lagao |
| **Carrier/Operator data** | `numverify.com` — **free 100/month, no card** → `NUMINFO_PROVIDER_URL=https://apilayer.net/api/validate` + `KEY` + `AUTH=query` + `KEY_PARAM=access_key` |
| **Vehicle / Challan** | Free API nahi hai (jhooth nahi bolenge). Bot me **VAHAN + e-Challan ke official free links** hain — user wahan se check kar sakta hai |

### Env vars (optional, sab free)
```
KEEPALIVE_PEERS   = https://osint-api-hub.onrender.com/health   (default yahi hai)
KEEPALIVE_MINUTES = 10
```
