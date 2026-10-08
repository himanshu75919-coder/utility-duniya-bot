# v82.0 — ZERO-CRASH PRO: kya badla, kyon badla

Ye file simple Hinglish me batati hai ki is update me kya theek hua, kya abhi bhi
limitation hai, aur aapko Render par kya ek-baar karna hai (optional).

> Bot ke kisi bhi user-visible prompt/message ko NAHI badla gaya. Sirf logic, tools
> aur error-handling upgrade hue hain.

---

## 1. Aapki 3 screenshot waali problem

### (a) Instagram: "SEND FAILED / Message text is empty"
**Asli karan:** photo/video bhejne ke BAAD bot ek chhota "credit note" bhejta hai.
Free mode me wo note khaali hota hai → Telegram ne "Message text is empty" error diya →
bot ne media bheji hone ke bavjood galat "SEND FAILED" dikhaya.

**Fix:**
- Khaali note ab kabhi nahi bheja jaata (27 jagah ek safe helper `_reply_nonempty` se).
- Media ek baar user tak pahunch gayi ho, to uske baad ka koi bhi error user ko
  "SEND FAILED" nahi dikhayega (`_delivered` flag).
- Global error handler bhi "Message text is empty" ko user ke samne error nahi banata.

### (b) Instagram link ke end me `?img_index=3`
- Ab agar post ek carousel (ek se zyada photo/video) hai, to `img_index=3` ka 3rd item hi bhejta hai.
- Agar post me itni items nahi hain, to pehle jaisa pehla photo jaata hai (koi error nahi).

### (c) Terabox: "DIRECT LINK NOT FOUND"
**Asli haal (2026):** Terabox ne bina login ke direct download link band kar diya hai.
Public proxies (jaise saahiyo tbx-proxy) bhi ab 403 "verification" dete hain.

**Ab kya hota hai:**
1. Pehle token-based "guest listing" chalti hai (share page se `jsToken` + `logid`).
   Isse file ka **naam + size** turant milta hai (test me 1.5 second).
2. Agar direct link nahi mila, to card me:
   - 📄 File ka naam aur size,
   - 🌐 web downloader ke buttons (5 tak),
   - 🌐 "Share page kholo" button.
3. `TERABOX_COOKIE` set ho, to direct download link bhi milta hai (neeche steps).

**Ek aur bada fix:** Terabox resolve pehle `bot.py` me synchronous tha — 6 engines ke
timeouts me poora bot 1–2 minute ke liye ruk jaata tha (sabhi users ke liye). Ab wo
background thread me chalta hai, aur 75 second ka hard timeout hai.

### (d) "Event loop is closed" / bot ruk jaana (crash jaisa)
**Asli karan:** webhook fail hone par bot usi purane event loop me polling shuru karta
tha, jo pehle hi band ho chuka tha → error → bot ruk jaata tha.

**Fix:**
- Webhook fail → **saaf process restart** (same PID, naya event loop, naya app), phir seedha polling.
- Polling me lagataar 3 non-conflict errors → saaf restart.
- Koi bhi unexpected crash → pehle jaisa "sleep" ke bajaye saaf restart.
- Restart bahut jaldi-jaldi ho raha ho, to 60 second ka cooldown (boot-loop se bachav).

### (e) Memory (Render free plan = 512 MB)
**Asli karan:** boot par hi bot ~207 MB (libraries) leta hai; media RAM cache 100 MB tak
bhar sakta tha → bade video ke time par OOM (out-of-memory) kill ka khatra.

**Fix (v82):**
- Media RAM cache 100 MB → **20 MB** (bade files ab disk cache me jaate hain).
- RAM me sirf 12 MB tak ki files cache hoti hain.

**Owner ka v81.2 memory fix (same release me, alag se):** `malloc_trim`, idle-only clean
restart (`MEM_RESTART_MB`), `/health` me trim/restart stats, aur opt-in leak-hunt
(`MEM_TRACE`). v82 ne is design ko waisa hi rakha — duplicate restart nahi jodha.

### (f) TikTok photo/slideshow post
- yt-dlp TikTok photo posts support nahi karta ("Unsupported URL" tha).
- Ab `/photo/` wale TikTok links par og:image se photo bheji jaati hai (pehla slide).

---

## 2. Aapko Render par kya karna hai (sirf optional, lekin recommended)

### Terabox direct download ke liye (`TERABOX_COOKIE`)
1. Ek **throwaway** (naya, bekar) Terabox account banao. Apna main account use mat karo.
2. Browser me us account se terabox.com login karo.
3. F12 (Developer tools) → Application/Storage → Cookies → `https://www.terabox.com` →
   `ndus` naam ki cookie ki **Value** copy karo.
4. Render → Service `utility-duniya-bot` → Environment → `TERABOX_COOKIE` = wo value → Save.
5. Render service restart/redeploy hoga. Ab Terabox link par direct download chalega.

> Ye cookie kisi ko mat do, aur chat me mat paste karo. Ye aapke account ka access hai.

### YouTube "Sign in to confirm you're not a bot"
Render ka server IP YouTube par kabhi-kabhi block hota hai. Iska pakka ilaaj YouTube
cookies file hai (`YTDLP_COOKIES_FILE`, `.env.example` me documented). Ye optional hai.

---

## 3. Testing jo kiya gaya

- Pehle se maujood saari test files (`tests/test_*.py`) chalaayi — **0 FAIL** (owner ka `test_v92.py` bhi pass).
- Naya `tests/test_v82_zero_crash.py` (35 checks): empty-text skip, img_index parse, hard restart
  (test me exec skip), RAM cache cap, Terabox token parsing, guest listing, fallback card,
  on_error skip, TikTok photo fallback.
- Local bot smoke run: boot clean, self-check OK, aur dummy token par restart logic
  real process me kaam karta hua dikha (HARD RESTART #1, #2 — koi crash trace nahi).
- Live Terabox test: `1024tera` share link par file naam + size mila (guest listing).
- Static check (pyflakes): koi undefined-name bug nahi.

## 4. Abhi ki limitations (imaandari se)

- **Terabox direct link bina cookie ke nahi milta** (Terabox ka 2026 ka rule). Cookie ke bina
  aapko file info + web/app ka rasta milega.
- **YouTube** kuch videos par bot-check aata hai (server IP) — cookies se hi pakka hoga.
- **Instagram reels** par kabhi-kabhi rate-limit / login wall aata hai — retry se aksar chal jaata hai.
- **TikTok photo** me sirf pehla slide aata hai.
- Har tool ko live (asli internet) par ek-ek karke test nahi kiya ja sakta — static checks
  aur existing 3,400+ tests se verify kiya gaya. Koi tool galat lage to batao, wo alag se fix hoga.

## 5. Technical summary (developers ke liye)

| Area | File | Change |
|---|---|---|
| Empty-text safety | `bot.py` | `_reply_nonempty()` (27 call sites), `on_error` skip |
| Instagram delivery | `bot.py` | `_delivered` flag, `_parse_img_index()`, carousel item pick |
| Terabox | `modules/cloud_tools.py` | `_tb_page_tokens`, `_tb_share_list`, `_tb_walk_list`, `_tb_guest_list` (token), `_tb_ndus` (token + legacy fallback), `resolve_terabox` (order + info card) |
| Terabox UX | `bot.py` | `to_thread` + 75s timeout, fallback buttons |
| Restart | `bot.py` | `_hard_restart()` (os.execve, sirf `python bot.py` par), `_supervise` clean restart, webhook→polling via restart, polling bad-streak restart |
| RAM | `modules/media_downloader.py` | cache 100MB→20MB, item cap 40MB→12MB |
| TikTok | `modules/media_downloader.py` | `/photo/` → og:image fallback |
| Tests | `tests/test_v82_zero_crash.py` | 35 checks |

Env flags (optional): `TERABOX_COOKIE`, `YTDLP_COOKIES_FILE`, `MEMORY_LIMIT_MB` (default 512),
`HEAVY_GATE=on`, `MEM_RESTART_MB` (owner ka v81.2 idle-restart threshold). Internal (auto-set, aap set mat karo): `UDB_RESTARTS`, `UDB_LAST_RESTART`,
`UDB_FORCE_POLLING`.
