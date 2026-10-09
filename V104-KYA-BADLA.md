# v104.0 HD-TRUTH — Kya badla (10 Oct 2026)

User ki do shikayatein (screenshots):
1. "YouTube pe 720 quality choose kiya — itna low quality video de rha, chhiiii."
2. "Instagram tools mein sirf reels ke links work kar rhe, post ke links pe blurry/ek photo."

Dono ke REAL karan milke theek kiye gaye — ab label = naapi hui reality.

---

## 🏆 YouTube — "jo dabao, wahi milega (ya uska sach)"

### Bug 1: itag 18 ka k-chehra order
`yt_download_at_height` ka format string `"18/22/..."` se shuru hota tha.
yt-dlp pehle matching format leta hai — **18 = 360p hamesha maujood** →
720/1080 maangne par bhi 360p file + "720p" label. FIX: `22/` (asli 720p
progressive) ab pehle, height-fitting best adaptive uske baad, aur 18 SIRF
aakhri fallback.

### Bug 2: Nakli HD (upscale)
Hub ka 360p "best" file ko ffmpeg se 720 me STRETCH karke "{h}p" label
chipkaya jaata tha = bada lekin blurry = "chhiiii" file. FIX: hub aur
loader results ki **asli height NAAP** jaati hai — source target se chhota
to transcode SKIP, file waisi hi + saaf note ("nakli upscale nahi bheja").

### Bug 3: Chain ka ulta order
loader.to ka v2 API ab **ASLI 720/1080** deta hai (live proof: format=720 →
1280×720 h264 @1.1 Mbps, 30 MB), par code me wo slow master-ladder
(1080-master → do ffmpeg passes → 156 second) ke PEECHE daba tha, aur uska
purana "720→360p" darr-map label bigaad raha tha. FIX:
1. `_yt_loader(url, maangi-height)` — DIRECT step 1 (prewarm pickup, ~30-50s)
2. Master-ladder backup sirf HD (720/1080) par
3. Direct yt-dlp
4. Hub (upscale-guard + naap ke saath)
Picker ab **720 + 1080 dono prewarm** karta hai.

### Naya trust layer: `_yt_honest`
Jo bhi video file deliver ho, uski height ffmpeg se naapi jaati hai.
Asli < maangi → label theek hota hai + user ko note: "Source me sirf asli
Xp tha — Yp ka nakli version bhejna theek nahi laga." AB KABHI koi file
"720p" kehkar 360p nahi hogi.

### Live results (10 Oct, Rick Astley 3:33, datacenter IP)
| Maangi | Mili (measured) | Time |
|---|---|---|
| 360p | 640×360 ✅ | 34s |
| 480p | 854×480 ✅ | 50s |
| 720p | **1280×720 ✅** | 74s (prewarm ke saath tap par ~30s) |
| 1080p | honest downscale + note (46MB me 1080 fit nahi, jhooth nahi) | — |

## 🔓 Instagram — posts/albums ka HD raasta + private ka sach

### Naya engine: `_ig_jina_hd`
Datacenter IP par IG hamare page me sirf 640px og:image deta hai (og URL
signed hai — size swap = 403; /media/ endpoint login-walled; archive.ph
timeout; hub ka IG bhi blocked — sab verify kiya). LEKIN r.jina.ai ka browser
page FULL render karta hai aur uske markdown me **post ki asli media URLs**
aati hain — 1080px se 3072px tak. Naya engine:
- poori carousel album ki saari photos (media-id se dedupe, sabse badi res)
- suggested-posts grid "Discover something new" marker + permalink-code check se KATTA hai (doosri post ki photo KABHI nahi)
- profile pictures/rsrc junk skip
- public reels ka mp4 bhi pick karta hai (agar render me dikha)
- LIVE TEST: public 2-photo carousel → dono 896×1600 HD photos ✅
  (pehle: 640px single blur)

### Private account = ab honestly bataya jaata hai
Screenshot wali post **private account** (_its_mayank._.113) ki thi — IG kisi
ko bhi us post ki poori album nahi dikhata (server-side wall). Pehle bot
chupchap ek blurri si photo bhej deta tha. Ab: photo ke saath note —
"🔒 Ye post PRIVATE account ki hai — Instagram server khud sirf preview
deta hai. Public accounts ki posts/carousels full HD aati hain."

### og-ab-hi-last
Photo race me og ka slot ab `_hd_then_og` wrapper hai: pehle jina-HD try,
phir hi 640px og. Photo budget 24s→34s (jina cold render ~20s). Reel race me
bhi `_ig_jina_hd` extra engine juda (v103 ke wayback+jina-embed ke saath).

## Tests
- `tests/test_v104_hd.py` — 32 naye checks (fmt order, honest-label contract,
  chain order, upscale guard, jina-hd filters, efg resolver, prewarm, version)
- Purane stale assertions v104 ke mutabik update: v89 (34s budget), v97
  (quality pipe + label), v98 (loader 720=asli 720), v100/v101/v102 (head)
- **SUITE: 55/55 PASSED** (231s, full live+offline)

## Files changed
- `modules/media_downloader.py` — YT chain fix + _yt_honest/_probe_data +
  upscale guards + loader label truth + _ig_jina_hd/_ig_efg_res + engine wiring
- `bot.py` — v104 head, picker prewarm 720+1080
- `tests/` — 1 new file, 5 updated
