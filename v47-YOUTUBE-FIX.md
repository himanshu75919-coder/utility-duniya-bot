# 🎬 v47 — YOUTUBE KA PAKKA ILAAJ (hub me 5 bugs mile the!)

Aapne kaha: *"saara chij fixed kar do permanently"* — to maine aapke hub ka code **poora scan** kiya
(pyflakes se) aur live test kiya. **5 asli bugs** mile — sab fix, sab live.

---

## 🔍 Pehle asli wajah samjho (chhoti si kahani)

`/api/youtube-download`, `/api/ytdl`, `/api/youtube-mp3` — teeno 502 de rahe the. Lagta tha "YouTube
ne block kiya hai". Sach ye tha ki **code me 5 bugs** the:

| # | Bug | Kya hota tha |
|---|---|---|
| 1 | **`_YT_STATE` kabhi define hi nahi hui thi** | Jab bhi yt-dlp chalta → `NameError` → seedha 502 |
| 2 | **`_INVIDIOUS_CACHE` undefined** | Invidious fallback apne aap crash ho jata tha |
| 3 | **`INVIDIOUS_INSTANCES` undefined** | wo bhi |
| 4 | **`PIPED_INSTANCES` undefined** | Piped fallback bhi dead |
| 5 | **yt-dlp ke galat player_client** `[tv_embedded, web_safari, mweb, web]` | yt-dlp "No video formats found!" deta hai — **default clients se 1 second me chalta hai** |

Upar se ordering ulti thi: pehle **dead** Invidious/Piped try hote the (13-19 second barbaad), aur
yt-dlp ko mauka hi nahi milta tha.

---

## ✅ Kya fix kiya (aur LIVE kya nikla)

1. Sab 5 bugs fix (pyflakes scan me ab **ek bhi undefined name nahi**).
2. Chain naya: **yt-dlp pehle** (6s budget) → **public providers** → Invidious/Piped → upstream.
3. **Naya `/api/ydl/stream` proxy** — YouTube ke googlevideo links **IP-locked** hote hain, isliye ab
   hub ke through stream hote hain (Range support + sirf YouTube hosts allow = safe).

### 🚧 Phir asli dushman mila: **Render ka IP YouTube se block hai**
Test se saaf dikha: sandbox se yt-dlp chalta hai, lekin Render se:
> `Sign in to confirm you're not a bot`

Iska **pakka ilaaj** — 2 public downloader providers laga diye jo **apne server par extract** karte hain
aur **CDN link** dete hain (CDN links kisi bhi IP se chalte hain):

- **savetube API** (`apis.davidcyriltech.my.id`) → video mp4 (480p/720p) + audio mp3 128kbps
- **loader.to** → 360p video / mp3 (polling wala, backup)

### 🎯 LIVE RESULT (aapke hub par, abhi):
```
/api/youtube-download?url=https://youtu.be/9bZkp7q19f0
   → success ✅  sources: ['savetube']  title: PSY - GANGNAM STYLE  (7 second)
   → video 480p mp4 + audio mp3

/api/youtube-mp3?url=...    → success ✅  audio: cdn405.savetube.vip/...mp3
/api/ytdl?url=...           → success ✅  sources: ['savetube']
```

---

## 🤖 Bot me kya badla (v47)

| Cheez | Pehle | Ab |
|---|---|---|
| 🎬 CLIP MAKER (YouTube) | hub se link **nahi** aata tha → local yt-dlp bhi Render par block | **hub ke naye /youtube-download se** (proxy link, 1-7s) |
| 📥 VIDEO DOWNLOADER (YouTube) | yt-dlp (block) | pehle **hub** (proxy), phir yt-dlp |
| Local yt-dlp fallback | pehle 5 galat clients try hote the | ab **default + android_vr/android pehle** (kaam karte hain) |

Bot ka code `hub_yt_download()` use karta hai: proxy link ko direct link se **pehle** try karta hai
(kyunki direct link IP-locked ho sakta hai). Hub down ho to local yt-dlp chalta hai — do raste, dono tested.

---

## 🧪 Tests (sab green)

| Test | Result |
|---|---|
| v45 hub suite (`_selftest_v45.py`) | **62 / 0** ✅ (naya: `hub_yt_download` check + mock `/youtube-download`) |
| Live check (asli hub + asli internet) | **122 / 122** ✅ (2 naye YouTube hub live checks) |
| baaki saare suites (imei, vehicle, clips, v44, v37, admin, v32/34/35/38, audits) | **sab 0 fail** ✅ |

**Hub me aaj total fix:** v2.1 (Snapchat + payment security) → v2.2/2.2.1 (YouTube NameError ×4) →
v2.3/2.3.1/2.3.2 (YouTube providers + budget) — sab push + live deploy ✅
