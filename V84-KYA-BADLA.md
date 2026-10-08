# v84.0 — ⚡ Smart Instant-Repeat Key

Ye update simple Hinglish me batata hai ki kya badla, kaise test hua, aur abhi kya
baaki hai. Bot ke koi bhi existing prompt ya user-visible message NAHI badla gaya.

---

## 1. Kya badla

### Pehle kya problem thi
Bot ek video ek baar download karke Telegram par upload karta hai, aur uska
"file_id" yaad rakhta hai. Agli baar wahi video turant chal jaati hai (0.1 second).
Lekin yaad rakhne ki pehchaan poora link tha, aur do problem thi:

1. **Tracking wale link par cache miss.** Same reel ka link `?igsh=abc` ke saath aaye
   to bot use naya samajhta tha aur dobara download karta tha.
2. **Poora link lowercase hota tha.** Instagram aur YouTube ki IDs case-sensitive
   hoti hain, to ek ID ka farq mit sakta tha (chhota lekin real risk).

### Ab kya hai
- **Instagram:** post ka shortcode hi pehchaan hai. `?igsh=`, `?stkn=` jaise params se farq nahi padta.
  Carousel ka `img_index` alag key hai (slide 2 aur slide 3 alag cache).
- **YouTube:** video ID (`youtu.be`, `watch?v=`, `shorts/` sab ek hi). Quality (360p, 720p) alag key.
- **TikTok:** video ID. Webapp params se farq nahi.
- **Facebook:** video ID (`watch/?v=`, `reel/`, page `/videos/` sab ek hi).
- **Baaki links:** sirf universal tracking (`utm_*`, `fbclid`, `gclid`) hatate hain.
  `source`, `ref` jaise params nahi hatate, kyunki kuch sites inse content badalti hain.
- **Lambe links:** pehle 400 characters par cut hota tha. Ab cut nahi hota, taaki
  do alag links kabhi same key na banayein.

### Safety
- ID hamesha case-sensitive hai.
- Har platform ka alag namespace hai (`ig:`, `yt:`, `tt:`, `fb:`, `fbw:`).
- Kisi bhi ajeeb input par key sirf cache-miss deti hai, galat video nahi.
- Agar naya module load na ho, to purana logic chalta hai. Bot kabhi is wajah se nahi rukta.

### Files
- `modules/core/dlkey.py` (naya): key banane ka logic.
- `bot.py`: `dl_fid_key()` ab is module ko use karta hai (fallback ke saath). `BOT_VERSION` → v84.0.
- `tests/test_v84_dlkey.py` (naya): 34 checks.
- `tests/test_v87.py`, `tests/test_v83_pro_all.py`: version check v84 par.

---

## 2. Kaise test hua

- `tests/test_v84_dlkey.py`: 34/34 PASS. Ye check karta hai:
  same video ke alag links, alag img_index / quality, case-sensitivity, unknown links,
  edge inputs (khaali, None, lamba link), 3000 random Instagram codes aur 3000 random
  YouTube IDs (koi takraav nahi), bot.py me `dl_fid_set` / `dl_fid_get` tracking variants
  par, aur fallback jab module load na ho.
- Purana instant-repeat test (`test_v68.py`): 51 PASS.
- Poora test suite: 42 files, sab PASS (0 FAIL).
- Pyflakes: 0 undefined names.
- **End-to-end (sandbox, mock Telegram):** same TikTok video ke do alag tracking links.
  Pehli baar: normal download + cache save. Doosri baar (`sender_device=pc&igsh=...` wala link):
  caption "⚡ INSTANT — ye video pehle hi download ho chuki thi (0.1 second)" aaya ✔.

Note: pehle se cache hui videos ek baar dobara download hongi (purani key format badal gaya).
Uske baad fir se instant chalega.

---

## 3. Abhi kya BAAKI hai (imaandari se)

- **Sab 54 tools ka deep feature upgrade:** ye ek hi round me imaandari se nahi ho sakta.
  Bot me pehle se bahut sa premium kaam hai (instant repeat, TTL cache, heavy-job gate,
  150 MB tak MTProto upload). Naye features kin tools me pehle chahiye, ye aap bataiye.
- **Render manual deploy:** pichhle reply me maine bola tha ki manual deploy Render key
  se karunga. Session me Render key saved nahi hai, aur chat se maine jo value nikali
  wo galat thi (Render ne 401 diya). Iske liye ya to aap key dobara bhejein, ya Render
  dashboard me **Manual Deploy → Deploy latest commit** par ek click karein.
- **Render live logs:** isi wajah se abhi check nahi ho sake. "background task error"
  ka exact source bhi abhi pakka nahi hai (ye sirf log me aata hai, bot chalta rehta hai).
- **Earning tool:** pick abhi pending hai. Build tabhi hoga jab aap chunein.
- **Terabox direct download:** `TERABOX_COOKIE` Render par set hona baaki hai (aapke account ka cookie).
