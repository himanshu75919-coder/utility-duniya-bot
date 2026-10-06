# 🔑 RENDER API KEY — Step by Step (aasan bhasha me)

> **Ye kya hai?** Ek chhoti si "chaabi" (key) jise de kar aap mujhe apne Render
> account me **sirf 2 line add karne** ki permission dete ho — bas itna hi kaam.
> Isse aapka password kisi ko dena hi nahi padta. ✅

---

## ⚡ Sabse chhota rasta (30 second) — Direct Link

**Ye link seedha "Create API Key" wala box khol dega:**

👉 **https://dashboard.render.com/u/settings?add-api-key**

- Agar **login** maange → wahi **email/Google** se login karo jisse aapne bot banaya tha
- Box khul jayega → **Name** me likho: `utility-duniya-bot` → **`Create API Key`** dabao
- Key aa jayegi, aisi: `rnd_xxxxxxxxxxxxxxxxxxxx` → **`Copy`** dabao

**Bas! Ho gaya** 🎉 Neeche se seedha **Step 5** padho.

Agar upar wala link kaam na kare, to neeche poora tarika hai 👇

---

## 🐢 Poora tarika (agar link na chale)

### Step 1 — Render par login karo
👉 **https://dashboard.render.com**

Wahi email/Google account use karo jisse aapne bot deploy kiya tha.
(Login hone par aapko apni services ki list dikhegi — jisme `utility-duniya-bot` hoga.)

### Step 2 — Account Settings kholo
**Desktop (laptop/PC) par:**
1. **Upar daayi taraf (top-right corner)** me apna **photo / naam ka circle** dikhega → us par click karo
2. Dropdown khulega → **`⚙️ Account Settings`** par click karo

**Mobile par:**
1. Upar left me **☰ (3 lines)** menu → `⚙️ Account Settings`

### Step 3 — "API Keys" section dhoondho
Account Settings page par **neeche scroll** karo.
Wahan sections honge — dhoondho **`API Keys`** (thoda neeche hoga, "Workspaces" ke aas-paas).

Uske andar ek **`Create API Key`** button hoga → **dabao**.

### Step 4 — Naam do aur banao
1. **Name** box me likho: `utility-duniya-bot` *(koi bhi naam chalega)*
2. **`Create API Key`** button dabao
3. Ab ek lambi key screen par dikhegi — shuru hoti hai **`rnd_`** se

> ⚠️ **ZAROORI:** Ye key **sirf EK BAAR** dikhti hai. Box **band karne se pehle**
> **`Copy`** dabao (ya poori key note kar lo).
> Agar copy karna bhool gaye → koi baat nahi, purani delete karke **nayi bana lo**.

### Step 5 — Mujhe bhej do
Chat me **sirf ye 2 cheez** bhej do:

1. **Key** — `rnd_` se shuru hone wali poori line
2. **Service ka naam** — jaisa Render par likha hai (jaise `utility-duniya-bot`)

> ⚠️ **Render ka PASSWORD ya email OTP kabhi mat bhejna** — sirf **API key** chahiye.
> API key se sirf services manage hoti hain, password jaisa kuch nahi hota.
> Aur kaam khatam hone ke baad **key delete kar dena** (Step 6).

### Step 6 — Main kya karunga (aapko kuch nahi karna)
1. Aapki services ki list dekhunga (naam se aapka bot dhoondhunga)
2. Bot me **2 line add** karunga:
   - `VEHICLE_PROVIDER_URL` = aapka RapidAPI endpoint
   - `VEHICLE_PROVIDER_KEY` = aapki RapidAPI key
3. **Deploy dabka** dunga (Render apne aap naya version chalayega)
4. Aap bot me **`/rcsetup`** bhej ke batana — main check kar dunga ki chal gaya ki nahi

### Step 7 — Kaam ke baad key delete kar do 🧹
**Account Settings → API Keys** → key ke aage **`Revoke` / delete icon** → bas.
(Isse purani key band ho jayegi. Zaroorat pade to nayi bana lena — 30 second ka kaam hai.)

---

## 🅱️ PLAN B — Agar key bilkul nahi banani (khud kar lo, 2 minute)

Ye kaam aap **khud bhi** kar sakte ho, usme koi key nahi chahiye:

1. 👉 https://dashboard.render.com par login karo
2. Apni service **`utility-duniya-bot`** par click karo
3. Left side menu me **`Environment`** par click karo
4. **`+ Add Environment Variable`** dabao → pehli line bharo:
   - **Key:** `VEHICLE_PROVIDER_URL`
   - **Value:** `https://vehicle-rc-information.p.rapidapi.com/VehicleInformation`
5. Phir se **`+ Add Environment Variable`** → doosri line:
   - **Key:** `VEHICLE_PROVIDER_KEY`
   - **Value:** aapki RapidAPI key (RapidAPI → My Apps → `default-application_12176190` → 🛡️)
6. Upar daayi taraf **`Save Changes`** dabao → Render **khud** deploy karega (2-3 minute lagega)
7. Bot me **`/rcsetup`** bhej ke check karo

**Bas itna hi!** Dono raste ka nateeja ek hi hai — fark sirf itna ki Plan B me aap khud karte ho.

---

## 🆘 Troubleshooting (kuch samajh na aaye to)

| Problem | Solution |
|---|---|
| "Account Settings nahi mil raha" | Upar daayi taraf apne **photo/naam ke circle** par click karo → dropdown me hai. Mobile me ☰ menu me |
| "API Keys section hi nahi dikh raha" | Settings page par **neeche scroll** karo. Browser me **Ctrl+F (mobile me page-search)** karke `API Keys` likho |
| "Key abhi dikh rahi hai, baad me gayab ho gayi" | Normal hai — key **ek hi baar** dikhti hai. Nayi banao (`Create API Key`), purani **Revoke** kar do |
| "Free plan me API key milti hai?" | **Haan** ✅ Free plan me bhi milti hai — card/paisa kuch nahi chahiye |
| "Key kis kaam ki hai, kya ye khatarnak hai?" | Sirf aapki Render services manage karne ke liye. Koi naya service/paisa wala kaam isse nahi hota. Kaam ke baad **Revoke** kar dena |
| "Create API Key dabaya, kuch nahi hua" | Pop-up block ho sakta hai → **laptop/desktop browser** me try karo, ya page reload karo |
| "Login nahi ho raha / password bhool gaya" | Render login page → **`Forgot password`** → email par reset link aayega |

---

## ✅ Ek line me yaad rakho

> **dashboard.render.com → top-right circle → ⚙️ Account Settings → neeche scroll →
> API Keys → Create API Key → naam do → Copy → mujhe bhej do → kaam ke baad Revoke.**
