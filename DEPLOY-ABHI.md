# 🚀 DEPLOY — 2 MINUTE ME (sirf 4 step)

> ⚠️ **Sabse pehle ye samjho:**
> Aapke screenshot me keyboard par **"VIDEO DOWNLOADER · 10+ APPS"** likha hai.
> Wo **PURANA version** hai (v59 ke aas-paas ka).
> **Isliye wahi purane error baar-baar aa rahe hain** — naya code abhi
> Render par pahuncha hi nahi hai.
>
> **Jaise hi ye 4 step karoge, error band ho jayega.**

---

## ✅ STEP 1 — Render kholo

👉 https://dashboard.render.com

Apne bot **`utility-duniya-bot`** par click karo.

## ✅ STEP 2 — Manual Deploy

1. Upar **`Manual Deploy`** button dabao
2. Menu me **`Clear build cache & deploy`** wala option dabao
   *(ye zaroori hai — warna purana code hi chalta rahega)*
3. Ab **3-4 minute** ruko (build hone do)

## ✅ STEP 3 — Check karo ki naya version chala ya nahi

Telegram me bot ko likho:

```
/version
```

**Aana chahiye:** `v66.1`
Agar **v59 / v64 / kuch purana** dikhe → deploy nahi hua, **Step 2 dobara** karo.

## ✅ STEP 4 — Naya keyboard dekho

Telegram me bot ko bhejo:

```
/menu
```

Ab keyboard par **neeche scroll** karo. Aise dikhna chahiye:

```
🌐 VIRTUAL NUMBERS   | ⚡ TERABOX DOWNLOADER
🔄 CHANNEL CLONER
📸 INSTA DL | ▶️ YOUTUBE DL | 📘 FACEBOOK DL
🎵 TIKTOK DL | 🐦 X (TWITTER) DL | 👻 SNAPCHAT DL
📌 PINTEREST DL | 🔴 REDDIT DL | 💬 THREADS DL
📺 VIMEO DL | 🎬 DAILYMOTION DL | 🟣 TWITCH DL
... (27 tools — har app ka apna alag tool)
```

❌ **"VIDEO DOWNLOADER" naam ka tool ab NAHI hoga.** (Wo delete kar diya.)
✅ Ab **har app apna alag tool** hai — jaise NUMBER INFO / IMEI / CLONER alag hain.

---

# 🧪 DEPLOY KE BAAD — 3 TEST

| Test | Karo | Kya hona chahiye |
|---|---|---|
| 1️⃣ **Insta** | `📸 INSTA DL` dabao → Insta reel ka link bhejo | 15 second ke andar video |
| 2️⃣ **YouTube** | `▶️ YOUTUBE DL` dabao → YouTube link bhejo | quality buttons, phir video (1-2 sec) |
| 3️⃣ **Purana button** | Purane keyboard ka `VIDEO DOWNLOADER` dabao | Saaf message: "ye tool hata diya — ab 27 alag tools hain" |

---

# 🍪 AGAR "SIGN IN TO CONFIRM YOU'RE NOT A BOT" AA JAYE

(Lekin ab ye 4 layer ke baad **bahut kam** aayega)

1. PC par Chrome kholein → **"Get cookies.txt LOCALLY"** extension lagayein
2. `youtube.com` kholein (login ho) → extension se **cookies.txt** download karein
3. Wahi **file bot ko bhej dein** (normal file ki tarah 📎)
4. Bot likhega: **"✅ COOKIES LAG GAYIN!"** — bas, ab ye error **nahi aayega**

Ya bot me **`/cookies`** likho → poora tarika likha aa jayega.

---

# 🛡️ CRASH KA ASLI KARAN (jo screenshot me tha) — FIX HO GAYA

Aapke log me tha:

```
Telegram backup fail: Unknown error in HTTP implementation:
RuntimeError('<asyncio.locks.Event ...> is bound to a different event loop')
```

**Matlab:** bot ka backup ek alag thread se naya "loop" bana raha tha — usi se bot tut raha tha.

**v66.1 me dono theek hain:**
1. ✅ Backup ab **main loop** par chalta hai (crash khatam)
2. ✅ Polling (bot ka dil) ab **kabhi haar nahi maanta** — Conflict aaye to
   ruk kar dobara chalata hai (pehle 5 try ke baad chhod deta tha → Render restart)

---

# 📞 KUCH BHI GALAT LAGE TO

Bot me ye bhejo:

```
/sys
```
(Aur screenshot bhej do — main turant dekh lunga.)
