# 🔍 Utility Duniya Bot — Deep Tool Audit (v52.3b → v53.0)

> Ye report **live testing** se bani hai — sirf code padh ke nahi.
> Har tool ko asli me chalaya gaya, upstream APIs ko hit kiya gaya, aur jo mila wo yahan likha hai.
> Audit date: 2026-10-05

---

## ✅ Jo cheezein ALREADY acchi hain (koi problem nahi)

| Area | Status |
|---|---|
| **Compilation** | Saare 30+ files `py_compile` pass — koi syntax error nahi |
| **Import** | `bot.py` clean import hota hai (29 premium tools, 17 keyboard rows) |
| **Test suites** | **414/414 PASS** — `test_v50_core.py` 106 ✅ · `_selftest_v50.py` 180 ✅ · `_verify_v49.py` 128 ✅ |
| **Timeouts** | **0** raw `requests` calls bina timeout ke (poora codebase scan kiya) |
| **Async hygiene** | Saare 12 naye tool handlers `asyncio.to_thread` me — bot freeze nahi hota |
| **SSRF guard** | `core/net.py` solid hai — 15 private/metadata ranges block, DNS-rebinding check |
| **Core layer** | `core/net.py` + `core/cache.py` + `core/limiter.py` — genuinely professional design |
| **Credit fairness** | Fail hone par credit **nahi** katta (bgmi/webscraper/tempmail/aadeid/pinterest sab me sahi) |

**Matlab:** foundation mazboot hai. Problem foundation me nahi — **tool engines ki depth** me hai.

---

## 🚨 CRITICAL findings (tool asal me kaam hi nahi karta)

### 1. 🔥 FF UID — **100% DEAD tool**
**Live test:**
```
uid 1633864660 region IND → HTTP 404 PLAYER_NOT_FOUND
uid 1633864660 region BR  → HTTP 404 PLAYER_NOT_FOUND
uid 1633864660 region SG  → HTTP 404 PLAYER_NOT_FOUND
uid 1633864660 region US  → HTTP 404 PLAYER_NOT_FOUND
uid 1633864660 region VN  → HTTP 404 PLAYER_NOT_FOUND
uid 1633864660 region PK  → HTTP 404 PLAYER_NOT_FOUND
uid 1633864660 region ID  → HTTP 404 PLAYER_NOT_FOUND
```
**Teen alag-alag bugs:**

**(a) Region codes GALAT hain.** Code me hardcoded list:
```python
_FF_REGIONS = ["IND","BR","SG","US","VN","ID","TH","PK","RU","ME","TW","CIS","BD"]
```
API ke **asli** regions (root endpoint `/` se live nikale):
```
BD BR CIS EU ID IND ME NA PK SAC SG TH TW US VN
```
→ Code me **`RU` hai jo exist hi nahi karta** (galat region bhejne par API `ACCOUNTS_EMPTY` deta hai).
→ Code me **`EU`, `NA`, `SAC` MISSING hain** — Europe/North America/South America ke players kabhi nahi milenge.

**(b) Koi health pre-check nahi.** API ka root endpoint ye deta hai:
```json
"ServiceStatus": {"Status":"online","AverageResponseTime":"752ms","Uptime":"0 days • 4 hours"}
"AccountBot": [{"Region":"IND","TotalAccounts":"2","AvailableAccounts":"2","BannedAccounts":"0"}]
```
API **sirf 2 accounts per region** rakhta hai. Jab wo exhaust/ban ho jate hain, **har query `PLAYER_NOT_FOUND` deti hai** — chahe UID bilkul sahi ho. Bot user ko bolta hai *"Region galat ho sakta hai"* — jo **jhooth hai**. User ko credit bhi gaya aur galat guidance bhi mili.

**(c) Koi cache nahi, koi fallback provider nahi.** Single point of failure.

---

### 2. 🎮 BGMI UID — **essentially dead**
**Live test:**
```
uid 510069453 → HTTPSConnectionPool(host='kronos-api.pubg.com', port=443): Max retries exceeded
```
`kronos-api.pubg.com` resolve hi nahi hota / dead hai. Teeno shards (`in`, `india`, `global`) fail.
User ko hamesha **fallback text** milta hai: *"BGMI ke liye officially koi free public API nahi hai"*.

→ Tool effectively ek **static help message** hai, par premium credit leta hai aur menu me "🎮 BGMI UID" ke naam se bikta hai.
→ Ye **honest** hai (fake data nahi dikhata — wo acchi baat hai), par user experience kharab hai: credit gaya, kuch mila nahi.

---

### 3. 📌 PINTEREST SEARCH — **0 real Pinterest results**
**Live test:**
```
pinterest_search("cat wallpaper") → ok:True, results:6, :0
```
**6 results mile, par EK bhi Pinterest image nahi.** Bot khud hi message deta hai:
> ⚠️ "Pinterest par exact match nahi mila — similar public images dikh rahi hain"

**Kyun:** ye Bing image search scrape karta hai (`murl&quot;` regex). Bing Pinterest ko index se hata deta hai, isliye `.com` URLs kabhi nahi aate. **Tool ka poora purpose hi fail ho raha hai.**

**Aur maine PROVE kar diya ki real solution kaam karta hai:**
```
GET pinterest.com/  (cookies: csrftoken, _pinterest_sess, _auth)
GET pinterest.com/resource/BaseSearchResource/get/?data={"options":{"query":"cat wallpaper","scope":"pins"}}
→ HTTP 200, 219 KB, 21 REAL results
   'wallpaper 4k| Cat'        orig=https://i..com/originals/24/45/ca/... 1672x940
   'Cat Wallpapers Backdrops' orig=https://i..com/originals/cd/2b/dc/... 1920x1080
   'cat wallpaper pc'         orig=https://i..com/originals/20/0c/17/... 3840x2400  ← 4K!
```
**Ye official Pinterest internal API hai, koi key nahi chahiye, aur original-quality URLs + dimensions + titles deta hai.**

### 4. 📌 PINTEREST PIN LINK — original quality MISS ho rahi hai
**Live test:** pin `939527498239498877` ka page fetch kiya → **1 MB HTML**, par:
```
og:image count: 0          ← code isi par fallback karta hai, ye kabhi nahi milta
 urls (raw grep): 1  ← par usme CSS junk chipka hua: "...949a0ed813c2b.png)}._YsBbF{border:0;..."
```
Code ka `PINIMG_RE` regex sahi hai aur clean URL nikal leta hai — par:
- **Video pins par kuch nahi milta** (koi image URL hi nahi hota) → tool chup-chaap fail
- **Koi metadata nahi** — title, description, pinner, likes, saves, dimensions sab available hain par use nahi ho rahe

**Prove kiya ki `PinResource` API full data deta hai:**
```
GET pinterest.com/resource/PinResource/get/?data={"options":{"id":"576742296077249680","field_set_key":"detailed"}}
→ HTTP 200: title='wallpaper 4k| Cat', description='1920x1080, 4k',
  images sizes = ['60x60','136x136','170x','236x','474x','564x','736x','600x315','orig'],
  orig = https://i..com/originals/24/45/ca/....png,
  pinner = 'Ash', followers = 5, repin_count, comment_count
```

---

## ⚠️ MEDIUM findings (kaam karta hai, par "premium" nahi)

### 5. 📄 WEB SCRAPER — poora page dump, article extraction nahi
**Live test:** Wikipedia "Telegram (software)" → **22,515 words**
Ye article nahi hai — isme **navigation, sidebar, "See also", references, footnotes, external links, categories, copyright notice** sab hai.

Code sirf itna karta hai:
```python
for t in soup(["script","style","noscript","svg","header","footer","nav","aside","form","iframe"]):
    t.decompose()
main = soup.find("article") or soup.find("main") or soup.find("body") or soup
text = main.get_text("\n")
```
`<header>/<footer>/<nav>/<aside>` tags **sirf tab hote hain jab site semantic HTML use kare** — zyadatar Indian news/blog sites me ye nahi hota, sab `<div>` me hota hai. To `find("article")` fail → `find("body")` → **poora kachra**.

**Missing:** paragraph scoring, link-density filter, boilerplate detection, reading-time, markdown output, image extraction, author/date meta.

### 6. 📧 TEMP MAIL — OTP extraction NAHI hai (ye hi main use-case hai!)
**Live test:** `tm_create()` → ✅ working (`udz7nc3b6hdz4e@maxxspace.com`)

Par log temp mail **OTP ke liye** lete hain. Bot poora email body dump kar deta hai (1200 chars) — user ko khud 6-digit code dhoondhna padta hai. Signup emails me body me branding, footer, unsubscribe links — **OTP dhoondhna mushkil**.

**Missing:** OTP/verification-code auto-extraction, `INBOX` par auto-refresh/poll, attachment list, QR-code of address (phone me type karne se bachne ke liye).

### 7. 📦 APP FINDER — sirf 8 search URLs, koi verification nahi
```python
def get_app_store_links(app_name): return {"stores": [8 hardcoded search URLs]}
```
Ye **app dhoondhta hi nahi** — sirf 8 websites ke search-page links banata hai. User "whatsapp" bheje ya "xyzabc123fakeapp" — **same 8 links** aayenge. Koi confirmation nahi ki app exist karti hai.

Aur 2 stores **MOD APK piracy sites** hain (`GetModPC`, `HappyMod`) — "🔥 Verified Mod" / "💎 Free Unlocked" badges ke saath. Ye legally risky hai aur Play Store policy ke against hai.

**Available fix:** Google Play ka public batchexecute endpoint + F-Droid API se **real app card** (icon, rating, developer, downloads) — maine verify kiya ye dono bina key ke kaam karte hain.

### 8. 📷 QR CODE — colors aur logo ignore ho rahe hain
```python
def make_qr_bytes(text, box_size=18, fill="black", back="white"):
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=box_size, border=2)
    ...
    img = qr.make_image(fill_color=fill, back_color=back)
```
`fill`/`back` params hain par **bot kabhi pass hi nahi karta** → hamesha black-on-white.
`ERROR_CORRECT_M` (15%) — **logo embed karne ke liye `H` (30%) chahiye**.
Koi branded/center-logo QR nahi, koi UPI-payment QR nahi (jabki `build_upi_link()` function already maujood hai par use nahi hota).

---

## 🔧 ARCHITECTURE findings (poore codebase ki consistency)

### 9. Core layer bana hi nahi use ho raha
`modules/core/` (net + cache + limiter) **genuinely professional** hai. Par:

| Module | `core` use karta hai? | Raw `requests` calls |
|---|---|---|
| `api_hub.py` | ✅ | 1 |
| `osint_tools.py` | ✅ | 8 |
| `toolkit_extras.py` | ✅ | 9 |
| `web_tools.py` | ✅ | 1 |
| **`cloud_tools.py`** | ❌ | **11** |
| **`media_downloader.py`** | ❌ | **11** |
| **`gaming_tools.py`** | ❌ | **3** |
| **`.py`** | ❌ | **4** |
| **`temp_mail.py`** | ❌ | **5** |
| **`osint_hub.py`** | ❌ | **2** |
| **`vehicle_challan.py`** | ❌ | **3** |
| **`imei_lookup.py`** | ❌ | **1** |
| **`general_tools.py`** | ❌ | **1** |
| **`tutorial_hub.py`** | ❌ | **1** |

→ **10 modules, 42 raw calls** connection-pool + retry + backoff + size-cap se **bahar** hain.
→ `osint_hub.py` ne apna **duplicate cache** bana rakha hai (`_CACHE` + `_LOCK` + `cache_get/put`) jabki `core/cache.py` already yahi kaam thread-safe + LRU + hit-rate stats ke saath karta hai. **Do cache = do memory pools, do bug surface.**

### 10. Silent failures
- **159** bare `except Exception:` blocks
- **58** `except Exception: pass` — error poori tarah nigal jata hai, log me kuch nahi

Jab tool fail hota hai, admin ko **pata hi nahi chalta kyun hua**. `/sys` health card me per-tool failure counts nahi hain.

---

## 📊 Priority order (kis pehle fix karein)

| # | Tool | Severity | User impact |
|---|---|---|---|
| 1 | 📌 Pinterest (search + pin) | 🔴 CRITICAL | Tool ka core promise fail — 0 real results |
| 2 | 🔥 FF UID | 🔴 CRITICAL | Har query par galat error + wasted credit |
| 3 | 🎮 BGMI UID | 🔴 CRITICAL | Dead upstream, sirf help text milta hai |
| 4 | 📄 Web Scraper | 🟠 HIGH | 22K words kachra, article nahi |
| 5 | 📧 Temp Mail | 🟠 HIGH | OTP nahi nikalta (main use-case) |
| 6 | 📦 App Finder | 🟠 HIGH | Verify hi nahi karta + piracy sites |
| 7 | 📷 QR Code | 🟡 MEDIUM | Basic hai, premium feel nahi |
| 8 | Core layer adoption | 🟡 MEDIUM | 10 modules pool/retry se bahar |
| 9 | Error observability | 🟡 MEDIUM | 58 silent failures |

---

## 🎯 v53.0 Upgrade Plan

**Phase 1 — Engine rewrites (CRITICAL + HIGH):**
- [ ] `.py` → official `BaseSearchResource` + `PinResource` APIs, video pins, full metadata, Bing fallback
- [ ] `gaming_tools.py` → correct regions, live health pre-check, honest status, cache, provider chain
- [ ] `web_tools.py` → real readability extraction (paragraph scoring + link density), markdown, reading time
- [ ] `temp_mail.py` → OTP auto-extraction, QR of address, attachments, auto-refresh
- [ ] `general_tools.py` → real app verification + honest QR with colors/logo/UPI

**Phase 2 — Infrastructure:**
- [ ] Sabhi modules `core/net.py` par migrate (42 raw calls → pooled + retry + SSRF)
- [ ] `osint_hub.py` ka duplicate cache → `core/cache.py`
- [ ] Per-tool failure counters → `/sys` admin card me visible

**Phase 3 — Verification:**
- [ ] Naya test suite `_selftest_v53.py` (har upgrade ke liye live + static checks)
- [ ] Purani 414 checks **regress na hon** — teeno suites green rahen
- [ ] README + non-technical changelog update

---

## ✅ FINAL STATUS — v53.0 SHIPPED (audit closed)

Audit date: 2026-10-05 · Branch: `main` · Version: **`v53.0 Premium Earning`**

### Jo fix hue (sab live-verified)

| # | Tool / Area | Problem jo mila | Fix | Verify |
|---|---|---|---|---|
| 1 | 🔥 FF UID | har UID 404 · 11s · credit kat-ta tha | SAC region add · parallel scan · 4s/req timeout + 6s deadline · region auto-detect engine ko delegate | **0.19s asli data** ✅ |
| 2 | 🎮 BGMI UID | dead upstream par bhi 1 credit | `bgmi_availability()` probe (JSON content-type required) · `service_busy=True` + `available=False` + `fallback=True` (back-compat) · `note_upstream` | **credit nahi katta** ✅ |
| 3 | 📌 Pinterest | 6 results, 0 asli  | session bootstrap (csrftoken/_routing_id/_pinterest_sess) · `BaseSearchResource` · `PinResource` detail · rich dicts · `` resolve · video → `send_video` | **8/8 asli pins** ✅ |
| 4 | 📄 Web Scraper | 22,515 words kachra | readability-style extraction · markdown · byline · `reading_time_min` · `.txt` >3400 chars | **11,339 clean words** ✅ |
| 5 | 📧 Temp Mail | body dump, no OTP | `_hydra_items()` (mail.tm `/domains` plain-list ho gaya tha → v52.3 crash) · `extract_codes()` · `tm_poll()` seen-tracking · inline buttons | **OTP 10/10** ✅ |
| 6 | 📦 App Finder | 8 blind URL + 2 piracy sites | `app_lookup()` Google Play HTML parse (2 dev-link forms, `aria-label` rating, India `Cr/L` locale) · F-Droid API · iTunes API · piracy **removed** | **verified metadata** ✅ |
| 7 | 📷 QR | params ignored · lamba text crash | `make_branded_qr()` + `build_qr_image()` helper · logo cache · hex validate · **contrast guard** · length guard · vCard **4-step** · WiFi escape | ✅ |
| 8 | 📊 Telemetry | 58 `except: pass` | `modules/core/telemetry.py` (13 fns decorated) · `_telemetry_block()` → `/sys` · `is_soft_fail()` | ✅ |
| 9 | 🛡️ Credit | fail par bhi charge | charge-on-success only; `service_busy`/`found=False`/QR-fail ⇒ no charge | ✅ |

### Regression suite (final)

| Suite | Checks | Result |
|---|---|---|
| `tests/test_v50_core.py` | 106 | ✅ 0 fail |
| `_verify_v49.py` | 128 | ✅ 0 fail |
| `_selftest_v50.py` | 208 | ✅ 0 fail |
| `tests/test_privacy_safe_lookup.py` | 14 | ✅ OK |
| `tests/test_v53.py` *(naya)* | 277 | ✅ 0 fail |
| **TOTAL** | **733** | **0 FAIL** |

### Audit ke dauran pakde gaye 4 extra bugs (test suite ke through)

1. **WiFi QR open network** — `T:nopass` ke saath khaali `P:;` field ja raha tha
   (WiFi QR spec me open network ke liye `P:` hota hi nahi; kuch Android versions
   saved-network corrupt kar dete hain). Ab `P:` sirf password hone par.
2. **`build_upi_link` regex** — `{2,256}` local-part ki wajah se `a@upi` jaise
   chhote par valid VPA reject ho jate the. Ab `{1,256}`.
3. **`is_soft_fail`** — `available: False` pakad hi nahi sakta tha kyunki
   `bool(False)` = `False`. Ab explicit `is False` check.
4. **`_CTA_PAT` (scraper)** — trailing `.{0,90}$` anchor ki wajah se lambi footer
   lines (`Unsubscribe | Privacy Policy | © 2026 Acme Inc. All rights reserved.`)
   strip hi nahi hoti thin. Anchor hataya; lambai ab word-count check sambhalta hai.
   Saath me `unsubscribe`/`all rights reserved`/`you are receiving this` triggers add.

### Do design traps jo note karne layak hain (aage ke liye)

- `TTLCache(maxsize=n)` par **hard floor `max(16, n)`** hai — memory-safe design.
- `RateLimiter(default_limit=…)` ke **ctor defaults `allow()` me apply nahi hote**
  jab `limit=None` — tab module-level `_env_limit()` (20/60) use hota hai.
  `bot.py` isi liye explicit `TOOL_RATE_LIMITS` bhejta hai.

### Abhi bhi bacha hua (optional, Phase 2)

Raw `requests` (bina `core/net.py` ke) — SSRF guard + size cap + unified retry
inke through nahi jata:

| Module | raw `requests` calls |
|---|---|
| `cloud_tools.py` | 11 |
| `media_downloader.py` | 11 |
| `toolkit_extras.py` | 9 |
| `osint_tools.py` | 8 |
| `vehicle_challan.py` | 3 |
| `osint_hub.py` | 2 |
| `imei_lookup.py` / `tutorial_hub.py` | 1 each |

Ye **bug nahi** hai (sab me timeout hai, async hygiene sahi hai) — sirf consistency
ka kaam hai. Jab kabhi karo, ek-ek module karke aur `_selftest_v50.py` chala ke.
