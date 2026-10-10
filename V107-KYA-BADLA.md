# V107.0 PRO-SPEED — KYA BADLA (10 Oct 2026)

> User ki shikayat thi: (1) Instagram tools 2-3 minute leta hai / "Media number out of
> range." error, (2) Render par baar-baar crash (MEMORY HIGH 466-489 MB), (3) GitHub
> backup 401 fail. Teeno ki jad tak gaya gaya — neeche poora hisaab.

## 0) PEHLE ASLI DIAGNOSIS (video + Render logs + live audit se)

| Saboot | Kya mila |
|---|---|
| Video frames | Link `.../p/Dd_5RQgH9J_/?img_index=4&xtok=...` par error box "Instagram / Instagram: / Media number out of range." |
| `/health` live check | Render par **v105.2** chal raha tha — v106 ka IG-FAST engine **deploy hi nahi hua tha** |
| Git history scan | "Media number out of range" string repo me KABHI nahi thi ⇒ ye **upstream/remote** kachra tha jo user ko raw dikh gaya |
| Live engine audit (datacenter IP = Render jaisa) | ig_fast official API **0.5s me FAIL** (login-wall), parth-dl **1.6s PASS**, embed-album **1.1s PASS**, loader-ig **30s** (slow rescue), wayback/jina **null** |
| Boot RAM measurement | `bot.py --check` = **224 MB** boot! Jonch: `osint_tools` ka top-level `phonenumbers` import = **+112 MB** (geocoder akela 95 MB) |

## 1) ⚡ INSTAGRAM SPEED + RELIABILITY (post / reel / carousel / story)

- **Engine order ab NAPAA hua hai** (andaaze se nahi): video race =
  `ig_fast → parth-dl → embed → yt-dlp → loader-ig(30s rescue) → jina-HD → wayback`;
  photo race = `ig_fast → parth-dl → embed-album → embed → hd_then_og → yt-dlp → jina-HD`.
- **Budget**: video 55s → **40s**, photo 34s → **26s** (fast engines 2s me jeet-te hain;
  budget sirf worst-case rescue ke liye).
- Natija (live test, isi code se): carousel link (wahi jo video me tha, `img_index=4`
  ke saath) → **1.6s me poori 6-item album**; reel → **2.8s me 6.6 MB video**.
- `img_index` wala link ab kabhi error nahi dega — query strip hoti hai, poori album
  jaati hai (v85 behaviour), caption me note lagta hai.
- **🧼 RAW ERROR SANITIZER (`user_safe_error`)**: upstream ka technical kachra
  ("Media number out of range.", "HTTP 403: {…}") user ko KABHI nahi dikhega —
  saaf Hinglish + solution + "credit nahi kata" message me badal jaata hai.
  Hamare apne likhe Hinglish/emoji messages jaise-hain waise jaate hain.
- **ig_fast login-wall backoff**: datacenter IP par Instagram 302/403 deta hai;
  3 lagataar wall ke baad 10 minute break (bekar calls + hammering band).
  `/health` diagnostics me `wall` / `wall_hits` dikhta hai.
- Story: bina cookie fast-fail (turant saaf message), cookie lage ho to isi fast
  engine se — behaviour wahi, message wahi.

## 2) 🩸 RAM-SAVER-III (crash fix)

- `phonenumbers` (core 3 MB + carrier 10 MB + **geocoder 95 MB**) ab **LAZY** —
  pehli number-lookup par import. **Boot RAM 224 MB → 113 MB** (napa hua).
- **Emergency RAM valve**: hard-limit ke paas safai ke baad bhi RAM high ho to
  geocoder (~95 MB) OS ko wapas; agli lookup par khud load ho jaata hai.
  (OOM-kill se behtar hai.)
- Media RAM cache 20 MB → **12 MB** (badi files disk cache sambhalta hai).
- Number Info / Family Info ke **RESULTS me koi badlaav nahi** — sirf import timing
  badli hai (spin-up ke turant baad pehli lookup par ~1s extra lag sakta hai).

## 3) 🛠️ SELF-CHECK + VAULT

- Boot self-check me `gaming_tools` (deleted module) ka reference hataya —
  ab `modules FAIL (1)` wali line nahi aayegi.
- Vault GitHub backup 401 par log + result me **poora ilaaj** likha milta hai:
  Render → Environment → `VAULT_GITHUB_TOKEN`/`GITHUB_TOKEN` me naya PAT (repo
  scope) → Save → restart. Telegram backup tab tak chalta rehta hai.

## 4) TESTS

- Naya `tests/test_v107_pro.py` (26 checks: lazy phonenumbers, RAM valve, engine
  order/budget, sanitizer, wall-backoff, version).
- Purane version/budget assertions (v101/v102/v103/v104/v105/v105.1/v105.2/v89/
  v100-familyinfo) v107 ke hisaab se update — **60/60 test files green**.
- Number Info (`mynum_api`) aur Family Info (`familyinfo_api`) ke CODE me
  **ek character bhi nahi chheda** (sirf test files me version-head string update).

## 5) DEPLOY NOTE (zaroori!)

Render par purana build chalta reh gaya tha (v105.2). Push ke baad:
- Agar service me **Auto-Deploy ON** hai → push se khud deploy.
- Warna Render dashboard → service → **Manual Deploy → "Clear build cache &
  deploy"** (ek baar cache saaf karna zaroori: naya yt-dlp/parth-dl tabhi aayega).
- Deploy verify: `https://utility-duniya-bot.onrender.com/health` par
  `version: v107.0 PRO-SPEED` dikhna chahiye.
