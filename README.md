# ⚡ Utility Duniya Super-Bot — **v53.0 Premium Earning**

## 🆕 v53.0 me kya badla — **"PRO ENGINE" upgrade**

> Is release me **koi naya tool nahi**. Purane tools ko *live* test karke (asli API,
> asli UID, asli link par) andar se theek kiya gaya hai. Do niyam ab hard-coded hain:
> **bot jhooth nahi bolega**, aur **kaam na hone par credit nahi katega**.

| Tool | Pehle (measure kiya hua) | Ab (v53.0) |
|---|---|---|
| 🔥 **FF UID** | har UID par `Player not found`, **11s**, credit kat-ta tha | **asli data, 0.19s** — SAC region add (jahan asli players the), parallel scan + 6s deadline |
| 🎮 **BGMI UID** | dead server par bhi **1 credit** kat-ta tha | **availability probe** → `service_busy`, **credit nahi katta**, kabhi fake stats nahi |
| 📌 **Pinterest** | 6 results, **0 asli ** link | **8/8 asli pins** + original quality + **video pins** + `` resolve + pinner/repin metadata |
| 📄 **Web Scraper** | **22,515 words** (menu/ads/footer kachra) | **11,339 words saaf article** + Markdown + author/date/site + reading time + `.txt` file |
| 📧 **Temp Mail** | poora body dump, OTP dhoondhna user ka kaam | **OTP auto-detect 10/10** + false-positive guard + inline buttons + sirf naye messages |
| 📦 **App Finder** | **8 blind guessed URL**, 2 **piracy** sites | **Google Play se verified** metadata (dev/rating/reviews/downloads/icon) + F-Droid + iOS; nakli app → `found=False`, **credit nahi** |
| 📷 **QR** | color/logo params **ignore**, lamba text → **crash** | `make_branded_qr()` wired: **center logo**, **custom colors**, **contrast guard**; vCard ab **4 step** (naam/phone/company/email); WiFi special-char escape |
| 📊 **Observability** | **58 `except: pass`** — chup-chaap fail | `modules/core/telemetry.py` — calls/ok/fail/latency/cache/errors; **`/sys`** par health card + DEAD upstreams + worst tools |
| 🛡️ **Credit fairness** | fail par bhi credit kat-ta tha | **charge-on-success only** — `service_busy` / `found=False` / QR-fail ⇒ **no charge** |

**Removed (hamesha ke liye):** GetModPC + HappyMod piracy links App Finder se.

**Naya module:** `modules/core/telemetry.py`
```python
tel_note(tool, ok, ms, soft=False, error="", credit=True, cache_hit=False)
tel_health_card(max_rows=12)   # /sys ke liye HTML block
tel_snapshot() · tel_tool_stats(t) · tel_worst_tools(n) · tel_upstream_status()
is_soft_fail(result)           # credit rokne ka decision
```

**Engine API contracts (v53.0):**
```python
# modules/general_tools.py
make_branded_qr(text, *, fg="#111111", bg="#FFFFFF", logo_bytes=None, size=620, label="")
app_lookup(name, use_cache=True, max_results=5)   # -> {ok, found, query, apps[...]}
wifi_qr_data(ssid, password="", security="WPA", hidden=False)   # special chars escaped
vcard_data(name, phone, org="", email="", title="", url="", address="", note="")  # CRLF
build_upi_link(pa, pn, amt=None, note="", txn_ref="", mam="")   # ValueError on bad VPA

# modules/gaming_tools.py
ff_player_info(text, region="")   # region aliases + auto-detect internally
ff_regions() · ff_service_status(force=False) · bgmi_availability(force=False)

# modules/.py
pinterest_search(q) · pinterest_pin_detail(id) · pinterest_from_pin_link(link)

# modules/web_tools.py
scrape_public_text(url, markdown=True, use_cache=True)
  # -> {ok,title,desc,text,markdown,words,reading_min,paragraphs,author,date,site}

# modules/temp_mail.py
tm_create() · tm_poll(addr, token, seen_ids) · tm_messages(...) · extract_codes(...)
  # tm_poll -> {ok,count,new_count,messages,codes,new_codes,all_ids,expired}
```

**bot.py ke naye helpers:** `build_qr_image()` (branded QR + contrast guard + telemetry),
`_qr_logo_bytes()` (cached brand logo), `_hex_ok()`, `_qr_luminance()`,
`_telemetry_block()` (`/sys` card), `_pin_meta_line()` (pin caption).

**Naye env vars** (sabke default set — Render par kuch dalna zaroori nahi):
`PIN_SEARCH_COUNT` `PIN_TIMEOUT` `PIN_CACHE_TTL` `FF_SCAN_TIMEOUT` `FF_SCAN_DEADLINE`
`GAMING_TIMEOUT` `GAMING_STATUS_TTL` `SCRAPER_TIMEOUT` `SCRAPER_MAX_MB`
`SCRAPER_MIN_WORDS` `MAILTM_TIMEOUT` `MAILTM_BODY_CHARS` `APP_TIMEOUT`
`APP_CACHE_TTL` `APP_MAX_RESULTS` `TELEMETRY_MAX_TOOLS` `TELEMETRY_LATENCY_WINDOW`

> 📖 Poori detail (Hinglish, numbers ke saath): **`V50-KYA-BADLA.md`** → v53.0 section.
> 🔍 Audit trail: **`V53-AUDIT-REPORT.md`**

---

## 🆕 v52.3 me kya badla

### 🎮🔥 NAYA: GAME PLAYER INFO (BGMI UID + FF UID)
Dost ka game UID bhejo → **player ka naam, level, rank, K/D, last login** — sab **public in-game data**.
- 🔥 **FF UID**: Garena ke public profile data se (free API) — 13 regions (IND/BR/SG/US...) support
- 🎮 **BGMI UID**: best-effort public stats + official in-game guide (BGMI India ke liye free public API officially nahi hai — kabhi fake data nahi)
- ⚠️ "Private leaderboard" / real identity wala data **kabhi nahi** — sirf public in-game data

### 📌 NAYA: PINTEREST (image HD download)
- **PIN LINK** bhejo (app se copy link) → **original quality** image download
- **KEYWORD** bhejo → 6 public images dikhte hain → tap karke download
- Pinterest ka official CDN (i..com) se direct — koi API key nahi

### 📄 NAYA: WEB SCRAPER (public page → clean text)
Koi bhi public article/blog/news page ka link bhejo → poora text saaf format me (bada page = .txt file).
SSRF-protected — private/internal IPs kabhi nahi khulte.

### 📧 NAYA: TEMP MAIL (disposable email + inbox)
`NEW` bhejo → ek-baar ka email ID (mail.tm free API) → kisi bhi jagah signup/OTP ke liye.
`INBOX` bhejo → messages yahan dikhte hain. Password bot generate karta hai, user ko sirf address dikhta hai. 30 din valid.

### 🪪 NAYA: AADHAAR EID STATUS HELPER (APNA EID)
Apna **14-digit Enrolment ID (EID/EPIC)** bhejo (Aadhaar acknowledgement slip ke top par) →
bot **ready SMS** bana deta hai: `UID STATUS xxxxxxxxxxxxxxxx` → **51969** pe bhejo → official UIDAI status.
- ✅ 100% legal: sirf APNA EID, official CAPTCHA-free SMS service + official web link
- ❌ Koi data leak nahi, koi CAPTCHA bypass nahi, kisi aur ka EID/Aadhaar nahi

> ⚖️ Teeno + baaki sab **100% legal** — sirf public data + official sources.
> Saare 6 naye tools **premium (1 credit/use)** hain.

### 🧪 Tests (5 suites, sab green)
```bash
python3 tests/test_v50_core.py            # 106 checks — core layer (SSRF/cache/rate-limit) + live APIs
python3 _selftest_v50.py                  # 208 checks — v52.3 tools + saare purane sections
python3 _verify_v49.py                    # 128 checks — purana regression suite
python3 tests/test_privacy_safe_lookup.py #  14 checks — privacy/IMEI/webhook guards (unittest)
python3 tests/test_v53.py                 # 277 checks — v53.0 pro-engine suite (LIVE internet par)
#                                         # ─────────
#                                         # 733 checks · 0 fail
```

---

## 🆕 v52.2 me kya badla

### 🌍 NAYA: DOMAIN OSINT (🌐 IP/DOMAIN tool ka upgrade)
Domain bhejo → **full public OSINT report**: whois (official RDAP registry), DNS records (A/AAAA/MX/NS/TXT),
**subdomains** (Certificate Transparency / crt.sh), + primary A-record ki **IP location/ISP/hosting**.
IP bhejo → wahi purana IP info card. Sab public/official sources — koi private info nahi.

### 🏦 NAYA: UPI VERIFY
VPA (UPI ID) bhejo → **format valid?** + **kis bank ka handle hai** (NPCI public bank codes se).
Sirf public info — linked mobile/account/holder naam **kabhi nahi** dikhega (wo publicly exist hi nahi karta).

### 📡 NAYA: TG PUBLIC INFO
Public `@username` bhejo → **naam + bio + member count** (public channels/groups Bot API `getChat` se,
user profiles t.me public page se). Sirf public info — private members/phone nahi.

> ⚖️ Teeno **100% legal** — sirf public data + official APIs (RDAP / DNS / Bot API / t.me).
> Premium hain (1 credit/use) — baaki info tools jaise hi.

### 🧪 Tests (3 suites, **414 checks** — sab green)
```bash
python3 tests/test_v50_core.py     # 106 checks — core layer (SSRF/cache/rate-limit) + live APIs
python3 _selftest_v50.py           # 179 checks — tools + deletion + TTS + GOVT-removed + YT quality + v52.2 tools
python3 _verify_v49.py             # 128 checks — purana regression suite
```

---

## 🆕 v52.1 me kya badla

### 🗑️ GOVT SERVICES PERMANENTLY delete (user order)
v52.0 me jo 4 govt tools aaye the (Court Case Status / Sarkari Result / Govt ID Status / Job Tracker)
— user ke order par **poore delete** ho gaye (button + engine module `modules/govt_tools.py` +
premium entry + rate-limit + tests + docs, sab). `ECOURTS_API_KEY` env bhi hata diya.
Purane keyboard ke users ko saaf "Govt Services hata diya gaya" message milta hai.

### 🎞️ NAYA (v52.0 se, abhi bhi hai): YOUTUBE QUALITY SELECTOR (Video Downloader)
YouTube link bhejo → **1080p / 720p / 480p / 360p buttons** aayenge → jo dabao wahi quality milegi.
Pipeline: pehle direct download (agar YouTube server IP allow kare), warna hub 1080p + **bot-side
ffmpeg downscale** (360p waghera). 1080p = original (koi re-encode nahi).

### 🚀 SPEED FIXES (premium feel)
| Kya | Detail |
|---|---|
| ⚡ **Self-ping keepalive** | Bot ab apna hi public `/health` ping karta hai (Render LB ke through) → 15-min sleep **nahi** hota → **cold start sirf pehli baar**, baad me bot ~instant respond |
| 🖼️ **Welcome photo cache** | `/start` par welcome photo ab file_id (CDN) se turant aati hai — har baar dobara upload nahi |

### 🧪 Tests (3 suites, **356 checks** — sab green)
```bash
python3 tests/test_v50_core.py     # 106 checks — core layer (SSRF/cache/rate-limit) + live APIs
python3 _selftest_v50.py           # 122 checks — tools + 6-tool deletion + TTS + GOVT-removed + YT quality
python3 _verify_v49.py             # 128 checks — purana regression suite
```

### ⚙️ Naye env vars (Render me)
| Var | Value | Kyu |
|---|---|---|
| `BOT_SELF_URL` | `https://utility-duniya-bot.onrender.com` | Self-ping speed fix |

---

## 🆕 v51.3 me kya badla

| Kya | Detail |
|---|---|
| 🛡️ **Deploy "Conflict" error ab friendly** | Deploy ke dauran purana + naya instance ~30 sec ek saath chalte hain → Telegram "Conflict" deta tha → log me scary red ERROR aata tha. Ab: ek saaf **NOTE** log hota hai (auto-heal message), user ko koi "ghatna" message nahi, duplicate spam nahi. Bot khud 1-2 min me theek ho jata tha — wo behavior wahi, bas log ab saaf. |
| 🏷️ **Log me asli version** | Purana hardcode "v30 Ultra" banner the — ab startup line me **asli BOT_VERSION** dikhta hai (kaunsa version chala, turant pata) |
| ✅ **Tests** | 3 suites, **338 checks sab green** (4 naye conflict-handling checks) |

## 🆕 v51.2 me kya badla

| Kya | Detail |
|---|---|
| 🗣️ **NAYA TOOL: TEXT → HINDI VOICE** | Media Studio me — text bhejo (max 1500 letters) → **ekdum real desi Hindi awaaz me MP3** (2 voices: Madhur male / Swara female). Engine: `edge-tts` (Microsoft neural, **free, koi API key nahi**). 1 credit/use. |
| ✅ **Tests** | 3 suites, **334 checks sab green** (naye 13 TTS checks: live male/female MP3 generation + wiring) |

**Ek hi bot me 27+ kaam:** video download, channel auto-forward, photo/document banane wale tools,
sarkari kagaz, bank statement → Excel, media studio (MP3 / status video / karaoke), info tools
(IMEI / vehicle / number / IFSC / pincode / IP), QR, link safety, aur
**VIP + payment system (ab SAARE tools premium)**.

Poora bot ka **text Hinglish** me hai — short prompt + example ke saath, taaki naya user bhi bina
padhe samajh jaye.

> 📖 **Non-technical ho?** [`V50-KYA-BADLA.md`](V50-KYA-BADLA.md) padho — aasaan bhasha me, bina jargon.

---

## 🆕 v51.1 me kya badla (Premium Earning Edition)

### 🗑️ 6 tools PERMANENTLY delete (code + bot + GitHub + videos, sab se gayab)
| Tool | Note |
|---|---|
| 🧮 **EMI / INTEREST CALC** | Menu button, 3-step flow, calculator engine (bank EMI + chakravritti vyaaj) — poora gayab |
| 🖼️ **SITE SCREENSHOT** | HD + Full Page dono, engine + SSRF wiring — poora gayab |
| 🖼️ **IMAGE→PDF** | Multi-photo PDF + A4, `on_pdf_cb` handler — poora gayab |
| 🔒 **PRIVATE CHANNEL SETUP** | Cloner ka private-help flow + "Poori Guide" button — poora gayab |
| 🆔 **ID & USERNAME FINDER** | `me`/forward/@username + 5-platform checker engine — poora gayab |
| 🌦️ **WEATHER / MAUSAM** (v51.1) | Menu button, prompt, Open-Meteo engine (`weather_report`, `WMO_WEATHER`, city aliases) — poora gayab |

> Purane keyboard ke users ko **tool ke hisaab se saaf "hata diya gaya" message + replacement suggestion** milta hai (crash nahi) + `/refresh` se naya menu.

### 💰 SAARE tools AB PREMIUM (earning model)
| Kya | Detail |
|---|---|
| 👑 **Sab tools premium** | Naye user ko **25 free credits** (1 use = 1 credit). Credits khatam → VIP lo. |
| ♾️ **VIP = unlimited** | 30d ₹49 · 60d ₹89 · 90d ₹129 · 120d ₹169 · Lifetime ₹199 — poora bot unlimited. |
|  **Vehicle key fix** | Ab `rto` action premium gate se sahi pass hota hai (pehle key mismatch thi). |
| 🛡️ **Credit spend** | Har tool ke result par 1 credit deduct (fail hone par credit nahi jata). |

### 🧪 Tests (3 suites, 356 checks — sab green)
```bash
python3 tests/test_v50_core.py     # 106 checks — core layer (SSRF/cache/rate-limit) + live APIs
python3 _selftest_v50.py           # 122 checks — tools + 6-tool deletion + TTS + GOVT-removed + YT quality + DB/credits
python3 _verify_v49.py             # 128 checks — purana regression suite
```

---

## 🆕 v50 Core Layer me kya badla (v50.1–v50.3)

| Kya | Detail |
|---|---|
| 🚨 **Bot freeze fix** | 9 tools (IP / IFSC / Pincode / Area / Vehicle / URL-short / Screenshot) blocking HTTP call kar rahe the — jab tak wo chalte, **poora bot sab users ke liye dead** tha. Ab sab `asyncio.to_thread` me. Screenshot par 30s tak freeze hota tha. |
| 🔒 **SSRF guard** | `expand_url` user ka link seedha fetch karta tha — `http://169.254.169.254/` (cloud metadata) ya `127.0.0.1` se server ke secrets nikal sakte the. Ab input **+ har redirect hop** validate hota hai. |
| ⚡ **Caching** | IFSC / pincode / IP / area / GST / PAN ab cached. Repeat query **instant**, API quota bachti hai. |
| 🛡️ **Rate limiting** | Har tool par per-user limit (central gate, `bot.on_text` me ek jagah). Pehle koi bhi spam karke API quota kha / upstream IP block karwa sakta tha. Admin + VIP bypass. |
| 🐛 **Area Search fix** | Bot ka apna help `Patna GPO` / `Kankarbagh` / `Boring Road SO` suggest karta tha — **teeno API par fail hote the**, aur jo milta tha wo galat state ka hota tha. Ab suffix-stripping + score-based ranking. `Patna GPO` → **800001 Bihar** ✅ |
| 🎯 **GST/PAN validation** | Galat format ab **bina network** pakda jata hai (pehle 60s hub call jata tha). State-code aur PAN holder-category bhi check hote hain. |
| 📡 **`/sys` command** | Admin ke liye live health: uptime, RAM, cache hit-rate, rate-limiter counters, mode. |
| 🧪 **107 naye tests** | `tests/test_v50_core.py` — asli `on_text` ko mocked Update ke saath chala kar rate-limit gate, SSRF, caching, validators verify karta hai. |

### Naya: `modules/core/`

Bot ka professional foundation layer — koi naya third-party dependency nahi, Render par kuch
install nahi karna padega.

| Module | Kaam |
|---|---|
| `core/net.py` | Ek hi HTTP layer: shared connection pool, **har request par default timeout**, backoff retry, 429/`Retry-After` handling, response size cap, `is_safe_url()` SSRF guard |
| `core/cache.py` | Bounded thread-safe TTL cache + `cached_call()` — LRU eviction, negative-result short TTL, hit-rate stats |
| `core/limiter.py` | Per-`(user, action)` sliding-window rate limiter, bypass support, auto-cleanup (memory leak nahi), env se configurable |

> ⚠️ **Gotcha:** `net.py` me transport-level retry **jaan-boojh kar OFF** hai. urllib3 ka
> retry `timeout` ko multiply kar deta tha (`timeout=2` → 6 second wait). Retry ka ek hi
> malik hai: `_request()` ka apna loop.

### Env (optional — sab ke sensible defaults hain)

```bash
# Rate limits: RATE_LIMIT_<MODE>="limit:window"
RATE_LIMIT_IFSC=15:60
RATE_LIMIT_SHOT=4:120
# Cache
INFO_CACHE_SIZE=4096
INFO_CACHE_TTL=1800
# HTTP
NET_TIMEOUT=20
NET_MAX_MB=150
```

### Tests

```bash
python3 tests/test_v50_core.py     # 106 checks — core layer (SSRF/cache/rate-limit) + live APIs
python3 _selftest_v50.py           # 122 checks — tools + 6-tool deletion + TTS + GOVT-removed + YT quality + DB/credits
python3 _verify_v49.py             # 128 checks — purana regression suite
```

---

## 🆕 v50 me kya badla (Premium Pro)

> ⚠️ **v51/v51.1 note:** v50 me jo tools aaye the — 🧮 EMI/INTEREST CALC, 🖼️ SITE SCREENSHOT, 🖼️ IMAGE→PDF,
> 🆔 ID & USERNAME FINDER — wo **v51 me permanently delete** ho gaye (upar dekho). 🌦️ WEATHER bhi **v51.1 me permanently delete** ho gaya.

### 🐛 BUG FIXES (real problems)
| Kya | Problem |
|---|---|
| 🆔 **ID Finder forward** | Forward karne par ID nahi milti thi (help text aa jata tha) — ab forward sabse pehle process hota hai |
| 🖨️ **8-in-1 sheet** | Photos 1.17×1.5" chhoti print hoti thi — ab **EXACT 3.5×4.5cm** (413×532px @300DPI) |
| 📸 **Passport photo size** | Kabhi 20KB se chhoti file banti thi (portals reject karte hain) — ab 20-50KB window pakka |
| 📱 **Toll-free numbers** | 1800-… (11 digit) US country code ban jata tha — ab +91 India |
| 🛠️ **Admin tutorial button** | Button par crash (galat HTML tag) — ab kaam karta hai + link dikhata hai |
| 📢 **Broadcast** | `<` jaise character par poora broadcast fail hota — ab plain-text fallback |
| 🗄️ **Database** | "database is locked" crash ka risk — `busy_timeout` laga |
| 🧹 **Dead code** | 70 lines duplicate admin code delete kiya |

### ⚡ SPEED + PRO UPGRADES
| Kya | Kya badla |
|---|---|
| 🔗 **URL Shortener** | Ab 6 providers **PARALLEL** chalte hain — 10-45s ki jagah **~1 second** |
| 🔍 **Link Check** | NAYA **domain-age** signal (free RDAP) — 30 din se naya domain = automatic risk +20. Phishing feed scan bhi ab instant |
| 🏦 **Bank PDF** | Password wale PDF par pehle **khud common passwords try** karta hai — aksar user ko matlaagne ki zaroorat hi nahi |
| 👤 **Error handling** | Koi ghatna ho to user ko saaf message milta hai (pehle chup-chaap fail hota) |

✅ **Test suite:** `_selftest_v50.py` = **122 checks** (tools, 6-tool deletion, TTS, GOVT, YT quality, conflict-fix, DB/credits)

---

## 🆕 v49 me kya badla

| Kya | Detail |
|---|---|
| 🗑️ **3 faaltu tools hate** | 🎬 CLIP MAKER · 🔓 LINK BYPASS · 📈 INTEREST CALC — menu, code, video, tutorial: sab se gayab |
| 🗣️ **Poora bot Hinglish** | Har prompt ab short Hinglish + `📌 Jaise:` example. Lambi English instructions hata di gayi |
| 📲 **IMEI tool fix** | Hub ka naya TAC endpoint + phone ki photo + poori spec sheet + `.json` file. Privacy: sirf pehle 8 digit dikhte hain |
| 🔌 **Hub URLs sahi** | Bot ab `osint-api-hub.onrender.com/api` (naya hub) use karta hai — purane dead host nahi |
| 🧹 **Saaf-safai** | 9 bekaar tutorial videos, 14 purane dev-note files aur 2 dead module (`clip_maker`, `ai_brain`) delete |
| ✅ **Test suite** | `_verify_v49.py` = **93 checks** (3-tool removal, 29 menu buttons, Hinglish texts, 26 live API checks, DB/credits) |

---

## 🚀 Deploy (Render) — 4 step

1. GitHub par push karo.
2. Render → apni service → **Manual Deploy** → **Clear build cache & deploy**.
3. Environment tab me ye 4 cheezein zaroor honi chahiye:
```
BOT_TOKEN=BotFather se mila token
ADMIN_ID=aapki Telegram user ID      (owner — unlimited, free)
UPI_ID=aapka@upi                     (VIP payment ke liye)
UPI_NAME=Utility Duniya
```
4. Telegram me `/start` bhejo → menu aa jayega. `/premium` → VIP plans. `/admin` → admin panel.

> 🚨 **Deploy ke baad ek baar `/refresh` (ya `/newmenu`) bhejo** — isse sab users ko naya
> keyboard mil jata hai (purane hataye gaye tools ke buttons hat jayenge).

---

## 💎 Credits + VIP ka hisaab

| Cheez | Kitna |
|---|---|
| Naya user | **25 credits free** (one time — roz nahi milte) |
| Premium tools | **1 use = 1 credit** |
| Baaki saare tools | **FREE** (koi credit nahi) |
| VIP (paid) / Owner | **Unlimited** — premium tools bhi free |

**Premium tools:** 📥 Video Downloader · 📱 Number Info · 🔄 Channel Cloner · 🔒 Private Channel Setup ·
🏦 Bank Statement PDF→Excel · 📜 Document Suite · ⚡ Media Studio · 🚗 Vehicle Info + Challan · 📲 IMEI / Phone Details.

VIP lene ka tarika: `/premium` → plan chuno → QR se paisa → **Step 2**: UTR bhejo (12 digit) →
**Step 3**: screenshot bhejo → admin verify karke activate kar dega. Status: `/mypay`.
**Direct VIP (bina payment):** `/admin` → plan select → `/activate <user_id>`.

---

## 🧰 Poori tool list (v49)

**Download / forward**
📥 Video Downloader (Instagram, YouTube, FB, X, TikTok, Pinterest… 20+ sites) · ⚡ Terabox/Mediafire/GDrive resolver ·
🔄 Channel Cloner — manual + **full-auto** (source → target, caption/watermark/thumbnail) · 🔒 Private Channel Setup

**Photo / document**
📸 Govt Exam Passport Photo (naam + DOP stamp) · 🖨️ 8-in-1 Print Sheet · 📄 Doc/Marksheet PDF Compress (100KB-500KB) ·
🖼️ Image → Multi-page PDF · 🏦 **Bank Statement PDF → Excel** · 📜 **Document Suite**
(kirayanama, affidavit, notice 138, bayana/pakki rasid, rin shodh, naam sudhar + **registry total cost** + **bigha/kattha converter**)

**Media studio**
⚡ YouTube→MP3 · 🎬 Status Video (9:16) · 🎧 Ringtone cutter · 🎤 Karaoke · 🔊 8D · 💥 Bass boost ·
🗣️ Voice change (kid / heavy / robot / ghost / gadget / echo) · ✂️ Trim · 🗜️ Compress · 🎼 Video→MP3

**Info**
🚗 Vehicle Info + Challan · 📲 IMEI / Phone Details (device + poori spec sheet + .json) · 📱 Number Info
(operator/circle/type + links) · 🏦 IFSC branch · 📮 Pincode + post offices (area ke naam se bhi) ·
🆔 ID & Username Finder · 🌐 IP/Domain · 📦 App Finder (8 trust stores)

**Chhote tools**
📷 QR (link/text, WiFi, contact) · 🔗 URL Short · 🔍 Link Check (scam detector) ·
🖼️ Website Screenshot (HD + full page) · 🏛️ Sarkari Seva Portals · 👤 My Account ·
❓ Help/Tutorial · 💎 VIP · 🎁 Refer & Earn (5 refer = 30 din VIP)

---

## 📖 Tutorial

- Bot ke andar: har tool ke neeche **🎬 video button** (30 sec video) + ❓ **Help/Tutorial** me saare video.
- Text tutorial: **`TUTORIAL.md`** (aur bot ka telegra.ph page — `/tutrefresh` se refresh).
- Admin commands: `/admin` (dashboard), `/payments` (pending list), `/activate <id> [days]`,
  `/credits <id> [n]`, `/refresh` (sabko naya keyboard), `/tutrefresh`, `/imeistatus`.

---

## 🗂️ Files

```
bot.py              — main bot (handlers, menus, credits, VIP, admin, kagaz flow, media studio flow)
database.py         — SQLite (users, credits, payments, VIP, referrals, cloner config)
modules/
  channel_cloner.py — cloner engine (auto-forward, branding, albums, floodwait retry)
  cloud_tools.py    — terabox / mediafire / gdrive direct-link resolvers
  cyber_studio.py   — passport photo, print sheet, PDF compress (grayscale/A4)
  desi_tools.py     — bank statement parser, kagaz PDFs, registry cost, land units, media studio (ffmpeg)
  general_tools.py  — QR, vCard, WiFi QR, image→PDF, screenshot, app store links
  media_downloader.py — yt-dlp / hub engine (20+ sites) + YouTube 1080p
  osint_tools.py    — IFSC, pincode, phone info, IP, username finder
  api_hub.py        — aapke OSINT API hub ke saare endpoints ka wrapper
  imei_lookup.py    — IMEI → brand/model/spec sheet (TAC privacy included)
  vehicle_challan.py— live vehicle RC + challan report
  render_health.py  — Render keepalive / health + webhook URL helper
  payguard.py       — payment proof check (UTR + duplicate + screenshot analysis)
  sarkari_hub.py    — government portals ke direct links
  tutorial_hub.py   — tutorial page (telegra.ph) + video links
  vip_payment.py    — VIP plans, UPI QR, payment flow
requirements.txt    — saare packages
TUTORIAL.md         — text tutorial (bot ke andar se bhi link milta hai)
1-PADHO-PEHLE.md    — sabse pehle ye padho (setup + zaroori baatein)
RENDER-ME-KYA-DALNA-HAI.md — Render me kaun-kaun se env var dalne hain
tutorial_videos/    — har tool ka 30 second video (CDN se serve hota hai)
```

---

## 🧪 Khud test karo

```bash
python3 _verify_v49.py        # 93 checks: menu, Hinglish text, live API, DB/credits
python3 _selftest_v45.py      # hub integration (61 checks)
python3 _selftest_v48.py      # video size / truncated-file checks
python3 _selftest_imei.py     # IMEI flow (70 checks)
python3 _selftest_vehicle.py  # vehicle + challan (78 checks)
python3 -m pytest tests/ -q   # privacy tests
```

---

## ⚠️ Zaroori baatein

- **Koi AI tool nahi** — sab deterministic (Render 512MB me aaram se chalega).
- **Legal:** Number info = live carrier/type + links (kisi ki niji jaankari nahi). Kuch hub endpoints
  owner ki marzi se off hain — bot us case me saaf Hinglish message deta hai, credit nahi katta.
- **Vehicle/challan** hub par disabled ho to bot graceful message + official portal link deta hai.
- **Copyright:** downloader sirf public links ke liye — kisi ka paid content dobara bechna galat hai.
- Payment proof sakhti se check hota hai: UTR format + duplicate + screenshot asli hai ya photo.
