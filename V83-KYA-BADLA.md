# v83.0 — ULTRA-PRO ALL-TOOLS: kya badla, kyon badla

Ye file simple Hinglish me batati hai ki is update me kya theek hua, kya test hua,
aur abhi kya limitation hai. Har tool ka detail table: `TOOLS-AUDIT-V83.md`.

> Bot ka koi bhi existing prompt / user-visible message NAHI badla gaya.
> Sirf logic, button routing aur error-handling badle hain. Ek naya chhota
> message sirf tab dikhta hai jab koi purana/adhoora button dabaye (neeche dekho).

---

## 1. Kya bugs mile aur kya theek hua

### (a) YouTube quality picker khatam ho jaata tha
**Asli karan:** YouTube link bhejne par "link mil gaya" status message par ek
progress ticker chalu hota tha (har 6 second me message edit). Quality choose karne
wala card usi message par dikhta tha, par ticker wahi message baar-baar overwrite
karta tha — quality buttons gayab ho sakte the.
**Fix:** handler khatam hote hi ticker band ho jaata hai (`_on_text_pro` / `_on_cb_pro`
ke `finally` me). Test me confirm hua: picker ke baad koi overwrite nahi.

### (b) Instagram / TikTok / Facebook ke baad bhi ticker chalta tha
Video/photo bhejne ke baad bhi progress message edit hota rehta tha (ya delete ho chuke
message ko edit karne ki koshish → "Message to edit not found" log).
**Fix:** same `finally` fix. Ticker ab kaam khatam hote hi band.

### (c) Do button kaam hi nahi karte the (dead buttons)
- **"🔙 Menu"** (Help/Tutorial wale keyboard par) — dabane par kuch nahi hota tha.
- **"📋 Saare tools ki list"** (free mode keyboard par) — dabane par kuch nahi hota tha.
**Fix:** dono ab sahi jawab dete hain (menu wapas, aur tools ki full list).

### (d) Galat / khaali button data se crash-jaisa error
Kuch purane buttons me ID khaali hoti thi (jaise `admpay_view:`), to handler `int('')`
par atak jaata tha. Global error handler bot ko zinda rakhta tha, lekin user ko kuch
nahi milta tha.
**Fix:** ab user ko saaf message milta hai:
> ❌ Ye button purana ya adhoora ho gaya. Menu se tool dobara kholo — phir kaam karega.

(Ye naya message sirf galat/purane button par dikhta hai — normal flow me nahi.)

### (e) Telegram ke "benign" errors ko error ki tarah treat karna
"Message to edit not found", "Message is not modified", "Query is too old" — ye
bot ki galti nahi, purane message ki wajah se aate hain. Ab inhe chup-chaap log karke
skip kiya jaata hai (user ko koi error nahi dikhta).

### (f) Version
Bot ka version label ab **v83.0** hai (`/health` par bhi). Purane guard words
(FREE4ALL, NO-GYAAN, SPEED, v77) waise hi rahe hain.

---

## 2. Har tool ka test kaise hua

- **Automated smoke test (mocked Telegram update):**
  - 129 text buttons → 0 crash, 0 timeout, har button ne reply diya.
  - 108 callback buttons (media, kagaz, rc, cloner, doc, tnum, vnum, qr, temp mail, vault, admin...) → 0 crash.
  - 81 command names (/start, /menu, /help, /vnum, /terabox, ...) user aur admin dono se → 154 case OK, 0 crash. (4 wrapper commands ko unke text-button se test kiya.)
  - 17 typed inputs (links, IFSC, IMEI, PAN, GST, vehicle, random text, 5000-char text) → 0 crash.
- **Live downloader test (sandbox ka real internet):**
  - Instagram (aapke jaisa link, `img_index=3` wala post) → photo mil gayi ✔
  - TikTok → video ✔
  - Facebook → video ✔
  - YouTube → quality picker ✔ → 360p video ✔
  - Terabox (aapke jaisa wap link) → file ka naam + size + web buttons ✔ (direct link cookie ke bina nahi milta — neeche dekho)
- **Existing test suite:** 41 test files — sab pass (0 FAIL).
- **Naya test:** `tests/test_v83_pro_all.py` — 12 checks, sab pass.
- **Boot test:** bot start hota hai, self-check OK; dummy token par sirf expected `InvalidToken` aata hai.

---

## 3. Abhi ki limitations (imaandari se)

- **Terabox direct download:** Render par `TERABOX_COOKIE` abhi set NAHI hai. Bina cookie
  ke bot file ka naam + size + web-downloader buttons dikhayega, direct video nahi bhejega.
  Steps neeche.
- **YouTube "Sign in to confirm you're not a bot":** Render ka server IP kabhi-kabhi
  block hota hai. Pakka ilaaj YouTube cookies file hai (`YTDLP_COOKIES_FILE`). Optional hai.
- **Instagram / TikTok / Facebook:** ye sites apna code roz badalti hain. yt-dlp har
  Render build par latest version install karta hai, isliye deploy se fayda hota hai,
  lekin 100% guarantee nahi di ja sakti.
- **"Kabhi crash nahi" ki 100% guarantee** main nahi de sakta. Render free plan me 512 MB RAM
  hai. Bot me har tool ke liye crash-guard, timeout, aur auto-restart hai — par koi bhi
  software 100% nahi hota.
- **Feature-level upgrade:** is round me focus reliability, button fixes aur error-handling
  par tha. Har tool me NAYE features (jaise naye options/buttons) add karna aapke
  priority ke hisaab se hoga — batayein kaunse tools pehle.
- **Real Telegram chat me test:** automated test aur sandbox ke live downloads ho chuke
  hain, lekin asli Telegram chat me aapko ek baar Instagram aur Terabox link bhejkar
  confirm karna hoga.

---

## 4. Aapko Render par kya karna hai (optional)

### Terabox direct download ke liye (`TERABOX_COOKIE`)
1. Ek **throwaway** (naya, bekar) Terabox account banao. Apna main account use mat karo.
2. Browser me us account se terabox.com login karo.
3. F12 (Developer tools) → Application/Storage → Cookies → `https://www.terabox.com` →
   `ndus` naam ki cookie ki **Value** copy karo.
4. Render → Service `utility-duniya-bot` → Environment → `TERABOX_COOKIE` = wo value → Save.
5. Save karte hi Render redeploy karega. Phir Terabox link par direct download chalega.

> Ye cookie kisi ko mat do, aur chat me mat paste karo. Ye aapke account ka access hai.

---

## 5. Technical summary (developers ke liye)

| Area | File | Change |
|---|---|---|
| Ticker lifecycle | `bot.py` | `_on_text_pro` / `_on_cb_pro` `finally` me `_stop_ping(context)` |
| Stale callback | `bot.py` | `_on_cb_pro` me `(ValueError, IndexError)` catch → `_cb_stale_reply` (saaf message) |
| Dead buttons | `bot.py` | `on_cb`: `alltools` aur `menu` ke handlers |
| Benign errors | `bot.py` | `on_error`: "message to edit not found" / "not modified" / "query too old" skip |
| Version | `bot.py` | `BOT_VERSION` → v83.0 (guard words kept) |
| Tests | `tests/test_v83_pro_all.py` | 12 checks (ticker, stale button, dead buttons, benign errors, version) |
| Tests | `tests/test_v87.py` | version check v82 → v83 |
