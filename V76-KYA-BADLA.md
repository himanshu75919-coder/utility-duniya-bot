# v76.0 — FORTRESS (sirf CRASH-FIX)

> ⚠️ **Is release me KOI NAYA TOOL ADD NAHI HUA.**
> Sirf ek kaam hua hai: **bot ko crash hone se rokna**.
> Naye tool ke *ideas* neeche **sirf list** kiye gaye hain (Hissa 3) —
> unme se koi bhi bot me daala nahi gaya. Aap bataayein kaunsa chahiye,
> tabhi add hoga.

Test suite: **2,709 checks · 0 FAIL** (33 test files)
Baseline (v75.2) se compare kiya — **ek bhi purana check nahi toota**.

---

## 🚨 CRASH KYUN HO RAHA THA (asli wajah)

Bot mein pehle se memory-watchdog aur hang-watchdog the. Phir bhi Render par
bot baar-baar crash hota tha. Poore code ki khoj (29,000+ lines) ke baad
**3 asli kaaran** mile — teenon ab band hain:

### ❌ Kaaran 1: Cache jo kabhi saaf nahi hota → **OOM KILL**

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
- Saare cache ek **registry** mein → memory watchdog ek hi baar mein sab saaf karta hai
- Thread-safe (6 thread ek saath test kiya — zero crash)

**Fix hue:** `osint_hub`, `username_hunter`, `vehicle_tool`, `business_tools` (fonts)

---

### ❌ Kaaran 2: `/tmp` bhar jaata tha → **DISK FULL**

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

### ❌ Kaaran 3: Atke hue process → **RAM + CPU leak**

Download timeout hone par uska **ffmpeg process chalta rehta tha** — RAM aur CPU
khaata rehta. 20 aise process = Render free 512 MB full = OOM kill.
Pehle unhe koi maarta hi nahi tha.

**✅ AB** janitor unhe dhoondh kar maar deta hai (`psutil` ho to usse, warna `/proc` se).

---

## ➕ Bonus: `/sys` aur `/health` ab crash ka kaaran **dikhate** hain

```
🧹 JANITOR (v76 — khud safai):
   🗑️ 12 folder · 3 file hataye (24.5 MB free)
   👻 Atke hue process maare: 2
   🪣 Cache: 118/512 entry · 3 baar saaf
   💾 Disk: 41% bhari · 86 safai cycle
```

Telegram par `/sys` dabayein (sirf admin) — ab aap **seedha dekh sakte hain**
ki bot kyun slow/crash ho raha tha. Pehle ye sab andhera tha.

Live par bhi: `https://utility-duniya-bot.onrender.com/health`

---

## 🔒 JO KUCH NAHI CHHERA GAYA (aapke order ke mutabiq)

- ✅ **Koi bhi purana prompt nahi badla** — saare purane tools ke prompt waise hi
- ✅ **Koi naya tool / button add nahi kiya**
- ✅ Saare 12 Business Studio tool waise hi zinda
- ✅ `BIZ_MENU` 12, `PREMIUM_TOOLS` 37 — sab wahi (tests check karte hain)
- ✅ VIP / credits / referral / vault system jaisa tha waisa hi
- ✅ **Koi nayi dependency nahi** — `requirements.txt` wahi hai (deploy safe)

---

## 📂 Files

| File | Kaam |
|---|---|
| `modules/core/bounded.py` | **NAYI** — Bounded cache + global registry |
| `modules/core/janitor.py` | **NAYI** — Temp safai · process safai · disk watchdog |
| `tests/test_v86.py` | **NAYI** — 42 naye checks (crash-fix + regression) |
| `bot.py` | Janitor ON karna, cache registry, `/sys` + `/health` report |
| `modules/osint_hub.py` | Cache → bounded |
| `modules/username_hunter.py` | Cache → bounded |
| `modules/vehicle_tool.py` | Cache → bounded |
| `modules/business_tools.py` | Font cache → bounded |

---

# 🌱 Hissa 3 — AUR EARNING TOOLS KE IDEAS

> 👉 **Ye SIRF IDEAS hain. Inme se kuch bhi bot me add NAHI kiya gaya hai.**
> Neeche se jo pasand aaye, bata dijiye — main wahi add kar dunga.

## 🔥 Sabse zyada maang wale (pehle inpe sochiye)

| # | Idea | Kya banega | Kaun use karega | Kitni baar |
|---|---|---|---|---|
| 1 | 🧾 **Rent Agreement** | 11 mahine ka rent agreement (stamp-paper format) | Kirayedar + makan malik | Saal me 1 baar |
| 2 | 🧾 **Rent Receipt** | Kiraya ki rasid (HRA tax claim ke liye), ek page par 3 | Kirayedar | **Har mahine** |
| 3 | 📒 **Udhaar Khata** | Dukaan ka ledger — udhaar, jama, balance | Kirana / dukaandaar | **Roz** |
| 4 | 🧾 **Fee Receipt** | School / coaching ki fee rasid | School, coaching | **Har mahine** |
| 5 | 📊 **GST Bill Register** | Poore mahine ke bill ek register me + GSTR-1 summary | Har dukaandaar | **Har mahine** |
| 6 | 👷 **Labour / Mistri Payment Slip** | Daily-wage worker ka payment record | Construction, factory | **Roz** |
| 7 | 📦 **Stock / Inventory Sheet** | Kya bacha, kya khatam, reorder list | Dukaandaar | Hafte me |
| 8 | 🎓 **Marksheet / Result Card** | School ka result card | School | Saal me |
| 9 | 💰 **Salary Slip Pack** | Ek baar me 10 staff ki salary slip | Chhoti company | **Har mahine** |
| 10 | ⏰ **Udhaar Reminder** | "Aaj 3 grahak ko reminder bhejo" — bot khud yaad dilaye | Dukaandaar | **Roz** |

## 💎 Premium feel badhane wale

11. 🪪 **Digital Visiting Card** — ek link jisme card + call + WhatsApp + Google Maps location. Dukaandaar ₹199–₹499 de sakta hai.
12. 🛒 **WhatsApp Catalogue Maker** — product photo + rate → catalogue PDF.
13. 🖼️ **Social Media Kit** — ek hi design me Instagram post + story + WhatsApp status.
14. 🎉 **Birthday / Anniversary Poster** — dukaan ka brand lagakar (har din kisi na kisi ko chahiye, viral bhi hota hai).
15. 🏪 **Shop Banner / Flex Design** — dukaan ke bahar lagane wala flex (festival + offer).
16. 📜 **Legal Notice Pack** — legal notice, rent notice, cheque-bounce notice.
17. 🏥 **Clinic Prescription Pad + Appointment Card**.
18. 🚚 **Delivery Challan / Transport Receipt**.
19. 🧮 **Business Loan / CC Calculator** — muddat, byaaj, EMI, total vyaj.
20. 📈 **Profit & Loss / Margin Card** — munafa, margin %, business health + salah.

## 💵 Kamai ka model (sabse zaroori)

| Tareeka | Kaise |
|---|---|
| **VIP subscription** | ₹99/mah · ₹249/3 mahine · ₹499/saal — unlimited sab tools |
| **Pay-per-file** | 10 credit free, uske baad ₹5–₹20 per file |
| **Reseller / bulk** | Dukaandaar ko 50-file pack ₹299 |
| **Apni branding** | Har document me dukaan ka naam/logo — log apna brand dekh kar khareedte hain |
| **Referral** | Pehle se hai — "5 dost lao, 1 mahina free VIP" |

> 💡 **Sabse tez kamai wala combo:** Rent Receipt + Rent Agreement + Fee Receipt +
> Udhaar Khata. Ye *mahine / roz* ke hisaab se chalte hain — matlab user
> baar-baar aayega. Ek baar aaya user = lifetime customer.

> 🎯 **Sabse zyada premium feel:** Digital Visiting Card + Social Media Kit —
> inme dukaan ka apna brand dikhta hai, isliye log paisa dene ko taiyaar rehte hain.

---

## ✅ Kaise verify karein

```bash
# poora test suite
python3 -m pytest tests/ -q

# sirf v76 ke crash-fix tests
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
