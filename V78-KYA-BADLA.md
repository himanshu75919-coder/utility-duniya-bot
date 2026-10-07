# v78 — KYA BADLA (Speed + Permanent Crash Fix)

Tarihe: 2026-10-08
Branch: `main` → Render par auto-deploy

---

## 1. ⚡ BOT AB FAST RESPOND KAREGA (DB 21–50× tez)

### Problem kya thi (asuman se nahi, nap kar pata lagaya)
Bot ki **har ek message** par kam se kam 2 SQLite calls hoti thi (`get_user` +
`add_use`). Purana `database.py` har call par:

1. naya `sqlite3.connect()` kholta tha,
2. 5 `PRAGMA` chalata tha,
3. 6 `CREATE TABLE IF NOT EXISTS` + 2 `table_info` check chalata tha,
4. phir ek chhota sa `SELECT`,
5. connection band kar deta tha.

Yaani **asli kaam se kahin zyada kaam sirf "darwaza kholne-band" me** jaata tha.
Aur ye sab event loop ke *andar* tha — loop ruka rehta, isliye pura bot slow.

Repo me **118 jagah** blocking DB calls async handlers ke andar mili (61 `add_use`,
45 `get_user`, 6 `vip_ok`, 4 `spend_credits`).

### Fix
`database.py`:
- **Thread-local connection reuse** — ek connection, ek thread ke liye, zindagi bhar.
- **Schema sirf ek baar per process** (`_create_schema` + `_schema_ready` flag).
- `_ConProxy` — `con.close()` ab **no-op** hai, isliye **100+ purani `con.close()`
  wali lines bina ek bhi badlav ke** reuse karti hain (risk zero).
- **Inode staleness check** — vault restore se DB file badal jaye to bot khud
  reconnect karta hai (purani file par likhta nahi).
- Naye public helpers: `reset_conns()`, `schema_ready()`.

### Numbers (isi sandbox me, ek jaisi machine par A/B)

| Kya napa | PEHLE | AB | Farak |
|---|---|---|---|
| Ek DB call (connect+DDL) | 0.312 ms (median) | 0.006 ms (median) | **~50×** |
| Ek DB call (mean) | 0.324 ms | 0.007 ms | ~46× |
| 1 message ka DB kharcha (2 calls) | 0.385 ms | 0.028 ms | **13.6×** |
| Pehle report kiya gaya (local SSD) | 0.299 ms | 0.014 ms | 21.3× |

Do nap alag-alag point se hain, dono sach hain: upar wali table **sirf DB layer**
napti hai (0.385 → 0.028 ms / message), aur v77-era me **handler ke andar se** napne
par poora message kharcha ~1.11 ms tha (`add_use` 0.57 + `get_user` 0.54).
Render ke **0.1 CPU** par har extra syscall mehnga hota hai, isliye wahan bachat
local se zyada mehsoos hogi — plus "database is locked" wale crashes khatam.

Jo check kiya aur **jaan-boojh kar nahi chheda**: 8-thread contention test me koi
penalty nahi mila (0.98 ms/op @8 threads vs 1.04 ms @1) — yaani lock serialization
bottleneck nahi tha, isliye busy_timeout (15s) ko chheda nahi.

---

## 2. 🛑 "BOT BAAR BAAR CRASH" — IS BAAR KE 4 ASLI ROOT CAUSE

### (a) BOOT crash: ek galat env value = bot ek baar bhi start nahi hota tha
`modules/core/limiter.py` aur `modules/core/proengine.py` module **import** ke waqt
`int(os.environ.get("RATE_LIMIT_WINDOW"))` chalate the. Render par agar koi value
khaali (`RATE_LIMIT_WINDOW=`) ya typo (`RATE_LIMIT_BURST=6x`) ho gaya to
`ValueError` → import fail → bot **boot hi nahi hota**, aur crash "mystery" lagta.
Ab dono jagah `safeconf.env_int` — kachra = default + WARN log, range clamp
(`RATE_LIMIT_DEFAULT` 999999 do to bhi 5000 par clamp, taaki DB blast na ho).

### (b) QR tool: lamba text bhejo → tool marta tha
`qrcode` library version 40 se upar nahi jaati. 2900+ characters par:
`ValueError: Invalid version (was 41, expected 1 to 40)` → user ko "⚠️ chhota sa
ghatna ho gaya". Ab:
- error-correction level **khud degrade** hota hai (H→Q→M→L) taaki zyada se zyada
  text **scan-hone-yogy** QR me sama jaaye (2953 bytes tak),
- jo sach me namumkin hai, usme **saaf wajah** milti hai (`QrTooLong` — `ValueError`
  ka bachha, purane `except Exception` blocks ise pakad lete hain),
- khaali/None/bool/list input par bhi ab wahi saaf message, crash nahi,
- naya `qr_capacity(text)` helper — limit batata hai (admin/UX me use ho sakta hai).
`vip_payment` ka QR bhi yahi helper share karta hai → dono fix.

### (c) Bank statement tool: aadha-pora parse → `KeyError`
`statement_summary_text` `res["summary"]` aur `s['count']`/`s['total_debit']:,.2f`
seedhha use karta tha. Parser jab koi field na bhar paya (kharab PDF/cam scan) to
**KeyError/ValueError = tool crash**. Ab sab `.get()` + `_num()` safe formatter —
missing = `—`, aur output **bilkul waisa hi dikhta hai** jab data pura hai
(copy 1 character bhi nahi badla).

### (d) Junk input = crash (46 sites, fuzz sweep se nikale)
Naya robustness sweep (44 modules × ~42 kachra inputs: `None/True/''/[]/{}/0/b''/3.5/object()`)
bataaya ki **46 jagah** public functions kachra input par exception se marti thi.
Fixed:

| Tool | Pehle | Ab |
|---|---|---|
| `desi_tools` karaoke / ringtone / status-video / video→mp3 (9 sites) | `TypeError: a bytes-like object is required, not 'str'` (download fail hua to str chala aata) | `_as_bytes()` — khaali/str/None = ffmpeg ki apni saaf error dict, crash nahi |
| `cyber_studio` printable sheet + stamped photo | `UnidentifiedImageError` (user photo ki jagah koi aur file bhej de) | `_load_photo()` → saaf `ValueError("photo padhi nahi ja saki…")` |
| `desi_tools.make_status_video` | `Image.open` crash | error dict: "Photo padhi nahi ja saki — JPG/PNG bhejo." |
| `business_tools.to_pdf` | `TypeError: string argument without an encoding` / `'int' object is not iterable` | type-safe coercion (bytes/BytesIO/str/list/dict) — galat ho to `None`, crash nahi |
| `imei_lookup.parse_imei_payload` | provider ne `"result": null` bheja → `AttributeError` (tool marta) | null-safe → "No device details found" |
| `toolkit_extras.analyze_link / expand_url / shorten_url` | `AttributeError` on `True`/`[]` | `_s()` coercion |
| `osint_tools` IFSC / pincode / phone / RTO | `TypeError: expected string or bytes-like object` | str coercion |
| `media_downloader.classify_instagram_url / save_cookies_text` | AttributeError | str coercion |
| `payguard.validate_utr` | `True.strip()` crash | str coercion |
| `tutorial_hub.text_to_nodes`, `cloud_tools._extract_surl` | AttributeError | str coercion |
| `core.limiter.check_limit` | `int('')` → ValueError — **aur ye har tool se pehle chalta hai** | safe uid/action coercion |
| `core.proengine.detect_enabled / set_detect_enabled` | `int('')` → ValueError | `_safe_uid()` (digits nikaalta hai) |
| `toolkit_extras.brand_in_text` | mera v77 bug: `bool` par `.lower()` crash | type-safe |

**Sweep dobara chalai (network-stub ke saath):** 46 → **23**. Un 23 ka hisaab:

- **6 aur fix kiye** (yahi asli the): `api_hub.gstin_format_ok/pan_format_ok` (GSTIN/PAN
  validator `True` par TypeError se marti thi), `desi_tools.detect_bank`, `chat_xray.parse_chat`
  (user ka forward kiya chat), `captcha_bridge.parse_result`, `bseb_result._extract_token`.
  Sab me ek chhota `_txt_in()` coercion — kyun ki `(x or "")` **truthy non-str** (True, 5, {})
  ko bhej deta tha, phir `re.sub` TypeError.
- **9 "crash" nahi, design hi saaf error hai** (harness exception gin leta hai): 4× `QrTooLong`,
  2× `ValueError: photo padhi nahi ja saki`, 2× `ValueError: Galat UPI ID format`,
  1× `NetError` (network down — exactly jo hona chahiye).
- **8 harness artifacts** — user inhe kabhi call nahi karta: stdlib re-exports
  (`urlparse`/`parse_qs`/`urlunparse`) aur internal helpers
  (`core.cache.stats(obj)`, `telemetry._stat/tool_stats`, `vehicle_tool._provider_lookup`).
  Inhe jaan-boojh kar nahi chheda — galat jagah guard lagana = dead code.

---

## 3. ✅ TEST SE PROOF

- Naya `tests/test_v88.py` — **118 checks, 0 fail**. Speed ko **timing se nahi**
  verify karta (sandbox slow ho sakta hai) — `sqlite3.connect` **call counter** se:
  *200 DB calls me 1 se zyada connect nahi banana chahiye*. Baaki: no-op `close()`,
  thread-local alag connection, 6 threads × 25 writes me 0 "database is locked" aur
  0 lost write, inode swap, QR capacity, aur upar wali 12-site junk sweep (offline,
  DNS stub se — warna suite 3 min lagta).
- Junk sweep ko test me **offline** rakha hai (`socket.getaddrinfo` stub), taaki
  network ki halat se test ka result na badle — ye v53 se seekha sabak hai.
- Full suite: **35 files** — run 1 me sirf `test_v50_core` ka 1 check fail hua, aur
  wo mere hi naye code ka **false positive** tha: static checker `s.get(...)` ko
  HTTP call samajh leta hai (base-name list me `s` hai), aur mera local variable
  `summ` ke badle `s` tha. Rename kiya — checker ko kamzor **nahi** kiya (repo me
  5 jagah asli `s = requests.Session()` hai). Uske baad `test_v50_core` = **97/0**.

## 4. 🚫 KYA NAHI KIYA
- **Koi user-facing prompt/copy nahi badla** — naye error messages sirf un sites par
  jahan pehle crash tha (wahan koi copy thi hi nahi). Statement summary ka output
  byte-for-byte waisa hi hai jab data pura ho.
- **Earning/premium/VIP pricing ko sparsh nahi kiya** — aapne kaha users aane par
  on karenge. `EARNINGS-PLAYBOOK-v77.md` parked hai.
- **Photo/PDF/passport/document type naye tools add nahi kiye** — aap kehte hai wo
  acche nahi lagte. (Jo *already* maujood hai unhe sirf crash-free banaya, delete
  nahi kiya — haan, aap bolo to menu se hata dunga.)

## 5. 👉 AAPKA EK MANUAL KAAM (main API se nahi kar saka)
Render dashboard → `utility-duniya-bot` → **Settings → Health Check Path → `/health`**
→ Save. Render API ye field set karne nahi deti (PATCH 200 de kar ignore kar deta
hai, PUT 405). Ye laga do to Render khud "hang" bot ko restart karega.
