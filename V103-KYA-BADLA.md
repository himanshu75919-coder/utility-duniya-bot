# v103 — IG-PRO (reel wala bug fix + poore tool-suite ka deep audit)

## 🎯 User ki report (screenshot, 10-Oct 01:34)
Reel ka link bheja → bot ne **doosri content ka COVER PHOTO** bhej di. Do asli wajah mili:

1. **Canonicalization ne "video" info kha gayi**: `insta_clean()` `/reel/<code>/` ko
   `/p/<code>/` bana deta tha → classifier "post" bolta → photo engine (og:image) race
   me jeet jaata tha.
2. **Cache bina referee ke serve hoti thi**: ek baar cache me padi purani photo-cached
   entry har dobara-par seedha bhej di jaati thi — chahe reel ho ya kuch bhi.

## ✅ Fixes (modules/media_downloader.py)
- **Video-intent ORIGINAL URL se**: `/reel/` `/reels/` `/tv/` `ig.it/` link aaya to
  `media_cat="reel"` force + `want_video=True` — canonical ke baad type nahi khota.
- **Cache par bhi referee**: galat-type cache entry (jaise reel par photo) serve NAHI —
  turant **delete** + fresh resolve. Sahi entry 0.1s me serve hoti hai (pehle jaisi speed).
- **Honest reel error**: video na mile to clear message — *"Reel par kabhi galat cheez
  (cover photo) nahi bhejenge"* — 30-60s retry hint ke saath. Galat media KABHI NAHI.

## 🌐 2 Naye engines (reel/video ke liye race me add)
Datacenter IPs par IG login-wall de deta hai — in do raaston se recovery milti hai:
- **`_ig_wayback`** — archive.org snapshot se asli `video_versions`/mp4; CDN link mara
  ho to wayback ke `web/2if_/` raw se file nikalti hai. Viral/purane reels ka safety net.
- **`_ig_jina`** — `r.jina.ai` reader IG ka `/embed/captioned/` page APNE IP se kholta
  hai; usme se `.mp4` extract.
- `_ig_embed` me **deep-unescape second pass** — triple-escaped embed variants bhi ab
  parse hote hain (pehle chhoot jaate the).
- Video budget 26s → **32s** (naye engines ke liye), photo 24s same.

## 🧹 Baaki saare tools ka LIVE audit (is session me network-tested)
| Tool | Test | Result |
|---|---|---|
| 📥 Instagram DL | pipeline sim + cache referee | ✅ fixed (v103) |
| ▶️ YouTube DL | yt-dlp live (info+formats) | ✅ LIVE (DC IP se bhi) |
| 🎵 TikTok DL | tikwm + yt-dlp probe | ⚠️ sandbox IP block karta hai; dual-host fallback ready; Render IP par chalta hai |
| 📱 NUMBER INFO | Supabase API | ✅ (user-verified, untouched) |
| 👪 FAMILY INFO | API + mask | ✅ (user-verified, untouched) |
| ☁️ TERABOX | worker /api | ✅ LIVE |
| 🏦 IFSC | razorpay 200 | ✅ |
| 📮 PINCODE | api.postalpincode 200 | ✅ |
| 📧 TEMP MAIL | mail.tm /domains 200 | ✅ |
| 📞 TEMP NUMBER | receivesms.co / receive-sms-free / temp-sms (301→follow) | ✅ teeno up |
| 📋 RESULT CHECK | resultapi.biharboardonline.org | ✅ host alive |
| 🌐 WEBSITE OWNER X-RAY | rdap.org (302→200 follow) | ✅ |
| 🔗 URL SHORT | da.gd + spoo.me live test | ✅ multi-provider |
| 📷 QR gen/scan | api.qrserver 200 + local libs | ✅ |
| 📲 IMEI | hub fetch_imei_details LIVE (brand/model aaya) + nanoreview search ✅ | ✅ |
| 🚗 RC+CHALLAN | hub vehicle endpoints up (bot ka key set) | ✅ |
| ⚡ MEDIA STUDIO / 🏦 BANK→EXCEL / 💼 BUSINESS STUDIO | local ffmpeg/pdfplumber/reportlab | ✅ (offline, safe) |
| 🔄 CHANNEL CLONER | Telegram-API based | ✅ (bot-side) |
| 🔍 LINK CHECK | offline heuristics + openphish (302→https follow) | ✅ |

##  Text leftovers
- insta_dl prompt head: `📥 VIDEO DOWNLOAD (Insta / YouTube / Facebook / TikTok)` →
  `(Insta · YouTube · TikTok)` — Facebook DL delete ke baad ka purana jhooth.
- "Send links from Instagram, YouTube, Facebook or TikTok" → Facebook hataya.
- VIP/wall feature line se "Facebook" downloader mention hata.
- (VIRTUAL NUMBERS ke `("fb", "🔵 Facebook")` service option ka koi lena-dena nahi — wo
  number-verify tool hai, waise hi rahega.)

## Tests
- **Naya `tests/test_v103_ig.py`** — 19 checks: video-intent lock, cache-referee
  integration (4 scenarios), naye engines presence, embed deep-pass, honest error,
  FB-text cleanliness, v102 style regression.
- Purani assertions updated: v85 (head), v89 (budget), version head tests.
- Full suite: **54/54 PASS**.
