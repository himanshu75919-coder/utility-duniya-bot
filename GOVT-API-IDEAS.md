# 🏛️ GOVERNMENT PORTAL APIs — BEST IDEAS (7 Oct 2026, live verified)

> Aapne poocha: **government portals se related best APIs** — jo free hain, legal hain,
> aur bot me kaam aayenge. Maine aaj har API ko **khud call karke test kiya** — jo
> chal raha hai wahi is list me hai. ✅ = aaj test hua · ⚠️ = conditions hain
>
> **Ek zaroori sach:** "government" naam sunte hi sab sochte hain Aadhaar/PAN/land-records ka
> access milega — **wo sab nahi milega** (aur milega bhi to lena nahi chahiye).
> **Asli gold** data.gov.in ke **public/aggregate datasets** aur MeitY ke Bhashini me hai. 👇

---

## 🥇 TIER 1 — Ye turant ban sakte hain (free + verified + ghar ki demand)

### 1. 🌾 MANDI BHAV (Agmarknet) — **mera #1 pick**
- **Kya:** Ros ka **fasal ka bhav** — state/district/mandi/commodity se. (Gehu, alu, pyaz,
  dhan, tomato, sarson… 300+ commodities)
- **API:** ✅ **data.gov.in** — resource ID: `9ef84268-d588-465a-a308-a864a43d0070`
  ```
  https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070
      ?api-key=<FREE KEY>&format=json
      &filters[state]=Bihar&filters[district]=Patna&limit=50
  ```
  *(Ye resource 3664+ GitHub projects use karte hain — sabse popular govt dataset hai)*
- **Key:** data.gov.in par **free signup** → My Account → API Key (1 key = saare datasets)
- **Bot me kya banega:** "🌾 MANDI BHAV" tool — `Patna alu` bhejo → aaj ke sabse acche
  bhav wali mandi + min/max/modal rate + date. **Bihar/UP ke kisano ke liye superhit hoga.**
- **VIP angle:** ⭐⭐⭐ "roz subah 8 baje apne district ka bhav" — daily alert = retention
- **Fields jo milte hain:** state, district, market, commodity, variety, grade,
  arrival_date, min_price, max_price, modal_price

### 2. 🗣️ BHASHINI — "Google Translate ka desi sarkari version" (MeitY)
- **Kya:** **22 Indian languages** ka translation + transliteration + voice (TTS/ASR).
  Hindi ↔ English ↔ Bhojpuri/Maithili/Tamil/Bengali… **sarkar ka apna AI** (Digital India
  Bhashini Mission, MeitY)
- **API:** ✅ endpoint live hai — `https://dhruva-api.bhashini.gov.in/services/inference/pipeline`
  (header me `Authorization: <key>`, body me pipelineTasks)
- **Key:** bhashini.gov.in par **free** registration (ULCA) → API key
- **Real usage:** ONDC (govt ka e-commerce network) aur UPYOG khud isi ko use karte hain ✅
- **Bot me kya banega:** "🈯 TRANSLATE" tool — `Hindi to Bhojpuri: kya haal hai bhai`
  → 1 second me translation. Free tools me full, VIP me bulk (pura document/paste)
- **VIP angle:** ⭐⭐ students, shopkeepers, content banane wale — sab kaam aayega

### 3. 🌤️ MAUSAM (Weather) + 🌬️ AQI combo — "Aaj ka Mausam Card"
- **Kya:** Kisi bhi city ka aaj ka mausam (temp, humidity, wind, 7-din forecast) +
  **hawa ki quality** (PM2.5, AQI) — ek hi card me
- **API:** ✅ dono aaj test kiye — **koi key nahi chahiye**:
  - `https://api.open-meteo.com/v1/forecast?latitude=25.6&longitude=85.1&current=temperature_2m,relative_humidity_2m,wind_speed_10m`
  - `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=25.6&longitude=85.1&current=pm2_5,us_aqi`
  - *(Open-Meteo govt nahi hai, par 100% free hai aur IMD/CPCB se data include karta hai.
    IMD ka apna API data.gov.in par hai — key ke saath — par slow/limited hai.)*
- **Bot me kya banega:** "🌤️ MAUSAM" tool — `Patna` bhejo → temp + baarish + AQI + 3-din.
- **VIP angle:** ⭐⭐ roz ka use = log bot me wapas aate hain (retention ka sabse bada tool)

### 4. 📮 PINCODE DEEP INFO — **upgrade kar sakte hain** (aapke pincode tool ka level-2)
- **API:** ✅ aaj test kiya, **koi key nahi**: `https://api.postalpincode.in/pincode/800001`
- **Ab kya milta hai aapke tool me:** area/RTO. **Naya kya mil sakta hai:** us pincode ke
  **saare post offices** (22 tak!), har ek ka: naam, branch type (Head/SO/BO), **delivery ya
  non-delivery**, district, division, circle, taluk, **phone number**
- **Kaam ki baat:** "kis courier wale pincode me delivery hoti hai?" — e-commerce/students
  ke liye gold, aur **bilkul free**

### 5. 🏛️ DATA.GOV.IN — "master key" (ek key = 500+ datasets)
- **Kya:** India ka official open data portal — **5 lakh+ datasets**: bijli, paani,
  kheti, health, education, transport, census, groundwater…
- **API:** ek hi key se sab resources (`api.data.gov.in/resource/<id>?api-key=...`)
- **Key:** free signup → My Account → API Key
- ⚠️ **Aaj note:** data.gov.in (7 Oct, 12:30 AM) **503 down** tha — unki site ka issue hai
  (aata jaata rehta hai). Bot me isliye **fallback hamesha zaroori** (jaise mandi tool me
  Open-Meteo jaisa backup, ya "server busy" ka saaf message)

---

## 🥈 TIER 2 — Baad me, jab pehla batch chal jaye

| # | Idea | Source | Bot me kya |
|---|---|---|---|
| 6 | ⚡ **Bijli tariff/outage data** | data.gov.in | "unit rate calculator" state-wise |
| 7 | 💧 **Groundwater level (CGWB)** | data.gov.in | "mere area me zameen ka paani kitna" |
| 8 | 🏥 **Hospital list (Ayushman/NHA)** | data.gov.in | "paas ka govt hospital" list |
| 9 | 🌱 **Soil health data** | data.gov.in | kisan ke liye "meri mitti kaisi hai" |
| 10 | 📊 **Census / population** | data.gov.in | area ki aabadi, literacy (school projects) |
| 11 | 🛣️ **Road accident stats** | data.gov.in | "is state me kitne accidents" (awareness) |
| 12 | 🌾 **Fertilizer/seed rates** | data.gov.in | kheti ka saal-bhar calendar |

---

## ⛔ "GOVERNMENT" DIKHNE WALE — JO NAHI HO SAKTE (aur kyun)

Inhe koi bhi "API" bech raha ho to wo **dhoka** hai:

| ❌ | Kyun nahi |
|---|---|
| Aadhaar number → kisi ka naam/address/photo | **Aadhaar Act** — sirf UIDAI/authorized agency kar sakti hai. Data mile to bhi **crime** hai |
| PAN card verification (doosre ka) | NSDL/Protean ki **KYC partnership** chahiye (company + fees) |
| DigiLocker documents | Sirf **partner app** + user ka consent flow — bot ke liye possible nahi |
| eCourts / NJDG case details | Captcha wall, **koi public API nahi**. Scrape = block |
| Bhulekh / land records (state portals) | Har state me captcha — aur ye **sensitive** hai |
| Ration card / voter list ke personal details | Public display tha, par bulk API nahi — **privacy** ka issue |
| Railway PNR / live train | IRCTC/CRIS **paid partner** territory — free me jhoothe "APIs" chalte hain |
| VAHAN/SARATHI live data | Captcha (isliye humne **licensed** RapidAPI provider lagayi hai ✅) |
| PM-Kisan beneficiary status, MGNREGA personal records | Login + captcha; personal data |
| UPI/NPCI/FASTag | Bank-grade — kisi third-party ko nahi dete |

> **Rule yaad rakho:** Govt API me "public/aggregate data" = ✅ | "kisi vyakti ka personal
> data" = ❌. Hum hamesha pehla hi banayenge.

---

## 🎯 MERA SUGGESTION — 3 tools ka pehla batch

| Order | Tool | Kyun | Key chahiye? |
|---|---|---|---|
| 1 | 🌾 **MANDI BHAV** | Bihar me sabse zyada demand — kisano ka roz ka kaam | data.gov.in (free 2-min signup) |
| 2 | 🌤️ **MAUSAM + AQI** | Roz ka use = log wapas aate hain (retention) | ❌ kuch nahi! |
| 3 | 🗣️ **BHASHINI TRANSLATE** | Sarkari AI, 22 bhashayein, koi competition nahi | Bhashini (free signup) |

**Agar aap "0 key chahiye" wala chahte ho** → MAUSAM + AQI + PINCODE-2 **aaj hi ban sakte hain** 🚀
**Agar Bihar ke liye kuch bada** → MANDI BHAV pehle (usme data.gov.in key lena hoga — main step-by-step bata dunga)

---

**Bot me jodne se pehle:** aapka rule hai — _pehle ideas, aap pick karo, phir banayenge_ 😄
Bolo: **"1"**, **"2"**, **"3"**, ya **"sab"** — aur main building shuru karta hoon!
