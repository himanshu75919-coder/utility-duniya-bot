# 🕵️ OSINT IDEAS — BATCH 3: "DIKHNE ME ILLEGAL, ASLI ME 100% LEGAL"

> Aapne kaha: *"aisa ideas btao jo dikhne mein illegal ho but wo legal ho really mein"*.
> Neeche wale **saare 10** wahi hain — **asli sarkari portal** se, **koi login nahi, koi hack nahi,
> koi leak nahi**. Rule ek hi: **"public hai to legal hai"** — jaise RTO office ki deewar par
> chhipe number dekhna illegal nahi hai.
>
> ⚠️ **IMPORTANT (sach baat):** inme se kuch cheezein **privacy ke liye aadhi masked** hain
> (jaise gaadi ke maalik ka naam). Bot **jo portal dikhata hai wahi** dikhayega — koi
> "extra" nahi. Ye sab **official .gov.in** portal hain.

**Chunne ka tarika:** `1, 3, 6` ya `poora pack A` likh do.

---

# 🅐 KAGAZ-RECORDS PACK — "kisi ka bhi public record khud verify karo"

| # | Tool | Kya karta hai | Dikhne me kaisa lagta hai 👀 | Asli faayda | Bot kaise | Speed |
|---|---|---|---|---|---|---|
| **1** ⭐ | 🚗 **GAADI KA MAALIK (RC CHECK)** | Number plate (`BR01AB1234`) dalo → **maalik ka naam (aadha masked), maker/model, fuel, registration date, insurance validity, PUC, loan (hypothecation) hai kya, blacklist hai kya** — sab **VAHAN (parivahan.gov.in)** se | "bhai ye number se owner nikal raha hai?!" | **Purani gaadi kharidne se pehle** — chori/loan/blacklist ka pata; accident ke baad gaadi verify | 🔗 Bot step-by-step + direct official link deta hai (captcha sarkari portal hi bharta hai) | 15 sec |
| **2** | 🪪 **DRIVING LICENCE VERIFY** | DL number + DOB → **naam, kaun-kaun class (bike/car), validity, status** — **SARATHI (sarathi.parivahan.gov.in)** se | "kisi ka DL check" | **Driver/taxi/delivery boy hire** karne se pehle asli DL; fake DL pakadna | 🔗 Step-by-step + link | 15 sec |
| **3** ⭐ | ⚖️ **COURT CASE SEARCH** | Naam / CNR number / vakil ka naam → **kisi bhi district court/high court me case hai kya, kya status** — **eCourts (ecourts.gov.in)** se | "kisi ke khilaf case dhoondhna" | **Business partner, dealer, contractor** se deal se pehle; apna case bina vakil ke track karna | 🤖 Bot CNR number se seedha result laa sakta hai (eCourts ka public data) | 8 sec |
| **4** ⭐ | 📜 **ZAMEEN KA MAALIK (LAND RECORDS)** | Khasra/khata/plot number → **jameen kiska naam par hai, kitna raqba, kis thana me** — Bihar Bhumi, UP Bhulekh + 8 state portals | "zameen ka record kholna" | Zameen/plot kharidne se pehle sach; purane kagaz match karna | 🔗 State-wise direct link + steps (har state ka apna portal hai) | 20 sec |
| **5** | 🏢 **COMPANY + DIRECTOR X-RAY** | Company ka naam/CIN/GSTIN → **kaun-kaun director, kab bani, active ya band, loan (charge), pata** — MCA + GST portal | "company ke directors nikalna" | Naya client/supplier/vendor verify — **"ye company asli hai ya bani hui?"** | 🤖 GST ka data bot khud dikha sakta hai + MCA ka link | 6 sec |

# 🅑 PAISA-TRACE PACK — "paisa kahan pada hai, kiska hai"

| # | Tool | Kya karta hai | Dikhne me kaisa lagta hai 👀 | Asli faayda | Bot kaise | Speed |
|---|---|---|---|---|---|---|
| **6** ⭐ | 🏦 **BHOOLA HUA PAISA (UNCLAIMED DEPOSITS)** | Naam + DOB/PAN → **30+ banks me kisi ke naam ki bhooli hui FD/account hai kya** — **RBI ka UDGAM portal (udgam.rbi.org.in)** | "bank account browse?! sach me?" | **Papa-dada ke bhoole hue paise** dhoondhna, kisi ki death ke baad family ka paisa nikalna — RBI ka apna portal hai | 🔗 Direct link + 4 step (RBI me OTP registration lagti hai) | 30 sec |
| **7** | 🗳️ **VOTER LIST SEARCH** | Naam / EPIC number → **voter list me hai kya, part number, assembly, polling station** — **ECI (electoralsearch.eci.gov.in)** | "voter database" | Apna/naye voter ka naam list me aaya ya nahi; EPIC number bhool gaye to | 🔗 Official ECI portal link + steps | 25 sec |
| **8** | 📡 **MERE NAAM PAR KITNE SIM?** | Aadhaar-mobile OTP → **aapke naam par kitne SIM active hain** — **DoT ka TAFCOP (sancharsaathi.gov.in)** | "SIM tracking" | **SIM fraud/identity chori** India me bahut bada issue hai — koi aapke naam par SIM chalaye to turant pata | 🔗 Official link + steps + fraud report (Chakshu) | 30 sec |

# 🅒 DIGITAL X-RAY PACK

| # | Tool | Kya karta hai | Dikhne me kaisa lagta hai 👀 | Asli faayda | Bot kaise | Speed |
|---|---|---|---|---|---|---|
| **9** ⭐ | 🔲 **QR X-RAY (BINA PAISA DIYE)** | Koi bhi QR ka photo/screenshot bhejo → bot batata hai **QR me kya likha hai: UPI ID, merchant ka naam, ya website link** — **bina payment ke, bina app khole** | "QR scan kar raha hai… paisa jayega?!" | **UPI fraud ka #1 hathiyar** — "ye QR asli dukaan ka hai ya scam?" — paisa bhejne se pehle check | 🤖 Bot khud (offline, 100% safe) | 1 sec |
| **10** | 🌐 **WEBSITE KA MAALIK (WHOIS)** | Koi bhi website ka naam → **domain kiska naam par registered, kab bana, kab renew, kahan hosted** | "website ka owner nikalna" | Online shop/site se deal se pehle — "kal bani site hai ya 10 saal purani?" | 🤖 Bot khud (public WHOIS) | 3 sec |

---

## 🧠 MERI SALAAH (honest analysis)

1. **#1 GAADI KA MAALIK** — sabse zyada "wow" wala tool. Log sochte hain ye illegal hai, jabki
   **sarkar khud** free me deti hai. Note: maalik ka naam **aadha masked** aata hai (privacy rule) —
   bot bhi wahi dikhayega, jhooth nahi bolega.
2. **#6 BHOOLA HUA PAISA (RBI UDGAM)** — India me bahut families ke papa-dada ke paise bank me pade hain
   aur unko pata nahi. Ye tool "illegal lagta hai lekin RBI ka apna portal hai" — iska emotional value sabse zyada.
3. **#9 QR X-RAY** — roz kaam aayega (har UPI payment se pehle). "Paisa diye bina QR padhna" — sabko chahiye.
4. **#3 eCourts** — business users ke liye gold, aur ye **bot khud automate** kar sakta hai.

**Mera top pick: `1, 6, 9` + ₹ agar business focus: `3, 5`.**

---

## ✅ LEGAL KYUN HAI (ek line me har ek)

| Tool | Source | Legal kyun |
|---|---|---|
| RC / DL | vahan.parivahan.gov.in, sarathi.parivahan.gov.in | MoRTH ke **khud ke public citizen services**, no login |
| Court case | ecourts.gov.in | **Khuli adalat** — case public record hota hai |
| Zameen | biharbhumi.bihar.gov.in, upbhulekh.gov.in wagairah | State sarkar ke **public land records** |
| Company | mca.gov.in, gst.gov.in | Company ka public register |
| Unclaimed paisa | udgam.rbi.org.in | **RBI ka apna portal**, family ke liye banaya gaya |
| Voter list | electoralsearch.eci.gov.in | **ECI ka official** public search |
| SIM count | sancharsaathi.gov.in | **DoT ka apna** tool (fraud se bachne ke liye) |
| QR / WHOIS | UPI QR standard, public WHOIS | Public technical record |

## ❌ AUR YE CHEEZEIN MAI NAHI BANAUNGA (chahe kitni baar kaho)

- ❌ **Aadhaar/phone/naam-pata "database"** — asli me **illegal** (IT Act + DPDP), API exist nahi karti.
  Jo "legal paid API" bolte hain wo **chori ka data** bechte hain → bot band + FIR ka risk.
- ❌ **Kisi ka live location, OTP, private chat, account access** — ye crime hai.
- ❌ **Face search (photo se banda dhoondhna)** — biometric, DPDP ke bahut kareeb, harassment ka hathiyar.
- ❌ **Leak dump search** — uplaod karne wale par bhi case banta hai (aapke Render/domain par bhi).

> **Aapki NUMBER INFO API** (jo pehle se aapke bot me hai) isse alag hai — usme data **aapki API**
> deti hai. Uska card ab bilkul aapke sample jaisa hai ✅ (v69.0 live hai).
