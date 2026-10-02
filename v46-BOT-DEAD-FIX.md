# v46 — "Bot dead ho gaya / kuch response nahi" — ASLI WAJAH AUR PERMANENT FIX

Push: `3387210` (v46) + `369e337` (v46.1)  ·  Repo: `himanshu75919-coder/utility-duniya-bot`

---

## 1) SABSE BADI WAJAH — do bot instance ek saath chal rahe the

Render log me ye dikha tha:

```
[8zmc9] ERROR | Exception handling update: Conflict: terminated by other getUpdates request;
        make sure that only one bot instance is running
[mvq5n] ERROR | Conflict: terminated by other getUpdates request
```

Matlab: **ek hi bot token se do jagah polling chal rahi thi** (01:41 aur 01:43 ke do
back-to-back deploys). Telegram dono ko ek saath allow nahi karta — dono ko
`Conflict` mila aur **bot har message chup-chap ignore karne laga**. Isme code ka
koi fault nahi tha.

### Permanent fix (Render dashboard — 2 minute ka kaam)
1. Render → Dashboard → services ki list dekho.
2. Agar **do service** hain jo isi bot ko chalati hain → ek ko **Suspend** ya **Delete**
   kar do. Sirf ek service chalni chahiye.
3. Ek hi service ho to uske **Events** tab me check karo: kya ek hi waqt me do
   "Deploy live" hue the? Haan to Manual Deploy karke purane instance ko mar do.
4. Deploy ke baad log me ye line dikhni chahiye (**v46 me add kiya hai**):
   `STARTING POLLING | instance=xxx pid=123 | only ONE instance must run`
   Agar **do alag instance-id** dikhe → wapas duplicate hai.

> Note: `drop_pending_updates=True` pehle se tha — ye conflict rokta nahi, sirf
> purane pending updates saaf karta hai. Duplicate instance hatana hi asli ilaaj hai.

---

## 2) DUSRI WAJAH — source slow tha, bot 30-60 second tak CHUP rehta tha

Hub (upstream sources) kabhi-kabhi 28-60 second leta hai. Purana flow:
`await asyncio.to_thread(...)` → user ko 30-60 second tak **koi bhi message nahi**.
User ko laga "bot mar gaya".

### v46 me kya banaya (permanent, code me)
`bot.py` me do naye helper:

```python
async def hub_with_progress(wait_msg, hub_fn, arg, what="", timeout=24)
async def deliver_hub_later(task, context, chat_id, build_fn)
```

- **har 6 second me** wait-message update hota hai:
  `🔎 Source se data aa raha hai... 12s ho gaye. Bas thoda aur wait karein ⏳`
- 18-24 second ke baad bhi result na aaye to call **background me chalti rehti hai**,
  user ko turant jo mil sakta hai wo mil jata hai, aur **result aate hi naya message
  aa jata hai** (60 second tak bhi).
- `OSINT_TIMEOUT` 45s → **70s** (ab chup-chap wait nahi karwana padta).

Lagoo hua:
| Tool | Pehle | Ab |
|---|---|---|
| 📱 Number Info | 30-60s khaali screen | Basic card **turant**, public records baad me |
| 🆔 Aadhaar Family | 30-60s khaali screen | Progress + late delivery |
| 🚗 Vehicle + Challan | 30-60s khaali screen | Free RTO card **turant**, live RC+challan baad me |
| 🔄 "Check again" button | 30s hang | Progress + late delivery |

---

## 3) Aadhaar "Unknown" naam

Hub ka source kabhi-kabhi naam `region` field me daal deta hai (jaise `Bipin Baitha`),
aur `full_name` khaali hota hai → card me `Unknown` dikhta tha.

- **Hub side** (`osint-api/main.py`): `_looks_like_person_name()` — agar naam khaali
  ho aur `region` naam jaisa lage (2+ words, mixed case, koi operator/state word nahi)
  to wahi naam use karo.
- **Bot side**: `Unknown` / `Name not in source` aaye to father se label banta hai
  (`Ram Dev Baitha ka parivar`), warna `—`.
- Hub me **family expansion ab phone numbers se bhi** hoti hai (ghar ke aur members
  milte hain) + saari expansion queries **parallel** (`asyncio.gather`).

---

## 4) Hub ki speed

`num-info` pehle 3 upstream call **ek ke baad ek** karta tha → 28 second.
Ab **teeno ek saath** → **2.2 second** (13x fast).

GitHub par push ho chuka hai (`40d219e`). Render service par **Manual Deploy →
Deploy latest commit** karna padega (auto-deploy off lag raha hai, kyunki live
response abhi bhi purane format ka aa raha hai).

Live check karne ka tarika:
```
https://osint-api-hub.onrender.com/api/aadhaar-family?key=Demo&aadhaar=992488068408&format=text
```
Naye format me `🎫 Ration Card Number:` aur `🏪 FPS ID:` ki line dikhegi.

---

## 5) Test results (v46.1 — sab green)

| Suite | Result |
|---|---|
| `_selftest_v45_hub.py` | PASS 89 \| FAIL 0 |
| `_audit_v44_tools.py` | 225 \| PASS 225 \| FAIL 0 |
| `_selftest_v44.py` | PASS 67 \| FAIL 0 |
| `_selftest_vehicle.py` | PASS 58 \| FAIL 0 |
| `_selftest_clips.py` | PASS 48 \| FAIL 0 |
| `_selftest_imei.py` | PASS 35 \| FAIL 0 |
| `_selftest_prompts_v42.py` | PASS 12 \| FAIL 0 |
| `_audit_tools_v39.py` | OK 69 \| FAIL 0 |
| `_live_check.py` | 110 pass \| 1 skip (fixture nahi) |

---

⚡ Powered by @Supermannn_x
