# V106 — ⚡ IG FAST ENGINE + Story Support + Speed Upgrade

## User ki shikayat (10 Oct 2026)
1. **Instagram tool 2-3 minute** leta tha, dusre bots 10-15 second me jawab dete hain.
2. Reel ka link bhejne par kabhi-kabhi galat/slow jawab.
3. Story links kaam nahi karte the (30-55s race ke baad fail).
4. Render par baar-baar crash ki shikayat.

## Asli wajah (deep analysis se mila)
- Purana engine **6-7 slow engines ki race** tha: loader.to (12-45s),
  r.jina render (~20s), yt-dlp (login-wall), og-scrape (sirf cover photo).
  Datacenter IP par Instagram 429/login-wall deta hai, isliye fast raaste
  mar jaate the aur jeet hamesha SLOW engine ki hoti thi.
- Story ke liye 30-55s ki race chalti thi jabki story **bina login ke
  kisi bhi service se nahi mil sakti** (IG ki apni privacy limit) —
  waqt pura zaya, phir bhi fail.

## Kya badla

### 1) NAYA ENGINE — `modules/ig_fast.py` (race me SABSE PEHLE)
Instagram ke **KHUD ke public JSON API** par chalta hai (wahi jo IG ka
web/app use karta hai):

| Link type | Kaise | Speed |
|---|---|---|
| Post / Reel / IGTV | shortcode → media-id → `/api/v1/media/{id}/info/` → HD mp4 / full photo | **1-5s** |
| Carousel (album) | `carousel_media` se **saari** photos+videos HD | 2-8s |
| Profile link | `web_profile_info` → HD profile photo | ~1s |
| Story / Highlight | cookie lagi ho to `reels_media` API se | 2-6s |

- Login nahi chahiye (public posts ke liye). Koi third-party site nahi.
- **429 COOLDOWN**: Instagram ne rate-limit kiya to engine 0.001s me raasta
  chhod deta hai (90-600s cooldown) — baaki engines waise hi chalte hain.
  Pehle jaisa "55 second atke rehna" ab nahi.
- Story **bina cookie ke TURANT saaf message** deti hai (ab 30-55s zaya nahi):
  `/cookies` command se cookie lagao → story/highlight ON.

### 2) `media_downloader.py` integration
- Race list me `IGF.fetch_media` **first position** par (jeet usually 1-5s me).
- Profile link par pehle ig-api ki HD photo, phir purana engine.
- Story fast-fail (bina cookie) — credit kabhi nahi katta.
- Purane engines (parth-dl, embed-mp4, loader.to, og, jina, wayback, yt-dlp)
  waise hi fallback me hain — kuch bhi delete NAHI hua.

### 3) Tests
- Naya `tests/test_v106_igfast.py` — 40+ offline checks (parsing, shortcode
  math, crash-proof junk input, mock API extraction, story fast-fail,
  429 cooldown, integration). **Poora suite: 59/59 green.**

## Number Info / Family Info — KOI CHANGE NAHI (user ka order)
`numinfo` aur `familyinfo` (Aadhar) tools ko haath bhi nahi lagaya.

## Render crash par note
Code me pehle se heavy-gate + memory-watchdog + janitor hai. V106 se RAM/time
pressure AUR kam hua: (a) story ki bekaar race band, (b) fast engine ke hote
slow engines start hi nahi hote, (c) 429 par hammer nahi. Free plan par
15 min idle ke baad instance sota hai — pehla message 30-60s le sakta hai
(ye Render ka behaviour hai, crash nahi).

## Story download ON karne ka tarika (user ke liye)
1. Phone me Instagram app → browser me `instagram.com` kholo → login.
2. Developer tools/cookie viewer se `sessionid` cookie copy karo.
3. Render → Environment → `IG_COOKIE` = `sessionid=XXXXXXXX`
   (ya bot me `/cookies` command).
4. Bas — story + highlight + private-followed content sab nikallega.
