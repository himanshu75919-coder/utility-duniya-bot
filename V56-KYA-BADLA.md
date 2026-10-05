# 🚀 v56.0 — "CRASH-PROOF + 5-TOOL CLEANUP"

**Release date:** 5 Oct 2026
**Tests:** **580 checks — 0 fail** (14 unittest + 97 v50 + 208 v53 + 67 v54.1 + 63 v55 + **131 naya v56**)

---

## 🚨 1. ASLI CRASH KI JADD MIL GAYI (aapka #1 problem)

Aapne likha tha: *"mera code crash ho jaata hai baar baar"*.
Render log me ye error baar-baar aa raha tha:

```
WARNING | pinpick send fail, document fallback:
          'Message' object has no attribute 'send_photo'
ERROR   | Exception handling update:
          'Message' object has no attribute 'send_document'
```

### Wajah (asli root cause)

`python-telegram-bot` me **`send_photo` / `send_document` / `send_video` sirf `Bot` object par hote hain — `Message` par NAHI.**

`Message` par sirf `reply_photo` / `reply_document` / `reply_video` hote hain.

Code **8 jagah** `Message` par `send_*` call kar raha tha:

| # | Line | Kya tha | Kaunse tool me |
|---|---|---|---|
| 1 | 3123 | `q.message.send_video(...)` | 📌 Pinterest video |
| 2 | 3128 | `q.message.send_photo(...)` | 📌 Pinterest image |
| 3 | 3133 | `q.message.send_document(...)` | 📌 Pinterest file |
| 4 | 3143 | `q.message.send_document(...)` | 📌 Pinterest fallback |
| 5 | 4671 | `update.message.send_photo(...)` | 📡 TG Public Info photo |
| 6 | 4838 | `update.message.send_video(...)` | 📌 Pinterest link |
| 7 | 4846 | `update.message.send_photo(...)` | 📌 Pinterest link |
| 8 | 4976 | `update.message.send_document(...)` | 📄 Web Scraper `.txt` |

Har baar user ko milta tha: **"⚠️ Chhota sa ghatna ho gaya!"** aur kaam adhoora.

### Fix

- Saare 8 call sites **hat gaye** (5 tools delete hone ke saath).
- Naya test `tests/test_v56.py` **check karta hai** ki ye galti dobara na ho —
  ye `hasattr(Message, "send_photo") == False` bhi verify karta hai.

### ✅ Aage ke liye rule (yaad rakho)

Media bhejne ke liye **Kabhi `message.send_photo()` mat likho.**
Sahi tarike:

```python
# Tarika 1 (recommended — Bot object)
await context.bot.send_photo(chat_id=..., photo=..., caption=...)

# Tarika 2 (reply — Message object par)
await message.reply_photo(photo=..., caption=...)
```

---

## 🗑️ 2. 5 TOOLS PERMANENTLY DELETE (aapke order par)

| Tool | Mode | Kya-kya hata |
|---|---|---|
| 🌐 **DOMAIN OSINT / IP** | `ip` | handler (85 lines) + `lookup_ip_domain()` + `domain_osint()` + `_doh_query()` |
| 📌 **PINTEREST** | `pinterest` | handler (123 lines) + **poori `modules/.py` file** + `_pinpick_download()` + `_pin_meta_line()` + pinpick callback (91 lines) |
| 📄 **WEB SCRAPER** | `webscraper` | handler (56 lines) + **poori `modules/web_tools.py` file** + `scrape_public_text()` |
| 🪪 **AADHAAR EID** | `aadeid` | handler (27 lines) + `desi_tools.aadhaar_eid_helper()` |
| 📡 **TG PUBLIC INFO** | `tginfo` | handler (78 lines) + `osint_tools.tg_user_public()` |

**Har jagah se hataya:** keyboard buttons · `BTN_MODE_MAP` · `PROMPTS` · `TOOL_RATE_LIMITS` · `PREMIUM_TOOLS` · `PREMIUM_TOOL_NAMES` · imports · help/tutorial text · tests · docs.

**bot.py: 332,627 → 301,603 bytes** (30.3 KB kam) · **modules se 2 poori files gayi** · **rubbish dev scripts 8 files gayi**.

### 💬 Purane keyboard walon ke liye friendly message

Jinke paas purana keyboard saved hai wo purana button dabaayenge — unhe **error nahi**,
ek saaf message milta hai:

```
ℹ️ 📌 Pinterest hata diya gaya hai.
━━━━━━━━━━━━━━━━━━━━━━
• 📌 Pinterest ki jagah → 📥 Video Downloader ya ⚡ Media Studio use karo

👇 Naya menu neeche hai:
```

**24 purane labels** ke liye ye message banaya gaya (har spelling/format ke liye).

**Safety check:** test verify karta hai ki koi bhi **ZINDA** tool galti se "removed" list me na aa jaye.
(Aur `"PIN"` jaisa generic label hata diya — warna **📮 Pincode Info** tool mar jaata!)

---

## 🛡️ 3. EXTRA CRASH-PROOFING

### 3a) `q.message` purana (Inaccessible) ho to crash nahi
PTB v21+ me callback ka `message` do tarah ka ho sakta hai — normal `Message`, ya
`InaccessibleMessage` (bahut purana message — usme `reply_text` hota hi NAHI).
Purane button dabane par crash hota tha. Ab `cbmsg()` helper dono case sambhalta hai.

### 3b) 🤖 YouTube bot-check error — ab saaf Hindi
Render log:
```
ERROR: [youtube] yaQCKQMiLo: Sign in to confirm you're not a bot.
       Use --cookies-from-browser or --cookies for the authentication.
```
User ko ye technical wall of text dikhta tha. Ab **17 tarah ke errors** ka
friendly Hindi + solution:

| yt-dlp error | User ko ab milta hai |
|---|---|
| Sign in to confirm you're not a bot | 🤖 YouTube ne server IP par **bot-check** laga diya → 1-2 min baad try karo, ya **720p/480p** chuno. Credit nahi kata |
| Video unavailable | 🚫 Video delete ho gaya → doosra link bhejo |
| Private / members-only | 🔒 Private hai / 👑 Membership chahiye |
| Age-restricted | 🔞 Login maangta hai → doosra video |
| Geo-blocked | 🌍 Region me blocked hai |
| Live stream / premiere | 🔴 Live download nahi hota |
| Format not available | 🎞️ Doosri quality chuno |
| HTTP 429 / 403 | ⏳ 2-3 min baad try karo |
| Timeout / connection | 🌐 10 sec baad try karo |
| File > 48MB | 📦 Chhoti quality ya Video compress |

**Har message me likha hota hai: "💳 Aapka credit nahi kata."**

### 3c) 🔌 Dead-link detection
`junk.nonexistent-xyz-qq.com` jaise **kabhi na khulne wale link** par pehle
**"SAFE ✅ 0/100"** aa jaata tha — jhootha bharosa! Ab:
**"LINK KHULTA NAHI 🔌"** + saaf wajah + OTP warning.

### 3d) 🧹 Raw technical error leak fix
`expand_url()` user ko ye dikhata tha:
```
HTTPSConnectionPool(host='junk', port=443): Max retries exceeded with url: /
(Caused by NameResolutionError(... getaddrinfo failed ...))
```
Ab: **"🔌 Ye website ka pata hi nahi chala — domain exist nahi karta ya spelling galat hai."**

---

## 🧪 4. NAYA TEST FILE — `tests/test_v56.py` (131 checks)

Ye file aapki **permanent suraksha** hai. Har baar code change karne par ye check karega:
- Message par `send_photo`/`send_document`/`send_video` **kahin bhi** na ho
- 5 tools ka **koi handler / import / dict entry** bacha na ho
- Purane keyboard walon ke **24 labels** ka friendly message maujood ho
- Koi **ZINDA** tool galti se removed list me na aa jaye
- `friendly_dl_error()` **9 tarah ke** yt-dlp errors theek se handle kare
- Dead-link detection kaam kare, raw error leak na ho
- `BOT_VERSION = "v56...` ho + duplicate dict keys na hon

```bash
python3 tests/test_v56.py     # 131/131 PASS
```

---

## 📊 FULL TEST RESULT (v56)

```
tests/test_privacy_safe_lookup.py   14 tests   OK
tests/test_v50_core.py              PASS 97 | FAIL 0
tests/test_v53.py                   PASS 208 | FAIL 0
tests/test_v541.py                  PASS 67 | FAIL 0
tests/test_v55.py                   PASS 63 | FAIL 0
tests/test_v56.py                   PASS 131 | FAIL 0   ← naya
-------------------------------------------------------
TOTAL                               580 checks — 0 fail
```

---

## 🎯 BOT MENU AB (28 buttons)

```
🌐 VIRTUAL NUMBERS      ⚡ TERABOX DOWNLOADER
🔄 CHANNEL CLONER       📥 VIDEO DOWNLOADER
📸 PASSPORT PHOTO       🖨️ 8-IN-1 PRINT SHEET
📄 DOCUMENT PDF         🏛️ SARKARI SEVA PORTALS
📱 NUMBER INFO          🏦 IFSC INFO
🏦 UPI VERIFY           📮 PINCODE INFO          ← layout compact hua
🎮 BGMI UID             🔥 FF UID
📧 TEMP MAIL            🏛️ SARKARI SEVA PORTALS
📷 QR CODE              📦 APP FINDER
🔗 URL SHORT            🔍 LINK CHECK
🏦 BANK STATEMENT       📜 SARKARI KAGAZ SUITE
⚡ MEDIA STUDIO (MP3/STATUS)
📲 IMEI / PHONE DETAILS  💎 VIP PREMIUM
🎁 REFER & EARN          👤 MY ACCOUNT
❓ HELP / TUTORIAL
(+ 🛠️ ADMIN PANEL · 👑 OWNER MODE — admin ke liye)
```

---

## ⚠️ IMPORTANT — GitHub Token

Aapne token chat me public likh diya tha. **Kaam khatam hone ke baad turant revoke karo:**
👉 https://github.com/settings/tokens

1. `himanshu75919-coder` → Settings → Developer settings → Personal access tokens
2. Wo token **Delete** karo
3. Naya token banao (sirf `repo` scope) — aur kisi ko na do
