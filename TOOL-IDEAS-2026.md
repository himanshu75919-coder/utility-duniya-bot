# 🕵️ "DIKHNE ME KHTARNAK, KAAM ME 100% LEGAL" — TOOL IDEAS + FREE APIs

> Aapne poocha: aise tools jo **dikhne me illegal lagte hain** par **actually legal** hain,
> government/OSINT related, aur **API free** mile. Ye list 7 Oct 2026 ko **live test karke**
> banayi hai (har API ko maine khud call karke check kiya).
>
> ⚠️ **Rule:** Naam/emoji "spy" jaisa ho sakta hai — par **data sirf PUBLIC ya AAPKA APNA hona chahiye**.
> Lat me "kabhi nahi" list bhi hai — unhe bhool hi jao.

---

## 🥇 TOP IDEAS (meri recommendation order me)

### 1. 📸 PHOTO X-RAY — "photo se location nikalta hai" 🥵
- **Kya dikhta hai:** "Photo bhejo → kahan kheechi gayi, kis phone se, kab — sab pata"
- **Actually kya hota hai:** Photo ke **andar hi** (EXIF metadata) camera, date aur **GPS location**
  likhi hoti hai. Bot usko padhta hai + **OpenStreetMap link** dikhata hai. Koi hacking nahi —
  data photo me pehle se hai.
- **API/key:** ❌ kuch nahi chahiye (Pillow library — already installed!)
- **Legal kyun:** Photo aapki bheji hui hai; data uske andar embedded hai (ye world me sabse
  purana "OSINT" trick hai — news channels bhi use karte hain).
- **VIP-able:** ✅ Haan — "📸 Photo Spy (VIP)" — sabse zyada share hoga ye feature.
- **Kaam ki baat:** WhatsApp/Telegram photos me EXIF **delete** ho jati hai — asli photo
  (camera se seedha) me milti hai. Ye bhi batana.

### 2. 🕵️ USERNAME HUNTER — "kisi bhi username se 300+ sites par profile dhoondho"
- **Kya dikhta hai:** "Person tracker" — username daalo, internet bhar me dhoondhta hai.
- **Actually:** Wo sites par **public profile pages** check karta hai (`github.com/username` khula
  hai kya). Open-source tool **Sherlock / Maigret** — bilkul free, koi key nahi.
- **API:** ❌ key nahi (open-source script; bot me offline logic bhi ho sakta hai).
- **Legal kyun:** Sirf **public pages** — jaisa koi Google me naam likhta hai.
- **VIP-able:** ✅ Haan — bahut "wow" feature hai.

### 3. 📧 EMAIL LEAK CHECK — "kya aapka email dark web me leak hai?"
- **Kya dikhta hai:** "Dark web scanner" 😱
- **Actually:** **XposedOrNot** (free API ✅ aaj test kiya) se check hota hai ki email kaun-kaun se
  **public data breaches** me aa chuka hai (naam, date, kitne records).
- **API:** ✅ `https://api.xposedornot.com/v1/check-email/<email>` — **bilkul FREE, key nahi**
- **Legal kyun:** Breach lists already public research hain (HaveIBeenPwned type). **Password
  kabhi nahi** maangna bhejna.
- **VIP-able:** ✅ — "Email Leak Report" bahut share hota hai.

### 4. 🛡️ PASSWORD LEAK CHECK — "password leaked hai kya?" (SAFE tarika)
- **Kya dikhta hai:** "Aapka password leak checker"
- **Actually:** **HaveIBeenPwned Pwned Passwords** API — **k-anonymity**: password ki sirf
  **pehli 5 characters** bheji jaati hain, poori password kabhi internet par nahi jaati.
- **API:** ✅ `https://api.pwnedpasswords.com/range/<first5>` — **FREE, key nahi** (test kiya)
- **Extra security:** Bot ko result ke baad password **bhoola dena chahiye** (memory se hata do).
- **Legal + safe:** ✅ — industry standard method hai.
- **VIP-able:** ✅ (security-conscious users ka favourite)

### 5. 🌐 WEBSITE HACKER X-RAY — "subdomains, SSL certificates, DNS — sab nikalta hai"
- **Kya dikhta hai:** "Kisi bhi website ki gehrai" — hacker style.
- **Actually:** **Certificate Transparency logs (crt.sh)** + **HackerTarget** se **public** info:
  subdomains (kitne hain), SSL certificates ka itihaas, server IPs.
- **API:** ✅ `crt.sh/?q=...&output=json` + `api.hackertarget.com/hostsearch/?q=...` — dono **FREE, key nahi** (dono aaj test kiye)
- **Legal kyun:** Ye **sab public records** hain (jaise RTO ka record public hai). Website ke
  andar kuch nahi todta (passive only).
- **VIP-able:** ✅ Haan — cybersecurity students me superhit.

### 6. 📡 IP X-RAY — "IP address se location/ISP"
- **Kya dikhta hai:** "IP Tracker"
- **Actually:** IP → city, region, ISP, company, VPN/proxy flag (approximate — ye ghar ka address
  nahi batata).
- **API:** ✅ `https://ipwho.is/<ip>` — **FREE, key nahi** (test kiya)
- **Legal kyun:** IP-geolocation public service hai.
- **VIP-able:** ✅

### 7. ✈️ FLIGHT X-RAY — "live flight ka route + callsign info"
- **Kya dikhta hai:** "Flight tracker / radar"
- **Actually:** Callsign (jaise `AIC101`) → **public flight route**: airline, from, to.
  Live position ke liye OpenSky Network (free, par kabhi rate-limit/slow ho jata hai).
- **API:** ✅ `api.adsbdb.com/v0/callsign/<code>` **FREE** (test kiya) · OpenSky: `opensky-network.org/api` (free, anonymous bhi chalta hai — slow ho to fallback)
- **Legal kyun:** Aircraft position broadcast (ADS-B) publicly hota hai.
- **VIP-able:** ✅ — students/families me bahut demand.

### 8. 🔍 LINK X-RAY — "chhota link kholne se pehle batata hai andar kya hai"
- **Kya dikhta hai:** "Short link ka asli roop"
- **Actually:** Short URL (bit.ly etc.) → asli destination URL + suspicious flags (typosquat,
  phishing patterns). **Click se PEHLE** warning.
- **API:** ✅ redirect follow (requests) + optional VirusTotal (free key 4/min)
- **Legal kyun:** Bilkul — safety tool hai.
- **VIP-able:** ✅ (bacchon wala safety feature — parents me popular)

### 9. 🏢 COMPANY X-RAY (GST) — "GST number se company ki sarkari kundli"
- **Kya dikhta hai:** "Company spy"
- **Actually:** GST number → legal name, address, registration date, status — **public GST registry** se.
- **API:** ✅ `gstinapi.in` (free tier) — hub me bhi connect ho sakta hai
- **Legal kyun:** GST data hi public hai (sarkar khud dikhati hai).
- **VIP-able:** ✅ — shopkeepers/business users me demand.

### 10. ⚖️ COURT CASE X-RAY — (FUTURE — mushkil hai)
- **Kya dikhta hai:** "Court case tracker" — bahut khatarnak lagta hai
- **Actually:** eCourts/NJDG ke **public case records**
- **Problem:** Captcha + bhaari site — reliable free API nahi. **Filhaal skip.**

---

## ⛔ "KABHI NAHI" LIST (ye "illegal-looking" nahi, ye asli illegal/immoral hain)

| ❌ Cheez | Kyun nahi |
|---|---|
| Mobile number → owner ka naam/address | Aadhaar/telecom data — **illegal**, kisi se bhi karwana galat |
| Aadhaar number ki info / Aadhaar-family linking | **Illegal** (Aadhaar Act) |
| Face search / photo se banda pehchano | **Illegal + privacy** |
| Instagram/Facebook **private** account ka data | Account access = **crime** |
| Leaked databases (loan apps, bank, etc.) ki API | **Illegal** — hub me bhi OFF rakhe hain |
| WhatsApp/Telegram chat padhna, OTP lena | **Crime** |
| Fake documents (RC, PAN, marksheet) banana | **Forgery — jail** |
| "SIM location tracker" wale jhoothe apps | Sab scam hai + illegal |

> Aapka hub inme se privacy-wale endpoints **code me lock** kar chuka hai (leak/phone/aadhaar)
> — aur wahi sahi hai. Bot ki value isi me hai ki **fake "hacker" apps (jo scam karte hain)
> se alag dikhe** — jo dete hain wo sach hota hai.

---

## 💰 Kamai (EARNING) se kaise jodo

| Feature | Free me | VIP (₹99/mo) me |
|---|---|---|
| Photo X-RAY | 3/din | Unlimited |
| Username Hunter | 3/din | Unlimited |
| Email Leak Check | ROI 2/din | Unlimited + month report |
| Website X-RAY | 5/din | Unlimited + subdomain list PDF |
| Flight/IP/Link | Unlimited | Same (+ fast lane) |
| RC/Challan | 10/mahina shared | (PRO aane par) unlimited-ish |

**Formula:** Free = "wow, ye to kaam karta hai! 😲" → VIP = "aur zyada, aur tez" → referral se log khud laate hain.

---

## 🚦 Aage kya — mere 2 sujhav (aap choose karo)

1. **Photo X-RAY + Username Hunter + Email Leak Check** — teeno ka key/chhota kaam hai,
   **aaj hi ban sakte hain** (koi API key nahi chahiye / free hai) → bot me "🕵️ SPY ZONE" section
2. **Website X-RAY + IP X-RAY + Flight X-RAY** — doosra batch (security/aviation students ke liye)

Bolo to pehla batch turant shuru karta hoon. (Pehle aap final approval do — _aapke rule:
bina puche naya tool nahi banata_ 😄)
