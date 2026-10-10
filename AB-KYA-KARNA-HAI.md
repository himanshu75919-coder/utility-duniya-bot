# ✅ AB AAPKO KYA KARNA HAI — sirf 3 kaam

Bot ka saara code ka kaam **ho chuka hai** aur GitHub par chadh chuka hai.
Ab aapke haath ke sirf **3 chhote kaam** bache hain. Teeno milakar ~5 minute.

Ye teeno **zaroori** hain — inke bina bot to chalega, par backup band rahega
aur aapka GitHub token khatre me rahega.

---

## 🔴 KAAM 1 — Purana GitHub token turant band karo (SABSE ZAROORI)

Humne baat-cheet me aapka GitHub token (`ghp_...`) use kiya tha. Wo ab
**chat me likha hua hai**, isliye use **band karna zaroori hai** — warna koi
aur aapke repo me kuch bhi badal sakta hai.

> Ye ghabrane wali baat nahi hai — token band karna 30 second ka kaam hai aur
> isse aapka bot bilkul nahi rukega.

**Steps:**

1. [github.com](https://github.com) kholo → upar dayein apni photo par click
2. **Settings**
3. Sabse neeche → **Developer settings**
4. **Personal access tokens** → **Tokens (classic)**
5. Jo token dikhe uske saamne **Delete** (ya **Revoke**) dabao → confirm

✅ Ho gaya. Purana token ab bekaar hai.

---

## 🟠 KAAM 2 — Naya token banao (Vault backup ke liye)

Aapke Render logs me ye error aa raha hai:

```
GitHub backup fail: HTTP 401 {"message": "Bad credentials"}
vault branch ready nahi
```

**Iska matlab:** Render me jo `VAULT_GITHUB_TOKEN` pada hai wo purana/expire ho
chuka hai. Isliye **aapke bot ka backup GitHub par ja hi nahi raha.** Restart
hua to data ja sakta hai. Naya token daalte hi ye theek ho jayega.

**Naya token banane ke steps:**

1. Wahi page khula rakho: **Settings → Developer settings → Personal access
   tokens → Tokens (classic)**
2. **Generate new token** → **Generate new token (classic)**
3. Bharo:
   - **Note:** `utility-duniya-bot vault`
   - **Expiration:** `No expiration` (ya 1 year)
   - **Select scopes:** sirf **`repo`** wale box par ✅ tick karo
     *(uske andar ke sab chhote box apne aap tick ho jayenge — yahi sahi hai)*
4. Neeche **Generate token**
5. Jo lamba code (`ghp_...`) dikhe use **abhi copy kar lo**

> ⚠️ Ye code sirf **ek baar** dikhta hai. Page band kiya to dobara nahi milega —
> phir naya banana padega. Isliye pehle copy, phir KAAM 3.

---

## 🟢 KAAM 3 — Naya token Render me daalo

1. [dashboard.render.com](https://dashboard.render.com) kholo
2. **utility-duniya-bot** service par click
3. Bayein menu me **Environment**
4. `VAULT_GITHUB_TOKEN` dhundo → uske saamne **Edit** (pencil 🖊️)
5. Purani value hatao → naya `ghp_...` token paste karo
6. **Save Changes**

Bot apne aap restart hoga (2–3 minute).

### Saath hi ye bhi check kar lo (ek hi page par hai)

| Key | Value | Kyun |
|---|---|---|
| `VAULT_KEY` | koi bhi lamba password | **agar khali hai to zaroor bharo.** Khali hone par encryption key `BOT_TOKEN` se banti hai — BotFather se token badla to purane backup kabhi nahi khulenge |
| `VAULT_GITHUB_BRANCH` | `vault-backup` | ⚠️ ise `main` **mat** karna, warna har backup naya deploy chalu kar dega aur bot restart loop me fas jayega |

---

## 🎉 Check karo sab theek hai

Render restart hone ke baad Telegram par bot ko bhejo:

```
/sys
```

Dekho:

- `🛡️ Premium Vault: 🟢 ON`
- `github: ✅ ready` *(401 wala error gaya — yahi KAAM 2+3 ka proof hai)*
- `RAM` me **60–120 MB** jaisa kuch *(pehle 450–490 MB aata tha)*
- Koi `⚠️ VAULT_KEY set karo` warning **na** dikhe

Phir `/start` bhejo — menu me sirf **2 button** honge:
**📱 NUMBER INFO** aur **👪 FAMILY INFO**. Dono test kar lo.

---

## ❓ Agar kuch gadbad lage

| Dikh raha hai | Kya karo |
|---|---|
| `/start` par purana bada menu | Telegram app band karke kholo, phir `/refresh` bhejo |
| `github: ❌` ab bhi | token banate waqt **`repo`** scope tick karna bhool gaye — naya token banao |
| Bot jawab hi nahi de raha | Render → Logs kholo, aakhri 20 line copy karke mujhe bhejo |
| RAM ab bhi 400+ | Render par deploy purana hai — Manual Deploy → **Clear build cache & deploy** |

**Aapke 2 tools (Number Info + Family Info) ka code ek line bhi nahi badla hai**,
isliye wo pehle jaisa hi chalega — bas ab rukega nahi. 🚀
