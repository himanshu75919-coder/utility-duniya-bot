# 🏦 UPI naam API — kaise lagayein (aur sach kya hai)

> **Pehle sach:** Screenshot me jo bot "Account Holder Name: ANIL KUMAR" dikha
> raha tha — wo naam **NPCI/bank ka PRIVATE data** hai. Jo bots ye dikhate hain
> wo **leaked ya unauthorized data** use karte hain (koi public API aisa naam
> nahi deti). India me iski sazaa **DPDP Act 2023 ke tahat ₹250 crore tak** hai,
> aur bot + channel **ban** ho jaate hain.
>
> **Aapka bot wo kaam LEGAL tarike se karega** — apni API lagao, consent ke
> saath naam aayega. Ye file batati hai kaise.

---

## 🔍 Sach: naam kahan se aata hai?

| Tarika | Legal? | Naam milta hai? | Kis ke liye |
|---|---|---|---|
| **NPCI Validate Address API** | ✅ Haan | ✅ Haan | sirf payment companies (PSP/merchant) |
| **B2B KYC APIs** (Eko, InstantPay, Surepay, PayU) | ✅ Haan | ✅ Haan | business (KYC + paid wallet + **consent**) |
| **Public bank-handle list** (aapka bot abhi) | ✅ Haan | ❌ Nahi | sabke liye |
| **Leaked databases / "OSINT" bots** | ❌ **Illegal** | ✅ (chori ka data) | 😡 koi nahi |

**Aapke bot me dono legal raste hain** — bina API par format/bank, aur API
lagane par **asli naam**.

---

## 💰 Kaun si API lagayein?

| Provider | Price | Kya milta hai | Kya chahiye |
|---|---|---|---|
| **Eko** (eps.eko.in) | **₹1.44 / lookup** | naam + VPA status + linked mobile | PAN + address verify, wallet load |
| **InstantPay** | negotiated | naam + `nameMatchPercent` + account type | business KYC |
| **Surepay / nxtBanking / Softpay** | negotiated | naam + VPA active status | business KYC |
| **PayU** (`validateVPA`) | merchant plan | VPA valid + naam | PayU merchant account |

> **Aasan shuruaat:** Eko ka developer console — sandbox turant milta hai,
> pehla API call paperwork se pehle kar sakte ho.

⚠️ **Ye free nahi hai** — per-lookup paisa lagta hai (~₹1-2). Isliye aapke bot
me ye feature **default OFF** hai; jab chaho on karo.

---

## 🎯 STEP 1 — API key lo

1. Kholo 👉 **https://eps.eko.in/products/upi-verification-api**
2. **Developer console** par sign up karo
3. **PAN + address** se identity verify karo (business KYC)
4. Wallet me thoda balance daalo (test ke liye ₹100 kaafi hai)
5. Dashboard se **API key / auth token** copy karo

---

## 🎯 STEP 2 — Render me daalo

1. 👉 **https://dashboard.render.com** → **utility-duniya-bot** → **Environment**
2. **`+ Add Environment Variable`** — ye 5 lines daalo:

| Key | Value |
|---|---|
| `UPI_VERIFY_URL` | `[API ka endpoint]` *(provider docs se)* |
| `UPI_VERIFY_KEY` | `[apni key paste karo]*` |
| `UPI_VERIFY_PARAM` | `vpa` *(`accountNumber` bhi ho sakta hai)* |
| `UPI_VERIFY_AUTH` | `query` *(ya `header` / `bearer`)* |
| `UPI_VERIFY_METHOD` | `GET` *(InstantPay jaisa POST ho to `POST`)* |

3. **Save Changes** → 1-2 minute wait

### Extra options (zaroorat pade to)

| Key | Kaam | Default |
|---|---|---|
| `UPI_VERIFY_KEY_PARAM` | key kis param me jaati hai | `key` |
| `UPI_VERIFY_HEADER` | `auth=header` par header ka naam | `X-Api-Key` |
| `UPI_VERIFY_CONSENT` | B2B APIs me `consent: Y` chahiye | `Y` |
| `UPI_VERIFY_TIMEOUT` | 4-30 second | `12` |

---

## 🎯 STEP 3 — Telegram se check karo

```
/upiapi                    → API lagi hai ya nahi (status)
/upiapi rahul@sbi          → live test
```

**Sab theek ho to:**
```
✅ UPI API CHAL RAHI HAI!
👤 Name: RAHUL KUMAR
🎯 VPA: rahul@sbi
🏛️ Bank: State Bank of India
⚡ Status: SUCCESS / ACTIVE
⏱️ Latency: 412ms
```

Ab **🏦 UPI VERIFY** me UPI ID bhejo — card me **naam** aayega:

```
┌──────────────────────────────
│ 🏦 𝐔𝐏𝐈 𝐕𝐄𝐑𝐈𝐅𝐘 𝐑𝐄𝐏𝐎𝐑𝐓
└──────────────────────────────
👤 Account Holder Name
   └ 💳 RAHUL KUMAR
💳 VPA / UPI ID: rahul@sbi
🏛️ Associated Bank: State Bank of India
...
📡 Name Source: 🟢 aapki UPI API se (consented)
```

---

## 🚑 Fail ho to (4 check)

| Message | Matlab | Kya karo |
|---|---|---|
| `key reject (HTTP 401/403)` | key galat | Render me key dobara paste karo |
| `HTTP 404` | URL galat | provider docs se **exactly** copy karo |
| `format match nahi hua` | response shape alag | provider ka sample response dekh ke `UPI_VERIFY_PARAM` theek karo |
| `HTTP 429` | limit khatam | wallet recharge karo |

> **API fail ho to tool band NAHI hota** — UPI Verify purane tarike se chalta
> rehta hai (format + bank handle + honest note). **Kuch crash nahi hota.**

---

## 🔒 RULES (tod na dena)

| ✅ KARO | ❌ NA KARO |
|---|---|
| Key sirf Render me rakho | Chat/screenshot me key na dikhao |
| **Har lookup par user ka consent** lo | Kisi aur ka naam uski marzi ke bina na dekho |
| Sirf apne/apne customer ke VPA check karo | Random numbers/VPA par mass lookup na karo |
| Provider ke terms follow karo | Data kahin store/sell na karo |

**Law yaad rakho:** kisi aur ka naam, address, ya govt ID uski **ijazat ke
bina** dekhna/dena — DPDP Act 2023 ke khilaaf hai. Isliye aapka bot wo kaam
**sirf API + consent** ke saath karta hai, warna saaf mana kar deta hai.

---

## 📌 Ek nazar me

```
STEP 1: Eko/InstantPay/Surepay par account → KYC → API key
STEP 2: Render → Environment → 5 lines (UPI_VERIFY_*) → Save
STEP 3: Telegram → /upiapi  →  /upiapi rahul@sbi
        → UPI Verify me naam aane laga ✅
```

**API nahi lagayi?** Koi dikkat nahi — UPI Verify phir bhi kaam karta hai
(format + bank handle + honest note), aur har jagah saaf likhta hai ki
holder naam public nahi hota. Bot **na jhooth bolta hai, na kuch crash hota hai**.
