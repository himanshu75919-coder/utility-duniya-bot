# 📱 Utility Duniya Bot — **v108.0 SLIM**

> **Ek line me:** 24 tools wala bhaari bot kaat kar **sirf 2 tools** ka halka,
> na-rukne wala bot bana diya gaya — **📱 NUMBER INFO** aur **👪 FAMILY INFO**.

[![RAM](https://img.shields.io/badge/RAM-62%20MB%20%2F%20512%20MB-brightgreen)]()
[![Tools](https://img.shields.io/badge/tools-2-blue)]()
[![Tests](https://img.shields.io/badge/tests-163%20passing-brightgreen)]()

---

## 😤 Problem kya thi

Bot beech kaam me ruk jaata tha, "sochta" reh jaata tha, aur kabhi-kabhi khud
restart ho jaata tha. Render ke logs me ye line baar-baar aati thi:

```
MEMORY HIGH 466 MB (limit 512) — aggressive safai
MEMORY HIGH 489 MB (limit 512) — aggressive safai
```

**Asli wajah:** Render ke free plan me kul **512 MB RAM** milti hai. Purane bot
me video downloader (`yt-dlp` + `ffmpeg`), PDF/Excel banane wale tools
(`reportlab`, `pdfplumber`, `openpyxl`), image tools (`Pillow`, `qrcode`) aur
150 MB upload (`telethon`) — ye sab **chalu hone se pehle hi**, sirf import
hote hi, 300+ MB kha jaate the. Jaise hi koi user ek bhaari tool chalata,
memory 512 ke paar — aur Linux ka OOM killer bot ko maar deta (logs me sirf
`Killed` dikhta).

Yani problem bot ke "slow code" ki nahi thi. **Bot me zaroorat se zyada saman
bhara hua tha.**

---

## ✅ v108 ka hal — saman hi nikaal diya

| | Pehle (v107) | Ab (v108 SLIM) |
|---|---|---|
| Tools | 24 | **2** |
| `bot.py` lines | 11,848 | **2,431** |
| Python libraries | 18 | **4** |
| Boot RAM | ~224 MB | **~54 MB** |
| Chalte hue RAM | 416–489 MB | **~62 MB** |
| 512 MB limit | baar-baar chhuti thi | **kabhi paas bhi nahi** |

> Ye andaaze nahi hain — har number asli bot chala kar naapa gaya hai.

---

## 🎯 Jo 2 tools bache hain

### 📱 NUMBER INFO
10-digit mobile number bhejo → owner ka naam, pita ka naam, address, operator,
circle, ported status — sab ek premium card me.

### 👪 FAMILY INFO
12-digit ID bhejo → poore parivaar ke members ek card me.

> **⚠️ Zaroori:** in dono tools ka code **ek line bhi nahi badla gaya hai**.
> Inke cards, prompts, API calls, masking rules — sab bilkul waise hi hain jaise
> v107 me the. Inhe `bot.py` se **verbatim (copy-paste) uthaya** gaya hai, aur
> 3 automatic checks lagaye gaye hain jo build ke waqt confirm karte hain ki
> code badla to nahi.

**Privacy:** Aadhaar/doc ID **hamesha masked** dikhta hai (`XXXX-XXXX-1234`).
Ye lock jaan-boojh kar lagaya gaya hai.

---

## 🗑️ Kya-kya permanently delete hua (23 tools)

<details>
<summary><b>Poori list dekhne ke liye click karo</b></summary>

**Aapki pehli list (15):**
YOUTUBE DL · TIKTOK DL · CHANNEL CLONER · TERABOX DOWNLOADER ·
WEBSITE OWNER X-RAY · TEMP MAIL · TEMP NUMBER · QR CODE · LINK CHECK ·
URL SHORT · BUSINESS STUDIO · BANK STATEMENT → EXCEL ·
MEDIA STUDIO (MP3/STATUS) · MY ACCOUNT · SUPPORT / MADAD

**Baad me add kiye (8):**
INSTA DL · VIRTUAL NUMBERS · RC + CHALLAN · PINCODE INFO · IFSC INFO ·
RESULT CHECK · QR SCANNER · IMEI / PHONE DETAILS

Inka **code, buttons, modules, libraries, env vars, docs aur tests** — sab hata
diya gaya. Sirf chhupaya nahi gaya, poora nikala gaya hai.

</details>

**Purane buttons ab bhi dabao to?** Bot crash nahi karega — ek simple message
aayega: *"ye tool ab band kar diya gaya hai"*, aur naya 2-button menu dubara
bhej dega.

---

## 🛡️ Safety sab waise hi hai (kuch kam nahi hua)

Tools kam hue, **suraksha nahi**:

- **Premium Vault** — poora data encrypted hokar GitHub + Telegram par backup,
  aur restart par apne aap wapas. Render free plan par restart hote hi local
  file gayab ho jaati hai — isliye ye zaroori hai.
- **Crash Shield** — 19 handlers guard me. Koi error aaye to sirf wahi message
  fail hoga, bot zinda rahega.
- **Memory watchdog** — 389 MB par safai, 420 MB par clean restart.
- **Hang watchdog** — 900 s atak jaye to khud restart.
- **Join-wall, rate-limit, update-gate, janitor** — sab chaalu.

---

## 🩺 v108 me 1 purana bug bhi theek hua

`/health` page kabhi-kabhi **HTTP 200 ke saath khaali body** bhejta tha (page
banate waqt ek line crash ho jaati thi to poora page gayab ho jaata tha).
Render ko 200 dikhta tha, isliye wo atke hue app ko restart hi nahi karta.

Ab `/health` ki **har line alag guard** me hai — ek line fail ho to sirf wahin
likha aayega `(ye line nahi ban payi: ...)`, page kabhi khaali nahi jayega.

Saath hi `delete_webhook(...)` call par `await` chhoot gaya tha (naye
python-telegram-bot me ye coroutine hai), isliye purana webhook kabhi hatta hi
nahi tha aur polling me `Conflict: can't use getUpdates` aa sakta tha. Ab fix hai.

---

## 🚀 Deploy (Render)

```bash
pip install -r requirements.txt
python bot.py
```

Render par bas do cheezein **zaroori** hain:

| Key | Value |
|---|---|
| `BOT_TOKEN` | BotFather ka token |
| `ADMIN_ID` | aapki Telegram numeric ID (@userinfobot se) |

Baaki sab optional — poori list `.env.example` aur `render.yaml` me comments ke
saath likhi hai.

📖 **Guides:**
- `NUMBER-INFO-API-SETUP.md` — Number/Family API lagane ka tarika
- `TOKEN-KAISE-LE-AUR-KAHAN-SE.md` — Vault ka GitHub token
- `RENDER-NAYI-SERVICE-KAISE-BANAYE.md` — Render par service banana

---

## 💬 Commands

| Command | Kaam |
|---|---|
| `/start` | menu kholo |
| `/menu` `/tools` | 2-button menu dubara |
| `/cancel` | chalu kaam rok do |
| `/refresh` `/newmenu` | keyboard dubara bhejo |
| `/version` | kaunsa version chal raha hai |
| `/numapi [number]` | Number API test |
| `/famapi [id]` | Family API test |

<details>
<summary><b>Admin commands</b></summary>

`/admin` · `/sys` (ya `/system`, `/health`) · `/ban` · `/unban` ·
`/broadcast` · `/vault` · `/backup` · `/restore`

</details>

---

## 🧪 Tests

```bash
python tests/test_v108_slim.py
```

**163 checks, sab pass.** Ye 8 cheezein check karte hain:
boot · menu me sirf 2 button · 23 deleted tools ka naam-o-nishaan na ho ·
dono cards ka output · offline parser · prompts · nakli Telegram se poora
end-to-end flow · source me koi leftover code na bache.

---

## 📁 Project structure

```
bot.py                      # poora bot (2,431 lines)
database.py                 # SQLite
requirements.txt            # sirf 4 libraries
render.yaml                 # Render blueprint (Hinglish comments ke saath)
.env.example                # config ka namuna

modules/
  mynum_api.py              # 📱 NUMBER INFO    (unchanged)
  familyinfo_api.py         # 👪 FAMILY INFO    (unchanged)
  osint_tools.py            # offline number parser
  render_health.py          # /health route

modules/core/               # safety layer
  vault.py                  # encrypted backup + restore
  guard.py                  # crash shield + memory watchdog
  joinwall.py  limiter.py  updategate.py  janitor.py
  safesend.py  html_safe.py  net.py  htmlnet.py
  cache.py  bounded.py  memtrace.py  telemetry.py  safeconf.py

tests/test_v108_slim.py     # 163 checks
```

---

## 📦 Dependencies — 18 se 4

```
python-telegram-bot[webhooks]>=22.8,<23
requests>=2.32,<3
phonenumbers>=8.13,<10
python-dotenv>=1.0,<2
```

Hataye gaye: `yt-dlp`, `ffmpeg-python`, `telethon`, `Pillow`, `qrcode`,
`reportlab`, `pdfplumber`, `openpyxl`, `beautifulsoup4`, `lxml`,
`python-whois`, `dnspython`, `pytesseract`, `instaloader` — **yahi 14
libraries milkar 300+ MB RAM khaati thi.**

---

<div align="center">

**v108.0 SLIM** · 2 tools · 62 MB · 163 tests passing

</div>
