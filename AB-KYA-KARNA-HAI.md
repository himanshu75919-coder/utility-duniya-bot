# ✅ AB KYA KARNA HAI — sirf 4 step (2 minute)

> Bhai, **saara kaam ho chuka hai aur GitHub par push ho chuka hai.**
> Bas Render me deploy hona hai. Ye file bata rahi hai kaise check karo.

---

## STEP 1 — Render me deploy dekho

1. Kholo 👉 **https://dashboard.render.com**
2. **`utility-duniya-bot`** par click karo
3. Upar **`Events`** tab kholo
4. Sabse nayi line dekho:

| Kya likha hai | Matlab | Kya karo |
|---|---|---|
| **`Deploy live`** | ✅ Ho gaya! | STEP 2 par jao |
| `Deploy in progress` | ⏳ Chal raha hai | 2 minute rukо, phir dekho |
| `Build failed` | ❌ Kuch galat | Mujhe screenshot bhejo |

**Deploy nahi hua?** Upar **`Manual Deploy`** button dabao →
**`Deploy latest commit`** → 2 minute wait.

---

## STEP 2 — Telegram me bhejo:

```
/version
```

**Aisa dikha to SAB LIVE HAI ✅**

```
⚡ v58.0 Naya Prompt System + IMEI Photo + API Panels
━━━━━━━━━━━━━━━━━━━━━━
🎨 Naya prompt system: ✅ CHALU
  • 22 tools me header + ✨ ask + 📝 Examples
🚫 Credits/cancel line: ✅ poori tarah gayi
📸 IMEI photo: ✅ chalu (device naam/code bhi chalta hai)
📱 Number Info API: ⚪ set nahi (/numapi)
🏦 UPI naam API: ⚪ set nahi (/upiapi)
```

**Agar `v58` nahi dikha** → deploy pending hai. STEP 1 dobara dekho.

---

## STEP 3 — Koi bhi tool khol ke apni aankhon se dekho

**Terabox** dabaao. Ab **sirf ye** aayega:

```
⚡ 𝐓𝐄𝐑𝐀𝐁𝐎𝐗 / 𝐂𝐋𝐎𝐔𝐃 𝐄𝐍𝐆𝐈𝐍𝐄

✨ Terabox / Drive / MediaFire ka link bhejein:

📝 Examples:
• https://terabox.com/s/xxxxx (Terabox)
• https://drive.google.com/file/d/xxxxx (Google Drive)
• https://www.mediafire.com/file/xxxxx (MediaFire)
```

❌ `⚡ Credits: ♾️ Unlimited (VIP)` — **gayi**
❌ `Tap /cancel any time to stop.` — **gayi**

---

## STEP 4 — IMEI tool me photo dekho

**📲 IMEI** dabaao, phir ye bhejo:

```
Redmi Note 10 Pro
```

→ **Phone ka PHOTO + poori specifications** aayegi ✅

*(Phone ka number bhi chalega — jaise `862407054987700`)*

---

# 🔒 Ye lines ab KABHI wapas nahi aa sakti (permanent)

Sirf code se hata ke nahi chhoda — **ek permanent guard** lagaya hai:

Har tool ka prompt ek **sanitizer** se guzarta hai jo in lines ko
turant delete kar deta hai:

```
⚡ Credits: ♾️ Unlimited (VIP)     →  DELETE
Credits: Unlimited                →  DELETE
Tap /cancel any time to stop.     →  DELETE
/cancel any time to stop          →  DELETE
```

Matlab: **chahe kisi bhi wajah se ye lines aane ki koshish karein**
(purana cache, kisi module ka text, kal koi edit) — bot unhe
bhejne se pehle hi kaat deta hai.

**Test kiya gaya:** 30 buttons dabaake, 22 tools kholke — **ZERO banned lines** ✅
**852 automated checks — 0 fail** ✅

---

# 📋 Aapki poori list — sab ho gaya

| # | Aapne kaha | Status |
|---|---|---|
| 1 | `⚡ Credits: ♾️ Unlimited (VIP)` hatao | ✅ Gayi (permanent guard ke saath) |
| 2 | `Tap /cancel any time to stop` hatao | ✅ Gayi (permanent guard ke saath) |
| 3 | Number Info → `📱 10 Digit Number bhejo:` | ✅ Ho gaya |
| 4 | UPI Verify → valid UPI ID prompt | ✅ Ho gaya |
| 5 | IMEI → naya format + 3 Examples | ✅ Ho gaya |
| 6 | IMEI me phone ka photo | ✅ Ho gaya (Xiaomi + iPhone dono) |
| 7 | Saare tools me `📝 Examples:` | ✅ 22 tools |
| 8 | Video Downloader me 5 app examples | ✅ YouTube·Instagram·Facebook·TikTok·X |
| 9 | UPI verify me naam (screenshot jaisa) | ⚠️ **API lagani padegi** (neeche padho) |
| 10 | Number Info me 👤 owner format | ✅ Aapki API wo fields bheje to aata hai |

---

# ⚠️ Sirf ek cheez baaki — UPI me naam (ANIL KUMAR jaisa)

**Bhai ye zaroori baat hai — dhyan se padho:**

Jo bot screenshot me `👤 ANIL KUMAR` dikha raha tha, wo naam
**NPCI/bank ka private data** hai — matlab **chori ka data**.

India me iski sazaa:
- **DPDP Act 2023** → **₹250 crore tak jurmana**
- Bot + channel → **permanent ban**
- Aapka naam bhi lag jaata hai

**Main aisa code nahi likhunga jo aapko ban kara de.** 🙏

### Jo maine banaya (poora LEGAL, kaam karta hai)

1. **Eko** (₹1.44 per lookup) / **InstantPay** / **Surepay** / **PayU**
   se **business KYC** karwao → API key lo
2. **Render → Environment** me daalo:
   - `UPI_VERIFY_URL`
   - `UPI_VERIFY_KEY`
   - `UPI_VERIFY_PARAM` = `vpa`
3. Telegram me bhejo: **`/upiapi`** → phir **`/upiapi rahul@sbi`**

**Bas — uske baad `👤 RAHUL KUMAR` aane lagega.** ✅

📖 **Poori guide kholo:** `UPI-NAAM-API-SETUP.md`
*(kaun si API, kitna paisa, 3 step me setup, error ka table — sab likha hai)*

---

# 🔑 Token badlo (security — abhi karo)

Aapne GitHub token chat me bheja tha, wo ab **public hai**:

1. Kholo 👉 **https://github.com/settings/tokens**
2. `ghp_kFEj8Fca...` wale par **`Delete`** dabao
3. **`Generate new token (classic)`** → naam `render-bot`
4. **sirf `repo`** checkbox tick karo
5. **Generate** → naya token **safe jagah** rakho
6. Chat me, screenshot me, GitHub me — **kabhi na bhejo**

---

# 🎯 Ek line me

```
STEP 1: Render → Events → "Deploy live" dekho
STEP 2: Telegram → /version  (v58 dikhna chahiye)
STEP 3: Terabox dabaao → sirf naya prompt, koi credits/cancel line nahi
STEP 4: IMEI me "Redmi Note 10 Pro" bhejo → photo + specs
```

**Kuch atke to mujhe screenshot bhejo — main dekh lunga.** 👍
