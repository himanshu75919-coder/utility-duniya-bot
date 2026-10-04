# 📖 1-PADHO-PEHLE.md — v50 Premium Pro (5 minute me poora samajh)

Bhai, ye file **sabse pehle** padh lo. Isme sirf kaam ki baat hai:

1. **v50 me kya badla** (2 line me)
2. **Deploy kaise karna hai** (4 step)
3. **Telegram me test kaise karna hai** (5 minute)
4. **Credits / VIP ka hisaab**
5. **3 zaroori baatein** (legal + copyright)

---

## 1️⃣ v50 me kya badla (short) — PREMIUM PRO

| Kya | Detail |
|---|---|
| 🌦️ **NAYA WEATHER tool** | Shehar ka naam bhejo (Gaya, Patna, Pune…) → abhi ka mausam + aage 3 din ka forecast. 100% free (koi API key nahi) |
| 🧮 **NAYA EMI/VYAAJ calculator** | 🧮 Bank EMI (amount + rate + months → EMI, total interest, milestones) + 🪔 gaon-wala chakravritti vyaaj hisaab |
| 🐛 **9 bug fixes** | ID Finder forward · 8-in-1 sheet EXACT 3.5×4.5cm · passport photo 20-50KB · toll-free numbers · admin button crash · PDF 10-photo limit · broadcast fallback · DB lock · dead code |
| ⚡ **4x FAST** | URL shortener 6 providers parallel (~1 sec) · ID finder parallel (~5-10s) · link check + domain-age signal · bank PDF auto-unlock |
| ✅ **Test suite** | `_selftest_v50.py` = **99 checks** — sab green |

### v49 (purana, context ke liye)
| Kya | Detail |
|---|---|
| 🗑️ **3 faaltu tools hate** | 🎬 CLIP MAKER · 🔓 LINK BYPASS · 📈 INTEREST CALC (INTEREST CALC v50 me 🧮 naye roop me wapas aaya) |
| 🗣️ **Poora bot Hinglish** | Har prompt ab chhota Hinglish + `📌 Jaise:` example |
| 📲 **IMEI tool fix** | Hub ka TAC endpoint + phone photo + poori spec sheet + `.json` file |
| 🔌 **Hub URL sahi** | Bot `osint-api-hub.onrender.com/api` use karta hai |
| 🧹 **Saaf-safai** | 9 bekaar tutorial video, 14 purane dev-note file, 2 dead module delete |

---

## 2️⃣ Deploy (Render) — 4 step

1. **GitHub par push ho chuka hai** (main branch). Kuch karne ki zaroorat nahi.
2. **Render → apni service → Manual Deploy → "Clear build cache & deploy"** dabao.
3. 2-3 minute ruko. Log me `Bot running...` dikhe to chalu ho gaya.
4. Telegram me `/start` → naya menu. **Ek baar `/refresh` bhejo** taaki sab users ko naya keyboard mil jaye.

**Render par ye Environment Variables** (Environment tab):

```
BOT_TOKEN   = BotFather ka token
ADMIN_ID    = aapki Telegram user ID (owner — unlimited)
UPI_ID      = aapka@upi
UPI_NAME    = Utility Duniya
```

Baaki optional: `FORCE_CHANNEL`, `FORCE_CHANNEL_LINK`, `REFER_NEED=5`, `FREE_CREDITS=25`,
`TUTORIAL_URL`, `HUB_API_KEY=Demo`, `NUM_LEAK_ENABLED=off`.

---

## 3️⃣ Telegram me test (5 minute)

| # | Karo | Kya hona chahiye |
|---|---|---|
| 1 | `/start` | Menu aaye — **CLIP MAKER / LINK BYPASS / INTEREST CALC ke button NAHI** |
| 2 | `/refresh` | Purane buttons wale users ko bhi naya keyboard mil jaye |
| 3 | 📲 IMEI / PHONE DETAILS | `*#06#` se 15 digit IMEI bhejo → brand, model, **photo**, poori spec sheet + `.json` file |
| 4 | 🏦 BANK STATEMENT PDF → EXCEL | PDF bhejo → Excel/CSV file + total ka summary |
| 5 | ⚡ MEDIA STUDIO → 🎬 Status Video | photo → gaana → text → 9:16 video ban ke aaye |
| 6 | 📜 DOCUMENT SUITE → kirayanama | ek-ek field poochhe → PDF ban ke aaye |
| 7 | 💎 `/premium` | plan chuno → UTR maange → screenshot maange (3 step) |

Computer par (optional):

```bash
python3 _verify_v49.py        # 93 checks — menu, Hinglish text, live API, DB
python3 _selftest_v45.py      # 61 checks — hub integration
python3 _selftest_imei.py     # 70 checks — IMEI flow
python3 _selftest_vehicle.py  # 78 checks — vehicle + challan
python3 -m pytest tests/ -q   # privacy tests
```

---

## 4️⃣ Credits + VIP

- Naya user: **25 credits free** (ek hi baar).
- **Premium tools:** 📥 Video Downloader · 📱 Number Info · 🔄 Channel Cloner · 🔒 Private Setup ·
  🏦 Bank PDF→Excel · 📜 Document Suite · ⚡ Media Studio · 🚗 Vehicle Info + Challan · 📲 IMEI — **1 use = 1 credit**.
- **Baaki saare tools FREE** — koi credit nahi.
- **VIP / Owner = unlimited.**
- VIP bechne ka tarika: `/premium` → plan → QR → UTR + screenshot → `/admin` me **Approve**.
- Bina payment VIP: `/admin` → plan select → `/activate <user_id>` (ya `/activate <user_id> 90`).
- Refer: **5 log = 30 din free VIP**.
- Status dekhne ke liye: `/mypay`.

---

## ⚠️ 3 baatein yaad rakho

1. **Koi AI tool nahi** — jo bhi bana hai, sab offline/deterministic hai (Render 512MB me aaram se chalega).
2. **Copyright:** downloader public links ke liye hai — kisi ka paid content bechna galat hai.
3. **Legal line:** sarkar ka public data ✅ · kisi ki niji jaankari ❌
   (public-records feature `NUM_LEAK_ENABLED=off` se band ho jata hai).
