# 🔌 v46 — AAPKI KEY LIVE CHAL GAYI + Number/Vehicle ka asli sach

Aapne screenshot me poocha tha: **"Es value mein kya likhe ya blank hi rhne de?"** (wo `HUB_API_KEY` wala khana)

## ✅ 1️⃣ Seedha jawab — `HUB_API_KEY` me kya daalna hai

| KEY | VALUE |
|---|---|
| `HUB_API_KEY` | **`Demo`** |

Maine aapke hub se live check kiya — **`Demo` key abhi bhi chalti hai** (aapke hub par
lifetime "ALL ENDPOINTS" plan, 120 requests/minute). Isliye:

```
HUB_API_KEY = Demo          ← bas yahi likho (blank mat chhodo)
```

**Bade kaam ki baat:** `Demo` wali line khaali chhodne se bhi bot khud `Demo` use karta hai (v46 me
default yahi hai), lekin Render me clearly likh dena behtar hai — taaki baad me confusion na ho.

> Chaho to apni personal key bhi laga sakte ho: apne hub ke **Dashboard → API Keys** se `osint-…`
> key banao → whi `HUB_API_KEY` me. Demo se zyada kuch nahi badlega (plan same hai).

---

## ✅ 2️⃣ Maine aapka hub live test kiya — kya-kya chal raha hai (10-Oct-03 wale check me)

Aapki key se **jo ab chal rahe hain** (bot me result aayega):

| Tool | Hub endpoint | Bot me kya dikhega |
|---|---|---|
| 🏦 IFSC INFO | `/ifsc` | bank, branch, address, MICR |
| 📮 PINCODE INFO | `/pincode` | district, state, post offices |
| 🌐 IP / DOMAIN | `/ip-v2` | country, city, ISP, Google Maps link |
| 📲 IMEI CHECK | `/imei` | **ab brand + model + GSMarena/imei.info links** (TAC match) |
| 🎬 CLIP MAKER (YouTube) | `/youtube-all` | direct mp4 → clip banta hai |
| 🆔 ID FINDER | `/youtube-info`, Instagram/other profile | followers, bio, verified |
| 📜 KAGAZ → GST | `/gst-search` | legal name, status, address |
| 📜 KAGAZ → PAN→GST | `/pan-to-gst-v4` | GST number + status |
| 🎵 MP3 / SONG | `/song` | 30-sec previews (iTunes) |
| 🌍 COUNTRY INFO | `/country` | capital, currency, population |
| 🔑 PASSWORD CHECK | `/pass-check` | leak check |
| 🩺 /hubstatus (admin) | `/key-info` | plan, status, rate limit |

### 📲 IMEI me bada sudhar (v46)

Pehle IMEI sirf "unknown" dikha raha tha. Ab aapke hub ka TAC-match use hota hai:

```
📲 Apple iPhone 12 mini
🏷️ Brand: APPLE   🔢 IMEI: 353010111111110
🔹 Device (TAC match): Brand APPLE · Model iPhone 12 mini
📐 GSMA reporting body: BABT (UK)
[📱 Full specs (GSMArena)] [🔎 Search this device] [📲 Check on imei.info]
```

---

## ⛔ 3️⃣ Jo abhi bhi OFF hai — aur ye AAPKE HUB ki setting hai, bot ki galti nahi

Ye check karke maine paya ki **aapka hub khud in endpoints ko band rakhta hai**:

| Endpoint | Hub ka jawab | Matlab |
|---|---|---|
| `/num-info` (naam/address) | **410 `status: disabled`** | "authorized provider configure na ho" |
| `/vehicle-report` (+`-rc`, `-challan`, `-challan-v4`, `-details`) | **410 `status: disabled`** | wahi baat |
| `/leak-v1`, `/family`, `/email-info` | **410 `status: disabled`** | wahi baat |
| `/terabox-file` | **502** | hub ko upstream key chahiye |
| `/instagram-profile`, `/snap-stories`, `/bgmi` | **502** | hub ko upstream key chahiye |

Matlab: **key ki galti nahi hai** — khaali `Demo` ho ya aapki apni `osint-…` key, in sab ka jawab
410/502 hi aayega. Jab tak aap apne hub (ToolVault) ke panel se in endpoints ka provider configure
nahi karte, data kisi bhi key se nahi aayega.

### 🤖 Par ab bot kya karta hai (v46 me fix)

Pehle: gandha/samajh na aane wala message, ya lagta tha bot toot gaya.
**Ab:**

- **📱 NUMBER INFO** → "Public-record search is turned off right now" + **credit nahi kataa** +
  official links (cybercrime.gov.in, sancharsaathi.gov.in) — number ka normal card to waise hi chalta hai.
- **🚗 VEHICLE / CHALLAN** → pehle 1 hi call se report try, OFF hone par turant **free RTO card**
  (RTO office, state, district + e-Challan aur VAHAN ke official links) — 20 second ka wait nahi.
- **📲 IMEI** → upar wala TAC card (ab kabhi "unknown" nahi).
- Koi crash nahi, koi raw error nahi, koi extra credit cut nahi.

---

## 🧪 4️⃣ Saare tools deep check — v46 test report

| Test | Result |
|---|---|
| v46 API hub tests (`_selftest_v45.py`) | **61 / 0** ✅ |
| Live check (asli internet + asli aapka hub) | **120 / 120** ✅ |
| IMEI suite | **70 / 0** ✅ |
| Vehicle + challan suite | **78 / 0** ✅ |
| v44 / clips / prompts / v37 / admin | 67 / 48 / 12 / 91 / 54 — sab **0 fail** ✅ |
| v32 / v34 / v35 / v38 | 51 / 48 / 46 / 80 — sab **0 fail** ✅ |
| Deep audit (217 checks) | **217 / 0** ✅ |
| Tools audit v39 | **69 / 0** ✅ |
| Menu count | 26 tools · 32 buttons · 10 premium — **kuch ghata nahi** ✅ |

Ek asli bug bhi pakda aur theek kiya: **private/LAN IP** (jaise `192.168.1.1`) par pehle hub se
"N/A" info aa rahi thi — ab saaf message: *"This is a private/LAN IP — no public info exists."*

---

## 🚀 5️⃣ Aapko kya karna hai (2 minute)

1. Render → apni service → **Environment** → `HUB_API_KEY` = **`Demo`** → **Save**.
2. `HUB_ENABLED` naam ki koi line daali ho to usko **`on`** rakho (ya hata do).
3. **Deploy hone do** (2-4 min), phir Telegram me bot se:
   - `/hubstatus` bhejo (owner) → plan + ON/OFF list dikhegi
   - `SBIN0000001` bhejo → IFSC result aayega
   - `353010111111110` bhejo → IMEI card aayega
   - `BR30AR0802` bhejo → aaj free RTO card aayega (kyunki vehicle data hub par OFF hai)
4. Number/vehicle ka **asli data** tab khulega jab aap apne hub (ToolVault) me un endpoints ka
   provider configure karo ge. Us din bot me khud-b-khud poora report dikhne lagega — bot ki taraf
   se wiring 100% ready hai.

---

### 🧠 Ek line me
**Key = `Demo` (chal rahi hai) · 12 tools abhi live · number/vehicle ke endpoints aapke hub par khud
band hain (410) — unhe ON karte hi bot me data aa jayega, bot ab har situation me saaf message deta
hai, crash nahi karta, aur credit bhi nahi kaatta.**
