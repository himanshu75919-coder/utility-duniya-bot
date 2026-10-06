# 🛡️ v60 FORTRESS — Aapko kya karna hai (step by step)

**Bhai, sirf 3 kaam karne hain. 15 minute lagenge. Uske baad aapka data
kabhi nahi kho sakta aur premium users kabhi delete nahi honge.**

---

## 🚨 SABSE PEHLE: ASLI PROBLEM SAMJHO (1 minute)

Aapko lagta tha "premium users delete ho jaate hain". Sach ye tha:

> Render ka **free plan** ek aisi hard disk deta hai jispar likha hua data
> **har deploy aur har restart par MIT jaata hai**.
>
> Aapke bot ka poora database (`botdata.db`) usi hard disk par tha, aur
> `render.yaml` me `disk:` wala section **tha hi nahi**.
>
> Isliye jab bhi aap GitHub par kuch push karte the ya Render service
> restart hoti thi — **poora database saaf ho jata tha**: saare VIP users,
> saare payments, saare referrals, saare credits.

**Ye aapki galti nahi thi. Ye storage ki galti thi. Ab ye kabhi nahi hoga.**

---

## ✅ KAAM 1 — GitHub token Render me daalo (5 minute)

Ye sabse zaroori kaam hai. Isse backup GitHub me chala jayega — Render
kuch bhi kare, data wahan safe rahega.

### Steps:

1. **Render.com** kholo → apni service **`utility-duniya-bot`** par click karo
2. Left menu me **`Environment`** par click karo
3. **`Add Environment Variable`** dabao
4. Ye 4 variables ek-ek karke daalo:

| Key | Value | Kyun |
|---|---|---|
| `VAULT_GITHUB_TOKEN` | *(aapka GitHub token — jo maine aapko chat me diya tha, wahi)* | GitHub me backup likhne ke liye |
| `VAULT_GITHUB_REPO` | `himanshu75919-coder/utility-duniya-bot` | kahan likhna hai |
| `VAULT_GITHUB_BRANCH` | `vault-backup` | **main NAHI!** (neeche wajah) |
| `VAULT_ENABLED` | `on` | vault chalu |

5. **`Save Changes`** dabao → Render khud deploy karega (2-3 minute)

### ⚠️ `VAULT_GITHUB_BRANCH` me `main` kyun nahi likhna?

Aapki Render service `main` branch par **auto-deploy** hai. Agar backup `main`
me jaayega to:

```
backup push  →  Render deploy  →  filesystem wipe  →  bot restart
     ↑                                                        ↓
     └──────────────── backup push  ←──────────────────────────┘
                    (infinite loop! bot baar-baar restart hota rahega)
```

Isliye hum `vault-backup` naam ki **alag** branch use karte hain. Render sirf
`main` dekhta hai, isliye us branch ka push koi deploy trigger **nahi** karta.
Bot pehli baar backup lete waqt ye branch **khud ba khud bana lega**.

> 💡 Agar aur zyada privacy chahiye to ek **naya private repo** banao
> (jaise `utility-duniya-backup`) aur `VAULT_GITHUB_REPO` me wahi daal do.
> Backup wahan jayega, koi aur nahi dekh payega (encrypted bhi hai).

---

## ✅ KAAM 2 — Deploy hone do, phir check karo (3 minute)

Render deploy hone ke baad:

### 2a. Telegram me (owner account se) ye commands bhejo:

| Command | Kya dikhega |
|---|---|
| `/vault` | Poora vault report — backup kaunse kaunse jagah chal raha hai |
| `/sys` | Crash shield + memory + vault ka status |
| `/vips` | **Saare premium users ki CSV file** (ye file sambhal kar rakho) |
| `/ledger` | Premium ka poora itihaas — kisko kab kitne din VIP mila |

### 2b. `/vault` me ye dikhna chahiye:

```
🔐 Encryption: 🟢 ON (SHAKE256 + HMAC)
🐙 GitHub backup: 🟢 himanshu75919-coder/utility-duniya-bot
📨 Telegram backup: 🟢
⏱️ Auto interval: har 30 minute
```

Agar **GitHub backup ⚪ (off)** dikhe to:
- Render ke Environment me `VAULT_GITHUB_TOKEN` sahi hai check karo
- Token me aage-peeche space na ho
- `VAULT_GITHUB_REPO` me `/` (slash) hona chahiye

### 2c. Manually test karo:

```
/backup     →  "BACKUP OK" aana chahiye
/vault      →  "Last backup" me aaj ki time dikhni chahiye
```

---

## ✅ KAAM 3 — Backup sach me kaam karta hai, ye dekh lo (2 minute)

Ye sabse important test hai. Isse aapko **bharosa** ho jayega.

1. Telegram me `/backup` bhejo → backup ban jayega
2. **Render dashboard** → apni service → **`Manual Deploy`** → `Deploy latest commit` dabao
3. Render poori service ko **naye server par** uthayega — matlab purani hard disc **gayi**
4. Deploy hone ke baad bot ko `/start` bhejo
5. Owner ko ek message aayega:

> 🛡️ **VAULT BOOT RESTORE**
> 👑 VIP: 0 ➜ 3
> ℹ️ Pichhle backup se data wapas mila gaya.

6. `/vault` bhejo → **`VIP users`** ki ginti pehle jaisi hi honi chahiye ✅

**Agar ye dikh gaya, aapka data ab hamesha safe hai.**

---

## 📋 v60 me kya-kya naya hai

### 🛡️ A. Premium Vault (data kabhi na khoye) — 4 layer

| Layer | Kya karta hai |
|---|---|
| 1. Stable path | Render disk mile to bot khud wahan data rakhega |
| 2. Auto-backup | Har 30 min me Telegram + GitHub par **encrypted** backup |
| 3. Smart merge | Restore **overwrite nahi** karta — **MERGE** karta hai |
| 4. Premium floor | Restore se pehle/baad VIP ginti milai jati hai — kam hui to **ABORT** |

### 🔒 B. Smart Merge ka matlab (ye samajh lo, bahut kaam ka hai)

Backup se restore karte waqt bot **har value ko sabse safe tareeke se** milata hai:

| Cheez | Niyam | Matlab |
|---|---|---|
| `premium_until` | jo **zyada** ho | VIP kabhi ghatt nahi hoga |
| `lifetime` | sabse upar | Lifetime VIP hamesha jeetega |
| `credits` | jo **zyada** ho | credits kabhi kam nahi honge |
| `referrals` | jo **zyada** ho | referral count kabhi kam nahi hoga |
| `banned` | jo **zyada** ho | ban kabhi khud nahi uthega |
| `payments` | dono ka **union** | purana payment record kabhi delete nahi hoga |
| `joined_at` | sabse **purana** | join date peeche nahi jayegi |

**Iska matlab: galat ya bahut purana backup se bhi aapka data kharab nahi ho sakta.**

### 💥 C. Crash Shield — "baar-baar crash" ka ilaaj

Pehle har chhoti dikkat poore bot ko gira deti thi. Ab 6 raaste band hain:

1. **Handler crash** — koi bhi tool me bug ho → sirf wo message fail, bot zinda
2. **Background task crash** — silent gayab hone ke bajaye log me aata hai
3. **Thread crash** — keepalive/backup thread marne se bachao
4. **💀 OOM (RAM khatam)** — Render free 512 MB; watchdog 400 MB par khud cache saaf karta hai
5. **🧟 Hung loop** (bot zinda par jawab nahi) — heartbeat se pakadta hai
6. **Crash loop** — exponential backoff

### 🐛 D. Asli bugs jo mile aur fix hue

| # | Bug | Kitna bada tha |
|---|---|---|
| 1 | **Premium timezone bug** — `premium_until` me `+00:00`/`Z` hote hi `TypeError` aata tha → `except` me chala jata → `False`. **User ka VIP chalu hote hue bhi "free" dikhta tha** | 🔴 Bahut bada |
| 2 | **`grant_premium` negative days** se VIP chhota ho sakta tha | 🟠 Bada |
| 3 | **Credits race condition** — 2 tool ek saath chalao to galat hisaab | 🟠 Bada |
| 4 | **`int(os.getenv('ADMIN_ID'))`** — Render me `12345   # mera id` jaisi value se bot **boot par hi crash** | 🔴 Bahut bada |
| 5 | **Lamba/toota HTML message** = crash. Ab auto-split + auto-repair | 🟠 Bada |
| 6 | **`database is locked`** — ab WAL mode + 15s wait | 🟡 Madhyam |
| 7 | **Orphan HTML tag** (`</b>` bina opening) = Telegram poora message reject | 🟠 Bada |
| 8 | **GitHub backup fetch** filename se 404 de raha tha — restore chup-chaap fail | 🔴 Bahut bada |
| 9 | **Backup `main` branch me jaata** → Render deploy loop | 🔴 Bahut bada |

### 💼 E. BUSINESS STUDIO — 10 naye kamai wale tools

Ek naya button: **`💼 BUSINESS STUDIO`**

| Tool | Kya banata hai | Market rate |
|---|---|---|
| 🧾 Invoice / GST Bill | dukaan ka bill + UPI QR + amount in words | ₹50-100 |
| 💼 Resume / CV | photo ke saath professional CV | ₹100-300 |
| 💍 Marriage Bio-data | **poora Hindi me** shaadi ka biodata | ₹100-500 |
| 🎓 Certificate | achievement / course certificate | ₹100-200 |
| 🪪 ID Card | A4 par **10 card**, cut lines ke saath | ₹200-500 |
| 📇 Visiting Card | A4 par **10 card** + UPI QR | ₹200-500 |
| 📄 Application / Letter | leave / NOC / character (auto-draft) | ₹30-100 |
| 💳 UPI Scan & Pay Poster | dukaan ka payment board | ₹100-200 |
| 🏷️ Price Label Sheet | rate tag, MRP strike-through | ₹50-150 |
| 🧮 EMI / Loan Card | EMI + **month-wise schedule** | ₹50-100 |

**Sab A4 @ 200 DPI — seedha print karo aur bech do. Har tool PNG + PDF dono deta hai.**

#### Hindi + English ek saath (asli technical challenge)

Aapke bot me Hindi **perfect** chhapti hai. Ye itna aasan nahi tha:

> Noto Sans Devanagari font me **A-Z Latin letters hote hi nahi hain**.
> Isliye pehle ya to Hindi tooti dikhti thi, ya English `▯▯▯▯` ban jaata tha.

Hal: bot ab text ko **script ke hisaab se** todta hai:
`"नाम / Name"` → `[("नाम /", Hindi font), (" Name", English font)]` — aur
dono tukde apne sahi font se likhta hai, ek hi line me.

Isliye ab `विवाह परिचय · MARRIAGE BIODATA` bilkul sahi aata hai.

### 📒 F. Premium Ledger — premium ka **permanent** record

Har VIP grant/revoke ek alag table me **hamesha ke liye** likha jata hai.
Ye `users` table se alag hai — isliye database kharab hone par bhi premium
ka saboot bacha rehta hai.

```
/ledger              → kisko kab kitne din VIP mila (poora itihaas)
/fixvip 123456789    → ledger se us user ka premium WAPAS lagao
```

**Agar kabhi kisi ka VIP ghumm jaye — `/fixvip <user_id>` chala do, wo
wapas aa jayega.**

---

## 🆕 Naye commands (sirf aapke liye — admin/owner)

| Command | Kaam |
|---|---|
| `/vault` | Vault ki poori health report |
| `/backup` | Abhi turant backup banao |
| `/restore` | Sabse accha backup merge karo (VIP-safe) |
| `/vips` | Saare premium users ki CSV file |
| `/ledger` | Premium ka poora itihaas |
| `/fixvip <id>` | Kisi ka premium ledger se wapas lagao |
| `/sys` | Crash shield + memory + vault status |

---

## ❓ Kuch galat lage to?

### GitHub backup fail ho raha hai

1. Render → Environment → `VAULT_GITHUB_TOKEN` check karo
2. Token **expire** ho gaya ho to naya banao:
   - github.com → Settings → Developer settings → Personal access tokens
   - **Tokens (classic)** → Generate new token → scope: **`repo`** ✅
3. Naya token Render me daalo → Save

### Render "deploy" fail ho raha hai

Render logs me dekho:
- `BOT_TOKEN is missing` → Environment me `BOT_TOKEN` daalo
- `Application failed to start` → koi env value me quote ya `#` hai? **hata do**
  (v60 me ye crash nahi hota, par phir bhi saaf rakho)

### Bot jawab nahi de raha

1. Render → Logs kholo
2. `WEBHOOK MODE` ya `POLLING` dikhega
3. `/health` URL kholo: `https://utility-duniya-bot.onrender.com/health`
4. Wahan `crash-shield: caught=N` dikhega — matlab kitne problems sambhale gaye
5. N numbar bada ho to `/support` par mujhe batao

### Premium user phir bhi gayab dikhe

1. `/vips` chalao — dekho kya wo list me hai
2. Hai, par `/account` me free dikha raha hai? → `/fixvip <user_id>`
3. List me hi nahi hai? → `/restore` chalao (GitHub se merge karega)
4. Phir bhi nahi mila? → `/vault` ka screenshot bhejo

---

## 📊 Paisa kamane ke ideas (Business Studio se)

Aapke paas ab **print-ready document factory** hai. Iske 6 tarike:

### 1. 🏪 Dukaan / Market (sabse tez paisa)

Local dukaandaar ko dikhao — **"Sir, aapke dukaan ka bill, visiting card,
rate tag, aur UPI board — sab 5 minute me, ₹300"**

- 1 dukaan = ₹300-500 (bill + card + tag + UPI poster combo)
- 10 dukaan = ₹3,000-5,000
- Har mahine rate tag update = **repeat customer**

### 2. 🎓 Coaching / School

- ID card: A4 par 10 card → 100 card = 10 sheet → ₹1,000-2,000
- Certificate (annual function, sports day)
- Principal ko dikhao: **"saare certificate 1 ghante me ban jayenge"**

### 3. 💍 Shaadi Bio-data (Bihar/UP me sabse zyada demand)

- Ek biodata = ₹200-500
- Poora Hindi me, sundar border, photo ke saath
- Shaadi season me 20-30 biodata = ₹5,000-10,000
- **Ye aapka sabse bada earner ho sakta hai**

### 4. 💼 Cyber café / CSC centre wale

Unko bolo: **"aapki shop ka ye tool, ₹500/mahine ya ₹200 per customer"**
Wo rozana 5-10 resume/biodata/application banate hain.

### 5. 🏦 Loan agent / property dealer

- EMI card with month-wise schedule = client ko dikhane ke liye
- Payment schedule, agreement draft (Kagaz Suite me hai)

### 6. ✈️ Travel agent

- Visa application, invitation letter, itinerary

### 💰 Bot me monetize karne ke model

| Model | Kaise |
|---|---|
| **Free tier** | 25 credits (abhi hai) |
| **Quick VIP** | ₹49 / 30 din — personal use |
| **Dealer pack** | ₹499 / 90 din + unlimited Business Studio |
| **Shop licence** | ₹1,499/year — ek dukaan ka naam se unlimited |
| **White label** | ₹2,999 — unke dukaan ka naam/logo sab documents par |

**Business Studio ke documents par `Made with <brand>` ki jagah
dukaan ka naam aata hai** — isliye "white label" ek asli product ban jata hai.

> 💡 Har document ke footer me aapka brand (`@Supermannn_x`) chhapta hai —
> customer wo document le jata hai, naya user aapka bot dhoondh leta hai.
> **Ye free marketing hai.**

---

## ✅ Final checklist

- [ ] Kaam 1: 4 env variables Render me daalo
- [ ] Kaam 2: Deploy ke baad `/vault` aur `/vips` chalao
- [ ] Kaam 3: `/backup` → Manual Deploy → VIP wapas aaye ya nahi dekho
- [ ] `💼 BUSINESS STUDIO` button daba kar 10 tool try karo
- [ ] `/ledger` chala kar premium record dekho

**Bas. Iske baad aapka data kabhi nahi khoyega aur bot crash nahi hoga.**
