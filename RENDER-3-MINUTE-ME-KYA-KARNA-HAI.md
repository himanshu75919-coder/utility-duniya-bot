# 🎯 RENDER PAR KYA KARNA HAI — EKDUM SIMPLE (3 MINUTE)

**Bhai, tension mat lo. Code already GitHub par chala gaya hai. Render me sirf
neeche wala kaam karna hai. Bas itna — aur kuch nahi.**

---

## ⚡ SABSE PEHLA KAAM — sirf 1 cheez samajh lo

Render ka **"Environment"** kya hai?
→ Ye bas ek **list** hai — jaise ek diary jisme likha hota hai:
**"key" (naam) = "value" (uski value/cheez)**

Jaise:
```
BOT_TOKEN   =  1234567890:AAHxxxxxx
ADMIN_ID    =  7567000000
```

Bas itna hi hai. **Key = naam. Value = us naam ke aage ki cheez.**
Isse zyada kuch nahi samajhna hai. 👍

---

## ✅ KAAM 1 — Render kholo aur Environment me 3 line daalo

1. Browser me kholo → **https://dashboard.render.com**
2. Apni service par click karo → naam hoga **`utility-duniya-bot`**
3. Left side me **`Environment`** par click karo
4. Wahan **`Add from .env`** naam ka button hoga → uspar click karo
5. Ab ye 3 line **copy** karke us box me **paste** kar do:

```
ALL_FREE=on
PREMIUM_ONLY=off
VAULT_GITHUB_REPO=himanshu75919-coder/utility-duniya-bot
```

6. Neeche **`Save Changes`** dabao ✅

> ℹ️ **`Add from .env` button na mile to?** Koi baat nahi.
> **`Add Environment Variable`** dabao aur ek-ek karke ye 3 daalo —
> **Key** me pehla word, **Value** me dusra word:
>
> | Key (naam) | Value (uske aage ki cheez) |
> |---|---|
> | `ALL_FREE` | `on` |
> | `PREMIUM_ONLY` | `off` |
> | `VAULT_GITHUB_REPO` | `himanshu75919-coder/utility-duniya-bot` |

---

## ✅ KAAM 2 — 1 secret key daalo (data na khone ke liye)

Same Environment page par ek aur variable daalo:

| Key (naam) | Value (uske aage ki cheez) |
|---|---|
| `VAULT_GITHUB_TOKEN` | *(wo long token jo maine aapko diya tha — neeche dekho)*

👉 **Token yahan hai:** isi folder me **`MERI-KEYS.txt`** naam ki file hai —
usme token likha hua hai. Wahan se copy karke paste kar do.
(Ye file GitHub par **nahi** jayegi — maine rok laga di hai.)

**Ye kyun zaroori hai?** Render ka free plan har deploy par purana data
delete kar deta hai. Ye token is liye daalna hai ki aapka data (users,
premium, credits) ek **alag branch me encrypted backup** ban kar safe rahe.

> Skip bhi kar sakte ho — par phir deploy par users ka data ud sakta hai.
> **Daal dena hi better hai, 20 second ka kaam hai.**

---

## ✅ KAAM 3 — Render ko chalao

1. Upar **`Manual Deploy`** button dabao
2. **`Deploy latest commit`** par click karo
3. **2-4 minute** ruko (screen par "Building" → "Deploying" → **"Live"**)
4. `Live` likha aa gaya? 🎉 **KAAM HO GAYA.**

---

## ✅ KAAM 4 — Bot ko check karo (30 second)

Telegram me apna bot kholo aur ye 3 cheez bhejo:

| Kya bhejo | Kya dikhna chahiye |
|---|---|
| `/start` | Menu khule + neeche likha ho **"SAARE TOOLS 100% FREE HAIN"** |
| Neeche wala button **`📋 ALL TOOLS (FREE)`** | Poori list dikhe, sab free |
| `/version` | `v61.0 FREE4ALL` likha ho |

**Menu me ab `💎 VIP PREMIUM` button nahi hoga** — uski jagah
**`📋 ALL TOOLS (FREE)`** aa gaya hai. Ye sahi hai, matlab kaam ho gaya.

---

## ❓ "Render mujhse aur bahut saari keys poochh raha hai — kya daalun?"

**JAWAB: KHALI CHHOD DO.** 👈 Sabse important line.

Render 16 keys poochh sakta hai. Aapko sirf **upar wali 3-4** bharni hain.
Baaki **sab khali chhod dena** — khali chhodne se kuch nahi bigadta, bot
normal chalega.

Khaas taur par inhe **DHYAN SE KHALI** chhodna:

| Key | Kya karna hai |
|---|---|
| `ADMINS` | khali chhodo *(sirf tab bharo jab aur admin add karne ho)* |
| `FORCE_CHANNEL` | khali chhodo |
| `FORCE_CHANNEL_LINK` | khali chhodo |
| `UPI_ID` | khali chhodo *(ab payment/UPI ka kaam hi nahi hai — sab free hai)* |
| `TUTORIAL_URL` | khali chhodo |
| `WEBHOOK_URL` | khali chhodo |
| `WEBHOOK_SECRET` | khali chhodo |
| `VAULT_KEY` | khali chhodo *(khali = bot khud BOT_TOKEN se lock laga dega)* |
| `VAULT_BACKUP_CHAT_ID` | khali chhodo |
| `VEHICLE_PROVIDER_URL / KEY` | khali chhodo |
| `NUMINFO_PROVIDER_URL / KEY` | khali chhodo *(khali = offline mode, phir bhi chalta hai)* |
| `BOT_TOKEN` | **❗YE PEHLE SE BHARA HAI — CHHEDNA NAHI** |
| `ADMIN_ID` | **❗YE PEHLE SE BHARA HAI — CHHEDNA NAHI** |

---

## 🆘 Kuch galat ho gaya to?

| Problem | Kya karo |
|---|---|
| Bot jawab nahi de raha | 2 minute ruko (free Render ko neend se uthne me time lagta hai), phir `/start` |
| Render me "Deploy failed" | **Logs** kholo → jo last red line ho wo mujhe bhej do |
| "Conflict" likha aa raha | 1 minute ruko, apne aap thik ho jata hai |
| Menu me purana VIP button dikh raha | Telegram me `/start` phir se bhejo (naya menu aa jayega) |

---

## 📌 SABSE ZAROORI 3 BAATEIN (yaad rakh lo)

1. **Aapko CODE me kuch nahi karna.** Main sab GitHub par push kar chuka hoon.
2. **Sirf 3-4 keys bharni hain, baaki sab KHALI.** Khali = koi problem nahi.
3. **Kisi user ka data delete NAHI hua.** Purane VIP users ka premium DB me
   safe hai. Sirf darwaza sabke liye khol diya gaya hai. 🎉

---

## 🔁 Agar kabhi wapas VIP/premium system chalu karna ho

Render → Environment me sirf itna badal do:

```
ALL_FREE=off
```

Save → Deploy. Bas. **Purana poora premium system wapas aa jayega** —
kyunki maine kuch delete nahi kiya tha, sirf ek switch lagaya tha. 🔒
