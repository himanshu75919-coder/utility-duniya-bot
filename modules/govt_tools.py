# -*- coding: utf-8 -*-
"""
Utility Duniya — GOVT SERVICES ENGINE (v52.0)
==============================================
4 government-related information tools — sab LEGAL (public data, no login,
no CAPTCHA-solving, no OTP, no credential storage):

  1) ⚖️ COURT CASE STATUS   — 16-digit CNR se poora case history
     (eCourtsIndia data API — free ₹200 credits, Bearer token env me)
  2) 📋 SARKARI RESULT      — latest results / admit cards (curated + official links)
  3) 🪪 GOVT ID STATUS      — PAN/Voter/Aadhaar ke CAPTCHA-free official SMS + helpline
  4) 🏛️ GOVT JOB TRACKER   — latest notifications + application last dates

Design rule: koi bhi cheez jo government portal me LOGIN/CAPTCHA/OTP maangta
hai, is bot me automated NAHI hota (legal — IT Act 43/66 + DPDP). Sirf
public information + official CAPTCHA-free tareeke (SMS/helpline) dikhaye jate hain.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

# ============================================================
#  1) ⚖️ COURT CASE STATUS (eCourts data API)
# ============================================================
# API: https://webapi.ecourtsindia.com — free signup par ₹200 credits, koi card nahi.
# Token env me: ECOURTS_API_KEY (eci_live_xxxxx format)
ECOURTS_API_BASE = "https://webapi.ecourtsindia.com"
CNR_RE = re.compile(r"^[A-Z]{4}\d{12}$")


def ecourts_token() -> str:
    return (os.environ.get("ECOURTS_API_KEY") or "").strip()


def validate_cnr(cnr: str) -> bool:
    """CNR = 16 char: 4 letters (court code) + 12 digits. e.g. DLHC010351552024"""
    return bool(CNR_RE.match((cnr or "").strip().upper()))


def ecourts_case_status(cnr: str) -> dict:
    """CNR se poora case status. Returns {ok, error?, data?}.

    Token nahi hai -> {ok: False, 'setup': True} (bot saaf 'pending' msg dikhega).
    """
    import requests

    cnr = (cnr or "").strip().upper()
    if not validate_cnr(cnr):
        return {"ok": False,
                "error": ("CNR number sahi nahi lag raha. 16 character hona chahiye — "
                          "4 letters + 12 digits (jaise <code>DLHC010351552024</code>). "
                          "Ye number aapki case filing receipt / first order me hota hai.")}
    token = ecourts_token()
    if not token:
        return {"ok": False, "setup": True,
                "error": ("Ye tool abhi activate ho raha hai — API setup pending hai. "
                          "Kuch hi din me live ho jayega ✅")}
    try:
        r = requests.get(f"{ECOURTS_API_BASE}/api/partner/case/{cnr}",
                         headers={"Authorization": f"Bearer {token}"},
                         timeout=30)
        if r.status_code == 401:
            return {"ok": False, "error": "API token invalid hai (Render env check karo)."}
        if r.status_code == 404:
            return {"ok": False,
                    "error": (f"Case <code>{cnr}</code> nahi mila. Number dobara check karo — "
                              "16 character exact hone chahiye (koi space/dash nahi).")}
        if r.status_code >= 400:
            return {"ok": False, "error": f"API error {r.status_code} — thodi der baad try karo."}
        payload = r.json()
        return {"ok": True, "data": payload.get("data") or payload}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Server slow hai — 10 second baad dobara try karo."}
    except Exception as e:
        return {"ok": False, "error": f"Connection issue: {str(e)[:120]}"}


def ecourts_card(res: dict) -> str:
    """API response ko Hinglish card me badlo (defensive — keys milne par hi dikhao)."""
    d = res.get("data") or {}
    # API response nesting handle karo: {data: {...}} ya seedha case dict
    c = d.get("case") or d
    if isinstance(c, list) and c:
        c = c[0] if isinstance(c[0], dict) else {}
    lines = [
        "⚖️ <b>CASE STATUS</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]

    def _g(*keys):
        for k in keys:
            if isinstance(c, dict):
                v = c.get(k)
                if v not in (None, ""):
                    return str(v)
        return None

    cnr = _g("cnr", "caseCnr", "cnnr")
    if cnr:
        lines.append(f"🔢 <b>CNR:</b> <code>{cnr}</code>")
    court = _g("courtName", "court", "courtNameH")
    if court:
        lines.append(f"🏛️ <b>Court:</b> {court}")
    ctype = _g("caseType", "caseTypeName", "caseTypeH")
    if ctype:
        lines.append(f"📄 <b>Case Type:</b> {ctype}")
    parties = _g("petitionerName", "petitioner", "parties")
    if parties:
        lines.append(f"👤 <b>Party 1:</b> {str(parties)[:120]}")
    resp = _g("respondentName", "respondent")
    if resp:
        lines.append(f"👤 <b>Party 2:</b> {str(resp)[:120]}")
    judge = _g("judgeName", "benchName", "judge")
    if judge:
        lines.append(f"⚖️ <b>Judge:</b> {str(judge)[:100]}")
    status = _g("caseStatus", "status", "statusH")
    if status:
        lines.append(f"📌 <b>Status:</b> {str(status)[:80]}")
    filing = _g("filingDate", "dateOfFiling", "filedOn")
    if filing:
        lines.append(f"📅 <b>Filing:</b> {str(filing)[:30]}")
    nxt = _g("nextHearingDate", "nextDate", "nextHearing")
    if nxt:
        lines.append(f"🗓️ <b>Aage ki hearing:</b> {str(nxt)[:30]}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("ℹ️ <i>Source: eCourts data (eCourtsIndia API) — official records ka mirror. "
                 "Legal advice ke liye advocate se consult karo.</i>")
    if len(lines) <= 3:
        # Expected keys nahi mile (API shape badal sakti hai) — raw fallback
        import json as _json
        raw = _json.dumps(d, ensure_ascii=False)[:900]
        lines.append(f"📄 <i>Case data mila (API format parse update ho raha hai):</i>\n<code>{raw}</code>")
    return "\n".join(lines)


# ============================================================
#  2) 📋 SARKARI RESULT CENTER (curated feed + official links)
# ============================================================
# Data weekly/monthly refresh hota hai (bot owner side se). Har entry:
# {exam, org, declared, detail, link, state}
GOVT_RESULTS = [
    {"exam": "SSC CGL 2026 (Tier-2 / Final Merit)", "org": "SSC",
     "declared": "14 May 2026", "detail": "15,118 candidates selected — merit list + cut-off",
     "link": "https://ssc.gov.in", "state": "Central"},
    {"exam": "SSC CGL 2026 — Admit Card (Tier-1, 6 Oct exam)", "org": "SSC",
     "declared": "Live abhi", "detail": "Hall ticket download active — ssc.gov.in par login se",
     "link": "https://ssc.gov.in", "state": "Central"},
    {"exam": "UP Board 10th/12th Compartment 2026", "org": "UPMSP",
     "declared": "July 2026", "detail": "Compartment result — roll code + roll number se check",
     "link": "https://upmsp.edu.in", "state": "Uttar Pradesh"},
    {"exam": "UPSSC Forest Guard — Answer Key 2026", "org": "UPSSSC",
     "declared": "Live abhi", "detail": "Answer key check + objection process",
     "link": "https://upsssc.up.nic.in", "state": "Uttar Pradesh"},
    {"exam": "UPSSC Forensic Science Lab — Admit Card 2026", "org": "UPSSSC",
     "declared": "Live abhi", "detail": "Admit card download active",
     "link": "https://upsssc.up.nic.in", "state": "Uttar Pradesh"},
    {"exam": "RRB NTPC 2026 — CBT schedule", "org": "RRB",
     "declared": "Updates aate rahenge", "detail": "3,477 posts — CBT dates Nov 2026 se",
     "link": "https://www.rrbapply.gov.in", "state": "Railway"},
]


def results_text() -> str:
    lines = [
        "📋 <b>SARKARI RESULT CENTER</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "📌 <i>Naye results jaise hi aayenge yahan update honge. Result nikalne ke baad "
        "official site par <b>roll number</b> se check karo:</i>",
        "",
    ]
    for r in GOVT_RESULTS:
        lines.append(f"• <b>{r['exam']}</b> ({r['org']})")
        lines.append(f"   📅 {r['declared']} — {r['detail']}")
        lines.append(f"   🌐 Official: <code>{r['link']}</code>")
        lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 <i>Apna result nahi dikha? Exam ka naam bhejo — main bataunga "
                 "ki kahan se check karna hai.</i>")
    return "\n".join(lines)


def result_search(query: str) -> str:
    q = (query or "").lower()
    hits = [r for r in GOVT_RESULTS
            if q in (r["exam"] + " " + r["org"] + " " + r["state"]).lower()]
    if not hits:
        return ("🔍 " + results_text() +
                "\n\n⚠️ <i>Is feed me wo exam abhi nahi hai — official site par jaake "
                "check karo, ya exam ka naam support me bhejo (@Supermannn_x).</i>")
    out = ["🔍 <b>Matched results:</b>", ""]
    for r in hits:
        out.append(f"• <b>{r['exam']}</b> — {r['declared']}")
        out.append(f"   {r['detail']}")
        out.append(f"   🌐 <code>{r['link']}</code>")
    return "\n".join(out)


# ============================================================
#  3) 🪪 GOVT ID STATUS — CAPTCHA-free official tareeke
# ============================================================
# Kya hota hai: official status check CAPTCHA maangte hain (jo bot nahi tod sakta —
# legal). LEKIN har service ka ek official SMS/helpline tareeka hai — wo CAPTCHA-free
# hai. Bot user ko EXACT SMS ready karke deta hai.
GOVT_ID_SERVICES = {
    "pan_nsidl": {
        "name": "🪪 PAN Card Status (NSDL/Protean)",
        "sms_label": "15-digit acknowledgement number",
        "sms_format": "NSDLPAN {num}",
        "sms_to": "57575",
        "helpline": "020-27218080 (TIN NSDL)",
        "note": "SMS aapke PAN application me diya gaya mobile number par status bhejega.",
    },
    "pan_utiitsl": {
        "name": "🪪 PAN Card Status (UTIITSL)",
        "sms_label": "10-digit application/coupon number + DOB",
        "sms_format": None,
        "sms_to": None,
        "web": "https://www.utiitsl.com/track-pan-card-status",
        "helpline": "022-61761900 (UTIITSL)",
        "note": "UTIITSL me status coupon number + DOB se milta hai (site par chhota captcha hota hai — wo aap khud solve karte ho).",
    },
    "voter_id": {
        "name": "🗳️ Voter ID / EPIC Status",
        "sms_label": "10-digit application/acknowledgement number",
        "sms_format": None,
        "sms_to": None,
        "web": "https://voter.nic.in",
        "app": "Voter Helpline App (NVSP)",
        "helpline": "1950 (Voter Helpline) / 011-24366894",
        "note": "NVSP app ya voter.nic.in par application number se status — app se sabse aasaan.",
    },
    "aadhaar": {
        "name": "🪪 Aadhaar / EPIC Status",
        "sms_label": "14-digit enrolment ID",
        "sms_format": None,
        "sms_to": None,
        "web": "https://uidai.gov.in/enquiry/",
        "helpline": "1800-103-0079 (UIDAI toll-free)",
        "note": "uidai.gov.in par 'EPIC Status Enquiry' — enrolment ID + DOB se. Yahan bhi chhota captcha hai (aap khud, browser me 10 sec ka kaam).",
    },
    "passport": {
        "name": "🛂 Passport Application Status",
        "sms_label": "15-digit file number / ARN",
        "sms_format": "STATUS {file_number} 9704100100",
        "sms_to": "9704100100",
        "web": "https://portal2.passportindia.gov.in",
        "helpline": "1800-258-1313 (Passport Seva)",
        "note": "SMS se police verification status bhi milta hai. File number + DOB se portal par bhi track hota hai.",
    },
    "dl": {
        "name": "🚗 DL / RC Status (PARIVAHAN)",
        "sms_label": "application number",
        "sms_format": None,
        "sms_to": None,
        "web": "https://parivahan.gov.in",
        "helpline": "0120-6740000 (Parivahan helpline)",
        "note": "Parivahan portal par application number se status (chhota captcha — aap khud).",
    },
}


def idguide_card(key: str) -> str:
    svc = GOVT_ID_SERVICES.get(key)
    if not svc:
        return "❌ Service nahi mili. Upar se dobara chuno."
    lines = [svc["name"], "━━━━━━━━━━━━━━━━━━━━━━"]
    if svc.get("sms_format"):
        lines.append(f"📲 <b>OFFICIAL SMS (CAPTCHA-free):</b>")
        lines.append(f"1. <b>{svc['sms_label']}</b> apne paas rakho")
        lines.append(f"2. Ye SMS bhejo:  <code>{svc['sms_format']}</code>")
        lines.append(f"3. SMS number: <b>{svc['sms_to']}</b>")
        lines.append(f"4. Status aapke registered mobile par aa jayega ✅")
    else:
        lines.append("🌐 <b>OFFICIAL TAREEKA:</b>")
        if svc.get("web"):
            lines.append(f"1. Site: <code>{svc['web']}</code>")
        if svc.get("app"):
            lines.append(f"   (ya app: {svc['app']})")
        lines.append(f"2. {svc['sms_label']} se status check karo")
    lines.append(f"📞 <b>Helpline:</b> {svc['helpline']}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"💬 <i>{svc['note']}</i>")
    lines.append("🛡️ <i>Security: sirf official sites/numbers — bot kabhi aapka "
                 "password ya OTP nahi maangta.</i>")
    return "\n".join(lines)


# ============================================================
#  4) 🏛️ GOVT JOB TRACKER (curated live notifications)
# ============================================================
# Data as of: 5 Oct 2026 — monthly refresh (bot owner side se).
GOVT_JOBS = [
    {"org": "SSC", "post": "CHSL (10+2 Level) — 2,536 posts", "qual": "12th Pass",
     "last": "2026-10-07", "link": "https://ssc.gov.in", "region": "Central"},
    {"org": "UPESSC", "post": "PRT Primary Teacher — 12,405 posts", "qual": "B.Ed/D.El.Ed",
     "last": "2026-10-15", "link": "https://upeessc.up.nic.in", "region": "Uttar Pradesh"},
    {"org": "UPESSC", "post": "Pravakta (PGT) — 2,607 posts", "qual": "B.Ed",
     "last": "2026-10-17", "link": "https://upeessc.up.nic.in", "region": "Uttar Pradesh"},
    {"org": "UPESSC", "post": "Assistant Professor — 1,936 posts", "qual": "Masters/M.Ed",
     "last": "2026-10-07", "link": "https://upeessc.up.nic.in", "region": "Uttar Pradesh"},
    {"org": "RRB", "post": "Paramedical Staff — 590 posts", "qual": "B.Pharma/B.Sc",
     "last": "2026-10-14", "link": "https://www.rrbapply.gov.in", "region": "Railway"},
    {"org": "GPRB", "post": "Lokrakshak Cadre — 3,000 posts", "qual": "12th Pass",
     "last": "2026-10-31", "link": "https://www.gprb.co.in", "region": "Goa"},
    {"org": "UPSSSC", "post": "Junior Engineer — 134 posts", "qual": "Diploma/BE",
     "last": "2026-10-07", "link": "https://upsssc.up.nic.in", "region": "Uttar Pradesh"},
    {"org": "UPSSSC", "post": "Senior Instructor — 132 posts", "qual": "Graduate",
     "last": "2026-10-05", "link": "https://upsssc.up.nic.in", "region": "Uttar Pradesh"},
    {"org": "RRC NCR", "post": "JE/ALP/Clerk — 656 posts", "qual": "Diploma/ITI/12th",
     "last": "2026-10-30", "link": "https://www.rrbncr.gov.in", "region": "Railway"},
    {"org": "NCRTC", "post": "Supervisor-I / Jr Maintainer — 90 posts", "qual": "12th/Diploma",
     "last": "2026-10-09", "link": "https://www.ncrtc.in", "region": "NCR"},
    {"org": "UPSC", "post": "Law Officer / JTO — 13 posts", "qual": "LLB/BE",
     "last": "2026-10-16", "link": "https://upsc.gov.in", "region": "Central"},
    {"org": "MPESB", "post": "Constable — 7,500 posts", "qual": "10th/12th",
     "last": "2026-10-04", "link": "https://mpesb.mponline.gov.in", "region": "Madhya Pradesh"},
]
JOBS_DATA_DATE = "5 October 2026"

# Quick region filter map (Hinglish input ke liye)
_REGION_MAP = {
    "up": "Uttar Pradesh", "uttar pradesh": "Uttar Pradesh", "upsssc": "Uttar Pradesh",
    "upeessc": "Uttar Pradesh",
    "bihar": "Bihar", "bpssc": "Bihar",
    "central": "Central", "ssc": "Central", "upsc": "Central", "railway": "Railway",
    "rrb": "Railway", "ncr": "NCR",
}


def jobs_text(region: str = "", keyword: str = "") -> str:
    items = list(GOVT_JOBS)
    rg = _REGION_MAP.get((region or "").strip().lower(), "")
    if rg:
        items = [j for j in items if rg in j["region"] or rg.lower() in j["org"].lower()]
    kw = (keyword or "").strip().lower()
    if kw:
        items = [j for j in items if kw in (j["org"] + " " + j["post"] + " " + j["qual"]).lower()]
    lines = [
        "🏛️ <b>GOVT JOB TRACKER</b> — latest notifications",
        f"📅 <i>Data as of: {JOBS_DATA_DATE} (regular update hota hai)</i>",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]
    if not items:
        lines.append("🔍 Is filter me abhi koi notification feed me nahi hai — "
                     "koi aur state/keyword try karo, ya official site check karo.")
        return "\n".join(lines)
    for j in items[:12]:
        lines.append(f"• <b>{j['org']}</b> — {j['post']}")
        lines.append(f"   🎓 {j['qual']} · ⏰ <b>Last date: {j['last']}</b> · 📍 {j['region']}")
        lines.append(f"   🌐 <code>{j['link']}</code>")
        lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("👉 <b>Filter ke liye bhejo:</b> <code>UP</code> / <code>Central</code> / "
                 "<code>12th</code> / <code>Diploma</code> / <code>ssc</code>")
    return "\n".join(lines)
