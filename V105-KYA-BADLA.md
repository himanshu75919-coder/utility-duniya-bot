# v105.0 BEST-ONLY — Kya badla (11 Oct 2026)

User ke order (seedha, saaf):
1. "YouTube se quality choose karne wala OPTION hi hata do — short/video ka
   link bhejo, best quality extract karke de do."
2. "Instagram: reels, 7-8 photo wale posts, stories — SAARE links kaam
   karein, usi quality me jo original hai."

---

## 🚀 1) YouTube — quality-picker HATAA DIYA (0 taps)
- 360/480/720/1080 buttons wala poora menu hata. Ab YT/Shorts link bhejte hi
  bot khud **server ki sabse upar available quality** nikaalta hai
  (v104 ka verified engine chain: loader-direct 1080 → master-ladder →
  yt-dlp → hub — sab par naap-ke-label).
- Flow: link → "🎞️ YOUTUBE — BEST QUALITY" status → `_yt_hd_bg(1080)`
  background me ready hote hi video chat me. Credit sirf video milne par.
- file_id instant-hit (q1080) bacha hua — dobara bhejo to 0.1s me video.
- Purane picker-messages ke **ytq:** buttons dabane par bhi wahi HD flow
  chalega (compat) — aur us handler ka 52-line dead-code block saaf kiya.
- Shorts par ye khaas tez hai: 60s wali short → loader 1080 direct,
  30-50s me asli HD haath me.

## 🎬 2) Instagram reels — AB VIDEO AAATA HAI (naya engine)
`_ig_loader_reel`: loader.to sirf YouTube ka nahi — usne **Instagram
reels/highlights ka video bhi nikaal diya** (live proof 10-11 Oct: public
reel 67s → 19 second me genuine MP4). Race ka naya member:
- Job (format=1080 maanga jaata hai) → poll → file fetch (≤46MB) →
  `_ig_ensure_playable`: VP9/HEVC ho to ffmpeg se h264 (Telegram
  streaming) — h264 tha to skip.
- **Label = file NAAPkar** (540×960 file par "640p" likhega, "FHD" kabhi
  nahi). IG jo anonymous ko deta hai wahi publicly-available best hai —
  aur usme se bhi parth-dl aaj 720×1280 full-length de raha hai (5s),
  loader fallback jab parth gire.
- Reel budget 32s→55s; insta tool overall timeout 40s→75s.
- Private/unknown links par engine chup-chaap None → honest error (crash 0).

## 📸 3) Posts/albums — "usi quality" ab literally
- `_ig_jina_hd` photo cap 1600px → **2400px, q93** (1080-1440px originals
  AB UNTOUCHED pass-through — koi downscale nahi).
- Album limit 10 → **12 photos** (user: "7-8 ya kitni bhi"; IG max 20,
  12 tak bot bhejta hai — har photo alag media-id se dedupe).
- `_jpeg_fit` default quality 90 → **94** (saare photo engines par —
  practically original).
- parth-dl (jo recover ho gaya) albums **20 tak** handle karta hai.
- Bot ka caption jhooth bolta tha: har file par "**(FHD)**" chipka. Ab
  FHD SIRF asli 1080p/1440p par; chhoti file par uski NAAPÍ hui height,
  aur label na milne par "jo publicly available best thi".

## 📱 4) Stories — sach ye hai
Instagram stories **sirf followers** ko dikhti hain — koi bhi bot (ye bhi)
story video bina login ke nahi kheench sakta, ye Instagram ka server-side
rule hai. Isliye story link par abhi bhi clearly likha error aayega
(kya wajah ho sakti hai + kya try karein) — galat media kabhi nahi.
Highlight/reel ban chuki stories `@archive` jaisi services se /p/ /reel/
link ban jaati hain — wo links v105 me HD chalenge.

## Tests
- `tests/test_v105_best_only.py` — 27 checks (picker-gone, compat handler,
  dead-code safai, loader-ig contract, playable fix, measured labels,
  photo caps, budgets, version)
- Stale assertions update: v59 (picker ab NAHI hona chahiye), v89/v103
  (budget 55s), v68/v85/v86 (75s timeout), v100-102 (head), v104
  (prewarm 720 line uthi)
- Live: reel DRCOLMJlKN1 → pipeline winner parth-dl 720×1280 @5s;
  loader-ig independent → 640p @18s; private post → None (safe)

## Files changed
- `bot.py` — YT best-only flow, caption trust-fix, dead code safai, 75s timeout
- `modules/media_downloader.py` — _ig_loader_reel + _ig_ensure_playable +
  parth video meta + jina-hd/photo quality raise + budgets
