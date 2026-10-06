# 🔍 OSINT IDEAS — BATCH 2 (naye 10, pehle wale se alag)

> Pehla batch: Photo/Link/Email/Website/Crypto tha.
> Ye **doosra batch** hai — sab **public data + legal**, sab bot ke andar chalega.
> Reply karo: `1, 3, 9` ya `pack A` — main wahi banaunga.

---

# 🅐 FRAUD X-RAY PACK — "scam pakadne ka hathiyar"

| # | Tool | Kya karta hai | Kis kaam ka | Speed |
|---|---|---|---|---|
| **1** ⭐ | 📧 **EMAIL HEADER X-RAY** | Email ka raw header paste karo → bot batata hai: **asli sender IP + uska sheher**, asli bhejne wala server, SPF/DKIM pass hua ya fail, kitne server se hokar aayi | "Bank/RBI/Income Tax ke naam se aayi email asli hai ya fraud?" — India me BEC/invoice fraud ka #1 hathiyar | 3-4 sec |
| **2** | 🌐 **IP ADDRESS X-RAY** | Koi bhi IP → ISP ka naam, sheher/state, ASN, aur **VPN/proxy/hosting hai kya** (scammer VPS se chal raha hai?) | Header X-RAY ka dost — mila hua IP iska jawab deta hai | 2 sec |
| **9** ⭐ | 🔤 **SCAM MESSAGE SCANNER** | WhatsApp/SMS jo aaya wahi message paste karo → bot 15 rule lagata hai (link+urgency+"OTP bhejo"+UPI ask+grammar) → **risk score + kya-kya shak hai** | Sabse zyada use hone wala tool — kuch bhi type karna nahi padta, message paste, jawab ready | 1 sec (offline) |
| **7** | 🧲 **GOOGLE DORK BUILDER** | Naam/business/sheher dalo → bot ready-made advanced search links banata hai (filetype, site:, intext:) — tap karo, Google khul jaye | Khud ki ya kisi biz ki **public** jankari dhoondhna, expert ki tarah | 1 sec |

# 🅑 KAGAZ-VERIFY PACK — "kaagaz asli hai ya banaya hua?"

| # | Tool | Kya karta hai | Kis kaam ka | Speed |
|---|---|---|---|---|
| **3** ⭐ | 📄 **DOCUMENT X-RAY (PDF/Word)** | Certificate/marksheet/offer letter ki file bhejo → bot batata hai: kis **software** se banaya (Word se? Photoshop?), **author ka naam** file me chhupa, kab banaya, kab badala (**edit hua ya nahi**) | Fake experience letter / marksheet / quote PDF pakadna. India me job+loan fraud me roz hota hai | 2 sec (offline) |
| **5** ⭐ | 🏢 **BUSINESS VERIFY** | GSTIN dalo → **business ka asli naam, status (active/cancel), type, registration date + Udyam/MSME check + company ka CIN link** | Naya supplier/dealer/client se deal se pehle — "ye Dhruv Traders asli hai ya bana hua?" Business users ka premium tool | 4-6 sec |
| **4** | 📮 **PIN CODE + ADDRESS VERIFY** | PIN code dalo → district, state, taluk, **saare post office + delivery sub-office**, ya area ka naam dalo → sahi PIN | Address sahi hai ya nahi (COD/parcel fraud, delivery address check) | 2 sec (India Post public data) |
| **10** | 🎬 **VIDEO X-RAY** | Video file bhejo → kis app/phone se bana, kab bana, kaunse software se banaya/finish kiya, resolution-asli | Fake "live proof" video, purani video nayi banakar bhejna — pakadne me help | 3 sec (offline) |

# 🅒 NAQSHAA (location) PACK

| # | Tool | Kya karta hai | Kis kaam ka | Speed |
|---|---|---|---|---|
| **6** ⭐ | 🛰️ **GPS → ADDRESS + MAP** | Latitude/longitude dalo (ya photo ka GPS) → **address, landmark, Google Maps + Street View + What3Words link, Plus Code** | Photo me GPS mila → ye jaga **exactly kahan hai** wo dekhna | 2-3 sec |
| **11** | 🕰️ **WEBSITE TIME MACHINE** | Website ka purana version dekho (Wayback) — 2008 me kaisa tha, kab se hai, purana content | Purani photo/post ka **asli saal** pata karna, site ki umar ka proof | 2 sec |
| **8** | 📰 **NAAM/BRAND MONITOR** | Apna naam ya brand dalo → public news + web mentions ke ready links + Google Alert banane ka tarika | Apne naam pe kya chal raha hai, brand ki chori hui ID/mention dekhna | 2 sec |

---

## 🧠 MERI SALAAH (analysis)

1. **#1 (Email Header X-RAY)** — ye mera **#1 pick** hai. Bank/IT/insurance ke naam se fraud email roz aati hai;
   header se asli IP + fail SPF nikalna wo cheez hai jo aam aadmi khud kabhi nahi kar sakta.
2. **#9 (Scam Message Scanner)** — sabse zyada baar chalega. Kuch bhejna nahi padta, message paste,
   risk score. Aapka bot isse "daily-use" ban jayega (log roz aayenge).
3. **#3 (Document X-RAY)** — fake marksheet/letter pakadna — WhatsApp par ek file bhejo, jawab ready.
4. **#5 (Business Verify + GSTIN)** — aapke **business/premium users** ka sona. Ise "advanced premium" bana sakte hain.

**Mera top pick: `1, 9, 3` (fraud x-ray + scam scanner + document x-ray) — teeno kuch type karne wale nahi, "bhejo aur jawab lo" wale tools hain.**

---

## ❌ YE PHIR BHI NAHI BANAUNGA (kyun)

- ❌ **Aadhaar / phone / naam-pata "database"** — India me illegal (IT Act + DPDP), API nahi milti, jo
  "legal API" bolte hain wo leak bechte hain.
- ❌ **Face search (photo se insaan dhoondhna)** — biometric + DPDP, aur harassment me use hota hai.
- ❌ **Kisi ka live location, OTP, private chat, account** — ye OSINT nahi, crime hai.
- ❌ **Credit card BIN/full card tools** — card fraud me use hote hain, chahe data public ho.
- ❌ **Kisi ki marzi ke bina uski personal profile khodna** — bot me hum aise tool nahi denge.

> **Aapki apni API (NUMBER INFO) alag hai** — usme data aapki API deti hai, bot sirf dikhata hai. Uska
> card ab bilkul aapke sample jaisa hai ✅ (v69.0 live).
