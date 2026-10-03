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
