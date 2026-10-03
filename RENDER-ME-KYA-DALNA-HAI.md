# 🔑 RENDER ME KYA ADD KARNA HAI — 2 minute ka kaam

Aapke Render → Environment page me abhi ye hain: `ADMIN_ID`, `BOT_TOKEN`, `FORCE_CHANNEL`,
`FORCE_CHANNEL_LINK`, `UPI_ID`, `UPI_NAME`, `WEBHOOK_URL` — **ye sab theek hai, inhe chhedna nahi hai.**

### 🆕 Sabse pehle ye 1 line add karo (v46) — API HUB

```
KEY   = HUB_API_KEY
VALUE = Demo
```

Bas. Isse IFSC, Pincode, IP, YouTube (clip maker), GST, PAN, Song, ID Finder, IMEI — sab aapke
hub se chalne lagte hain. (Wahi `HUB_API_KEY` wala khaana jo screenshot me khaali tha —
**usme `Demo` likho**, blank mat chhodo.) Detail: **`v46-HUB-LIVE.md`**.

---

Uske baad **1 nayi key** add karni hai (AI ke liye). Chaaho to 2 add kar sakte ho.

---

## ✅ STEP 1 — Gemini ki free key banao (1 minute)

1. Phone/computer me kholo: **aistudio.google.com/apikey**
2. Google account se login karo (wahi jisse aap Gmail karte ho).
3. **"Create API key"** dabao → koi project chuno → **"Create API key in new project"**.
4. Ek lambi key dikhegi jo **`AIza...`** se shuru hoti hai → **copy** dabao.

> Ye key **free** hai. Card / paisa nahi lagta.

## ✅ STEP 2 — Render me daalo

1. Aap jo screenshot bheja usi page par, **top-right me "Edit"** button dabao.
2. Neeche **"+ Add Environment Variable"** aayega (ya khaali row) → dabao.
3. Do khane aayenge:
   - **KEY** me likho: `GEMINI_API_KEY`
   - **VALUE** me paste karo: wo `AIza...` wali key
4. **"Save Changes"** dabao. ✅ (Render khud naya deploy shuru kar dega.)

## ✅ STEP 3 — Deploy hone do

**Deploys** tab me jao → naya deploy "In progress" dikhega → **"Live"** hone tak ruko (2-4 minute).
Agar apne aap deploy na chale to: **Deploys → Manual Deploy → Deploy latest commit**.

## ✅ STEP 4 — Check karo

Telegram bot me **`/aistatus`** bhejo. Aisa aana chahiye:

```
🧠 AI BRAIN — status
• Provider: Google Gemini ✅
• Model: gemini-2.5-flash
• Video: frames + audio samajhta hai ✅
• Live test: ✅ working (ok · Gemini gemini-2.5-flash)
```

Ye aa gaya = AI **live** hai. 🎉 Ab 🎬 CLIP MAKER → video → **🧠 Smart AI ✅** ON → 🚀 Make clips.

---

## 🎁 Chaaho to doosri key bhi (optional — Groq)

Dono key ho to aur behtar: Gemini video dekhta hai, Groq **Whisper** se bolne wali baatein padhta hai.

1. Kholo: **console.groq.com/keys** → sign up (Google se) → **"Create API Key"** → copy karo (`gsk_...`)
2. Render me wahi tarika: KEY = `GROQ_API_KEY`, VALUE = wo key → Save.

---

## ❌ Ye keys mat add karna (default theek hai)

| Key | Kyun nahi |
|---|---|
| `GEMINI_MODEL` | default `gemini-2.5-flash` sahi hai |
| `GROQ_MODEL`, `GROQ_WHISPER_MODEL` | default sahi hain |
| `AI_MODE` | default `auto` = key mile to AI on, na mile to off. AI band karni ho to `off` |
| `CLIP_MAX_MINUTES`, `CLIP_COUNT`, `CLIP_LEN` | default 15 / 6 / 35 sahi hai |
| `YTDLP_COOKIES_FILE` | sirf jab YouTube cookies file ho |
| `IMEI_API_KEY`, `VEHICLE_API_KEY` | aapke paas already chal raha hai (hub `Demo` key se) |

---

## 🔒 Safety (zaroori)

- Ye AI key **password jaisi** hai — kisi ko chat me na bhejo, screenshot me na dikhao.
- Sirf Render ke Environment me daalo.
- Galti se leak ho jaye to usi page (aistudio.google.com/apikey) par **Delete/Regenerate** kar dena.

> Key **bilkul na daalo** to bhi bot poora chalega — bas Clip Maker purane
> (loud + scene) engine se clips banayega, AI titles nahi aayenge. Aapki marzi. 🙂
