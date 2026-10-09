# 📱 NUMBER INFO — API SETUP (v99, bahut aasaan)

Tumhara apna number API bot me **pehle se laga hai** (built-in) — tumhe kuch
karne ki zaroorat **nahi** hai. Number Info tool kholo → 10-digit number bhejo →
naam/pita/address wala card aa jayega. 🔥

Endpoint: `.../bot-api?key=KEY&tool=num&term=NUMBER` (GET request hai).

---

## STEP 1 — Check karo API lagi hai ya nahi

Telegram par bot ko bhejo:

```
/numapi
```

`✅ SET HAI (built-in)` dikhe to sab ready hai.

## STEP 2 — Live test karo (1 number)

```
/numapi 9876543210
```

30-40 second me naam/operator/circle dikhe to API **chal rahi hai**. ✅

> Note: API thodi slow hai (30-40s). Ye normal hai — wait karo, dobara mat bhejo.

## STEP 3 — Key badalni ho (Demo → asli key)

Abhi `Demo` key chal rahi hai. Kabhi asli key mile to:

1. [dashboard.render.com](https://dashboard.render.com) kholo
2. **utility-duniya-bot** service kholo → **Environment** tab
3. **Add Environment Variable**:
   - Key: `MYNUM_API_KEY`
   - Value: tumhari asli key
4. **Save Changes** — bot khud restart ho jayega (2-3 min)

Bas! Code me kuch badalne ki zaroorat nahi.

## STEP 4 — Safety (zaroor padho)

| ✅ KARO | ❌ NA KARO |
|---|---|
| Key sirf Render → Environment me rakho | Key kisi ko mat do, screenshot me mat bhejo |
| Record na mile to number dobara check karo | Bot ko public group me admin mat banao |
| `/numapi` se pehle test karo | Kisi aur ka data idhar-udhar mat forward karo |

**Imandaar note:** owner ka naam/pata API ke paas **hai tabhi** aata hai. Agar
API ke paas us number ka record **Nahi** hai to bot offline card dikhata hai
(sirf country) — iska matlab API kharab nahi, bas record Nahi mila.

**Kanoon wali baat:** Aadhaar number bot **hamesha mask** karke dikhata hai
(`XXXX-XXXX-1234`). Poora Aadhaar dikhana kanoon ke khilaaf hai — isliye bot
me ye lock hai, koi khol nahi sakta. 🔒
