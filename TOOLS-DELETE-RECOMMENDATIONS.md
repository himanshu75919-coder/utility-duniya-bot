# 🗑️ KAUN SE TOOLS PERMANENTLY DELETE KAR SAKTE HO (Render space/RAM + maintenance bachat)

> Niyam: jo tool (a) bahar ke dead/upstream API par nirbhar hai, (b) `/toolstats` me
> usage near-zero hai, ya (c) abuse/credit-burn ka source hai — wo delete candidate hai.
> Number Info aur Family Info **kabhi nahi hatane** (aapka order + sabse zyada use).

## Pehle sach: "space" se kya bachta hai

- Render free plan ki asli cheez **512 MB RAM** hai (disk nahi). Code size chhota hai
  (poora repo ~2 MB) — isliye module hatane se **boot RAM bahut nahi** girta.
- v107 me asli RAM bomb phoda ja chuka hai (phonenumbers geocoder 95 MB lazy +
  emergency valve) — boot 224 → 113 MB.
- Module delete karne ka asli fayda: **per-call RAM/CPU spikes** (reportlab/PIL/
  ffmpeg wale tools), **maintenance/bug surface**, **abuse/credit-burn**, aur
  **build time** kam hota hai.

## 🔴 TIER-1 — abhi delete kar sakte ho (kam nuksan, zyada fayda)

| Tool | Module | Kyun |
|---|---|---|
|  Temp Number (`/vnum`) | `temp_number.py` (30 KB) | Free SMS-OTP services 90% dead/rotate; user ko OTP milta nahi; shikayat ka source |
| ✉️ Temp Mail | `temp_mail.py` (23 KB) | Wahi kahani — public inboxes spam-blocked; bs4 top-import bhi |
| 🔐 Captcha Bridge | `captcha_bridge.py` (11 KB) | Niche flow (user khud captcha solve kare); usage near-zero |
| 📱 IMEI Lookup | `imei_lookup.py` (49 KB — sabse bada single tool module) | Bina paid/upstream key ke adhoora; `/imeistatus` khud batata hai key nahi hai |
| 🔄 Channel Cloner | `channel_cloner.py` (16 KB) | Bot ko har channel me admin chahiye; flood-limit/abuse risk; premium me bhi usage kam |

Anuman bachat: ~130 KB code + har call ke heavy sockets/cache + 5 tools ka
maintenance/bug surface khatam.

## 🟡 TIER-2 — `/toolstats` dekh kar faisla karo (seasonal / heavy)

| Tool | Module | Note |
|---|---|---|
| 📋 BSEB/Board Result | `bseb_result.py` (32 KB) + `boards.py` | Seasonal (Feb–May). Result season me keep, baaki 8 mahine delete kar sakte ho |
| 🏢 Business Tools ke rare sub-tools | `business_tools.py` (99 KB — sabse bada module) | reportlab/PIL se per-call RAM spike. Poora module nahi — sirf jo cards kabhi nahi bikte (menu se button hatao) |
| 🌐 OSINT hub paid upstream | `osint_hub.py` | Bina hub key ke kayi providers "upstream key chahiye" dikhate hain — dead weight buttons |
| 🚗 Vehicle/RC | `vehicle_tool.py` (25 KB) | Bina VAHAN key ke sirf offline parse; usage kam ho to delete |

## 🟢 KABHI NA HATAO (core earning + aapka order)

- 📱 Number Info (`mynum_api`) + 👪 Family Info (`familyinfo_api`) — aapka order
- 📸 Insta / ▶️ YouTube / 🎵 TikTok downloader + ytmp3 (v107 ke baad ye sabse tez hain)
- 🔗 Link/media studio ke basic tools, QR, `vault` (backup), `payguard`/payments

## Delete karne ka SAHI tarika (galat delete = crash)

1. `bot.py` ke menu (`kb_for`) se button hatao
2. `PROMPTS` / `DL_SITES` / mode-branch se entry hatao
3. Handler (`on_text`/`on_cb`) ke `if mode == "..."` block hatao
4. Top import line hatao (`from modules import X`)
5. Module file delete karo + `tests/` me uske version-tests ke references hatao
6. `python3 bot.py --check` + poora test suite chalao → commit

> Chaaho to agle message me bolo "Tier-1 delete kar do" — main upar wala poora
> surgical process khud kar ke push kar dunga (number/family info ko chhue bina).
