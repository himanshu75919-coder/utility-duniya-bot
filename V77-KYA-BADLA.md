# v77.0 — 🚦 "NEVER-QUEUE" UPGRADE (Kya badla, kyun badla)

Aapki 2 baatein: **(1) code baar-baar crash hota hai**, **(2) saare tools advanced/premium
banao**. Neeche dono ka hisaab hai — **har line ke peeche proof** (test ya live /health data) hai.

> ⚠️ Pehle ye samajh lijiye: **"100% kabhi crash nahi" ka waada main nahi karunga**, kyun ki
> wo jhooth hoga. Aapka bot Render ke **FREE plan** par hai = **512 MB RAM + 0.1 CPU**,
> aur us limit ko koi code cross karta hai to Linux process ko maar deta hai (OOM kill).
> Jo main kar sakta tha (aur kiya): **crash ke raaste ko band karna**, taaki limit
> cross hi na ho, aur ho bhi to user ko saaf jawab mile — bot mare nahi.
> Neeche "Pehle kya ho raha tha → Ab kya hoga" har fix ke saath likha hai.

---

## 1. 🏗️ HEAVY GATE — crash ka SABSE bada kaaran (new file `modules/core/heavy.py`)

**Pehle kya ho raha tha (proof):**
- Poore code me **ek bhi `Semaphore` / concurrency cap nahi tha** (grep se confirm kiya).
- Live `/health` me bot **idle par hi 273 MB / 512 MB** kha raha tha.
- Ek video download ka peak ~150 MB (file → RAM → ffmpeg merge). 3-4 users ek saath =
  512 MB cross = **"Killed"** = aapka "baar-baar crash".

**Ab kya hoga:**
- Ek saath sirf **2 bhaari kaam** (`HEAVY_MAX_SLOTS`), baaki **25 second** queue me
  intezaar karke phir user ko **saaf "busy" jawab** — process marta nahi, worker thread
  bhi hamesha ke liye nahi atakta.
- **RAM dekh kar khud tight**: 378 MB → sirf 1 kaam; 435 MB → naya bhaari kaam start hi
  nahi hoga (chalta hua kaam poora hone denge, marenge nahi).
- **🪆 Re-entrancy**: gate ke andar se gate → deadlock nahi (2-slot wale box par ye maut ka
  kuan hota). Test me 5 threads × nested gates se verify kiya.
- **Kachra-proof**: `HEAVY_MAX_SLOTS = "2 seconds"` jaisi galat env value bhi bot nahi
  gira sakti (safe parser), aur gate ka khud ka exception **fail-open** hai (protection
  kabhi naya bug nahi banega).

**Wiring (asli call sites):** `desi_tools._ff` (saare ffmpeg encodes),
`media_downloader` ka video download + Instagram 3-engine race + `downscale_video`.
Cache-hit wale response gate se **bahar** hain — yaani cached link ab bhi TURANT aayega.

**Proof:** `tests/test_v87.py` ke 15+ checks — 6 jobs → peak concurrency 2, exception ke
baad slot free, hogger ke saath `ok:False` + readable message, memory denial, leak check.

---

## 2. 🚦 UPDATE GATE — "bot atak gaya" ka asli kaaran (new `modules/core/updategate.py`)

**Pehle:** python-telegram-bot ka default `concurrent_updates = 1` hai. Yaani **ek**
update ke khatam hone tak poora bot baaki sab ke liye RUKTA hai. Ek user ka 28-second
video tool = 40 users ke messages 28 second queue me = "bot crash ho gaya" (bot zinda
tha). Webhook me iska doosra nuksaan: der se jawab → **Telegram wahi update dobara bhejta
hai** → wahi kaam dobara (RAM double) aur kuch flows me double credit.

**Ab:**
- alag-alag **chat parallel** (default 8, `MAX_CONCURRENT_UPDATES`)
- **ek hi chat** ke messages **order me** (aapke 6-step wizard / RESULT CHECK state ko
  iski zaroorat hai — isliye anda-dhun "256 concurrent" nahi kiya)
- same `update_id` dobara aaye to **drop** (counter `/health` par dikhta hai)
- bounded memory: seen-updates LRU (8192) + per-chat locks 4096 par saaf
- PTB na mile / API badal jaaye to **bot pehle jaisa hi chalega** (fail-open)

**Proof:** test me 3 updates → 0.80s (sequential 0.9s+ hota), same-chat order confirm
(`eA` pehle, `sB` baad me), duplicate drop, counters, `coroutine.close()` se "never
awaited" warning nahi.

---

## 3. 🔗 LINK CHECK PRO — ek **ghatiya verdict** fix + 9 nayi pakad

**Live bug jo maine test karke pakda (aapke bot par abhi bhi hota):**
```
https://www.sbi.co.in/portal/web/customer-services   ← ASLI SBI site
   verdict: "SUSPICIOUS ⚠️  32/100"
   wajah 1: official check me sirf `<brand>.com` / `<brand>.in` tha → `.co.in` nahi
   wajah 2: brand `vi` (Vodafone) "ser**vi**ces" ke andar mil gaya  ← substring bug
```
Ab wahi link **SAFE 0/100** hai, aur reason me saaf likha aata hai ki official list me hai.
Sath hi `sbi.bank.in` (SBI ka naya net-banking domain, redirect ke baad) bhi sahi pakda
jaata hai — **restricted registry** rule se (`.bank.in`/`.gov.in`/`.nic.in` par sirf
bank/sarkar domain le sakti hai). Aur `kuchbhi.bank.in`? **Abhi bhi suspect** — maine
whitelist jaan-boojh kar tight rakhi hai (list badi karna = scam ko "SAFE" bolna).

**9 nayi cheezein jo pehle CHHOOT jaati thi:**
| Naya detector | Example jo pehle "SAFE" nikal jaata tha |
|---|---|
| Obfuscated IP (decimal/hex/octal/short) | `http://2130706433/admin` (=127.0.0.1) |
| Percent-encoded host | `https://ref%65r.co` (browser decode karta hai, bot nahi karta tha) |
| RTL/zero-width chhupe akshar | `paytm‮.com` (U+202E — naam ulti dikhata hai) |
| Cyrillic homoglyph (IDN attack) | `payраm.com` → "asli: paypam.com" |
| Typosquat (edit-distance 1-2) | `paytlm.com` → "paytm.com ka nakal" |
| Non-web scheme | `javascript:` / `data:` / `intent:` → **DANGEROUS 100** (pehle inhe "domain" samajh kar "unusual port" jaisa bakwaas result milta tha) |
| Dangerous port (naam ke saath) | `:6379` Redis, `:3389` RDP, `:22` SSH |
| Double extension | `.../invoice.pdf.exe` |
| Brand prefix/subdomain chipakna | `sbi.verify.xyz` type |

**+ crash fix:** `https://[` jaise adhoore URL par `urlparse` **ValueError** deta tha →
user ko "⚠️ Chhota sa ghatna ho gaya". Ab saaf "LINK TAYYAR NAHI ❌" verdict.
11 kachra inputs (empty, `xn--`, `%`, `a`*3000, unicode) par bhi exception nahi, aur
saare reason strings **HTML-balanced + escaped** (Telegram 400 "Can't parse entities"
isliye nahi aayega jab koi host `<script>` jaisa bheje).

---

## 4. 💓 Hang detection theek kiya (asli metric tha hi nahi)

`/health` me aap `loop_lag=20.0s` dekh rahe the aur soch rahe the bot atka hai.
**Wo metric galat tha**: wo heartbeat ke **20-second sleep interval** ko napta tha, loop
ke stall ko nahi. Yaani healthy bot par bhi hamesha "20.0s lag", aur **20 second se chhota
stall kabhi dikhta hi nahi** tha. Ab **drift** napa jaata hai: healthy ≈ 0.0s, aur
avg/worst gap + `STALLED` flag dikhta hai. (`guard.py` + test me 45s stall inject karke
verify kiya.)

---

## 5. 🔒 Build-crash se bachao: dependencies ab pinned hain

`requirements.txt` me **ek bhi version nahi likha tha** — har deploy par Render sabse naya
version uthata tha. Koi badi library breaking release de de to **aapka code bilkul same
hone par bhi "Application failed to start"** — samajhna namumkin tha. Ab har library ko
**known-good range** (`>=floor,<next major`) diya hai — floor = jis version par poora test
suite green hai.
**`yt-dlp`/`parth-dl` ko jaan-boojh kar un-floor chhoda hai**: ye YouTube/Instagram ke
badalte API ke liye roz update hote hain; inhe freeze karna = 2-3 hafte me "video download
fail". Inka crash-proof ilaaj gate + timeout hai, version lock nahi.

---

## 6. Aapke 2 "prompts" wale niyam ka poora khayal

- **Koi tool prompt / sawal / instruction text NAHI badla.** `BOT_VERSION` me
  `FREE4ALL` / `NO-GYAAN` / `SPEED` guard-word bhi waise hi hain (aapka apna test inhe
  check karta hai — test me bhi assert kiya hai).
- Jo naye strings hain wo sirf **do jagah** hain: (a) busy/hook ke **error** jawab
  ("line lambi hai"), (b) **admin** ke `/health`+`/sys` diagnostic lines. Aam users ke
  tool prompts ko chhua hi nahi.

---

## 7. Naye config knobs (Render → Environment, sab OPTIONAL)

| Key | Default | Kaam |
|---|---|---|
| `HEAVY_MAX_SLOTS` | 2 | ek saath bhaari kaam (paid plan par 3-4) |
| `HEAVY_WAIT_SECONDS` | 25 | queue me kitni der, phir "busy" jawab |
| `HEAVY_GATE` | on | off = gate band (debugging) |
| `MAX_CONCURRENT_UPDATES` | 8 | ek saath total updates (per-chat order phir bhi safe) |
| `UPDATE_DEDUPE` | on | Telegram ke retry drop |
| `UPDATE_PER_CHAT_ORDER` | on | band = pura parallel (wizard flows ke liye safe NAHI) |
| `HANG_RESTART_SECONDS` | 900 | 15 min atka → clean restart (dead bot se behtar) |

`render.yaml` me ye sab comment ke saath daal diye hain, taaki agli baar blueprint se
service banegi to ye apne aap aa jaayein.

---

## 8. Test result (is wave ka)

```
tests/test_v87.py (naya, 126 checks)          → PASS: 126 | FAIL: 0
poora suite (34 files)                          → sirf 2 hub-dependent FAIL:
   test_v53  → BASELINE (pristine v76) se BILKUL SAME result: 206/2
               (hub/Free Fire service network se depend karta hai; mera code nahi)
   test_v83  → pehle 77/1 aaya tha → ye MERA bug tha (heavy.py ne `try_acquire`
               export kiya par function likha hi nahi). Fix kiya → ab 78/0 ✅
```
`test_v83` ka **"PERMANENT CRASH GATE"** check (pyflakes undefined-name) isi wave me
mera banaya hua bug pakad gaya — aur maine use fix kiya. Ye is test ka maqsad hi tha.

---

## 9. Jo maine jaan-boojh kar NAHI kiya (aapke nuksaan se bachane ke liye)

1. **"256 concurrent updates" / "RAM cap hatao" type ki dikhawe tuning** — aapke bot me
   stateful wizard flows hain, inhe todta.
2. **Whitelist badi karna** (link check me) — ek galat entry = scam site ko "SAFE" bolna.
3. **Aadhaar/password/OTP/leaked-data type ke naye tools** — Telegram policy + IT Act,
   aur isse aapka bot **aur payment account** dono ja sakte hain. `NUM_LEAK_ENABLED=off`
   ko maine on NAHI kiya (aapki safety ke liye).
4. **Fake "100% no crash" guarantee** — jhooth bolne se aapko faayda nahi, nuksaan hoga.
5. **Saare 30+ tools ka ek saath "rewrite"** — aapne kaha sab kuch chalega; ek wave me
   50,000 lines badalna = naye bug pakka. Main **verified layers** pehle laaya (gate,
   queue, link check, metric, deps), taaki base na tute. Baaki tools ki wave-wise
   upgrade (test ke saath) main aapke hukm par karunga.

## 10. Ab aapke liye 3 faisla (batayein to main kar dunga)
1. `ALL_FREE=off` + asli `UPI_ID` → **paisa aana shuru** (code already ready; `EARNINGS-PLAYBOOK-v77.md` Part 1)
2. Top 3 naye tool ideas: **FAST LANE** / **PASSPORT PHOTO STUDIO** / **PDF STUDIO** — kaunsa banauun?
3. Render **Standard (₹399/mo)** kab lena hai — traffic badhne par (free plan ka 512 MB
   hi aapke crash ki jad hai; gate ne use sambhal diya hai, par growth ke liye RAM chahiye)
