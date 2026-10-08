# v85.0 — 📸 FULL-ALBUM + 🔗 LINK SANITIZER + 🛡️ FORTRESS-II

Ye update simple Hinglish me batata hai ki kya badla, kaise test hua, aur abhi
kya baaki hai. **Bot ke koi bhi input prompt NAHI badle gaye** (PROMPT_DATA ke
42 tools ke head/ask/tip bilkul wahi hain — test me lock hai).

Aapke 3 live links isi version ka reason hain:
1. `instagram.com/p/DeJgDvDIFg2/?img_index=3&stkn=...` → FAIL ho gaya tha
2. `1024tera.com/wap/share/filelist?surl=YfyQ...&fbclid=...` → FAIL ho gaya tha
3. `instagram.com/p/DdmJ952D3ux/?img_index=3...` (6-7 photos) → sirf 1 photo mili

---

## 1. Kya badla

### A. 🔗 LINK SANITIZER (naya: `modules/core/urlclean.py`)
- `&amp;amp;amp;` (2-3 baar escape hua `&`), markdown `[text](url)` wrapper,
  aas-paas ka text, `fbclid/stkn/igsh` tracking — sab download se PEHLE saaf.
- `insta_clean()` → hamesha canonical post URL (`/p/CODE/`).
- `tera_surl()` → wap/1024tera/markdown/`shorturl=` sab se surl nikalta hai.
- `safe_button_url()` → Telegram button me galat URL kabhi nahi (galat button
  URL = handler crash = user ko "ghatna" — ye raasta ab band hai).
- Kabhi exception nahi: junk (None/bytes/number/khaali) par khaali string.

### B. 📸 FULL-ALBUM FIX (6-7 photos me se 1 milti thi — ROOT CAUSE MILA)
- **Asli wajah:** v82 me `?img_index=N` aane par bot carousel ka SIRF N-wan item
  bhejta tha. Aapka link slide-3 se copy hua tha → sirf 1 photo mili.
- **Ab:** img_index ho ya na ho — **poori album (10 tak) hamesha jaati hai**.
  Caption me chhota note: "slide 3 ka link tha".
- **Naya 5th engine `_ig_embed_album`:** kabhi parth/yt-dlp carousel ko "single
  photo" samajh lete hain. /embed/ page se SAARE `display_url` ikattha karke
  poori album bana deta hai (2+ milein tabhi carousel).
- **Double safety:** race me single photo jeet jaye to bhi /p/ post par album
  engine se ek baar aur check hota hai.
- **Cache key se img_index hata** (`dlkey.py`): same post = same key, chahe koi
  bhi slide ka link ho. (Purani keys ek baar miss hongi, phir sab instant.)
- Photo budget 22s → 24s (5th engine ke liye), reel/video 26s wahi.

### C. ⚡ TERABOX 2026 refresh
- Entry par link safai + `shorturl=` variant + markdown support.
- Share page hamesha canonical URL se khulti hai (1024tera/wap links bhi).
- Desktop fail → mobile UA retry; jsToken ke 3 naye patterns + `dplogid` pattern.
- `getattr` defensive (fake/ajeeb response par crash nahi).

### D. 🛡️ FORTRESS-II (crash ke naye raaste band)
- Album send: khaali items filter + total 45MB cap (OOM + Telegram limit) +
  caption 900-char guard (Telegram 1024 limit) + **media-group fail → ek-ek
  karke fallback** (user khaali haath nahi jayega).
- Terabox + link-mode ke SAARE buttons validate (koi button crash nahi).
- Badi photos `_jpeg_fit` se Telegram-safe (max 2160px, 10MB photo limit guard).
- `instagr.am` short links bhi chalte hain (share sheet se aate hain).
- Background-task error me ab SOURCE bhi log hota hai (task naam + traceback) —
  v84 tak "background task error" ka source pakka nahi tha, ab hoga.

### Files
- `modules/core/urlclean.py` (naya): sanitizer.
- `bot.py`: version v85.0, `_clean_link_in` + `_safe_btn_url` helpers, FULL-ALBUM
  block, safe buttons, richer loop-error logging. **Koi prompt nahi badla.**
- `modules/core/dlkey.py`: img_index key se hata + andar hi safai + non-str safe.
- `modules/media_downloader.py`: entry safai, instagr.am, `_ig_embed_album`,
  `_jpeg_fit`, album fallback, photo budget 24s.
- `modules/cloud_tools.py`: entry safai, surl robust, canonical page, naye tokens.
- `tests/test_v85_fullalbum.py` (naya): 47 checks.
- `tests/test_v84_dlkey.py`, `test_v89.py`, `test_v87.py`, `test_v83_pro_all.py`:
  sirf jaan-boojhkar badle behaviour ke asserts update (img_index key, budget,
  version).

---

## 2. Kaise test hua

- Naya `tests/test_v85_fullalbum.py`: **47/47 PASS** (aapke 3 asli links par bhi).
- Poora suite: **43 files, sab PASS (0 FAIL)** — v84 me 42 the, ab 43.
- Pyflakes: **0 undefined names**.
- `bot.py` import + `/start` wiring untouched (sirf result-side changes).

---

## 3. Imaandari se — kya BAAKI hai / kya guarantee NAHI hai

- **100% crash-free ki guarantee koi nahi de sakta** (Render free = 512MB RAM,
  Instagram/Terabox roz apna system badalte hain). Par crash ke har KNOWN
  raaste par ab guard hai, aur naye crash ka source ab log me dikhega.
- **Link #1 (DeJgDvDIFg2) FAIL ki wajah:** ho sakta hai post delete/private ho
  ya rate-limit laga ho. Code ab link ki gandagi saaf karke 5 engines try karta
  hai — par delete/private post koi bot nahi nikal sakta. Dobara bhejke dekho;
  ab error me saaf wajah aayegi.
- **Terabox direct link bina `TERABOX_COOKIE` ke kabhi-kabhi nahi nikalta**
  (Terabox ne 2026 me public API band kar di). Cookie set ho to 100%. Bina
  cookie ke bot file-info + web-download buttons deta hai (khaali haath nahi).
- **Sab 40+ tools ka deep feature upgrade** ek round me imaandaari se nahi ho
  sakta. v85 me downloader + terabox + crash-shield premium hue. Agle round me
  aap batao kin tools me pehle (Number Info? IFSC? Business Studio?).
- **Earning tool:** pick pending hai — neeche "4. Earning ideas" me se chunne
  par hi build hoga (aapka order: pehle ideas, pasand aaye tabhi build).

---

## 4. 💰 EARNING IDEAS (pick karo — tabhi build hoga)

1. **📄 Bulk Excel Report (PRO)** — CA/bank agent: 100 IFSC/pincode/mobile ek
   file me bhejo → poori Excel report wapas. Heavy shops iske liye pay karti hain.
2. **🧾 GST Invoice PRO+** — logo + signature + Hindi invoice + WhatsApp-share
   PDF. Dukaandaar ka daily kaam = daily earning.
3. **📸 Passport Photo STUDIO** — background change + suit overlay + 8-in-1
   print sheet. Studio wale per-photo charge karte hain.
4. **🎓 Certificate/ID-Card BULK** — school/coaching: 200 bachchon ke certificate
   ek Excel se. Bulk = bulk payment.
5. **🔍 Link Check PRO API** — cyber-cafe/digital seva: fraud-link report + PDF.
6. **📱 Number Info PRO+** — business verification report (operator/circle/type
   + risk tags + PDF).
7. **🤖 Auto-Post / Channel Manager** — paid channels ke liye scheduled posts.

Batao kaunsa #1 pasand hai — wahi banega aur bot me integrate hoga.
