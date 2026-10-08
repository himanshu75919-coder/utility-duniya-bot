# v86.0 — KYA BADLA (Instagram Mega + QR Scanner + Crash-Sweep II)

**Date:** 2026-10-08 · **Base:** v85.1 → v86.0 · **PROMPT_DATA:** 42 → 43 (naya: QR Scanner — koi purana prompt change NAHI)

## 1) Instagram — FULL ALBUM MEGA (multi-photo carousel)

- **20-photo intake, 10+10 Telegram groups:** carousel/post ke 20 tak photos, album parts me code-split sticker ke saath (Part 1/2 ...).
- **Profile / share / highlight links:** /p/ aur /reel/ ke saath /share/, /stories/highlights/ ab sahi classify hote hain. Public profile link par HD profile photo milti hai.
- **Story links:** photo-story Parth/yt-dlp se seedha bhejne ki koshish; private/expired/login-wall story par saaf Hindi wajah ("login/private ya expired story").
- **Per-photo 15 MB cap + JPEG normalize:** ek fail photo poora album nahi rokta — fail photos gine jaate hain, baaki sab deliver hote hain. Total 60 MB cap.
- **Video-only judgement safe:** story URLs forced video-only rule se baahar — photo stories deliver hoti hain.

## 2) QR SCANNER (naya tool — photo ya link/tgph dono)

- Kisi bhi QR photo bhejo (Tools > QR Scanner kholkar) — decode hokar text/link milta hai.
- Link nikle to "Link Kholo" safe button; link/text sab scan hota hai.
- Photo seedha link/tgph ho to scanner wahi use karta hai (bina download-run ke).
- Guards: 1600px resize + 6 MB cap (garbage input = clean error, crash nahi).
- Keyless free decode API — koi Madhav/Pari key nahi chahiye.

## 3) Crash-Sweep II (galat/junk input par 0 crash)

Fuzz round 2 me mile 8 crash fix, 22 functions x junk inputs par 0 crash:
- search_by_area_name (Biz Area), platform_name (Media), video_compress (Toolkit)
- clean_body (Mail), render_caption (IMEI), + media_downloader platform guard

## 4) Link/button safety

- LinkCheck final-URL button, short-link rows, appfind buttons — sab `_safe_btn_url` wrap (http/https + host wali links hi button banti hain).
- Khaali short-result par markup=None (InlineKeyboardMarkup([]) crash fix).

## 5) Tests

- Naya tests/test_v86_instamega.py — 54 checks PASS.
- Version-locked tests (v83/v85/v87/v89/v86) v86.0 + 43 prompts + _album_chunks/60MB par update.
- Full suite: 44/44 files PASS · pyflakes: 0 undefined-name errors.
- V86 live deployment verified via /health (BOT_VERSION startswith v86).
