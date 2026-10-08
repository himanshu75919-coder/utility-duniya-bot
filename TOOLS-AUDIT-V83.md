# TOOLS AUDIT — v83.0 (har tool ka automated + live check)

Ye report batati hai ki bot ke har tool ko kaise check kiya gaya aur result kya raha.
Har row ek **button label / tool mode** hai. "OK" ka matlab: tool dabane par bot ne
crash nahi kiya aur user ko reply mila (mocked Telegram update se test).

## 1) Automated smoke test — summary

| Category | Kitne cases | Result |
|---|---|---|
| Text buttons (main menu + sub-menu labels) | 129 labels / 54 tool modes | 0 crash, 0 timeout, sab ne reply diya |
| Callback buttons (inline buttons) | 108 | 0 crash, 0 timeout |
| Slash commands (/start, /menu, /vnum, ...) | 154 cases (+8 wrapper cases) | 0 crash |
| Typed inputs (links, IFSC, IMEI, PAN, GST, vehicle, random text, 5000 chars) | 17 | 0 crash; sahi prompt / lookup mila |

Notes:
- Commands `/vnum`, `/terabox`, `/cloner`, `/sarkari` main() ke andar define hain; inhe
  unke text-button version se test kiya gaya (VIRTUAL NUMBERS, TERABOX DOWNLOADER, CHANNEL CLONER, SARKARI SEVA PORTALS) — ye OK.
- Admin-only buttons normal user ko silent rehte hain (by design). Admin uid se
  `admpay_view:` jaise malformed button test hua — ab saaf message deta hai.

## 2) Live downloader flows (sandbox ka real internet)

| Tool | Input | Result |
|---|---|---|
| Instagram (INSTA DOWNLOADER) | `instagram.com/p/DeJgDvDIFg2/?img_index=3&stkn=…` | Photo bheji gayi ✔ (ticker ab kaam ke baad band) |
| Terabox (TERABOX DOWNLOADER) | `1024tera.com/wap/share/filelist?surl=…` | File naam + size + web buttons ✔ (direct link ke liye `TERABOX_COOKIE` chahiye) |
| YouTube (YOUTUBE DL) | `youtube.com/watch?v=jNQXAC9IVRw` | Quality picker ✔ → 360p video bheji gayi ✔ |
| TikTok (TIKTOK DL) | `tiktok.com/@…/video/…` | Video bheji gayi ✔ |
| Facebook (FACEBOOK DL) | `facebook.com/watch/?v=…` | Video bheji gayi ✔ |

## 3) Tool-wise table (54 tool modes)

| Tool (mode) | Button label(s) | Test | Reply bheja? |
|---|---|---|---|
| `account` | My Account | OK | Haan |
| `admin` | Admin Panel | OK | Haan |
| `alltools` | All Tools, All Tools (Free), Saare Tools | OK | Haan |
| `appfind` | App Finder | OK | Haan |
| `bankpdf` | Bank Pdf To Excel, Bank Statement - Excel, Bank Statement To Excel (+1) | OK | Haan |
| `bgmi` | Bgmi, Bgmi Uid | OK | Haan |
| `biz_biodata` | Biodata, Marriage Biodata, Shaadi Biodata (+1) | OK | Haan |
| `biz_certificate` | Certificate, Certificate Maker | OK | Haan |
| `biz_emi` | Emi / Interest Calc, Emi / Vyaaj Calc, Emi Calc (+5) | OK | Haan |
| `biz_idcard` | Id Card, Id Card Maker | OK | Haan |
| `biz_invoice` | Bill Banao, Gst Bill, Invoice (+1) | OK | Haan |
| `biz_labels` | Price Label, Price Tag, Rate Tag | OK | Haan |
| `biz_letter` | Application Letter, Leave Application, Letter Maker | OK | Haan |
| `biz_resume` | Cv Maker, Resume, Resume / Cv | OK | Haan |
| `biz_upi` | Scan And Pay, Upi Payment Qr, Upi Qr | OK | Haan |
| `biz_vcard` | Visiting Card, Visiting Card Maker | OK | Haan |
| `bizstudio` | Business Studio, Business Tools | OK | Haan |
| `bsebr` | All Boards Result, Bihar Board Result, Board Result (+3) | OK | Haan |
| `bsebr_direct` | Bihar Board Result Check, Bseb Result, Bseb Result Check | OK | Haan |
| `cbse_info` | Cbse Result, Digilocker Result | OK | Haan |
| `cloner` | Channel Cloner | OK | Haan |
| `cxray` | Chat X-Ray, Chat X-Ray Report, Chat Xray (+1) | OK | Haan |
| `dl_facebook` | Facebook Dl | OK | Haan |
| `dl_gone` | Any Video Link, Downloader, Universal Video Downloader (+7) | OK | Haan |
| `dl_instagram` | Insta Dl, Insta Downloader, Instagram Downloader | OK | Haan |
| `dl_tiktok` | Tiktok Dl | OK | Haan |
| `dl_youtube` | Youtube Dl | OK | Haan |
| `doc_compress` | Document Pdf Compress, Document Pdf Compressor | OK | Haan |
| `ffuid` | Ff Uid, Free Fire Uid | OK | Haan |
| `ifsc` | Ifsc Info | OK | Haan |
| `imei` | Imei / Phone Details, Imei Info, Imei Lookup (+1) | OK | Haan |
| `kagaz` | Kagaz Suite, Sarkari Kagaz Suite | OK | Haan |
| `linkcheck` | Link Check | OK | Haan |
| `mediastudio` | Media Studio, Media Studio (Mp3/Status), Mp3 Status Studio | OK | Haan |
| `numinfo` | Number Info | OK | Haan |
| `osint_whois` | Domain Owner, Website Owner, Website Owner X-Ray (+1) | OK | Haan |
| `owner` | Owner Mode | OK | Haan |
| `pin` | Pincode Info | OK | Haan |
| `pp_stamp` | Passport Photo (Name/Dop) | OK | Haan |
| `premium` | Vip Premium | OK | Haan |
| `print_sheet` | 8-In-1 Print Sheet | OK | Haan |
| `qr` | Qr (Link / Text), Qr Code | OK | Haan |
| `qr_vcard` | Qr (Contact Card) | OK | Haan |
| `qr_wifi` | Qr (Wifi Share) | OK | Haan |
| `sarkari` | Sarkari Seva Portals | OK | Haan |
| `short` | Url Short | OK | Haan |
| `support` | Support / Madad | OK | Haan |
| `tempmail` | Temp Mail, Tempmail | OK | Haan |
| `terabox` | Terabox Downloader | OK | Haan |
| `tnum` | Temp Mail (Number), Temp Mail Number, Temp Number | OK | Haan |
| `tutorial` | Madad, Madad / Tutorial | OK | Haan |
| `uhunt` | Username Hunter, Username Hunter (Public) | OK | Haan |
| `vahan` | Gaadi Ka Record, Gaadi X-Ray, Rc + Challan (+3) | OK | Haan |
| `vnum` | Virtual Numbers | OK | Haan |

## 4) Callback groups (108 buttons)

| Group | Buttons | Result |
|---|---|---|
| media (Media Studio) | 11 | OK |
| kagaz (Kagaz / documents) | 10 | OK |
| rc (RC / vehicle) | 10 | OK |
| cloner (Channel cloner) | 7 | OK |
| doc (Document PDF compress) | 6 | OK |
| tnum (Temp number) | 6 | OK |
| vnum (Virtual number) | 4 | OK |
| qr (QR tools) | 3 | OK |
| tm (Temp mail) | 3 | OK |
| vault (Admin vault) | 3 | OK (admin-only) |
| admin / admpay / admact / others | remaining | OK (malformed `admpay_view:` ab saaf message) |

## 5) Known limits (imaandari se)

- Telegram ke andar real send ka test automated hai (mock), asli chat me aapka ek test confirm karega.
- Instagram / TikTok / Facebook / YouTube / Terabox ki external sites roz badalti hain — inka
  live result network aur time ke hisaab se badal sakta hai.
- File-upload tools (PDF compress, image/passport, media studio audio/video) ka automated test
  sirf "button → reply" tak hai; asli file ke saath end-to-end test har tool ke liye alag se karna hoga.
- Feature-level upgrade (naye options/buttons) is round me nahi hua; reliability aur UX bugs fix hue.
