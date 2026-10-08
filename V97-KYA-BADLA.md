# v97 — ⬇️ YOUTUBE BINA COOKIES + TikTok PHOTO FIX

**Date:** 8 Oct 2026 | **Suite:** 50/50 files green (v97: 23/23) | **Prompts:** 43 (koi change nahi)

## 1. YouTube BINA cookies — loader.to engine (naya)
- Naya engine `_yt_loader()` — loader.to job + progress-poll → savenow CDN se seedha mp4.
- **Quality picker khulne par background prewarm** — user ke quality chunte-chunte (10–30s)
  video pehle se ready; tap par turant pickup, 40s timeout se pehle.
- Order: 1080p = loader → hub6 → hub12 → (yt-dlp wale direct); 720p = prewarmed loader →
  hub6 → hub12 → chhota loader-retry → direct; Audio = hub-audio → loader(360) → direct.
- Purana sab kuch fallback me barkarar — kuch toota nahi.

**Live proof (asli network, 8 Oct):**
| Test | Result |
|---|---|
| Shorts 360p | ✅ 1.36MB, 25s, asli title, engine `loader.to` |
| Shorts 720p (prewarm→pickup) | ✅ 3.68MB, 31s, quality `720p` |
| 1080p job | ✅ savenow `mp4 [1080p]` link (~18s) |

## 2. TikTok photo-post = saari photos (bug fix)
- Bug: photo-post me `play` (slideshow video) bhi hota hai, isliye bot video bhej deta tha.
- Fix: `images` mile to **hamesha carousel** (IG jaisa) — slideshow ko ignore.
- Live proof: photo post → `type: photo`, engine `tikwm-photo`.

## 3. Note (imaanadari se)
- Bahut lambi videos me loader job 40s se zyada le sakta hai — tab dobara try karne par
  prewarmed file turant mil jati hai (cache 25 min).
- TikTok multi-photo carousel ka end-to-end proof aapke kisi asli multi-photo link se
  hoga — bot par bhejkar dekhein.
