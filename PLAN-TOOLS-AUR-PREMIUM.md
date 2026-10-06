# 🚀 PLAN — TOOLS AUR PREMIUM (aage ka poora rasta)

---

# ✅ PART 1 — AAJ KE 2 NAYE TOOLS (ban gaye, live hain)

## 💰 1. Salary Slip Maker — `biz_salary`
Staff ka **monthly pay slip** — Basic, HRA, PF, ESI, Professional Tax, Net Pay,
amount in words, payment details — sab automatic calculate ho jata hai.

**Kaise use karein:**
> Neeche button **`💼 BUSINESS STUDIO`** → **💰 Salary Slip** → phir ye line bhejo:

```
Sharma Kirana | Ramesh Kumar | Salesman | September 2026 | 18000 | 500
```
`company | naam | post | month | salary | advance`

**Example results (maine test kiya):**
- `18000` salary → Basic 9000, HRA 3600, PF 1080, ESI 135, PT 200 → **Net Pay ₹16,085**
- `50000` salary → ESI **nahi** katta (21000 se upar) → sahi hisaab
- Sirf `18000` likh bhejo → phir bhi slip ban jati hai

## 🍽️ 2. Menu / Rate Card — `biz_menucard`
Dhaba, hotel, restaurant ya dukaan ka **rate list** — 2 column, dotted line,
print-ready. 5 item ho ya 80 — page apne aap set ho jata hai.

**Kaise use karein:**
```
Hotel Shivam | Shudh Desi Khana | Chai:10, Samosa:15, Veg Thali:80
```
`naam | tagline | item:rate, item:rate`

**Bonus:** `item:rate:tag` bhi chalta hai — jaise `Thali:80:unlimited roti`
Hindi naam bhi chalta hai — `श्री राम भोजनालय | शुद्ध देसी खाना | चाय:10`

**Ab Business Studio me 12 tools hain** (pehle 10 the).

---

# 📋 PART 2 — AAGE KAUNSE TOOLS ADD KARNE CHAHIYE

Maine 60 ideas ki list banayi thi (`TOOL-IDEAS-60.md`). Unme se **sabse kaam ke**
chun kar 3 phase me baanta hai:

## 🟢 PHASE 1 — YE 6 SABSE PEHLE (100% FREE, koi API nahi)
Ye sab bot ke andar hi ban jaate hain — **ek rupya kharch nahi** hoga.
Log inhe rozana use karte hain, isliye **users sabse zyada inhi se aayenge**:

| # | Tool | Kya karega | Kyun best |
|---|---|---|---|
| 1 | **Photo → PDF** | 10-15 photo bhejo → ek PDF file | Form bharne me sabko chahiye |
| 2 | **Photo Size Reducer** | 3 MB photo → 200 KB (form upload) | Rozana ka kaam hai |
| 3 | **Signature Background Clear** | Signature photo → saaf + transparent PNG | Bank/kagaz ke form me chahiye |
| 4 | **PDF Merge / Split** | 2 PDF jodo ya ek ko kaato | Office/school me rozana |
| 5 | **PDF me Password** | PDF par lock lagao / hatao | Ye log Google par search karte hain |
| 6 | **Photo par Naam / Date** | Photo par apna naam-dinank likho | Shaadi/party me bahut chalta hai |

## 🟡 PHASE 2 — AI WALE (thoda kharcha, par sabse zyada share hote hain)
Inke liye AI ka thoda paisa lagta hai (₹0-500/month) — par main **free AI** se
bana sakta hoon (thoda dheema chalega, par chalega).

| # | Tool | Kya karega |
|---|---|---|
| 7 | **AI Se Instagram Caption** | Photo/idea bhejo → 10 caption + hashtag |
| 8 | **MCQ / Quiz Maker** | Koi topic → 20 sawal jawab ke saath (students ke liye) |
| 9 | **Notes Summarizer** | 10 page ka note → 1 page summary |
| 10 | **AI Chat (Hinglish)** | Bot ke andar hi chhota assistant |

## 🔴 PHASE 3 — NAYE DOCUMENT TOOLS (Business Studio me aur)
Ye bilkul waise hi banenge jaise Salary Slip bana:

| # | Tool | Kya karega |
|---|---|---|
| 11 | **Rent Agreement** | Makaan ka kiraaya-nama |
| 12 | **Purchase Order / Quotation** | Supplier ko rate quote ya order |
| 13 | **Cash Memo / Kachha Bill** | Bina GST wala simple bill |
| 14 | **Attendance Sheet** | Mahine ka haziri register (31 din) |
| 15 | **Salary Register** | Poori company ka salary ek page par |
| 16 | **Wedding Card** | Shaadi ka nimantran card |

> 💡 **Meri sifarish:** Pehle **Phase 1 ke 6 tools** banwao.
> Wajah: ye free hain, rozana use hote hain, aur inhe dekh kar log bot
> **doston ko share karte hain** = aapke users sabse tez badhenge.

---

# 👑 PART 3 — PREMIUM WAPAS ON KARNE KA PLAN (jab users aa jayein)

Aaj aapne kaha: **"abhi sab free chahiye"** — theek hai, wahi kiya hai.
Jab users aa jayein, tab premium wapas on karne ka **poora plan** ye hai:

## 🎯 STEP 1 — Kab on karna hai? (yaad rakhne ka target)

| Users | Kya karo |
|---|---|
| 0 – 200 | ⛔ **Premium off rakho.** Pehle log aayein, bot chalayein, share karein |
| 200 – 500 | 🟡 Sochne lago — kaunse tools sabse zyada chal rahe hain, dhyan se dekho |
| **500+** | ✅ **Premium on kar do** — ab log paise denge |

## 🎯 STEP 2 — ON kaise karna hai (ek line ka kaam)

Render → service `utility-duniya-bot` → **Environment** → `ALL_FREE` ki value
`on` se badal kar **`off`** kar do → **Save Changes**.

Bas. Bot khud deploy ho jayega (2-3 minute) aur **purana poora premium system
wapas aa jayega**:

| System | Wapas aayega |
|---|---|
| Naye user ko 25 free credits | ✅ |
| Credits khatam = tool band | ✅ |
| VIP plans (₹49/30d · ₹89/60d · ₹129/90d · ₹169/120d · **₹199 Lifetime**) | ✅ |
| Refer & Earn (5 dost = free VIP) | ✅ |
| Menu me `💎 VIP PREMIUM` button | ✅ |
| Admin panel se VIP dena | ✅ |

> 🔒 **Kisi ka data nahi khoya, nahi kho jayega.** Aaj tak jo bhi VIP tha,
> uska `premium_until` DB me **safe para hai**. `ALL_FREE=off` karte hi wo
> log dobara VIP ban jayenge — automatically.

## 🎯 STEP 3 — VIP dena-hataana (commands)

| Kaam | Command |
|---|---|
| Kisi ko VIP dena | `/grant 123456789 30` (30 din) · `/grant 123456789 9999` (lifetime) |
| VIP hatana | `/revoke 123456789` |
| Sab VIP ki list | `/vips` |
| Kisi ke credits dena | `/credits 123456789 50` |
| Payment check karna | `/payments` |
| Poora admin panel | `/admin` |

## 🎯 STEP 4 — Behtar model (meri salah)

Poora "sab band" karne se naye log bhaag jaate hain. Isliye **ye model** best hai:

```
Naye user ko 25 FREE credits  →  wo 25 baar tool chalaye  →  aadat lag jaye
                    ↓
        "Bahut kaam ka hai!"  →  ₹49 me 30 din VIP le le
```

Matlab: **credit khatam hone par hi VIP maango, shuruaat me nahi.**
Ye model pehle se bot me laga hua hai — `ALL_FREE=off` karte hi ye chalu ho jayega.

## 🎯 STEP 5 — Business Studio ka alag plan (sabse zyada kamai)

Business Studio ke documents (Invoice, Salary Slip, Menu Card…) ki market rate
**₹30 – ₹500 per document** hai. Isliye chahe baaki sab free rahe,
**ye 12 tools VIP me rakhna** sabse zyada paisa dega:

| Model | Kimat | Kiske liye |
|---|---|---|
| Free | 5 documents/month | Try karne ke liye |
| **Dukaan Pack** | **₹499 / 90 din** | Dukaan, coaching, clinic |
| Shop Licence | ₹1,499 / saal | Ek dukaan ka poora saal |
| White-label | ₹2,999 | Aapka naam lagakar bechne ke liye |

---

# 🎯 AB AAPKO KYA KARNA HAI

**Sirf 3 cheezein, isi order me:**

1. **Render par deploy karo** (guide: `RENDER-3-MINUTE-ME-KYA-KARNA-HAI.md`)
2. **Naya token banao** — purana 3 Nov ko khatam ho raha hai
   (guide: `TOKEN-KAISE-LE-AUR-KAHAN-SE.md`)
3. **Mujhe batao kaunse tools banau** — jaise: *"Phase 1 ke 6 tools banao"*
   ya *"11, 12, 13 banao"*

Main bana ke, poora test kar ke (aaj **1364 checks** pass hue hain),
**seedha GitHub par push** kar dunga. Aapko sirf Render par deploy dabana hai. 🙌
