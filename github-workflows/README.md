# 🛰️ OPTIONAL WORKFLOWS (ye chahiye tabhi jab GitHub se chalana ho)

**Zaroori nahi hai!** Aapka bot **khud hi** hub ko har 4 minute me ping karta hai
(`KEEPALIVE_PEERS` = `https://osint-api-hub.onrender.com/health`) — isliye hub
sota nahi aur bot ka jawab tez rehta hai. Kuch karne ki zaroorat nahi.

Agar phir bhi GitHub Actions se chalana ho:

1. GitHub par repo kholo → **Add file → Create new file**
2. File ka naam: `.github/workflows/keep-hub-awake.yml`
   (naam me `/` likhte hi GitHub folders bana dega)
3. Is folder me se file ka content copy-paste karo → **Commit changes**
4. Bas — har 10 minute apne aap chalega (Actions tab me dikhega)

> Note: GitHub par PAT (token) se workflow file push karne ke liye `workflow` scope
> chahiye hota hai. Web UI se banane me wo jhanjhat nahi hai.
