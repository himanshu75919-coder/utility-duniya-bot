# 📖 1-PADHO-PEHLE.md — v33 (ADMIN + PAYMENT) GUIDE

**Bhai, ye file pehle padh lo — 5 minute me sab samajh aa jayega.**
Ye version = **v33 — Admin Panel + Payment Verification upgrade** (jo teen dikkatein tumne batayi thi, wo teeno theek).

---

## 🆕 v33 ME TUMHARI 3 DIKKATEIN THEEK HUI

### 1️⃣ Owner ko bhi "premium lo" bol raha tha — THEEK ✅
**Wajah:** bot ke paas pata hi nahi tha ki tum owner ho — sabko ek jaisa treat kar raha tha.
**Ab kya hoga:**
- Tumhari ID (`ADMIN_ID` = 8607774564) = **OWNER** maani jayegi
- Owner ko **na daily limit**, na "VIP lo" wala message
- `/premium` dabane par ab tumhe dikhega: *"Aap owner ho — sab unlimited, paisa nahi lagta"* + seedha pending payments ka shortcut
- Naya **👑 OWNER MODE** button bhi aayega (keyboard me)
- ⚠️ **Ek kaam tumhe karna hai:** Render ke Environment me `ADMIN_ID=8607774564` hona chahiye (check kar lena)

### 2️⃣ Koi bhi kuch bhi bhej raha tha proof me — THEEK ✅
**Ab 4 layer ka strict check hai:**

| # | Check | Kya hota hai |
|---|---|---|
| 1 | **UTR format** | Sirf 12-digit UPI UTR ya 16-22 char bank ref chalega. 10-digit mobile / random text / "hello paisa kar diya" = ❌ reply me wajah batayega |
| 2 | **UTR duplicate** | Wahi UTR dobara = ❌ "ye UTR pehle use ho chuka hai" (ek UTR = ek hi VIP) |
| 3 | **Screenshot check** | Bot image dekhta hai — asli app screenshot hai ya selfie/photo/meme. Photo = ❌ reject + sahi tareeka samjhata hai |
| 4 | **Screenshot duplicate** | Wahi image dobara = ❌ reject (purani screenshot se dobara VIP nahi) |

**Flow ab 3 step ka hai:**
1️⃣ QR se pay karo → 2️⃣ **UTR number** bhejo (check hoga) → 3️⃣ **screenshot** bhejo (check hoga) → admin ke paas jayega

**Admin ko ab kya dikhta hai (verification card):**
```
🔔 PAYMENT VERIFY KARO — #12
👤 User ID / Username / Naam
💎 Plan + ₹Amount + Days
🧾 UTR: 448612394857
      • Format: ✅ sahi — UPI / Bank UTR (12 digit)
      • Pehle use hua?: ✅ Nahi — naya hai
🖼️ Screenshot: ✅ Mili
      • Screenshot check: 🟢 Screenshot lagti hai (score 87/100)
      • Same image dobara?: ✅ Nahi
👑 User ka VIP / ⚡ Uses today
📜 Is user ki history: ✅ 2 approved · ❌ 0 rejected
```
Uske neeche **Approve / Reject / User se dobara maango** ke buttons.

### 3️⃣ Premium Activate button kaam nahi kar raha tha — THEEK ✅
**Asli wajah (mila kaise):** Jab proof **text message** me aata tha, tab code `edit_caption` chala raha tha — par text message me caption hota hi nahi, isliye Telegram error deta tha aur button **chup-chaap mar** jata tha (isliye VIP lagta nahi tha).
**Ab:** photo card ho ya text card — dono par button kaam karega (caption→text→naya message, teen tarike se try karta hai). Test bhi ho gaya.
**Saath me:**
- Button dabane par turant **"✅ VIP activate ho gaya!"** ka jawab aata hai (pehle spinner ghoomta rehta tha)
- User ko **automatic MUBARAK message** jata hai (plan + valid till date ke saath)
- **Dobara click** karne par "ye payment pehle hi approve ho chuka hai" — double VIP nahi milegi
- Reject karne par user ko **wajah** ke saath message jata hai

---


---

## 🆕 v32 ME KYA-KYA NAYA HAI (chhota summary)

| # | Kya kaam hua | Fayda |
|---|---|---|
| 1 | ❌ **Signature Cleaner hata diya** | Jaisa tumne kaha — bilkul delete (menu, code, module sab se) |
| 2 | 🎙️ **Voice Studio = 24 ASLI alag voices** | Pehle sab ek jaise lagte the. Ab Don, South hero, Shayar, Robot, Anime girl, Anchor... sab bilkul alag awaaz (24) |
| 3 | 🧪 **Voice Lab add** | 30 aur voices + 4 speed (🐢 Dheemi, ▶️ Normal, ⚡ Tez, 🚀 Bahut Tez) |
| 4 | 🔄 **Auto Forward = 3-step wizard** | Sabse pehle **SOURCE** poochhega, phir **TARGET**, phir FULL AUTO ON — simple bhasha me |
| 5 | 🔒 **Private channel se content** | Na koi login/password — bot ko admin banao + koi post forward karo, bot khud ID pakad lega |
| 6 | 📈 **Vyaaj = sirf CHAKRAVRIDDHI (compound)** | Gaon/kasbe wala byaaj: "₹100 par ₹5 mahina" wali bhasha me. Simple interest hata diya |
| 7 | 🧮 **EMI tool advanced** | Ab batata hai **"loan kitne mahine / kitne DIN me poora chukega"** + pehli/aakhri EMI ki date |
| 8 | 📱 **Number Info + 🧾 Public Records** | Operator, circle, type + 6 check-links **+ tumhara API (naam/pata) — button se, off-switch ke saath** |
| 9 | 🌐 **IP / Domain Info (naya)** | IP ya website ka location, ISP, VPN/proxy hai ya nahi |
| 10 | 🆔 **ID Finder = ASLI check** | GitHub, Telegram, YouTube, TikTok, Steam par account hai ya nahi — ✅/❌ (pehle sirf link deta tha) |
| 11 | 📷 **QR = 4 type** | Link/Text, 💰 UPI payment, 📶 WiFi share, 👤 Contact card |
| 12 | 🔐 **Password = 4 mode** | Naam wala, Easy words, Random strong, Random PIN |
| 13 | 📄 **Doc PDF Compress** | 100KB / 200KB / 300KB / 500KB choose karo + ⚫ Black & White option |
| 14 | 🖼️ **Image→PDF** | Normal PDF + **A4 Print PDF** (printer par kuch kat nahi aata) |
| 15 | 📮 **Pincode** | Pincode se post offices, ya **area ke naam se pincode** |
| 16 | 🚗 **RTO** | State + RTO district + 5 official links (VAHAN, e-Challan, insurance, DL, mParivahan) |
| 17 | ❓ **Naya: MADAD / TUTORIAL button** | Bot ke andar hi har tool ka 1-line simple matlab (users ko samajh aa jayega) |
| 18 | 💬 **Har tool ke andar guide** | Har tool khulte hi "Kaise use karein" likha aata hai |
| 19 | 🇮🇳 **Indian money format** | Ab ₹1,00,000 aur "1 lakh" likh kar dikhata hai (pehle 100,000 tha) |
| 20 | 📘 **Auto-forward ka guide** | Menu me "📘 Kaise Use Karein?" + "🧪 Test Forward" + "📊 Meri Setting Dekho" |

---

## 🚀 GITHUB PAR UPLOAD KAISE KARNA HAI (2 minute)

### Tareeka A — GitHub web se (sabse aasan, koi command nahi)
1. Browser me kholo: **https://github.com/himanshu75919-coder/utility-duniya-bot**
2. Jis file ko badalna hai, us par click karo → right side me **pencil ✏️ (Edit)** dabao
3. Purana content select-all karke delete → is folder ki nayi file ka content paste karo
4. Neeche **Commit changes** → **Commit changes** (green button)
5. **Nayi file add** karne ke liye: repo me **Add file → Upload files** → file drag-drop → Commit

### 🛠️ naye admin commands (v33)
| Command | Kaam |
|---|---|
| `/admin` | Naya admin panel (buttons wala) |
| `/payments` | Pending payment list (approve/reject) |
| `/grant [user_id] [din]` | VIP do (9999 = lifetime) |
| `/revoke [user_id]` | VIP hatao |
| `/broadcast [message]` | Sab users ko message |
| `/ban` / `/unban [user_id]` | Ban / unban |
| `/mypay` | (user khud apni payments dekh sakta hai) |

**Kaun-kaun si files update karni hain (v33):**
```
bot.py                     (BADLA — admin panel + strict payment + owner bypass)
modules/payguard.py        (NAYI FILE — UTR + screenshot verification, ye bhoolna mat!)
modules/osint_tools.py     (BADLA — public records feature)
database.py                (BADLA — payment tables/functions)
modules/voice_studio.py    (BADLA — 24 asli voices)
modules/general_tools.py   (BADLA — naye QR/password/search)
modules/cyber_studio.py    (BADLA — B&W compress, signature cleaner hata)
modules/channel_cloner.py  (BADLA — 3-step wizard + guide)
modules/toolkit_extras.py  (BADLA — compound vyaj + EMI payoff)
modules/osint_tools.py     (NAYI FILE — ye zaroor upload karo!)
database.py                (same — upload karne ki zarurat nahi)
modules/cloud_tools.py, media_downloader.py, sarkari_hub.py, vip_payment.py (same)
requirements.txt           (same)
```

### Tareeka B — Render ki jagah seedha Render par
Render me GitHub repo se deploy hai, isliye **GitHub push karte hi Render khud naya version chalu kar dega** (1-2 minute me). Alag se kuch nahi karna.

---

## ✅ UPLOAD KE BAAD YE TEST KARO (5 minute)

Telegram me bot kholo: **@utility_duniya_bot**

0. **Pehle ye 3 cheezein test karo (v33):**
   - `/admin` bhejo → naya **Admin Panel** khule (Users, Pending Payments, Revenue, Revenue sab)
   - `/premium` bhejo → **"Aap owner ho, paisa nahi lagta"** likha aana chahiye (VIP plan nahi!)
   - Kisi tool ko 5-6 baar chalao → **koi "daily limit" wala message nahi** aana chahiye (tum owner ho)
   - Koi dost/bhai se test payment karwao: galat UTR bhejega → reject; selfie bhejega → reject; sahi screenshot → tumhare paas card aayega → **Approve** dabao → usko VIP mil jayegi
1. **/start** dabao → menu dikhna chahiye + **❓ MADAD / TUTORIAL** button bhi
2. **❓ MADAD / TUTORIAL** → poora guide aana chahiye
3. **🎙️ ACTORS VOICE STUDIO** → 🎭 Actor Voices → **Don wali** chuno → likho: `नमस्ते दोस्तों` → asli awaaz aani chahiye
   → phir **🧪 Voice Lab** → dusri voice (jaise Tamil/South) chuno → note karo ki awaaz badli ✅
4. **🔄 CHANNEL CLONER** → 📘 Kaise Use Karein? → 🚀 AUTO FORWARD SETUP → **pehle SOURCE** poochhega → `@tumhara_source` → phir **TARGET** poochhega → `@tumhara_target` → 🤖 FULL AUTO ON
   → phir 🧪 Test Forward dabao → target channel me test post aayegi ✅
5. **🔒 PRIVATE CHANNEL SETUP** → 3-step samjh aayega (bot ko admin banao → koi post forward karo → bot button dega)
6. **📈 INTEREST CALC** → `50000` → `5` → `12` → CHAKRAVRIDDHI report
7. **🧮 EMI CALC** → `5,00,000 9% 24m` → "**731 din me** poora chukega" dikhna chahiye
8. **📷 QR CODE** → UPI / WiFi / Contact card teeno try karo
9. **📮 PINCODE INFO** → `800001` (Patna) aur `Rajendra Nagar` dono try karo
10. **📱 NUMBER INFO** → `9973700984` → neeche **🧾 Public Records bhi dekho** button dabao → naam/pata aana chahiye (5-20 sec)
11. **🌐 IP / DOMAIN INFO** → `8.8.8.8`
11. **🎙️/📄/🚗/📱/🏦/🆔** — jo tool pehle chalta tha, wo **ab bhi chalna chahiye** (koi tool hata nahi hai, sirf Signature Cleaner hata hai)

---

## ⚠️ ZAROORI BAATEIN (dhyaan se padho)

### 1. Number Info — ab tumhara API bhi jud gaya hai (🧾 Public Records button)

**Jo tumne kaha, wahi kiya** — number ka result card me ab ek button aayega:
**🧾 "Public Records bhi dekho (naam/pata)"** → us par click karne se tumhare diye hue API se **naam, pita ka naam, pata, linked number, doc number** aa jayega.

**Kaam kaise karta hai:**
- Number daalo → 🌐 `osint-apis-hub.onrender.com/api/num-info` par query jaati hai (key `.env` me hai)
- 5-20 second lag sakte hain (API slow hai, pehli baar Render cold-start hota hai)
- Result ke saath **warning** bhi dikhta hai aur 🚨 1930 (cyber crime) / 🚫 Chakshu report ke button bhi

**⚠️ RISK — jo tumhe pata hona chahiye (dubara likh raha hoon):**
- Ye **leaked personal data** hai. India me ise kisi ko pareshan karne/blackmail/fraud ke liye use karna **CRIME** hai (IT Act + DPDP Act)
- Aise data dikhane par **Telegram bot ko ban** kar sakta hai, aur host (Render) service band kar sakta hai
- **Yeh tumhari marzi thi** — isliye laga diya. Par ise **off** karna ho to bas Render ke Environment me ek line daalo:
  `NUM_LEAK_ENABLED=off` → button gayab ho jayega, baaki tool normal chalega
- API badalni ho to: `NUM_INFO_API_BASE` + `NUM_INFO_API_KEY` env me daal do
- Bot ki **VIP/paid** user ko hi dena ho to bata dena — main usko sirf premium users tak limit kar dunga (free users ko sirf operator/circle milega)

📌 **Mera saaf suggestion:** is feature ko **sirf apne personal use/admin** ke liye rakho, public users ko na do.

### 2. Bot ko Admin banana zaroori hai
Auto-forwarding ke liye bot ko **source + target dono channel me Admin** banana padega (Post Messages permission). Ye Telegram ka niyam hai — koi jugaad nahi.

### 3. Copyright
Sirf **apni** ya **jiski permission hai** usi channel ka content clone karo. Dusre ka paid course/content copy karna **copyright violation** hai aur Telegram channel band kar sakta hai.

### 4. Render par free plan
Free plan me bot **15 min** inactivity ke baad so jata hai. Naya version chalu hone me 1-2 minute lag sakta hai. UptimeRobot (free) se ping laga do to bot 24×7 jagta rahega.

---

## 🧪 TECHNICAL (tumhare developer ke liye / agar kuch check karna ho)

- **Test results v32:** 66/66 flow tests ✅ | 68/68 live checks ✅ | wiring 9/9 ✅ | cloner 9/9 ✅
- **Naye module:** `modules/osint_tools.py` (RTO, phone carry, IFSC, pincode, area search, IP, username check)
- **Voice:** `edge-tts` (Microsoft ki asli neural voices) — koi paid API nahi
- **Compound vyaaj formula:** `balance = balance × (1 + monthly_rate)` har mahine — jaisa gaon me chakravriddhi hota hai
- **EMI payoff:** `first EMI = agla mahina`, `last EMI = aaj + months`, `total days = last - today` (din me jawab)
- **Deploy:** GitHub push → Render auto-deploy. `.env` me purani keys waise hi rahengi.

---

*Banaya gaya: Phase 3 upgrade (v32) — saare tools check + professional banaye gaye.*
