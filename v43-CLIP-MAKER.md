# 🎬 v43 — CLIP MAKER (video → 4-7 clips)

**Kya hai:** user ek video bhejta hai → bot uske **4-7 short clips (25-60 sec)** bana ke deta hai —
"best moments" (jahan awaaz tez / action hai) ya "equal parts" (barabar hisse), aur **16:9 (normal) ya
9:16 (Shorts/status)** me.

---

## 1️⃣ Paisa/limit — kya set hai

| Cheez | Value | Env se badal sakte ho |
|---|---|---|
| Video ki lambai | **15 min tak** | `CLIP_MAX_MINUTES` |
| Kitne clips | **6** (3-8 ke beech) | `CLIP_COUNT` |
| Clip ki length | **35 sec** target (15-60 ke beech) | `CLIP_LEN` |
| File size (Telegram) | **20MB** (Telegram bot limit) | — |
| Direct `.mp4` link | ~46MB tak download hota hai | — |
| YouTube | optional (yt-dlp) — **kabhi-kabhi block hota hai** | `CLIP_YTDLP=0` band karne ke liye |
| Credits | **1 credit** per successful job · VIP unlimited | — |

> **ffmpeg** Render par already hai — `imageio-ffmpeg` package ke saath bundled binary aata hai
> (media studio bhi usi se chalta hai). `/clipstatus` chala kar confirm kar lo.

---

## 2️⃣ User ka flow (bot ke andar)

1. Menu → **🎬 CLIP MAKER** → prompt: *"Now send the video file (or link)"*
2. User **video file** bhejta hai (ya direct `.mp4` link / YouTube link)
3. Bot 3 buttons dikhata hai:
   ```
   🎯 Best Moments   |   ⏱️ Equal Parts
   🖥️ Normal 16:9    |   📱 9:16 (Shorts)
                  🚀 Make clips
   ```
4. Kaam chalta hai: "🔍 Analysing…" → "✂️ 6 clips ready — sending…"
5. Clips ek-ek karke aate hain — caption me:
   `🎬 Clip 3/6 ⭐⭐ · 📱 9:16` + `00:12:30` + `28s` + `1.6MB`
   aur score-wise top clips par **🔥 Best of best** likha hota hai
6. End me: `✅ 6 clips sent (9:16) — took 84 sec` + `⚡ 1 credit used`

---

## 3️⃣ "Best" kaise nikalta hai (bina AI — deterministic)

1. **🔊 Loudness** — ffmpeg `astats` se har 0.5 sec ka RMS nikalta hai (cheering, hasi, shouting, goal).
2. **🎬 Scene changes** — ffmpeg scene detect (keyframes par, fast) — action/cut/edits ke liye.
3. **🎯 Score** — har window ka score = us hisse ki loudness + usme aaye scene cuts × 4
4. **Ranking** — top score wale non-overlapping windows = clips. Sabse upar wale 3 par 🔥 mark.
5. Audio na ho to scene/equal par chala jaata hai (crash nahi).
6. **Equal Parts** me bas barabar hisse — aur boundary ho to scene cut par snap kar deta hai (clean lagta hai).

> AI tools nahi lagte (aapka rule) — isliye lecture/podcast me ye "loud + action" par hi chalta hai,
> bolne ke content (topic) nahi samajhta. Sports, comedy, music, gameplay video me best chalta hai.

---

## 4️⃣ Error messages (sab me **credit nahi katta**)

| Situation | Bot kya kehta hai |
|---|---|
| Video 20 sec se chhoti | "Video is only 15 seconds long — need at least 20 seconds" |
| Video 15 min se lambi | "Video is 32 min long. Limit is 15 min (server limit) — send a shorter part" |
| YouTube download fail / bot-check | "YouTube download is not available right now. Send the video file itself, or a direct .mp4 link" |
| Link se download fail | "DOWNLOAD FAILED … Send the video file instead — that always works" |
| Clips ban hi na paye | "CLIPS NOT MADE … No credit was cut — you can try again" |
| 0 credits | VIP card (baaki premium tools jaisa) |

**Copyright:** prompt me likha hai *"Use your own video or one you are allowed to reuse."*
Kisi aur ka YouTube video clip karke repost karna us bande ka right violate karta hai — bot me warning hai.

---

## 5️⃣ Admin commands

- **`/clipstatus`** — ffmpeg ready hai ya nahi, limit kya hai, YouTube (yt-dlp) available hai ya nahi.
- Logs: har clip send fail hone par `log.warning("clip send fail: …")` aata hai (Render logs me dikhega).

---

## 6️⃣ Test

Naya test: **`_selftest_clips.py` (48/0)** — asli ffmpeg se 90 sec ka test video banata hai
(3 hisse loud, 3 normal) aur check karta hai:
probe · loudness detection (loud hisse hi pakde) · best clips ka loud hisso par girna · no overlap ·
rank · equal split · 16:9 aur 9:16 output (540x960) · silent video · 15 sec error · poora bot flow
(video → mode buttons → clips bheje → 1 credit) · 0 credits block · YouTube off message · /clipstatus.

Baaki poora batch green: prompts v42 12/0 · v37 91/0 · v32 51/0 · v34 48/0 · v35 46/0 · v38 80/0 ·
admin 54/0 · vehicle 78/0 · imei 70/0 · cloner ✅ · **live_check 105/105** · audit 69/0.
