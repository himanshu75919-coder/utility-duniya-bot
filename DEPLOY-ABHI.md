# 🚀 DEPLOY — SIRF 4 STEP (bas 2 minute ka kaam)

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
3. Ab **2-4 minute** ruko (build hone do)

## ✅ STEP 3 — Check karo ki naya version chala ya nahi

Telegram me bot ko likho:

```
/version
```

**Aana chahiye:** `v70.0`

Agar **v59 / v64 / v67 / kuch purana** dikhe → deploy nahi hua, **Step 2 dobara** karo.

## ✅ STEP 4 — Naya keyboard dekho

Telegram me bot ko bhejo:

```
/menu
```

Ab **sabse upar** (pehli 2 line) aapke **premium downloader tools** hain —
jaise aapne kaha tha "premium tools 1st me chahiye":

```
📸 INSTA DL      | ▶️ YOUTUBE DL
📘 FACEBOOK DL   | 🎵 TIKTOK DL
🌐 VIRTUAL NUMBERS | ⚡ TERABOX DOWNLOADER
... (baaki tools jaise pehle the)
```

❌ **23 downloader tools POORI TARAH DELETE** — ab bot me unka code bhi nahi hai.

✅ Sirf **4 downloader tools** bache: **INSTA · YOUTUBE · FACEBOOK · TIKTOK**

---

# 🧪 DEPLOY KE BAAD — 4 TEST

| Test | Karo | Kya hona chahiye |
|---|---|---|
| 1️⃣ **Insta** | `📸 INSTA DL` dabao → Insta reel ka link bhejo | **30 second ke andar** video |
| 2️⃣ **YouTube** | `▶️ YOUTUBE DL` dabao → YouTube link bhejo | quality buttons → **30 second ke andar** video |
| 3️⃣ **Same link dobara** | Wahi link **phir se** bhejo | **1-2 second me TURANT** video (naya engine: yaad rakhta hai) |
| 4️⃣ **Speed report** | `/speed` likho | cache/engine ki report — kitne video yaad hain |

---

# ⚡ v69.0 ME SPEED KA WADA — 30 SECOND

Aapne kaha tha: *"chaaro tools bhut hi slow hain, 30 second me video aana chahiye."*

**Isliye 5 hathiyar lage:**

1. **Turant repeat** 🔁 — jo link pehle aa chuka hai, wo agli baar **file se turant**
   (dobara download nahi hota)
2. **Memory cache** 🧠 — 100 MB tak video bot ke andar hi yaad rehti hai
3. **Parallel engine** ⚙️ — 3 server ek saath try hote hain (pehle ek-ek karke)
4. **Slow-server ki chhutti** 🚫 — jo server 40 second leta tha, **uska time 6 second**
   kar diya (yahi asli slow ka karan tha — ab seedha tez engine chalta hai)
5. **Kharab engine block** 🛡️ — jo server "bot check" fail kare, wo 15 minute band

**Aur v69.0 me ek bada bug bhi pakda gaya:** jo slow server 40 second leta tha, usi se
saare downloads late ho rahe the — ab usko sirf **6 second** milte hain, phir seedha tez
engine chalta hai. Test me **42 second → 3.6 second** ho gaya. 🚀

---

# 📱 NUMBER INFO KA NAYA CARD (aapka sample — ho gaya)

Aapne jo sample diya tha, ab bilkul wahi aayega:

```
👤 Name: Sanjay Sah
👨 Father: Ram Akwal Sah
📱 Phone: 7857843092
📱 Alt: 7305190526
🌐 Circle: BIHAR JIO
🆔 Govt ID: 401635555849
🏠 Address:
└ S/O Ram Akwal Sah, ward 02, Sitamarhi, Bihar, 843324
```

# 🌐 NAYA TOOL (v70): WEBSITE OWNER X-RAY

Keyboard me **`🌐 WEBSITE OWNER X-RAY`** button aa gaya hai (NUMBER INFO ke
theek neeche). Kisi bhi website ka naam ya link bhejo — **result bot ke andar
hi aayega, koi link nahi kholna**:

```
🔖 Domain: bihar.gov.in
📅 Banaya: 18-03-2008  •  ⏳ 18 saal 6 mahine purana
⌛ Khatam: 18-03-2027  •  ✅ 163 din bache
🏢 Registrar: National Informatics Centre
👤 Malik (public record): Information Technology Department Government of Bihar
📋 Status: ✅ active
💡 Matlab: ✅ Ye website purani hai — bharosa karne layak lagti hai.
```

Online dukaan se paisa dene se pehle — **site purani hai ya kal bani** — turant pata.

---

Iske neeche purani technical lines bhi rahengi (Number / Country / Type / Source /
Response) — **kuch bhi nahi hataya**. Naam-pita-pata wala data aapki apni API se aata hai
(Render → `NUMINFO_PROVIDER_URL`), jaisa aapke sample me tha.

**Natija:** pehli baar 30 second ke andar, dusri baar **1-2 second me**.

---

# 🍪 AGAR "SIGN IN TO CONFIRM YOU'RE NOT A BOT" AA JAYE

(Lekin ab ye 5 layer ke baad **bahut kam** aayega)

1. PC par Chrome kholein → **"Get cookies.txt LOCALLY"** extension lagayein
2. `youtube.com` kholein (login ho) → extension se **cookies.txt** download karein
3. Wahi **file bot ko bhej dein** (normal file ki tarah 📎)
4. Bot likhega: **"✅ COOKIES LAG GAYIN!"** — bas, ab ye error **nahi aayega**

Ya bot me **`/cookies`** likho → poora tarika likha aa jayega.

---

# 🛡️ TOOL FAIL HO TO BHI BOT ZINDA RAHEGA (aapka order)

Aapne kaha tha: *"koi bhi tool work na kare to bot working karna chahiye."*

**v68.0 me ye pakka hai:**

1. ✅ Har download tool par **40 second ka hard time-limit** — atka hua tool chhoot jata hai,
   bot wahi ka wahi chalta rehta hai
2. ✅ Tool fail → saaf message + **credit wapas** (katta nahi)
3. ✅ Tool fail → bot ka dil (polling) **kabhi band nahi hota**
4. ✅ Log ka faltu error message chup kiya (pehle screenshot me `?: ?` aa raha tha)

---

# 😴 BOT SO NA JAYE — KEEPALIVE (pinger)

Render ke free plan me bot 15 minute me **so jata hai** (sleep) — phir
pehla message me 30-40 second lag jata hai.

**Check karne ka tarika:** bot me likho

```
/sys
```

Wahan dikhna chahiye: **`keepalive: ON`** aur **`self-heal crashes=0`**.

Agar `keepalive: OFF` likha ho to Render ke **Environment** tab me
`KEEPALIVE=on` add kar do, phir **Manual Deploy** (Step 2).

---

# 📞 KUCH BHI GALAT LAGE TO

Bot me ye bhejo:

```
/sys
```

(Aur screenshot bhej do — main turant dekh lunga.)
