# v45 OSINT Hub — purana leaked-data flow retire kiya gaya

Yeh purani guide ab valid nahi hai. Isme pehle unsafe personal-record aur Aadhaar-family lookup ka zikr tha; woh examples aur lookup claims jaan-bujhkar hata diye gaye hain.

## Abhi ka privacy-safe scope

- **Number Info:** local carrier/type/region/timezone metadata aur official safety-report links. Leaked naam, family/member names, alternate numbers, address, Aadhaar ya doosre government ID ko search/return nahi kiya jata.
- **IMEI:** full 15-digit IMEI bot par locally validate hota hai. Hub ko sirf pehle 8 digits ka TAC bheja jata hai. Local catalog me brand/model hint mil sakta hai; full specifications/photo har model ke liye guaranteed nahi. Serial number, owner, blacklist ya tracking lookup nahi hota.
- **Vehicle / challan:** default me live lookup band hai. Bot sirf local RTO/state-format hint aur official VAHAN/e-Challan links deta hai. Live provider tabhi consider karein jab data use aur display ke liye uski documented authorization ho; result kabhi fabricate nahi hota.
- **Aadhaar / family:** Aadhaar number bot ya hub me mat bhejein. Apne record ke liye UIDAI/NFSA ke official, consent-based portals ka use karein.
- **Hub status:** `/hubstatus` sirf `/health` route check karta hai; koi phone number, plate ya Aadhaar sample bheja nahi jata.

## Bot configuration

Render → `utility-duniya-bot` → Environment me:

```text
NUM_LEAK_ENABLED=off
VEHICLE_PROVIDER_AUTHORIZED=0
IMEI_API_BASE=https://osint-api-hub.onrender.com/api
IMEI_API_KEY=Demo
BRAND_TAG=@Supermannn_x
```

`VEHICLE_PROVIDER_AUTHORIZED=0` par owner/RC/challan data fetch nahi hota. Kisi provider ke liye written permission aur documented API use-policy verify kiye bina is flag ko enable na karein.

## Official links

- UIDAI MyAadhaar: https://myaadhaar.uidai.gov.in/
- NFSA: https://nfsa.gov.in/
- VAHAN RC status: https://vahan.parivahan.gov.in/nrservices/faces/user/searchstatus.xhtml
- e-Challan: https://echallan.parivahan.gov.in/
- Sanchar Saathi / Chakshu: https://sancharsaathi.gov.in/sfc/
- National Cyber Crime Reporting Portal: https://cybercrime.gov.in/
