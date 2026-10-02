# 🔧 Bot ki service wapas kaise banayein (Render) — Step by Step

**Problem:** Dashboard me `utility-duniya-bot` repo se judi koi service nahi hai —
wo delete ho chuki hai. Ab nayi service banani padegi.

**Pehle note kar lo:** Render par aapke 4 services hain —

| Service | Status |
|---|---|
| `osint-api-hub` | ✅ chal raha hai (API) |
| `hosint` | Suspended |
| `hosint-api-jj7t` | Suspended |
| `hosint-bot-jj7t` | Suspended |

👉 **In purani wali services ko Suspended hi rehne do.** Resume mat karna.
Ek se zyada bot service chalegi to wapas `Conflict: terminated by other getUpdates
request` aayega aur bot chup ho jayega.

---

## ✅ Tareeqa 1 — Blueprint (SABSE AASAN, 4 click)

Maine `render.yaml` file repo me bana di hai, to Render khud sab kuch set kar dega.

1. **Render Dashboard** kholo → upar right me **"New +"** button
2. **"Blueprint"** chuno
3. **"Connect a repository"** —
   - agar GitHub account dikhe to `himanshu75919-coder/utility-duniya-bot` chuno
   - nahi dikhe to **"Connect account" / "Configure account"** → GitHub authorize karo
     (public repo par "Only select repositories" ki jagah **All repositories** chunna
     aasan rahega)
4. Repo select hone ke baad Render `render.yaml` padhega aur dikhayega:
   `tg-utility-bot` (Python · Singapore · Free)
5. **do cheezein poochhega — yahan bharo:**
   - `BOT_TOKEN` → BotFather wala token (jaise `8123456789:AAFxxxxxxxx`)
   - `ADMIN_ID` → apni Telegram numeric ID (`@userinfobot` se milegi, jaise `123456789`)
   - baaki sab khali chhod do (baad me bhi bhar sakte ho)
6. **"Apply"** / **"Create Resources"** dabao
7. **5-8 minute wait karo** (pehli baar build slow hota hai)

---

## 🛠 Tareeqa 2 — Manual (agar Blueprint me dikkat aaye)

1. **"New +"** → **"Web Service"**
2. **"Build and deploy from a Git repository"** → **Connect** `himanshu75919-coder/utility-duniya-bot`
   (ya "Public Git repository" me ye URL daalo:
   `https://github.com/himanshu75919-coder/utility-duniya-bot`)
3. Form me bharo:
   - **Name:** `tg-utility-bot`
   - **Region:** **Singapore**
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Plan:** **Free**
4. Neeche **"Advanced"** → **Add Environment Variable** se ye daalo:

   | Key | Value |
   |---|---|
   | `BOT_TOKEN` | *(BotFather ka token)* |
   | `ADMIN_ID` | *(apni numeric Telegram ID)* |
   | `OSINT_API_BASE` | `https://osint-api-hub.onrender.com` |
   | `OSINT_API_KEY` | `Demo` |
   | `OSINT_TIMEOUT` | `70` |
   | `FREE_CREDITS` | `25` |
   | `REFER_NEED` | `5` |

5. **"Create Web Service"** dabao → 5-8 minute wait

---

## ✅ Kaise confirm karein ki bot chal gaya

Service kholo → **"Logs"** tab. Ye lines dikhni chahiye:

```
Keepalive server listening on port 10000 for UptimeRobot / Render
Commands set successfully!
STARTING POLLING | instance=xxx pid=1 | only ONE instance must run
```

- `STARTING POLLING` **ek hi baar** aana chahiye. Do baar aaye (do alag instance-id)
  → matlab duplicate service chal rahi hai.
- Agar `❌ ERROR: BOT_TOKEN is missing` aaye → Environment tab me `BOT_TOKEN` nahi pada.

Uske baad Telegram par apne bot ko `/start` bhejo.

---

## ⚠️ Free plan ki ek baat

Render free instance **15 minute inactive rehne ke baad so jata hai**, aur
agle request me 50 second tak lag sakta hai. Bot ke liye:

- **UptimeRobot** (free) banao → monitor karo:
  `https://tg-utility-bot.onrender.com/`
  (har 5 minute ping → bot kabhi soega nahi)
- `osint-api-hub` ke liye bhi yahi karo: `https://osint-api-hub.onrender.com/health`
  (upar wale screenshots me /health ke ping aa rahe the — wo theek hai)

---

## ❓ Agar bot phir bhi chup rahe

1. Logs me sabse upar **"Newer logs may be unavailable because a recent deploy failed"**
   likha ho → deploy fail hua hai. Deploy ka red row kholo, error padh kar mujhe bhejo.
2. `Conflict: terminated by other getUpdates request` → **do services chal rahi hain**.
   Sirf ek rakho.
3. `BOT_TOKEN is missing` → Environment me token nahi pada.

---

⚡ Powered by @Supermannn_x
