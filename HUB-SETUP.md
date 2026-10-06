# ⚡ HUB + RC/CHALLAN — EK BAAR KA SETUP (10 minute, ₹0)

> Ye file bataati hai: **kya chal raha hai**, **kya band hai**, aur **kaise on karo** —
> bilkul step by step. Kuch bhi delete nahi hota.

---

# ✅ PART 1 — ABHI JO CHAL RAHA HAI (kuch karne ki zaroorat NAHI)

Aapka hub: **https://osint-api-hub.onrender.com** (version 2.8.4, 60+ endpoints)

| Hub ka tool | Bot me kahan | Status |
|---|---|---|
| `/api/pincode` | 📮 PINCODE INFO | ✅ chal raha |
| `/api/gst-info`, `/gst-direct` | 📜 KAGAZ → GST | ✅ chal raha |
| `/api/pan-info`, `/pan-to-gst` | GST card me PAN | ✅ chal raha |
| `/api/pass-check` | (password leak check) | ✅ chal raha |
| `/api/ip-v2` | 🌐 IP tools | ✅ chal raha |
| `/api/device-specs` | 📲 IMEI / phone | ✅ chal raha |
| `/api/youtube-*`, `/ytdl` | downloader backup engine | ✅ chal raha |
| `/api/terabox-*` | ⚡ TERABOX | ✅ chal raha |

**Hub jaagta kaise rehta hai?** Aapka **bot khud hi** hub ko har **4 minute** me ping
karta hai (`KEEPALIVE_PEERS` → `https://osint-api-hub.onrender.com/health`) — isliye hub
sota nahi aur jawab tez rehta hai. **Kuch setup nahi chahiye.**

(Chaaho to GitHub Actions se bhi chala sakte ho — file `github-workflows/` folder me hai,
uska README padho. Ye optional hai.)

---

# 🚗 PART 2 — RC + CHALLAN (GAADI X-RAY) — ye khud se ON nahi ho sakta, 2 minute ka kaam

**Sach ye hai:** RC/owner/challan ka data VAHAN par **captcha** ke peeche hai.
Bot captcha nahi todta — wo illegal hai. Isliye iske liye **ek licensed provider API**
chahiye (ye har bada app karta hai).

## 🆓 Sabse sasta rasta — RapidAPI ka BASIC (free) plan

1. Kholo 👉 **https://rapidapi.com/fatehbrar92/api/vehicle-rc-information**
2. **Sign up** karo (Google se 10 second) — **card ki zaroorat nahi**
3. **Subscribe to Test** / **BASIC (Free)** dabao
4. **Endpoints** tab kholo → `POST` wala endpoint → right side me aapki
   **`X-RapidAPI-Key`** dikhegi → copy karo
5. Ye 2 cheezein mujhe bhej do (ya khud lagao, neeche tarika hai):
   - `Key` = aapki `X-RapidAPI-Key`
   - `Host` = `vehicle-rc-information.p.rapidapi.com`

> 💡 Free plan par mahine me kuch hundred calls milte hain — naam, model, insurance,
> RC status, blacklist sab. (Bade volume ke liye baad me ₹2.5/check wala pack.)

## 🔧 Lagane ke 2 tarike (dono support hain — jo aasan lage)

### Tarika A — Bot ke Render me (2 minute)
Render → **utility-duniya-bot** → **Environment** → ye 4 add karo:

```
VEHICLE_PROVIDER_URL   = https://vehicle-rc-information.p.rapidapi.com/
VEHICLE_PROVIDER_KEY   = <aapki X-RapidAPI-Key>
VEHICLE_PROVIDER_METHOD= POST
VEHICLE_PROVIDER_BODY  = {"vehicle_number":"{number}"}
VEHICLE_PROVIDER_HEADERS = X-RapidAPI-Key:{key}|X-RapidAPI-Host:vehicle-rc-information.p.rapidapi.com
```
Phir **Manual Deploy** → Teleagrm me `🚗 RC + CHALLAN` dabao → `BR01AB1234`
→ **poora record bot ke andar card me** aa jayega.

### Tarika B — Hub ke Render me (same env naam)
Render → **osint-api-hub** → Environment → wahi 4 lines (upar wali).
Bot khud hub se pooch leta hai — bot me kuch nahi badalna padta.

### ⚡ Tarika C — GitHub se hi (dashboard bhi nahi kholna)
Repo → **Settings → Secrets and variables → Actions** → 2 secrets banao:
`HUB_RENDER_API_KEY` (Render account ka API key) + `HUB_SERVICE_ID` (hub ka `srv-...` id)
→ **Actions → "Hub: providers ON" → Run workflow** → URL/key box me daalo → Run.

## Provider NA ho to kya hota hai? (jhooth nahi bolta)
Bot tab bhi khaali nahi lautta — plate ka **sarkari matlab** dikhata hai:
state + RTO office + series, aur **official SMS tarika**:
`VAHAN BR01AB1234` ya `CHALLAN BR01AB1234` likhkar **7738299899** par bhejo
(MoRTH/NIC ka apna gateway, free) — poora RC/challan SMS me aa jata hai.

---

# 🔒 PART 3 — HUB KA ACCESS PASSWORD (`#HINdustan03`)

Password **public repo me kabhi nahi daalna** — GitHub bots usko 2 minute me utha lete hain
aur hub par kisi ka bhi control ho sakta hai. Behtar:
1. Password **badal do** (jo ab tak chat/screenshot me aaya hai, use purana maano)
2. Bot/hub me lagane ke liye Render ke **Environment** me secret ke roop me daalo
3. GitHub par lagana ho to **Settings → Secrets** me daalo — code me kabhi nahi

---

# 🎁 PART 4 — FREE ME AUR KYA-ON HO SAKTA HAI (batao to jod dunga)

| Service | Free plan | Kya milega bot me |
|---|---|---|
| **Have I Been Pwned** | Free API key (email check) | Email leak check — result bot ke andar |
| **VirusTotal** | Free (4 calls/min) | 📦 FILE TYPE X-RAY ka bhai — link/APK virus scan |
| **gstinapi.in** | 100 checks/month | Double GST source (hub + direct) |
| **OpenCage / BigDataCloud** | Free tier | Photo GPS → poora address (better) |
| **Abstract API (phone)** | Free tier | Number ka carrier/line-type backup |

Bolo kaunsa chahiye — mera pick: **VirusTotal + HIBP** (dono fraud se bachne ke liye sabse kaam ke).
