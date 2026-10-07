# -*- coding: utf-8 -*-
"""
🎓 STUDENT HUB (v72.1) — GK Quiz + Yojana Checker + Marks Calculator
=====================================================================
User ka order (7 Oct 2026): "Students Pack" — teen tools, sab 100% FREE:

  1. 🎯 GK QUIZ CHALLENGE  — roz 5 sawal, score + streak, groups me challenge
  2. 🏛️ YOJANA CHECKER     — apni details do → kaun-kaunsi sarkari yojana milegi
  3. 📊 MARKS CALCULATOR   — % + grade + division, aur "pass ke liye kitne chahiye"

Sabse badi baat: teeno tools **poora offline** hain (koi website/API nahi) —
isliye ye kabhi fail nahi honge (na toota link, na band API).

Content:
  • QUESTIONS — ~90 sawal (Bihar GK + India GK + Science + Sports) — evergreen,
    jaan-boojh ke aise chune jo saal bhar sach rahenge (changing current affairs
    nahi, warna galat jawab ka darr).
  • SCHEMES — ~30 sarkari yojana (Central + Bihar) — eligibility rules ke saath.

Note (imaandari): yojana ki final eligibility official portal / block office hi
confirm karti hai — card me ye line hamesha jaati hai.
"""

import random
import re

# ============================================================ QUESTIONS
# Format: (sawal, (A, B, C, D), sahi_index, chhota fact)
QUESTIONS = (
    # ---------------- BIHAR GK ----------------
    ("Bihar ki rajdhani kya hai?", ("Gaya", "Patna", "Muzaffarpur", "Bhagalpur"), 1,
     "Patna ka purana naam Pataliputra tha."),
    ("Bihar Diwas kab manaya jata hai?", ("15 August", "26 January", "22 March", "1 May"), 2,
     "22 March 1912 ko Bihar-Bengal se alag hua tha."),
    ("Nalanda Vishwavidyalaya kis liye mashhoor thi?", ("Sena", "Bunkar", "Shiksha", "Vaidya"), 2,
     "Duniya ka sabse purana university maana jata hai."),
    ("Bodh Gaya me Bhagwan Buddha ne kya paya?", ("Rajya", "Gyaan (Bodhi)", "Dhan", "Sena"), 1,
     "Mahabodhi Mandir yahin hai — UNESCO site."),
    ("Madhubani painting kis rajya ki mashhoor hai?", ("Rajasthan", "Gujarat", "Bihar", "Odisha"), 2,
     "Madhubani (Mithila) art duniya bhar me famous hai."),
    ("Bihar ka rajyapal nivas kis shehar me hai?", ("Gaya", "Patna", "Purnia", "Darbhanga"), 1,
     "Raj Bhavan Patna me hai."),
    ("Ganga nadi Bihar ke kis shehar se hokar guzarti hai?", ("Bhopal", "Patna", "Jaipur", "Ranchi"), 1,
     "Patna Ganga ke kinare basa hai."),
    ("Chhath Puja me sabse zyada kya diya jata hai?", ("Dhan", "Surya ko Arghya", "Phool", "Ghee"), 1,
     "Bihar me sabse bada tyohar — Surya upasana."),
    ("Bihar ka rajya pashu kaun hai?", ("Sher", "Hathi", "Bail", "Ghoda"), 2,
     "Bihar ka rajya pashu Bail hai."),
    ("Bihar ka rajya pakshi kaun hai?", ("Mor", "Tota", "Kabutar", "Baya"), 3,
     "Bihar ka rajya pakshi Baya (weaver bird) hai."),
    ("Bihar me sabse zyada kheti kis fasal ki hoti hai?", ("Chawal", "Chai", "Coffee", "Nariyal"), 0,
     "Chawal + gehun Bihar ki main fasalein hain."),
    ("Vishwa ka pehla ganit ka 'Zero' kis se joda jata hai?", ("Aryabhatta", "Newton", "Einstein", "Galileo"), 0,
     "Aryabhatta Bihar (Kusumapura) se jude the."),
    ("Bihar ka sabse bada shehar (aabadi se) kaunsa hai?", ("Gaya", "Patna", "Bhagalpur", "Muzaffarpur"), 1,
     "Patna hi sabse bada hai."),
    ("Bihar me silk (resham) ka sabse bada kendra kaunsa hai?", ("Bhagalpur", "Ara", "Siwan", "Sasaram"), 0,
     "Bhagalpur 'Silk City' kehlata hai."),
    ("Champaran Satyagraha kab hua tha?", ("1917", "1920", "1930", "1942"), 0,
     "Gandhi ji ka pehla satyagraha Bihar (Champaran) me."),
    ("Bihar ka rajya geet kis bhasha me hai?", ("Bhojpuri", "Maithili", "Hindi", "Magahi"), 2,
     "'Mere Bharat Kanth Mani' — Hindi me."),
    ("Sasaram ka mashhoor Smarak kis ka hai?", ("Ashoka", "Sher Shah Suri", "Akbar", "Chandragupta"), 1,
     "Sher Shah Suri ka maqbara Sasaram me hai."),
    ("Bihar ke kis shehar me loktantra ka 'Loknayak' Jayaprakash Narayan ka janm hua?", ("Sitabdiara", "Gaya", "Begusarai", "Katihar"), 0,
     "Sitabdiara (Saran) me 1902 me janm."),
    # ---------------- INDIA GK ----------------
    ("India ke rashtrapita kaun kehlate hain?", ("Nehru", "Mahatma Gandhi", "Patel", "Tagore"), 1,
     "Gandhi ji ko 'Rashtrapita' kaha jata hai."),
    ("Bharat ka rashtriya pashu kaun hai?", ("Hathi", "Sher", "Bagh", "Mor"), 2,
     "Royal Bengal Tiger."),
    ("Bharat ka rashtriya pakshi kaun hai?", ("Kabutar", "Tota", "Mor", "Baya"), 2,
     "Mor 1963 me chuna gaya."),
    ("Bharat ki rajdhani kya hai?", ("Mumbai", "Kolkata", "Nayi Dilli", "Chennai"), 2,
     "Nayi Dilli 1911 me rajdhani bani."),
    ("Bharat ka sabse lamba samundri kinara kis rajya ka hai?", ("Kerala", "Gujarat", "Tamil Nadu", "Odisha"), 1,
     "Gujarat ka kinara sabse lamba hai."),
    ("Bharat ka sabse uncha pahad kaun hai?", ("K2", "Kanchenjunga", "Mount Everest", "Nanda Devi"), 1,
     "Kanchenjunga India me hai (Everest Nepal me)."),
    ("Bharat ka rashtriya khel (sarkari) kaunsa hai?", ("Cricket", "Hockey", "Kabaddi", "Koi nahi"), 3,
     "Sarkari taur par koi rashtriya khel nahi hai!"),
    ("Hockey ke jaadugar kaun kehlate hain?", ("Sachin", "Major Dhyan Chand", "Kohli", "Milkha"), 1,
     "Dhyan Chand ke naam par Khel Ratna ka naam hai."),
    ("Bharat me pehli railway kab chali?", ("1853", "1900", "1947", "1800"), 0,
     "16 April 1853 — Mumbai se Thane."),
    ("Taj Mahal kis shehar me hai?", ("Delhi", "Agra", "Jaipur", "Lucknow"), 1,
     "Shah Jahan ne banwaya — UNESCO site."),
    ("Bharat ka pehla Pradhan Mantri kaun tha?", ("Sardar Patel", "Jawaharlal Nehru", "Rajendra Prasad", "Lal Bahadur"), 1,
     "Nehru 1947 se 1964 tak."),
    ("Bharat ke pehle Rashtrapati kaun the?", ("Nehru", "Rajendra Prasad", "Radhakrishnan", "Patel"), 1,
     "Dr. Rajendra Prasad Bihar ke the!"),
    ("'Jana Gana Mana' kisne likha?", ("Bankim Chandra", "Rabindranath Tagore", "Premchand", "Iqbal"), 1,
     "Tagore ne likha, 1950 me rashtriya gaan bana."),
    ("Bharat ka rashtriya jhande me kitne rango ka chakra hai?", ("Bhagwa", "Neela", "Lal", "Hara"), 1,
     "Ashok Chakra neela hai, 24 taare."),
    ("Bharat ka sabse bada rajya (kshetrafal) kaunsa hai?", ("UP", "Madhya Pradesh", "Rajasthan", "Maharashtra"), 2,
     "Rajasthan sabse bada hai."),
    ("Bharat ki sabse lambi nadi kaun hai?", ("Yamuna", "Ganga", "Godavari", "Brahmaputra"), 1,
     "Ganga 2,525 km."),
    ("ISRO ka headquarters kahan hai?", ("Mumbai", "Bengaluru", "Hyderabad", "Delhi"), 1,
     "Bengaluru me hai."),
    ("Chandrayaan-3 ne kis saal chand par landing ki?", ("2019", "2023", "2021", "2025"), 1,
     "23 August 2023 — duniya me pehla south pole landing."),
    ("Bharat ka Constitution kab lagu hua?", ("15 Aug 1947", "26 Jan 1950", "26 Nov 1949", "2 Oct 1950"), 1,
     "26 January 1950 ko lagu hua."),
    ("Constitution ke banane wale (Drafting) chairman kaun the?", ("Nehru", "Ambedkar", "Patel", "Prasad"), 1,
     "Dr. B.R. Ambedkar."),
    ("Lok Sabha ke sabse zyada seat kis rajya me hain?", ("Bihar", "UP", "Maharashtra", "WB"), 1,
     "UP ke 80 seat hain."),
    ("Bharat ka national song kaunsa hai?", ("Jana Gana Mana", "Vande Mataram", "Sare Jahan Se", "Ae Mere Watan"), 1,
     "'Vande Mataram' — Bankim Chandra."),
    ("Bharat me sabse zyada bhasha kis rajya me boli jati hain (ginti se)?", ("UP", "Bihar", "Maharashtra", "TN"), 0,
     "UP me sabse zyada bhashayein hain."),
    # ---------------- SCIENCE ----------------
    ("Paudhe khana khud banate hain — is process ko kya kehte hain?", ("Shwasan", "Photosynthesis", "Vाष्पोत्सर्जन", "Pachan"), 1,
     "Sunlight + paani + CO2 se khana banta hai."),
    ("Insaan ke shareer me kitni haddiyan hoti hain (bade insaan)?", ("206", "300", "150", "250"), 0,
     "Bachpan me 300+, badi umar me 206."),
    ("Paani ka rasayanik formula kya hai?", ("CO2", "H2O", "O2", "NaCl"), 1,
     "2 hydrogen + 1 oxygen."),
    ("Suraj se humein kya milta hai (energy)?", ("Dhoop/light", "Hawa", "Baadal", "Barish"), 0,
     "Solar energy ki jadd suraj hai."),
    ("Duniya ka sabse bada mahasagar kaunsa hai?", ("Atlantic", "Indian", "Pacific", "Arctic"), 2,
     "Pacific sabse bada hai."),
    ("Barish kis se hoti hai?", ("Hawa", "Baadal", "Dhoop", "Mitti"), 1,
     "Baadal me paani ki boondein bhaari hokar girti hain."),
    ("Earth ka ek chakkar (24 ghante) kis wajah se hota hai?", ("Ghoomna", "Suraj", "Chaand", "Hawa"), 0,
     "Earth apni axis par ghoomti hai."),
    ("Bijli ka avishkar/shodh kisne kiya (bulb)?", ("Newton", "Edison", "Einstein", "Tesla"), 1,
     "Thomas Edison ne practical bulb banaya."),
    ("Sabse tez raftar kya hai?", ("Hawa", "Roshni", "Awaaz", "Paani"), 1,
     "Light ~3 lakh km/second."),
    ("Newton ne kya dhoondha (apple wali kahani)?", ("Gravity", "Bhaap", "Bijli", "Atom"), 0,
     "Gravity ka niyam."),
    ("Vitamin D humein kahan se milta hai?", ("Chawal", "Dhoop", "Doodh", "Namak"), 1,
     "Suraj ki dhoop se skin me banta hai."),
    ("Bharat me monsoon kis mahine se aata hai?", ("June", "January", "March", "October"), 0,
     "June-September — kharif season."),
    ("Kite ka sabse bada planet kaunsa hai?", ("Mars", "Jupiter", "Venus", "Saturn"), 1,
     "Jupiter sabse bada hai."),
    ("Human heart din bhar kitni baar dhadakta hai (average)?", ("~100", "~1 lakh", "~10 lakh", "~1000"), 1,
     "~72 per minute × 1440 = ~1 lakh."),
    ("DNA ka full form kya hai?", ("Deoxyribo Nucleic Acid", "Dinamik Acid", "Data Nova", "Dual Nitro"), 0,
     "Jeev ka genetic code."),
    # ---------------- SPORTS ----------------
    ("Cricket me ek over me kitni ball hoti hain?", ("4", "6", "8", "10"), 1,
     "6 ball = 1 over."),
    ("Sachin Tendulkar ne kitne international century banaye?", ("50", "100", "85", "76"), 1,
     "100 international centuries — world record."),
    ("Olympic khel kitne saal me ek baar hote hain?", ("2", "3", "4", "5"), 2,
     "Har 4 saal me."),
    ("Kabaddi ka home kya India hai?", ("Haan", "Nahi", "Japan", "Iran"), 0,
     "Kabaddi India ka traditional khel hai."),
    ("Chess (shatranj) ka janm kis desh me hua?", ("China", "India", "Russia", "Iran"), 1,
     "Chaturanga se shuru hua — India."),
    ("FIFA World Cup sabse zyada baar kisne jeeta?", ("Germany", "Brazil", "Argentina", "Italy"), 1,
     "Brazil ke 5 khitab."),
    ("Bharat ne Olympic me pehla gold (individual) kisne jeeta?", ("Neeraj", "Abhinav Bindra", "Sushil", "PV Sindhu"), 1,
     "Abhinav Bindra — 2008 shooting."),
    ("Neeraj Chopra kis khel ke star hain?", ("Cricket", "Javelin", "Wrestling", "Badminton"), 1,
     "Javelin throw — Olympic gold 2021."),
    ("IPL kab shuru hua?", ("2005", "2008", "2010", "2012"), 1,
     "2008 me pehla season."),
    ("Badminton me 'Sindhu' ka poora naam?", ("Saina", "PV Sindhu", "Sindhu Devi", "Pusarla Sindhu"), 1,
     "Pusarla Venkata Sindhu."),
    # ---------------- MATHS / LOGIC ----------------
    ("15% of 200 = ?", ("15", "30", "20", "25"), 1,
     "200 ka 10% = 20, 5% = 10 → 30."),
    ("Ek train 60 km/h se 2 ghante chali — kitna door gaya?", ("120 km", "100 km", "60 km", "90 km"), 0,
     "Speed × Time = 60 × 2."),
    ("10, 20, 30, ? — agla number?", ("35", "40", "45", "50"), 1,
     "Har baar +10."),
    ("Rectangle ka area kaise nikalte hain?", ("l+b", "2(l+b)", "l×b", "l/b"), 2,
     "Lambai × Chaudai."),
    ("Ek din me kitne minute hote hain?", ("1440", "1200", "1000", "2400"), 0,
     "24 × 60 = 1440."),
    ("1 se 100 tak ka sum? (1+2+...+100)", ("5000", "5050", "5500", "500"), 1,
     "n(n+1)/2 = 5050."),
    ("2, 4, 8, 16, ? — agla?", ("20", "24", "32", "30"), 2,
     "Har baar double."),
    ("Agar 1 dozen = 12, to 5 dozen = ?", ("50", "55", "60", "65"), 2,
     "12 × 5 = 60."),
    # ---------------- COMPUTER / TECH ----------------
    ("Computer ka 'brain' kaunsa part hai?", ("RAM", "CPU", "Mouse", "Monitor"), 1,
     "CPU = Central Processing Unit."),
    ("WWW ka matlab kya hai?", ("World Wide Web", "Wide Web World", "Web World Wide", "World Web Wide"), 0,
     "Tim Berners-Lee ne banaya."),
    ("UPI ka full form?", ("United Payment India", "Unified Payments Interface", "Universal Pay India", "Union Pay Interface"), 1,
     "NPCI ne banaya — India ka digital payment."),
    ("RAM ka kaam kya hai?", ("Hamesha save", "Aarzi memory", "Chhapna", "Net chalana"), 1,
     "Bijli jaane par RAM saaf ho jaati hai."),
    ("1 GB me kitne MB hote hain?", ("100", "512", "1024", "1000"), 2,
     "1024 MB = 1 GB."),
    ("Email me '@' ka kya kaam hai?", ("Message", "Address alag karna", "File", "Photo"), 1,
     "naam@server.com."),
    ("Wi-Fi ka istemal kya hai?", ("Bijli", "Internet bina taar", "Call", "Camera"), 1,
     "Wireless internet."),
    ("'Ctrl + C' ka kaam?", ("Cut", "Copy", "Paste", "Save"), 1,
     "Copy ke liye."),
    # ---------------- WORLD GK ----------------
    ("Duniya ka sabse bada desh (kshetrafal) kaunsa hai?", ("China", "USA", "Russia", "Canada"), 2,
     "Russia sabse bada hai."),
    ("Duniya me sabse zyada aabadi kis desh ki hai?", ("China", "India", "USA", "Indonesia"), 1,
     "2023 se India pehle number par."),
    ("Nepal ki rajdhani kya hai?", ("Dhaka", "Kathmandu", "Thimphu", "Colombo"), 1,
     "Kathmandu."),
    ("Duniya ka sabse uncha pahad?", ("K2", "Mount Everest", "Kanchenjunga", "Makalu"), 1,
     "Everest 8,848.86 m — Nepal/China border."),
    ("Saudi Arab ki currency kaunsi hai?", ("Dinar", "Riyal", "Dirham", "Dollar"), 1,
     "Saudi Riyal."),
    ("UAE ki currency kaunsi hai?", ("Riyal", "Dinar", "Dirham", "Pound"), 2,
     "UAE Dirham."),
    ("America ke kitne states hain?", ("48", "50", "52", "49"), 1,
     "50 states."),
    ("Neela (blue) rang kis cheez ka symbol hai?", ("Shaanti", "Aag", "Rishta", "Khatra"), 0,
     "Blue = shaanti."),
    ("Kis desh ko 'Land of Rising Sun' kehte hain?", ("China", "Japan", "Korea", "Thai"), 1,
     "Japan — duniya me pehle suraj nikalta hai."),
)


def q_at(i: int):
    try:
        return QUESTIONS[int(i) % len(QUESTIONS)]
    except Exception:                                       # noqa: BLE001
        return QUESTIONS[0]


def daily_set(uid: int, day_key: str, n: int = 5):
    """Aaj ka quiz set — user + date se seed, isliye dobara khole to wahi set."""
    try:
        rnd = random.Random(f"{uid}-{day_key}")
        idxs = rnd.sample(range(len(QUESTIONS)), min(int(n), len(QUESTIONS)))
        return idxs
    except Exception:                                       # noqa: BLE001
        return list(range(5))


# ============================================================ MARKS CALCULATOR
GRADES = ((91, "A1", "Outstanding"), (81, "A2", "Bahut achha"), (71, "B1", "Achha"),
          (61, "B2", "Achha"), (51, "C1", "Theek"), (41, "C2", "Theek"),
          (33, "D", "Pass"), (0, "E", "Fail"))


def pct_of(obtained: float, total: float) -> float:
    try:
        total = float(total)
        if total <= 0:
            return 0.0
        return max(0.0, min(100.0, (float(obtained) / total) * 100.0))
    except Exception:                                       # noqa: BLE001
        return 0.0


def grade_for(pct: float):
    try:
        for minp, g, note in GRADES:
            if pct >= minp:
                return g, note
    except Exception:                                       # noqa: BLE001
        pass
    return "-", "-"


def division_for(pct: float) -> str:
    try:
        if pct >= 60:
            return "First Division 🥇"
        if pct >= 45:
            return "Second Division 🥈"
        if pct >= 33:
            return "Third Division 🥉"
        return "Fail — mehnat badhao 💪"
    except Exception:                                       # noqa: BLE001
        return "-"


def parse_marks(text: str) -> dict:
    """Do tarah ka input:
       •  '350/500'          → percentage + grade + division
       •  '80 75 90 66'      → (har subject 100 me se) total + padha hai kya
       •  'chahiye 33 500 350' → pass ke liye aur kitne chahiye (marks | total | obtained)
    Return: {"ok": True, ...} ya {"ok": False, "error": "saaf wajah"}
    """
    try:
        t = str(text or "").strip().lower()
        if not t:
            return {"ok": False, "error": "Marks bhejein — jaise <code>350/500</code> ya <code>80 75 90</code>"}

        # ---- mode: "chahiye 33 | 500 | 350" ----
        if t.startswith("chahiye") or t.startswith("pass"):
            nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", t)]
            if len(nums) < 3:
                return {"ok": False, "error": "Aise bhejein: <code>chahiye 33 500 350</code> (pass% total obtained)"}
            need_pct, total, got = nums[0], nums[1], nums[2]
            need_marks = (need_pct / 100.0) * total
            left = need_marks - got
            if left <= 0:
                return {"ok": True, "mode": "need", "need_pct": need_pct, "total": total,
                        "got": got, "need_marks": need_marks, "left": 0.0,
                        "passed": True, "pct": pct_of(got, total)}
            return {"ok": True, "mode": "need", "need_pct": need_pct, "total": total,
                    "got": got, "need_marks": need_marks, "left": left,
                    "passed": False, "pct": pct_of(got, total)}

        # ---- mode: "350/500" ----
        m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", t)
        if m:
            got, total = float(m.group(1)), float(m.group(2))
            if total <= 0:
                return {"ok": False, "error": "Total marks 0 nahi ho sakta."}
            p = pct_of(got, total)
            g, note = grade_for(p)
            return {"ok": True, "mode": "ratio", "got": got, "total": total,
                    "pct": p, "grade": g, "grade_note": note,
                    "division": division_for(p)}

        # ---- mode: "80 75 90 66" (subjects, har ek 100 me) ----
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", t)]
        if len(nums) >= 2:
            subs = [n for n in nums if n <= 100]
            if not subs:
                return {"ok": False, "error": "Marks 100 ke andar bhejein."}
            total = 100.0 * len(subs)
            got = sum(subs)
            p = pct_of(got, total)
            g, note = grade_for(p)
            return {"ok": True, "mode": "subjects", "subjects": subs, "got": got,
                    "total": total, "pct": p, "grade": g, "grade_note": note,
                    "division": division_for(p)}
        if len(nums) == 1:
            return {"ok": False, "error": "Ek number se kuch nahi banta — <code>350/500</code> ya <code>80 75 90</code> bhejein."}
        return {"ok": False, "error": "Samajh nahi aaya — <code>350/500</code> ya <code>80 75 90</code> bhejein."}
    except Exception as e:                                  # noqa: BLE001
        return {"ok": False, "error": f"Technical dikkat ({type(e).__name__})."}


# ============================================================ YOJANA CHECKER
# fields: name, emoji, kis ke liye (age/who), 1-line, apply-hint
#  who: farmer / labour / student / business / women / all / old / girl
#  gender: "" (sab) / female / male
#  income_cap: saalana (None = koi limit nahi)
SCHEMES = (
    # ---- kisan ----
    {"n": "PM Kisan Samman Nidhi", "e": "🌾", "who": ("farmer",),
     "inc": None, "g": "", "d": "Kisan ko Rs.6,000/saal (3 kist) seedha bank me",
     "a": "PM Kisan portal / CSC centre par registration — zameen ke kagaz chahiye"},
    {"n": "Kisan Maandhan Yojana", "e": "👨‍🌾", "who": ("farmer",),
     "inc": None, "g": "", "d": "60 saal ke baad Rs.3,000/month pension",
     "a": "CSC centre par — bank + Aadhaar chahiye, chhoti monthly kist jama karni hoti hai"},
    {"n": "Fasal Bima Yojana (PMFBY)", "e": "🌦️", "who": ("farmer",),
     "inc": None, "g": "", "d": "Fasal kharab hone par bima ka paisa",
     "a": "Bank / CSC se — buwai se pehle karwana zaroori hai"},

    # ---- labour / mazdoor ----
    {"n": "e-Shram Card", "e": "🦺", "who": ("labour",),
     "inc": None, "g": "", "d": "Mazdoor ki pehchaan — Rs.2 lakh tak ki durghatna bima",
     "a": "e-Shram portal / CSC par free registration (Aadhaar + bank)"},
    {"n": "PM Vishwakarma Yojana", "e": "🔨", "who": ("labour", "business"),
     "inc": None, "g": "", "d": "Karigar (badhai, lohar, darzi...) ko sasta loan + talim",
     "a": "Vishwakarma portal / CSC — karigari ka certificate chahiye"},
    {"n": "Ayushman Bharat (PM-JAY)", "e": "🏥", "who": ("all", "labour", "farmer"),
     "inc": None, "g": "", "d": "Rs.5 lakh tak FREE ilaaj ka card",
     "a": "Panchayat / block office / CSC — ration card jaisi jaankari"},

    # ---- students (school) ----
    {"n": "Post Matric Scholarship", "e": "🎒", "who": ("student",),
     "inc": 250000, "g": "", "d": "Class 11 se aage ki padhai ka kharcha (SC/ST/OBC/Minority)",
     "a": "SC/ST/OBC portal ya college office — income certificate chahiye"},
    {"n": "Pre Matric Scholarship", "e": "📚", "who": ("student",),
     "inc": 100000, "g": "", "d": "Class 9-10 ke students ko fees + kitab ka paisa",
     "a": "School office / state portal — income certificate"},
    {"n": "Pragati / Saksham Scholarship", "e": "🎓", "who": ("student",),
     "inc": 800000, "g": "", "d": "Technical college (diploma/degree) ki ladkiyon/differently-abled ke liye",
     "a": "AICTE portal — college se form"},
    {"n": "National Scholarship Portal (NSP)", "e": "🧑‍🎓", "who": ("student",),
     "inc": 250000, "g": "", "d": "Ek hi jagah sab central scholarship (fees + mahine ka kharcha)",
     "a": "scholarships.gov.in par OTP se login (school/college verify karta hai)"},

    # ---- Bihar special ----
    {"n": "Bihar Student Credit Card", "e": "💳", "who": ("student", "business"),
     "inc": None, "g": "", "d": "Padhai ke liye Rs.4 lakh tak ka loan — koi guarantee nahi chahiye",
     "a": "DRCC / bank branch — 12th pass + admission letter"},
    {"n": "Mukhyamantri Kanya Utthan Yojana", "e": "👧", "who": ("student", "girl"),
     "inc": None, "g": "female", "d": "Bihar ki ladkiyon ko padhai par ticket-ticket paisa (graduation tak)",
     "a": "College / university ke through — kagaz college jama karta hai"},
    {"n": "Ladli Behna (Bihar)", "e": "👩", "who": ("women",),
     "inc": None, "g": "female", "d": "Bihar ki mahilaon ko mahine ka samman nidhi (kul MMRY)",
     "a": "Zila/prakhand office — list me naam check karo"},
    {"n": "Bihar Divyangjan Pension", "e": "♿", "who": ("all",),
     "inc": None, "g": "", "d": "Divyang jan ko mahine ki pension",
     "a": "Anchal/block office — divyang certificate chahiye"},
    {"n": "Bihar Old Age Pension", "e": "👴", "who": ("old",),
     "inc": None, "g": "", "d": "60+ walon ko mahine ki pension",
     "a": "Block/panchayat office — umar ka proof (Aadhaar)"},
    {"n": "Bihar Widow Pension", "e": "🕊️", "who": ("women",),
     "inc": None, "g": "female", "d": "Vidhwa mahilaon ko mahine ki pension",
     "a": "Block office — pati ka death certificate"},

    # ---- ghar / bijli ----
    {"n": "PM Awas Yojana (Gramin)", "e": "🏠", "who": ("all", "labour"),
     "inc": None, "g": "", "d": "Pakka ghar banane ke liye paisa (kist me)",
     "a": "Panchayat / block office — SECC list me naam hona chahiye"},
    {"n": "Ujjwala Yojana (LPG)", "e": "🔥", "who": ("women",),
     "inc": None, "g": "female", "d": "Free / sasta LPG gas connection mahilaon ko",
     "a": "Gas agency / CSC — BPL card jaisi jaankari"},
    {"n": "Saubhagya (Bijli Connection)", "e": "💡", "who": ("all",),
     "inc": None, "g": "", "d": "Ghar me bijli ka naya connection",
     "a": "NIWASI/BSPHCL office ya CSC"},

    # ---- paisa / rozgar ----
    {"n": "Mudra Loan (Shishu/Kishor/Tarun)", "e": "🏦", "who": ("business",),
     "inc": None, "g": "", "d": "Chhota dhandha shuru karne ke liye Rs.10 lakh tak loan",
     "a": "Bank branch — dhandhe ka chhota plan + KYC"},
    {"n": "Stand Up India", "e": "🚀", "who": ("business",),
     "inc": None, "g": "", "d": "SC/ST ya mahila udyami ko Rs.10 lakh-Rs.1 crore loan",
     "a": "Bank branch — project report ke saath"},
    {"n": "PM SVANidhi", "e": "🛒", "who": ("business",),
     "inc": None, "g": "", "d": "Rehdi-pathar wale ki dukaan ke liye sasta loan",
     "a": "Nagri nikaya / CSC — vendor certificate"},
    {"n": "MGNREGA (100 din ka kaam)", "e": "⛏️", "who": ("labour", "all"),
     "inc": None, "g": "", "d": "Gaon me 100 din ka kaam — pura ka pura paisa bank me",
     "a": "Gram panchayat — job card banwao (free)"},
    {"n": "Atal Pension Yojana", "e": "🧓", "who": ("all", "labour", "business"),
     "inc": None, "g": "", "d": "60 ke baad Rs.1,000-Rs.5,000 mahine ki pension",
     "a": "Bank / post office — auto-debit lagta hai"},

    # ---- ladki / bachcha ----
    {"n": "Sukanya Samriddhi (ladki ki bachat)", "e": "🌸", "who": ("girl", "women", "all"),
     "inc": None, "g": "", "d": "Beti ke naam par sarkari bachat — bharose wala interest",
     "a": "Post office / bank — beti ki janm-praman patra"},
    {"n": "PM Matru Vandana Yojana", "e": "🤰", "who": ("women",),
     "inc": None, "g": "female", "d": "Pehli bar maa banne par Rs.5,000 madad",
     "a": "Aanganwadi / CSC — MCP card chahiye"},
    {"n": "Poshan Abhiyan (Aanganwadi)", "e": "🍲", "who": ("women", "girl"),
     "inc": None, "g": "female", "d": "Bachcha + maa ke liye free poshan",
     "a": "Nazdeeki aanganwadi kendra"},
    {"n": "Ration / NFSA Card", "e": "🍚", "who": ("all", "labour", "farmer"),
     "inc": None, "g": "", "d": "Sasta ration — gareeb parivar ke liye",
     "a": "Block supply office / CSC — parivar ke kagaz"},
    {"n": "Antyodaya (AAY) Ration", "e": "🥇", "who": ("all", "old"),
     "inc": None, "g": "", "d": "Sabse gareeb parivaron ko extra sasta ration",
     "a": "Block supply office — BPL/AAY list check"},
)

WORK_OPTIONS = (
    ("farmer",   "🌾 Khetee / Kisan"),
    ("labour",   "🦺 Mazdoori / Karigari"),
    ("student",  "🎓 Padhai kar raha hoon"),
    ("business", "🏪 Chhota dhandha / Dukaan"),
    ("women",    "👩 Ghar / Mahila (kaam nahi)"),
    ("old",      "👴 Pension ki umar (60+)"),
    ("all",      "🔹 Kuch aur / All"),
)

INCOME_OPTIONS = (
    ("100000", "₹1 lakh se kam"),
    ("250000", "₹1-2.5 lakh"),
    ("800000", "₹2.5-8 lakh"),
    ("999999999", "₹8 lakh se zyada"),
)


def match_schemes(work: str, gender: str = "", income: float = 1e12, age: int = 0):
    """Profile ke hisaab se yojana chuno (approx — final official portal par)."""
    out = []
    try:
        for sch in SCHEMES:                                 # 's' naam jaan-boojh ke nahi
            who = sch.get("who") or ()
            if work and work not in who and "all" not in who:
                continue
            g = sch.get("g") or ""
            if g and gender and g != gender:
                continue
            cap = sch.get("inc")
            if cap and float(income or 0) > float(cap):
                continue
            out.append(sch)
        # relevant score: work exact match > all
        out.sort(key=lambda x: (work not in (x.get("who") or ()), x.get("n") or ""))
        return out
    except Exception:                                       # noqa: BLE001
        return out
