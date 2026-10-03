# API aur privacy-safe lookup setup

## IMEI / device model

- User apne ya authorized device ka 15-digit IMEI bhejta hai; bot Luhn check locally karta hai.
- Network par sirf pehle 8 digits (TAC) jaate hain. Serial/check digit store ya report nahi hota.
- Canonical hub route: `/api/imei?key=Demo&imei=<8-digit-TAC>`.
- Abhi hub me chhota local TAC hint table hai: kuch models ka brand/model mil sakta hai. Full technical specs, product photo aur model URL tabhi dikhte hain jab authorized device-spec catalog unhe deta ho; har model ke liye guarantee nahi.
- JSON ka safe shape: `device_name`, `image_url`, `url`, `brand`, `model`, `tac`, `specifications`, `source`.
- Is lookup se owner, blacklist, carrier-lock ya location details nahi milti.

Render → service → **Environment**:

| Variable | Value |
|---|---|
| `IMEI_API_BASE` | `https://osint-api-hub.onrender.com/api` |
| `IMEI_API_KEY` | `Demo` (sirf public demo endpoint ke liye) |
| `IMEI_TIMEOUT` | `25` |

Admin `/imeistatus` sirf fixed demo device test karta hai; kisi user ka IMEI test ke liye mat bhejein.

## Number Info

Number tool sirf carrier/operator, circle/region, number type, validity aur safety/official links dikhata hai. Leaked databases se kisi number-holder ka naam, family relation, linked numbers, ghar ka pata, Aadhaar ya doosra government ID search/return nahi kiya jata. Is personal-record feature ka network lookup retire kar diya gaya hai.

## Vehicle / Challan

Free mode me number-plate se sirf state/RTO ka approximate format aur official VAHAN / e-Challan links milte hain. Live RC/challan ke liye documented, authorized provider ya official portal ki OTP/CAPTCHA zaroori hai. Bot owner ka naam, phone, address ya challan record guess/fabricate nahi karega.

Default Render setting:

```text
VEHICLE_PROVIDER_AUTHORIZED=0
```

`/vehstatus` real number plate submit nahi karta. Live provider tabhi configure karein jab uske data use aur display ke liye likhit permission ho.

## Health monitor

Webhook aur polling dono mode me Render/UptimeRobot ke liye `GET /health` aur `GET /` ko HTTP 200 dena chahiye. Monitor me path `/health` rakhein. Telegram webhook route alag hi rahega.

## Test / limitation

- `GET /health` — service health; isme koi phone, Aadhaar ya vehicle lookup nahi hota.
- `GET /api/imei?key=Demo&imei=35301011` — TAC-only demo check (hub update deploy hone ke baad).
- Number/vehicle endpoints ka empty result database ko indicate nahi karta; authorized provider ke bina personal lookup available nahi hai.
