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

---

## 👪 FAMILY INFO ka bhi wahi tarika

Family Info tool bhi **pehle se laga hai** — kuch karne ki zaroorat nahi.
Check karne ke liye bot ko bhejo:

```
/famapi
/famapi 123456789012
```

Key badalni ho to Render → Environment me ye daalo (bilkul upar wale steps
jaise hi):

| Key | Kya hai |
|---|---|
| `FAMINFO_API_URL` | family API ka endpoint (khali = built-in default) |
| `FAMINFO_API_KEY` | family API ki key |
| `FAMINFO_API_TIMEOUT` | `40` (second) |

Yahan bhi Aadhaar **hamesha masked** rehta hai, aur ek baar me **zyada se zyada
12 members** dikhte hain (card bahut lamba na ho jaye isliye).

---

## 🆕 v108 note

Bot ab **SLIM** version par hai — sirf ye 2 tools bache hain, isliye RAM
450+ MB se girkar **~62 MB** ho gayi. In dono tools ka code **ek line bhi nahi
badla**, to jo pehle kaam karta tha wo ab bhi bilkul waise hi karega — bas ab
bot beech me rukega nahi.
