# v76.0 — FORTRESS + EARN STUDIO

**Ek line me:** Bot ab *crash-proof* hai (3 chhupe kaaran khatam) aur 5 **naye kamai wale** tools jud gaye hain.

Test suite: **2,981 checks · 0 FAIL** (33 test files)

---

## 🚨 Hissa 1 — CRASH KYUN HO RAHA THA (aur kya fix hua)

Bot mein pehle se memory-watchdog aur hang-watchdog the. Phir bhi Render par bot
baar-baar crash hota tha. Poore code ki khoj (29,000+ lines) ke baad **3 asli
kaaran** mile — teenon ab band hain:

### ❌ Kaaran 1: Cache jo kabhi saaf nahi hota (OOM KILL)

```python
# PEHLE (modules/osint_hub.py, username_hunter.py, vehicle_tool.py)
_CACHE: dict = {}          # ← har nayi query = PAKKI entry, kabhi delete nahi
```

Har naya IMEI / username / number-plate / website ek nayi entry banata tha.
Din bhar mein hazaaron, hafton mein lakhon entry → RAM bhar jaati →
Render free (**512 MB**) bot ko **OOM KILL** kar deta tha. Log mein sirf
`Killed` likha aata tha — samajh hi nahi aata tha kyun.

**✅ AB — `modules/core/bounded.py` (nayi file)**

```python
_CACHE = BoundedCache("osint_hub", maxsize=512, default_ttl=300)
```

- Zyada se zyada 512 entry — usse aage purani apne aap nikal jaati hai (LRU)
- TTL khatam → entry apne aap hat jaati hai
- Saare cache ek **registry** mein → memory watchdog ek hi baar mein sab saaf kar deta hai
- Thread-safe (6 thread ek saath test kiya — zero crash)

**Fix hue:** `osint_hub`, `username_hunter`, `vehicle_tool`, `business_tools` (fonts)

---

### ❌ Kaaran 2: `/tmp` bhar jaata tha (DISK FULL)

Media tools `tempfile.mkdtemp(prefix="udl_")` banate hain. Agar download ke
beech error aaye to `shutil.rmtree` tak pahunch hi nahi paata — folder
**chhoot jaata hai**. Din bhar mein 500 MB kachra → disk full →
ffmpeg likh hi nahi paata → tool fail.

**✅ AB — `modules/core/janitor.py` (nayi file): khud-safai**

| Kaam | Kitni baar |
|---|---|
| Purane `udl_*` / `qsc_*` / `ud_*` folder-file hatana | har 10 min |
| Atke hue **ffmpeg / yt-dlp** process maarna | har 10 min (30 min purane) |
| Expire cache entry nikalna | har 10 min |
| Disk **88%** se upar → turant aggressive safai | turant |

⚠️ **Suraksha:** sirf `udl_`, `qsc_`, `ud_`, `udv`, `ud_q_` prefix wali cheezein
chhoo-ta hai — kisi doosre program ki file ko haath nahi lagata (test mein check hai).

---

### ❌ Kaaran 3: Atke hue process (RAM + CPU leak)

Download timeout hone par uska **ffmpeg process chalta rehta tha** — RAM aur CPU
khaata rehta. 20 aise process = Render free 512 MB full = OOM kill.
Pehle unhe koi maarta hi nahi tha.

**✅ AB** janitor unhe dhoondh kar maar deta hai (`psutil` ho to usse, warna `/proc` se).

---

### ➕ Bonus: `/sys` aur `/health` ab aur bhi zyada batate hain

```
🧹 JANITOR (v76 — khud safai):
   🗑️ 12 folder · 3 file hataye (24.5 MB free)
   👻 Atke hue process maare: 2
   🪣 Cache: 118/512 entry · 3 baar saaf
   💾 Disk: 41% bhari · 86 safai cycle
```

Ab aap `/sys` dabakar **seedha dekh sakte hain** ki bot kyun slow/crash ho raha hai.

---

## 💰 Hissa 2 — 5 NAYE KAMAI WALE TOOLS (EARN STUDIO)

Naya main-keyboard button: **💰 EARN STUDIO**

| Tool | Kya banta hai | Kaun use karega | Kitni baar |
|---|---|---|---|
| 🧾 **Rent Receipt** | Ek A4 page par **3 kiraya rasid** (revenue-stamp box, PAN, HRA ke liye) | Kirayedar + makan malik | **Har mahine** |
| 📒 **Udhaar Khata** | Dukaan ka ledger — udhaar, jama, running balance, net baaki | Kirana/dukaandaar | **Roz** |
| 🎨 **Offer Poster** | HD 1080×1920 poster — Diwali/Holi/Sale/Opening (9 themes) | Har dukaan | **Har tyohar** |
| 💼 **Quotation** | Professional estimate — items, GST, validity, terms | Contractor, designer, electrician | Kaam ke hisaab se |
| 📈 **Profit Card** | Munafa/nuksan + margin % + business health + salah | Har business owner | Mahine mein |

**Kyun ye 5?** Kyunki inki maang *roz / har mahine* ki hai — matlab user
baar-baar aayega. Ye sab **100% offline** hain (koi API kharidni nahi padti,
koi monthly bill nahi). PNG **+ PDF** dono bhejta hai.

Kaise chalega: `💰 EARN STUDIO` → tool chuno → **step-by-step** sawalon ke
jawab do → file tayyar. Chahein to **ek line** mein bhi likh sakte hain.

---

## 🔒 Hissa 3 — JO NAHI CHHERA GAYA

Aapke order ke mutabiq:

- ✅ **Koi bhi purana prompt nahi badla** — saare 22 purane tool ke prompt waise hi hain
- ✅ Saare 12 purane Business Studio tool waise hi zinda (tests check karte hain)
- ✅ VIP / credits / referral / vault system jaisa tha waisa hi
- ✅ Naye tools ke liye **naye** prompt add kiye (purane chhune nahi gaye)
- ✅ **Koi nayi dependency nahi** — `requirements.txt` wahi hai (deploy safe)

---

## 📂 Nayi files

| File | Kaam |
|---|---|
| `modules/core/bounded.py` | Bounded cache + global registry |
| `modules/core/janitor.py` | Temp safai · process safai · disk watchdog |
| `modules/earn_studio.py` | 5 naye kamai wale tools |
| `tests/test_v86.py` | 126 naye checks |

**Badli gayi:** `bot.py`, `modules/osint_hub.py`, `modules/username_hunter.py`,
`modules/vehicle_tool.py`, `modules/business_tools.py`

---

## 🌱 Hissa 4 — AAGE KYA-KYA ADD KAR SAKTE HAIN (aur earning ideas)

Yeh woh tools hain jinse aage **sabse zyada kamai** ho sakti hai. Priority ke hisaab se:

### 🔥 Pehle ye (sabse zyada maang)

1. **🧾 Kiraya Agreement (Rent Agreement)** — 11 mahine ka rent agreement, stamp paper
   ke saath. Rent receipt ka *natural next step* — same user khareedega.
2. **📊 GST Bill Book (monthly register)** — poore mahine ke bill ek register me,
   GSTR-1 jaisa summary. Dukaandaar ko har mahine chahiye.
3. **🧮 Business Loan / CC Calculator** — muddat, byaaj, EMI, total vyaj.
4. **👷 Labour / Mistri Payment Slip** — daily-wage workers ka payment record
   (construction, factory — Bahut bada market).
5. **🏪 Shop Stock / Inventory Sheet** — kya bacha, kya khatam, reorder list.
6. **📅 EMI Reminder / Udhaar Reminder** — "aaj 3 grahak ko reminder bhejo"
   (bot khud yaad dilaye) — retention badhata hai.
7. **🎓 School / Coaching Fee Receipt** — har mahine, har student.
8. **🧾 Payslip Pack (10 staff ek saath)** — ek baar mein 10 salary slip.

### 💎 Premium feel badhane wale

9. **🪪 Digital Visiting Card (link + QR)** — ek link, jisme card + call + WhatsApp
   + Google Maps location. Dukaandaar ₹199–₹499 de sakta hai.
10. **🛒 WhatsApp Catalogue Maker** — product photo + rate → ek catalogue PDF.
11. **🖼️ Social Media Kit** — ek hi design me Instagram post + story + WhatsApp status.
12. **🎉 Birthday / Anniversary Wishing Poster** — dukaan ka brand lagakar
    (har din kisi na kisi ko chahiye — viral bhi hota hai).
13. **📜 Legal Notice / Notice Format Pack** — legal notice, rent notice.
14. **🏥 Medical / Clinic Prescription Pad + Appointment Card**.
15. **🚚 Delivery Challan / Transport Receipt.**

### 💵 Kamai ka model (sabse zaroori)

| Tareeka | Kaise |
|---|---|
| **VIP subscription** | ₹99/mah · ₹249/3 mahine · ₹499/saal — unlimited sab tools |
| **Pay-per-file** | 10 credit free, uske baad ₹5–₹20 per file |
| **Reseller** | Dukaandaar ko 50-file pack ₹299 (bulk) |
| **Apni branding** | Business Studio me dukaan ka naam/logo — log apna brand dekh kar khareedte hain |
| **Referral** | Pehle se hai — "5 dost lao, 1 mahina free VIP" |

> 💡 **Sabse tez kamai wala combo:** Rent Receipt + Rent Agreement + Fee Receipt.
> Ye teeno *mahine ke hisaab se* chalte hain, matlab user har mahine wapas aayega.

---

## ✅ Kaise verify karein

```bash
# poora test suite
python3 -m pytest tests/ -q        # ya: har file alag se chalayein

# sirf naye v76 tests
python3 tests/test_v86.py

# bot ki health (bina Telegram ke)
BOT_TOKEN=x ADMIN_ID=1 python3 bot.py --check
```

Telegram par bot kholo → `/sys` (sirf admin) → **JANITOR** aur **Cache** wala
block dikhna chahiye.

---

## ⚙️ Naye settings (Render → Environment)

Chahein to badal sakte hain, **default kaafi hai** (kuch set karne ki zaroorat nahi):

| Variable | Default | Matlab |
|---|---|---|
| `JANITOR_ENABLED` | `1` | `0` kar dein to safai band |
| `JANITOR_INTERVAL_MIN` | `10` | Safai ke beech ka waqt (minute) |
| `JANITOR_TMP_MAX_AGE_MIN` | `45` | Itne minute purani temp file hatayein |
| `JANITOR_PROC_MAX_AGE_MIN` | `30` | Itne minute purana ffmpeg maarein |
| `JANITOR_DISK_ALERT_PCT` | `88` | Disk itne % bhare to turant safai |
| `OSINT_CACHE_SIZE` | `512` | osint cache ki max entry |
| `UHUNT_CACHE_SIZE` | `512` | username hunter cache |
| `VEHICLE_CACHE_SIZE` | `512` | gaadi record cache |
