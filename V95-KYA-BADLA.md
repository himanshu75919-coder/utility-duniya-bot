# v95.0 IG-CAROUSEL-FIX — KYA BADLA (10-photo post par 1 photo milti thi)

**Date:** 2026-10-08 · **Base:** v94.0 → v95.0 · **PROMPT_DATA:** 43 (koi purana prompt change NAHI)

## User ki shikayat (live proof ke saath)

Link `instagram.com/p/DeMepBMjx2T/` (10-photo carousel) par dusre bots saare
photo de rahe the, hamara bot sirf **1 photo (0.04 MB thumbnail)** de raha tha,
caption me `&quot;` kachra, aur log me `No video formats found` errors.

## Asli wajah (3 bugs mile, live test karke pakde)

1. **Instagram ne embed HTML badal diya** — `display_url` GAYAB (0 mile), ab har
   photo `display_resources:[{src,config_width}...]` (triple-escaped JSON) me hai.
   Hamara album engine purana format dhoondhta raha → 0 URLs → 1-photo fallback.
2. **Galat User-Agent** — DESKTOP UA par IG khaali React shell (630KB, 0 data)
   deta hai; **crawler (FB) UA par asli data page** (342KB, poora carousel).
3. **Photo ko video-format se khinchna** — yt-dlp download string sirf-video hai,
   isliye photo entry par `No video formats found` = photo skip.
4. **Caption `&quot;`** — title escape hota tha, unescape kabhi nahi (double-encoded
   og:title jaisa ka taisa) + double-hesc bug.

## Fix

- `_deep_unescape` + `_ig_album_candidates` (naye + purane format, max-width src,
  **sidecar-window** — related-post/profile ki galat photos bahar, order barkarar).
- Album + video embed engines **FB_UA pehle** (data page), DESKTOP backup.
- `_ytdlp_direct_image_bytes` — photo entries/formats/thumbnails seedha CDN se;
  single-photo branch me rescue fallback. Video path bilkul untouched.
- `title` pehle double-unescape, phir usage par single hesc (double-escape fix).
- `_ig_embed_album` ab 1 photo mile to bhi single-photo result deta hai (None nahi).

## Proof

- User ke link par sandbox live test: `carousel | embed-album | count: 10`
  (500KB+ full-quality, order sahi, 3 related-post junk bahaar).
- Naya tests/test_v95_igcarousel.py — 31 checks PASS.
- Full suite: **48/48 files PASS** · pyflakes: 0 undefined-name errors.
- V95 live deployment verified via /health (BOT_VERSION startswith v95).
