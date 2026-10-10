# v108.0 SLIM — KYA BADLA (10 Oct 2026)

**User ka order (seedha-seedha):**
> "Sab tools permanently delete kar do. Sirf 📱 NUMBER INFO aur 👪 FAMILY INFO
> rehne do — inka **ek bhi code mat chuna**. Bot RAM kam le aur beech me ruke
> nahi."

Ye poora kar diya gaya hai.

---

## 1) Asli problem kya thi (sirf "slow" nahi tha)

Render free plan = **512 MB RAM**. Purane bot me ye libraries import hote hi,
**koi tool chalaye bina**, ~300 MB kha jaati thi:

| Library | Kis tool ke liye | Kyun bhaari |
|---|---|---|
| `yt-dlp` + `ffmpeg-python` | YouTube/TikTok/Insta DL | video process = RAM blast |
| `telethon` | 150 MB upload | poora dusra Telegram client |
| `Pillow`, `qrcode` | QR, Media Studio | image buffers |
| `reportlab`, `pdfplumber` | Business Studio, Bank→Excel | PDF engine |
| `openpyxl` | Bank Statement → Excel | Excel engine |
| `beautifulsoup4`, `lxml`, `python-whois`, `dnspython` | X-Ray, Link Check | HTML/DNS parsers |
| `pytesseract`, `instaloader` | QR Scanner, Insta | OCR + scraper |

Isliye logs me ye aata tha:

```
MEMORY HIGH 466 MB (limit 512) — aggressive safai
MEMORY HIGH 489 MB (limit 512) — aggressive safai
```

Aur user ke kaam ke beech me OOM killer bot ko maar deta tha (`Killed`).

**Natija:** code optimize karne se kuch nahi hota — **saman hi nikaalna** tha.

---

## 2) Kaise delete kiya (aur kaise pakka kiya ki 2 tools na bigden)

Purani `bot.py` **11,848 line** ki thi. Usme se line-by-line kaat-chhaant
karna khatarnak tha (ek galat line hat jaye to kuch bhi toot sakta hai).

Isliye ulta kiya — **nayi file banayi**, aur usme 2 kept tools ka code purani
file se **verbatim (jaisa ka taisa) copy** kiya. Build ke waqt **3 automatic
checks** chalte hain jo confirm karte hain ki uthaya gaya code bilkul wahi hai.

Verbatim uthaya gaya:
- `numinfo_card()` — 92 lines
- `familyinfo_card()` — 59 lines
- `on_text` ka numinfo + familyinfo branch — 114 lines
- `PROMPT_DATA` ke dono entries
- rate-limit aur button-mapping entries

> **Yani in 2 tools me ek bhi character nahi badla.**

---

## 3) Numbers

| | v107 | v108 SLIM |
|---|---|---|
| Tools | 24 | **2** |
| `bot.py` lines | 11,848 | **2,431** |
| Libraries | 18 | **4** |
| Import RAM | — | **49 MB** |
| Boot (`--check`) | ~224 MB | **54 MB** |
| Live (polling) | 416–489 MB | **62 MB** |
| `.md` docs | 85 | **5** |
| Tests | purane 60+ | **1 file, 163 checks, sab pass** |

---

## 4) Deleted tools (23)

**Pehli list (15):** YOUTUBE DL · TIKTOK DL · CHANNEL CLONER · TERABOX
DOWNLOADER · WEBSITE OWNER X-RAY · TEMP MAIL · TEMP NUMBER · QR CODE ·
LINK CHECK · URL SHORT · BUSINESS STUDIO · BANK STATEMENT → EXCEL ·
MEDIA STUDIO (MP3/STATUS) · MY ACCOUNT · SUPPORT / MADAD

**Baad me add (8):** INSTA DL · VIRTUAL NUMBERS · RC + CHALLAN · PINCODE INFO ·
IFSC INFO · RESULT CHECK · QR SCANNER · IMEI / PHONE DETAILS

Inka code, buttons, modules, libraries, env vars, assets, docs aur tests —
**sab hataya**. `tests/test_v108_slim.py` ka ek poora section sirf yahi check
karta hai ki inka naam-o-nishaan source me na bache.

**Purana button daba diya to?** Crash nahi — friendly message *"ye tool ab band
kar diya gaya hai"*, mode clear, aur naya 2-button menu dubara.

---

## 5) Safety me kuch kam nahi hua

Vault (encrypted backup + auto-restore) · Crash Shield (19 handlers) · Memory
watchdog (389/420/430 MB) · Hang watchdog (900 s) · Join-wall · Rate-limit ·
Update-gate (dedupe + per-chat order) · Janitor · HTML safety net · Self-ping —
**sab waise ke waise chaalu hain.**

---

## 6) 2 purane bug bhi theek hue

### 🩺 `/health` khaali body bhejta tha (v77 se chala aa raha tha)

Page banate waqt agar **ek bhi line** me exception aa jaati to poora page gayab
ho jaata — par HTTP status phir bhi **200** jaata tha. Render ko lagta "app
theek hai", isliye wo atke hue bot ko **restart hi nahi karta tha**.

**Fix:** ab har line `_hline()` ke andar hai. Line fail ho to sirf wahin
`(ye line nahi ban payi: <ErrType>)` likha aata hai, baaki page poora banta hai.

Verify: `/health` → **HTTP 200, 2,070 bytes**, saari lines present.

### 🔌 `delete_webhook` par `await` chhoot gaya tha

```python
_Bot(BOT_TOKEN).delete_webhook(drop_pending_updates=True)   # ❌ await nahi
```

Naye python-telegram-bot (v21+) me ye **coroutine** hai — bina `await` ke ye
chalta hi nahi, bas chup-chaap ignore ho jaata hai. Matlab purana webhook kabhi
hatta hi nahi tha, aur polling start hone par Telegram `Conflict: can't use
getUpdates while webhook is active` de sakta tha.

**Fix:** ab `asyncio.run()` + `async with` ke andar sahi se `await` hota hai.

---

## 7) Test coverage

`tests/test_v108_slim.py` — **163 checks, 0 fail**, 8 section:

1. Boot — bot bina error import ho
2. Menu — sirf 2 button
3. Deleted tools — 23 naam source me kahin na milein
4. Cards — dono ka output sahi bane (Aadhaar masked)
5. Offline parser — number parse
6. Prompts — dono prompt sahi
7. **End-to-end** — nakli Telegram se poora flow (button → prompt → input → card)
8. Source scan — koi leftover handler/import/button na bache

---

## 8) Aapko kya karna hai

`AB-KYA-KARNA-HAI.md` padho — 3 chhote kaam hain (purana GitHub token band
karo, naya banao, Render me daalo). ~5 minute.
