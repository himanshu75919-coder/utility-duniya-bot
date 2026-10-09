# v100.0 FAMILY-INFO — 👪 Naya Tool: Family Info

**Date:** 9 Oct 2026 · **Status:** ✅ Live · **Tests:** 53/53 green (v100 selftest 47/47)

---

## 🎉 Kya naya mila?

**👪 FAMILY INFO — Aadhaar se Ration Family Card** (38th premium tool)

1. Menu me **👪 FAMILY INFO** button dabao (NUMBER INFO ke neeche).
2. **12-digit Aadhaar number** bhejo.
3. Turant milega:
   - 🪪 Ration Card number + type (PHH/AAY…)
   - 📍 State / District
   - 🏪 FPS (ration shop)
   - 👥 Kitne members + 🏠 poora address
   - 👨‍👩‍👧 Har member ka **naam + eKYC status** (✅ Verified / ⏳ Pending)

Ye tool **aapki `familyinfo` API** par chalta hai (bot me built-in — kuch lagana nahi hai).

---

## 🔐 Aadhaar safety (sabse zaroori)

- Aadhaar **HAMESHA masked** dikhta hai — sirf `XXXX-XXXX-1234` (aakhri 4 digit).
- Poora Aadhaar **KAHIN nahi**: na card me, na error me, na kahin save.
- API khud 6 digit bhejta hai (`401****849`) — hum wo bhi **NAHI dikhate**, sirf apna sakht mask.
- Galat Aadhaar (typo) API tak **jaata hi nahi** — pehle hi pakda jaata hai.

## 💳 Credit ka niyam (naya, behtar)

- Record **mile tabhi 1 credit** katega.
- Galat Aadhaar ya "record nahi mila" par **ZERO credit** — free retry.

## 🛡️ Purane tools? Bilkul untouched.

- Purane **37 tools + 43 prompts** me **ZERO change** — proof: code me sirf nayi lines judi, 1 bhi purani line nahi badli (version number ke siva).
- Number Info, YouTube, IMEI — sab jaise the, waise hi.

## ⚙️ Zaroorat ho to (optional)

- API key badalni ho to Render → Environment me `FAMINFO_API_KEY` set karo (default `Demo` chalta hai).
- Baaki `FAMINFO_API_URL` / `FAMINFO_API_TIMEOUT` khali = built-in default.

---

**Test saboot:** `tests/test_v100_familyinfo.py` — 47/47 PASS · Full suite 53/53 green · Live API verified (5-member family record + clean miss).
