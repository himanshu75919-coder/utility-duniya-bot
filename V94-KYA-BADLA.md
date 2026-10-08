# v94.0 MERGED-PRO — KYA BADLA (v93 + v86 dono ek saath)

**Date:** 2026-10-08 · **Base:** v93 (remote) + v86 (local) ka merge · **PROMPT_DATA:** 43 (42 + QR Scanner — koi purana prompt change NAHI)

Do parallel kaam ek branch par aa gaye the — merge me dono ke features rakhe gaye, kuch hataaya nahi.

## v93 side (remote — pehle se pushed tha)

- **10+ album chunking:** `[:10]` wali chup-chaap kataai khatam; `clean_album_items` + `build_album_chunks` helpers + `ALBUM_CHUNK=10`.
- **Terabox FILE REPORT card:** size/type/video length/resolution/thumbnail.
- **HTML SAFETY NET** (`modules/core/htmlnet.py`): ~500 send sites par "can't parse entities" ab message gayab nahi karta.
- Version checks ab exact-prefix ki jagah `>= 85` (har bump par toot-te nahi).

## v86 side (local — is session ka kaam)

- **Insta-mega:** 20-photo carousel intake, story/highlight/share link classification, public profile HD photo, per-photo 15MB + total 60MB caps, JPEG normalize.
- **QR Scanner (naya tool):** QR photo bhejo → text/link + safe Link button; 1600px/6MB guards; keyless decode.
- **Crash-sweep-II:** 8 fuzz-crash fix (Biz Area, Media, Toolkit, Mail, IMEI, media_downloader).
- **Safe buttons:** LinkCheck/short/appfind URLs `_safe_btn_url` wrap; khaali rows par markup=None.

## Merge me kya juda (conflict resolution)

- Album handler dono ka MELA: v86 `_album_chunks` intake (20-item + junk filter) → v93 45MB cap + "size-limit se chhoote" note → `ALBUM_CHUNK` stepping → `Part N/M` captions → one-by-one fallback.
- Version `v94.0 MERGED-PRO` (history chain v93/v86/v85/v84/v83/v77 barkarar).
- Version asserts dono taraf v93-style `>= 85`.

## Tests

- Full suite: **47/47 files PASS** (v93 trio 41+26+47, v86 instamega 54, sab purane green).
- pyflakes: 0 undefined-name errors.
- Note: test_v53 me 3 live-network flake aaye the (dobara run par 211/0) — code issue nahi.
- V94 live deployment verified via /health (BOT_VERSION startswith v94).
