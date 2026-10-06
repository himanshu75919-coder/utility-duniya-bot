# 🔑 VAULT_GITHUB_REPO aur VAULT_GITHUB_TOKEN — POORI JAANKARI

**Do cheezein samajh lo, bas itna hi hai:**

| Key (naam) | Value me kya jaata hai | Kahan se milega |
|---|---|---|
| `VAULT_GITHUB_REPO` | `himanshu75919-coder/utility-duniya-bot` | Ye **bas likh dena hai** — kuch dhoondhna nahi |
| `VAULT_GITHUB_TOKEN` | `ghp_` se shuru hone wala **lamba code** | GitHub se banate hain (neeche step-by-step) |

**Ye kyun chahiye?** Render ka free plan har deploy par purana data **delete**
kar deta hai. Ye token is liye daalte hain ki aapka data (users, premium,
credits) GitHub ke ek **alag branch me encrypted (lock laga kar) backup**
ban kar chala jaye. Deploy hone par bot usi backup se sab wapas le aata hai.

> 🔒 Backup **encrypted** hota hai — repo public ho to bhi koi padh nahi sakta.

---

# ✅ KAAM 1 — `VAULT_GITHUB_REPO` me kya likhna hai

**Bahut simple. Bas ye exact ye line copy karke paste kar do:**

```
himanshu75919-coder/utility-duniya-bot
```

Koi `https://` nahi, koi space nahi. Bas `naam/repo`. Done ✅

---

# ✅ KAAM 2 — `VAULT_GITHUB_TOKEN` kahan se lena hai (6 STEP)

### 📍 Step 1 — GitHub kholo aur login karo
👉 **https://github.com**
(aapka username hai: `himanshu75919-coder`)

### 📍 Step 2 — Token wala page kholo
👉 **https://github.com/settings/tokens**

*(Ya: right corner me apni photo → `Settings` → left menu me sabse neeche
`Developer settings` → `Personal access tokens` → `Tokens (classic)`)*

### 📍 Step 3 — Naya token banao
Upar right me **`Generate new token`** dabao → **`Generate new token (classic)`** chuno.
(GitHub aapka **password** maang sakta hai — daal do.)

### 📍 Step 4 — Form bharo (3 cheezein)

| Kya | Kya bharna hai |
|---|---|
| **Note** | `render-bot-vault` (koi bhi naam likh do) |
| **Expiration** | ⚠️ **`No expiration`** chuno — *ye sabse zaroori step hai* |
| **Select scopes** | ✅ Sirf **`repo`** wale box me tick lagao (uske andar ke sab apne aap tick ho jayenge) |

Baki kuch **tick mat karo**.

> ⚠️ **Expiration me "No expiration" kyun?**
> Agar date lagayi, to us date ke baad backup **chup-chaap band ho jayega**
> aur aapko pata bhi nahi chalega. (Aapka abhi wala token **3 November 2026**
> ko khatam ho raha hai — neeche detail me likha hai.)

### 📍 Step 5 — Token banao aur COPY karo
Neeche **`Generate token`** dabao.
Ab ek **lamba code** dikhega — jaise:
```
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
👉 Uske aage wala **copy button** (📋) dabao. **Ye code sirf EK BAAR dikhta hai**,
page band kiya to wapas nahi milega (phir naya banana padega).

### 📍 Step 6 — Render me paste karo
1. 👉 **https://dashboard.render.com** kholo
2. Apni service **`utility-duniya-bot`** par click
3. Left me **`Environment`** → **`Add Environment Variable`**
4. **Key** me likho: `VAULT_GITHUB_TOKEN`
5. **Value** me wo copy kiya hua `ghp_...` code paste karo
6. **`Save Changes`** dabao ✅

---

# ⚠️ ZAROORI — AAPKA ABHI WALA TOKEN 3 NOVEMBER 2026 KO KHATAM HO RAHA HAI

Maine aapka current token check kiya. Ye **kaam kar raha hai** (sahi chal raha hai),
**lekin** ye **3 November 2026** ko expire ho jayega.

Us din ke baad kya hoga:
- ❌ GitHub backup band ho jayega
- ✅ Bot band NAHI hoga, crash NAHI hoga — Telegram backup chalta rahega
- ⚠️ Par offsite (bahar wala) backup ruk jayega

**Isliye abhi hi naya token bana lo** (upar wale 6 step, bas **`No expiration`**
chunna) aur Render me purane `ghp_...` ki jagah naya paste kar do. **5 minute ka kaam hai.**

> 📌 Yaad rakhne ka aasan tarika: **mahine me ek baar `/vault` command chala lo** —
> wo batata hai backup chal raha hai ya nahi.

---

# 🔍 KAAM 3 — CHECK karo ki token sahi laga ya nahi

1. Telegram me apne bot par ye 3 command chalao:

| Command | Kya dikhna chahiye |
|---|---|
| `/vault` | GitHub: **ON** likha ho (🔴 OFF nahi) |
| `/backup` | `✅ Backup ban gaya` aur ek `.enc` file aayegi |
| `/sys` | Sab 🟢 green |

2. GitHub par check karo 👉 **https://github.com/himanshu75919-coder/utility-duniya-bot/branches**
   → **`vault-backup`** branch me ek `.enc` file dikhni chahiye. ✅

> ⚠️ **`main` branch me backup kabhi nahi jayega** — ye jaan-boojh kar aisa hai.
> `main` me gaya to Render har backup par naya deploy karta rehta, aur bot ka
> **infinite restart loop** ban jata. Isliye alag branch `vault-backup` hai.

---

# 🚫 TOKEN BILKUL NAHI LENA CHAHTE? (chalega, par…)

**Token ke bina bhi bot chalta hai — crash nahi hoga.**

Us case me backup sirf **Telegram par** aayega: bot har 30 minute me aapko
(aapki admin chat me) ek **`.enc` file** bhej dega — wahi encrypted backup.

| | Token ke saath | Sirf Telegram |
|---|---|---|
| Data safe rehta hai | ✅ | ✅ |
| Deploy par khud restore | ✅ **automatic** | ⚠️ file se manual |
| Offsite (bahar) copy | ✅ GitHub par | ❌ aapke Telegram me |
| Mehnat | 5 minute, ek baar | 0 |
| Risk | kam | **thoda zyada** |

**Meri sifarish:** token laga do. Ek baar ka 5 minute ka kaam hai, aur
**poora data hamesha safe** rehta hai.

---

# 🔐 TOKEN KI SAFETY — 4 BAATEIN (bahut important)

1. ❌ Token **kabhi kisi ko na do** — dost, group, YouTube comment, kisi ko nahi.
   Token = aapke GitHub ka **master key**.
2. ❌ Token **kabhi code me na likho** aur **GitHub par push mat karo**.
   (Ek baar maine galti se guide me likh diya tha — GitHub ne **push reject**
   kar diya. Achha hua, warna leak ho jata.)
3. ✅ Token **sirf Render ke Environment tab** me daalo.
4. ❌ Screenshot me bhi token dikhta ho to usko **kaat do** (blur/crop).

> **Galti se leak ho gaya?** Turant 👉 https://github.com/settings/tokens
> → us token ke aage **`Delete`** dabao → naya banao. Purana token **turant band** ho jata hai.
> (Bina delete kiye bhi, GitHub ke `Settings → Sessions` me sab dikh jata hai.)

---

# 🎯 CHHOTA SUMMARY (yaad rakhne ke liye)

```
VAULT_GITHUB_REPO   =  himanshu75919-coder/utility-duniya-bot
VAULT_GITHUB_TOKEN  =  ghp_....  (github.com/settings/tokens se, No expiration)
```

Bas ye 2 keys. Iske alawa Render me kuch aur **bharna zaroori nahi**. 🙌
