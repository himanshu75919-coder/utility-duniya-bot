# v96.0 SOCIAL-FIX — KYA BADLA (TikTok + Facebook + YouTube-asliyat)

**Date:** 2026-10-08 · **Base:** v95.0 → v96.0 · **PROMPT_DATA:** 43 (koi purana prompt change NAHI)

## User ki shikayat

Instagram fix hone ke baad YouTube ("Sign in to confirm you're not a bot" +
40s timeout), TikTok aur Facebook kaam nahi kar rahe the.

## Jaach me kya mila (sab live test karke)

- **YouTube:** hub thanda hone par 31s leta hai (6s/12s cap miss), uske links
  savenow captcha-HTML hai (video nahi), Piped/Cobalt ke public instance dead
  hain, aur yt-dlp ke saare clients Render IP par bot-check me phas-te hain.
  Matlab: **bina login-cookies YouTube kisi bhi free-server bot par nahi chal
  sakta** — ye YouTube ki taraf se block hai, code bug nahi. Bot me `/cookies`
  flow pehle se bana hai (file bhejo → DB → boot-restore) — wahi asli ilaaj hai.
- **TikTok:** sirf yt-dlp tha (block) — tikwm keyless API live verify hua
  (video/mp4, no-watermark, 2-3s).
- **Facebook:** sirf yt-dlp tha — page ke `browser_native_hd/sd_url` live
  verify hue (video/mp4, login-free).

## Fix

- `_tt_tikwm` — TikTok video (hdplay/play/wmplay best-that-fits) + photo
  slideshow → carousel (yt-dlp ye karta hi nahi tha). Chain me yt-dlp se PEHLE.
- `_fb_native` — FB reel/watch/share page → HD (warna SD) mp4 + title unescape.
  Chain me yt-dlp se PEHLE. Dono fail → purana yt-dlp fallback waisa hi.
- `_http_get_capped` — size cap + content-type guard (HTML kabhi media nahi).
- Hub guard — `text/html` link turant skip (52KB captcha "video" band).
- YouTube: code me kuch tootna nahi tha — `/cookies` chain verify (command +
  file-handler + DB meta + boot-restore + yt-dlp cookiefile, sab intact).

## Proof

- TikTok vm link (sandbox live): `video | tikwm | 4.67MB | @Selai Design`.
- FB watch link (sandbox live): `video | fb-native | 5.14MB | sahi title`.
- Naya tests/test_v96_socialfix.py — 25 checks PASS (fixture-based, no network).
- Full suite: **49/49 files PASS** · pyflakes: 0 undefined-name errors.
- V96 live deployment verified via /health (BOT_VERSION startswith v96).

## Note (YouTube ke liye zaroori)

Bot me `/cookies` bhejo → guide ke hisaab se `cookies.txt` export karke bot ko
file bhejo → "COOKIES LAG GAYIN" → YouTube turant chalne lagega (redeploy ke
baad bhi DB se wapas lag jaati hain). Ye ek-time 5-minute kaam hai.
