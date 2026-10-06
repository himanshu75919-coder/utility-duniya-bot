# 🔍 OSINT TOOLS — 12 IDEAS (aap chuno, phir banayenge)

> **OSINT matlab:** sirf **public** (sabke liye khuli) cheezein — photo ke andar chhupi
> jankari, website ka sach, email ka bharosa. Kisi ke account me ghusna, private
> chat padhna, ya kisi ke naam-pata ka "database" kharidna — **ye OSINT nahi,
> ye crime hai** (India me IT Act + DPDP). Neeche sirf saaf-suthre tools hain.

**Kaise chuno:** bas reply karo — jaise `1, 2, 7` ya `poore Photo pack + 7, 8`.
Sabse pehle **top 4** banaunga (aapke bot ki speed wahi rahegi — 30 second wala rule).

---

## 🅐 PHOTO PACK — "ye photo me sach kya hai?"

| # | Tool | Kya karta hai | Kis kaam ka | Time |
|---|---|---|---|---|
| **1** | 📷 **PHOTO METADATA (EXIF)** | Photo bhejo → bot batata hai: kis mobile/camera se khichi, kab khichi, aur **GPS location** (Google Maps link ke saath) | Shaadi/portfolio ka photo chori hua? Catfish/fake profile pakadna, photo ka asli source janna | 2 sec (bot ke andar hi, offline) |
| **2** | 🕵️ **PHOTO EDIT CHECK** | Photo edit hui hai ya asli — ELA heatmap photo + details | Aadhaar/bank screenshot, marksheet, "proof" photo fake hai ya nahi | 3 sec (offline) |
| **3** | 🔍 **REVERSE IMAGE KIT** | Ek photo dalo → 6 ready links (Google Lens, Yandex, TinEye, Bing…) tap karke dekho photo internet par kahan-kahan hai | Fake ladki/ladka profile, chori hui DP, apni photo ka misuse pakadna | 1 sec (links) |

## 🅑 EMAIL PACK — "ye email/website bharosemand hai?"

| # | Tool | Kya karta hai | Kis kaam ka | Time |
|---|---|---|---|---|
| **4** | 📧 **EMAIL LEAK SELF-CHECK** | Apna email dalo → kya wo kisi purane data leak me aa chuka hai (Have I Been Pwned, free) + password leak me hai kya (safe check, password bhejna nahi padta) | Apna account surakshit rakhna, naya password lene ka signal | 2 sec |
| **5** | ✉️ **EMAIL TRUST CHECKER** | Email ka domain asli hai ya nakli — MX/SPF/DMARC/DKIM check + "ye free/hacker domain hai?" | Business owner ke liye: invoice/bank email asli hai ya fraud (BEC scam India me bahut common) | 4 sec |
| **6** | 🌐 **WEBSITE DUE-DILIGENCE** | Website/shop ka sach: kitni purani hai (domain age), kiska naam, SSL hai ya nahi, subdomains (crt.sh), blacklist me hai kya | Online shopping se pehle — "ye site bharose layak hai?" | 8 sec |

## 🅒 FRAUD-CHECK PACK — WhatsApp par aane wale shak wale link

| # | Tool | Kya karta hai | Kis kaam ka | Time |
|---|---|---|---|---|
| **7** | 🔗 **SHORT LINK OPENER** | `bit.ly/tinyurl` chhupa link → asli poori link + poora redirect chain | WhatsApp/SMS ke scam links bina click kiye pehle dekh lena | 2 sec |
| **8** | 🛡️ **SCAM LINK CHECKER** | Link ko 70+ antivirus + safe-browsing me check (VirusTotal free key) | Lottery/KYC/UPI fraud link turant pakadna | 4 sec |
| **9** | 📦 **APK CHECKER** | Koi bhi `.apk` bhejo → asli package name, version, permissions, signature — "ye asli SBI/PhonePe app hai ya copy?" | Fake banking APK India me bahut failte hain — ye unka ilaaj | 5 sec (offline) |

## 🅓 APNI CHHAAP (self-audit) PACK

| # | Tool | Kya karta hai | Kis kaam ka | Time |
|---|---|---|---|---|
| **10** | 🕵️ **USERNAME FOOTPRINT** | Apna username dalo → top 40 sites par wahi username profile hai kya (WhatsMyName list se) | Apni purani ID se bani profile dhoondhna, brand naam chori hui kya dekhna | 15-25 sec (40 sites) |
| **11** | 🧼 **EXPOSED FILE SELF-CHECK** | Apni website ka naam do → Google dork links ready (`site:merasite.com filetype:pdf` wagairah) | Apni hi site ke khule (leak ho rahe) files/emails dhoondhna — client data bachana | 1 sec (links) |
| **12** | 🪙 **CRYPTO WALLET CHECK** | Wallet address dalo → balance + transaction history + kya ye scam list me hai (public blockchain) | Crypto payment lene se pehle — "ye wallet saaf hai?" | 3 sec |

---

## 🧠 MERI SALAAH (hamara analysis)

1. **Photo pack (1+2+3) sabse zyada chalega** — 90% users ke paas photo hota hai,
   kuch type karna nahi padta, aur result turant. Indian users ke liye catfish/fraud
   sabse badi dikkat hai.
2. **6 (Website Due-Diligence) business ke liye sona hai** — aapke premium/business
   users (dukaan, online seller) ise roz use karenge. Isko "advanced premium" bana sakte hain.
3. **9 (APK Checker) India-specific killer tool hai** — koi aur bot ye nahi deta.
4. **4 (Email leak self-check) free API se chalta hai** — kharche ka jhanjhat nahi.

**Mera top pick: `1, 2, 3, 6, 9` (Photo pack + Website + APK).**

---

## ❌ YE MAI NAHI BANAUNGA (aur kyun)

- **Leak/leak-database wale tools** (naam-pata-number wale dump) — India me **illegal**
  (IT Act + DPDP), aur aapka Render account + domain band ho sakta hai.
- **Aadhaar / phone-dump / "Govt ID" lookup** — ye data kisi bhi legal API se nahi milta.
  Jo log "legal API" bolte hain wo leak bech rahe hote hain.
- **Face search (PimEyes jaisa)** — biometric, DPDP ke bahut kareeb, aur galat hath me
  harassment ka hathiyar. Nahi banaunga.
- **Kisi ke account me ghusna / OTP lena / private chat padhna** — ye OSINT nahi, crime hai.

**Aapki NUMBER INFO API (jo aapke Render me lagi hai) alag baat hai** — usme data
aapki apni API deti hai, bot sirf dikhata hai. Uska card ab bilkul aapke sample jaisa hai. ✅
