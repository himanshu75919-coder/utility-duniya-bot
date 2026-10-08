# v80 — tutorial-video ka poora kachra gaya (aur osint hub fix)

## Bot me kya badla (user-visible)

Ab bot me tutorial-video ka **naam-nishan nahi** bacha — pehle videos delete ho
chuke the, lekin unke *waade* aur *dead machinery* bachi hui thi. Ye sab hataya:

| Pehle | Ab |
|---|---|
| `/start` VIP card: "Free VIP chahiye? 5 dost ko bulao (/refer)" | line hi gayi (tool remove ho chuka) |
| Menu card: "Har tool ke neeche 🎬 Tutorial Video button hai" | "Tool band karne ke liye /cancel dabao, ya 📩 Support button se pooch lo" |
| `/account`: "VIP free chahiye? 5 dost ko share karo (/refer)" | line gayi |
| Cloner guide: "🎬 Neeche video dekho — 30 second me poora tarika" | line gayi (3-step text + 2 asli buttons bache hain) |
| `TUTORIAL_NOTICE` — "/help" ka text: "Har tool ke saath 🎬 30 second ka video hai" | `HELP_NOTICE` — /menu → tool → bhejo, /cancel se band (koi jhootha waada nahi) |
| `send_tool_video()` — CDN → raw → document → link fallback ka 40-line mechanism | poora function delete |
| `toolvid:<tool>` callback + `🔁 Watch Again` button | delete (ab koi dead tap nahi) |
| `tool_tutorial_kb()` — `has_video()` se gated 🎬 row | `tool_support_kb()` — sirf 📩 Support (9 jagah se wire) |
| `VIP_FREE_CB_PREFIX` me `"toolvid:"`, `"vid:"` | dono gaye (koi producer hi nahi tha) |
| `tutorial_footer()`, `tutorial_link_line()` (khaali return karte the) | delete |
| `bot.py` me `has_video`, `video_urls`, `video_caption` imports | import hi nahi hoti ab |

**Chheda nahi:** `modules/tutorial_hub.py` (vid map khaali + `VIDEOS_REMOVED=True`,
iske baare me hi tests likhe hain — aur iska `strip_tutorial_lines()` text prompts me
kaam aata hai), aur admin ka `/tutrefresh` + telegraph **text** page (video nahi).
`🎬 Status Video Maker` aur `🎬 Clip Maker`-type emoji **asli tools** hain — wo waise hain.

Tests: `tests/test_v89.py` me 11 naye/rewritten checks — `toolvid` string poore
`bot.py` me (comments chhod ke) nahi milna chahiye, `has_video`/`video_urls`/
`video_caption` import nahi hone chahiye, `send_tool_video`/`tool_tutorial_kb`/
`TUTORIAL_NOTICE` naam nahi hone chahiye, `HELP_NOTICE` me "video" shabd nahi,
copy me "/refer" ka waada nahi. `tests/test_v59.py` ka symbol bhi update kiya.

**Poora suite: 36 files, 3259 PASS / 0 FAIL** (`test_v89` 119/0, `test_v59` 237/0,
`test_v84` 95/0, `test_v88` 124/0, `test_v50_core` 97/0).

## Osint Hub (`osint-api-hub.onrender.com`) — v2.8.6, usi GitHub se auto-deploy

1. **Privacy bug:** code me *doosre aadmi ka demo hub* default `UPSTREAM_BASE` tha
   (`osint-apis-hub.onrender.com`) — matlab bina kuch set kiye users ke GSTIN/phone/
   vehicle numbers us anjaan server par jaate the. Ab default khaali = **kuch bahar nahi jata**.
2. **Khota key checker:** aapki saved key 7 char ki `GST/…` thi, aur purana checker sirf
   3 exact words ("", "Demo", "KEY") jaanta tha → isliye wo "asli key" lagti thi, har
   request 45 s wait/`Invalid API key` khati thi aur `/health` me **558 skipped calls**
   likhe the. Ab lambai+format heuristic (`/`, `:`, khaali, 12 se chhota = kachra).
3. **Auto-off:** 3 baar lagataar invalid key = us process me upstream band (har 15 min
   baad dobara probe nahi) — cold Render instance bekar me nahi jaagta.
4. **Aapke liye sabse bada fix:** provider keys ab **hub ke dashboard → Settings** se
   lagti hain (`numinfo_provider_key`, `gst_provider_key`, `vehicle_provider_*`) —
   Render env se jaane ki zaroorat nahi. `/admin/env/status` bhi ab settings dekhta hai.
5. `/health` ka note ab sach likhta hai: *manually OFF* / *auto-off* / *base set nahi* /
   *key invalid* / *ok*.
6. Live settings maine theek kar diye: `upstream_enabled=0`, `upstream_key=""`,
   `upstream_base=""` → `/health` me `skipped_calls: 0`.

Poora step-by-step (numverify.com signup, gstinapi.in signup, kaunsa field me kya
daalna hai, `/health` kaise padhna hai): **`HOW-TO-KEYS.md`** (hub repo me).

> Security note: aapka hub admin password chat me aa gaya tha — dashboard → Settings →
> `admin_password` se badal lijiye.
