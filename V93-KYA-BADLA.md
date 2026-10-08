# 📌 V93 — KYA BADLA (8 October 2026)

> **⚠️ PEHLE YE PADHO:** Render par **v85.0 already LIVE tha** jab ye kaam shuru hua
> (deploy `dep-db3pkgobr16s73ebaleg`, status `live`, commit `163cafd`).
> v85 ne **carousel wala main fix pehle hi kar diya tha** — `img_index` wala link ho
> tab bhi poori album jaati hai. Yaani aapki pehli shikayat ka main ilaaj **already
> deployed hai**.
>
> **v93 uske upar build karta hai, usse override nahi karta.** v85 ka saara kaam
> (LINK SANITIZER, FORTRESS-II, safe buttons, 45MB cap, one-by-one fallback) bacha
> hua hai. Neeche likha hai ki v93 ne **kya naya** kiya.

Owner ki 3 shikayatein thi. Teeno **jaanch kar** (live API calls se) dekhi gayi hain —
andaza nahi.

**Test result: 3767 PASS / 0 FAIL** (v85 par 3622 the; 145 naye checks jude)
+ 15 privacy tests OK. `python3 bot.py --check` bhi green.

---

## 1️⃣ 📸 "Instagram link me 6-7 photo hain, bot ek hi deta hai" — THEEK ✅

**Aapka link:** `https://www.instagram.com/p/DeJgDvDIFg2/?img_index=3&stkn=...`

**Jaanch (live, aaj):**
```
parth_dl.get_info(".../p/DeJgDvDIFg2/")  →  type=carousel, entries=8   ← 8 photo!
parth_dl.get_info(".../p/DdmJ952D3ux/")  →  type=carousel, entries=4   ← 4 photo!
```
Yaani **data poora aa raha tha** — bot khud 7 photo phek raha tha.

**Asli wajah:** Instagram app jab share-link banata hai to apne aap `?img_index=N`
chipka deta hai (N = wo photo jo aap us waqt dekh rahe the). v82 us flag ko
"user ko sirf N-wan item chahiye" samajh kar poore album ko 1 item par kaat deta tha.

**v85 ne kya theek kiya (already LIVE):**
- Carousel ab hamesha **POORA album** bhejta hai — `img_index` wala link ho tab bhi.
- Caption me note: *"slide 3 ka link tha"*.
- Khaali/kharab items filter, 45MB cap, aur group fail ho to one-by-one fallback.

**v93 ne usme kya AUR add kiya:**
| Bug (v85 me bhi tha) | Pehle | v93 me |
|---|---|---|
| 10+ item wala album | `(res["items"] or [])[:10]` → 12 photo me se **2 chup-chaap gayab** | `ALBUM_CHUNK` se chunk-by-chunk (10-10), **sab** jaate hain; har part par "part 1/2" note |
| 45MB cap kuch rok de | Chup-chaap kat jaata tha, user ko pata nahi chalta | Caption me note: *"⚠️ N item size-limit se chhoote"* |
| Album helper logic inline tha | Test karna mushkil | `clean_album_items()` + `build_album_chunks()` — alag, testable |

**Naye functions:** `bot.py` → `clean_album_items()`, `build_album_chunks()`, `ALBUM_CHUNK`
· Test: `tests/test_v93_album.py` (**41 checks**, aapke asli Instagram link par end-to-end)

---

## 2️⃣ ☁️ "1024tera wala link fail ho gaya" — AB POORI REPORT MILTI HAI ✅

**Aapka link:** `https://www.1024tera.com/wap/share/filelist?surl=YfyQ2DSJWSE8mbuw3QMxbA`

**Jaanch (live, aaj) — ye 1024tera nahi, TeraBox ka mirror hai:**

| API | Result |
|---|---|
| `share/list` (file listing) | ✅ `errno 0` — poora byora milta hai |
| `share/download` (download link) | ❌ `{"errno":400310,"errmsg":"need verify_v2"}` ← **CAPTCHA wall** |
| `api/sharedownload` | ❌ `{"errno":2}` |
| Public workers (robin/hnn/qtcloud) | ❌ teeno mar chuke hain (500 / Page not found / "Failed to get share info") |

**Sacchi baat:** TeraBox ne 2026 me **bina-login download par CAPTCHA** laga diya hai.
Direct download link bina cookie nikalna ab possible nahi — ye main jhooth nahi bolunga.
(Permanent ilaaj: `TERABOX_COOKIE` env me apne throwaway account ka `ndus` daalo —
cookie wale raaste par CAPTCHA nahi aata.)

**Lekin tool fail NAHI tha** — listing chalti thi, par user ko sirf ek adhuri line
dikhti thi aur 5 mar-chuke web downloader buttons. Isliye laga "tool toota hai".

**Ab kya milta hai:**
```
📂 1 file • 42.75 MB total • 🎬 1 video

1. 🎬 All Viral Videos and MMS Link(1).mp4
    📊 42.75 MB • Video • ⏱️ 4m 51s • 📐 480×856
    🗓️ 03 Sep 2026
```
+ **thumbnail photo** bhi jaati hai + saaf batata hai Terabox ne kya lock kiya
+ folder ki **saari** files (pehle sirf pehli dikhti thi) + total size.

**Naye:** `modules/cloud_tools.py` → `tb_file_report()`, `tb_fetch_thumb()`,
`_fmt_dur()`, `_kind_of()`, `_tb_thumb_url()` · Test: `tests/test_v93_terabox.py`
(**47 checks**, aapke asli link par end-to-end)

---

## 3️⃣ 🧯 "Code crash ho jaata hai baar baar" — SABSE BADI WAJAH BAND ✅

Bot ke paas pehle se supervisor, infinite-retry polling, watchdog, heavy-gate,
memory janitor the (v60–v92). Wo sab theek hain. Par jaanch me ek **chhupi hui**
wajah mili jo "crash" jaisi dikhti thi:

**Problem:** `bot.py` me **~500 jagah** `parse_mode=HTML` ke saath direct
`reply_text` / `edit_text` / `send_message` hota hai. Text me zara si HTML gadbad
(engine ke title me `<`, adhoora tag, user ke naam me `&`) → Telegram **poora
message reject** kar deta hai:
```
BadRequest: Can't parse entities: can't find end tag 'b'
```
**Kaam ho chuka hota hai, jawab taiyaar hota hai — par user tak jaata nahi.**
User ko "⚠️ Chhota sa ghatna ho gaya!" dikhta hai = "bot crash ho gaya".

**Ilaj — `modules/core/htmlnet.py` (naya):** Bot class ke 10 send/edit methods par
ek patla safety net. Telegram "parse entities" se mana kare to wahi message
1. pehle `repair_html()` se theek karke,
2. phir bhi na mane to tags hata kar (plain text)

dobara bhej deta hai. **Message kabhi gayab nahi hota** — bas formatting chali jaati hai.

**Suraksha:**
- Sirf "parse entities" wale error par kaam karta hai — `Conflict` / `RetryAfter` /
  `Forbidden` ka apna handling pehle jaisa chalta hai.
- `parse_mode` set na ho to wrapper **bilkul chhedta nahi**.
- Idempotent hai (dobara lagane par double-wrap nahi).
- Net khud fail ho jaaye to bhi bot pehle jaisa chalega (try/except me hai).

**Test:** `tests/test_v93_htmlnet.py` (**26 checks**) — positional + kwargs text,
photo caption, `edit_message_text`, non-HTML error passthrough, idempotency.

> Note: is banate waqt 2 asli bug mile aur theek hue — (a) fallback path repair-fail
> par `raise` kar deta tha (message phir bhi gayab), (b) positional index me `self`
> count ho raha tha (off-by-one). Dono tests me pakde gaye.

---

## 📊 Test summary

| | Pehle | Ab |
|---|---|---|
| Test files | 44 (v85 par) | 47 |
| Checks PASS | 3622 | **3767** |
| Checks FAIL | 0 | **0** |
| Privacy tests | 15 OK | 15 OK |

Nayi test files:
- `tests/test_v93_album.py` — 41 checks (aapke asli Instagram link par)
- `tests/test_v93_terabox.py` — 47 checks (aapke asli 1024tera link par)
- `tests/test_v93_htmlnet.py` — 26 checks

4 purane tests **exact version-prefix** ("v85 se shuru hota hai") par lage the — har
version bump par toot jaate the. Ab wo `version >= 85` check karte hain (intent wahi,
par bar-bar nahi tootega). Saath me `test_v82` ka C13 Terabox ke purane headline text
par laga tha — ab wahan saaf-sach likha jaata hai, isliye wo naye wording par update hua.

---

## 💰 Naya document

`EARNING-IDEAS-V93.md` — **naye** earning ideas (pehle wale repeat nahi).
Top 3: Passport Photo Maker, Shaadi Card Maker, Dukaan Bill Maker.
Meri sifarish: **Paid Alert Channel** (recurring, aapka content engine already taiyaar).

---

## ⚠️ ZAROORI — TOKENS

Is kaam ke liye GitHub aur Render token chat me paste hue the. **Wo ab leak ho chuke
hain** — koi bhi unhe dekh kar aapka poora GitHub account aur Render account chala
sakta hai. Turant revoke karo:

- **GitHub:** Settings → Developer settings → Personal access tokens → **Delete/Revoke**
- **Render:** Account Settings → API Keys → **Revoke**

Naya token kisi ko mat dena — mujhe bhi nahi. Deploy aap khud Render dashboard se
"Manual Deploy → Deploy latest commit" daba kar kar sakte ho (2 click ka kaam).
