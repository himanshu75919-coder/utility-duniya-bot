# -*- coding: utf-8 -*-
"""
🔐 CAPTCHA BRIDGE (v74.6) — captcha USER solve karta hai, bot sirf form bhar ke
result laata hai. Ye koi bypass NAHI hai:

  1. Bot official portal ka asli form fetch karta hai (sek jaisa browser).
  2. Captcha ka ASLI image bot user ko Telegram par dikhata hai.
  3. USER captcha padh ke likhta hai (+ roll number).
  4. Bot wahi captcha official server par bhejta hai (bilkul jaise user khud
     browser me karta hai) → result page aata hai.
  5. Bot us page se data nikaal ke PDF marksheet banata hai.

Isliye: bot captcha kabhi khud solve nahi karta, na OCR, na bypass. Insaan ki
aankh se captcha verify hota hai — phir download. Jis board ka form khulega,
wahi board ise use kar sakta hai.
"""
import io
import re
import time

try:
    import requests
except Exception:                                                # noqa: BLE001
    requests = None

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 15

# form me ye field naam aam hote hain (board ke hisaab se badalte hain)
_ROLL_KEYS = ("roll", "rollno", "roll_no", "regno", "reg_no", "enroll", "index",
              "candidate", "registration")
_CAP_KEYS = ("captcha", "imgcode", "seccode", "verifycode", "securitycode", "code")
_DOB_KEYS = ("dob", "birth", "dtbirth")
_SUBMIT_KEYS = ("submit", "btn", "search", "getresult")


def _sess() -> "requests.Session":
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "en-IN,en;q=0.9"})
    return s


def _hidden(html: str) -> dict:
    out = {}
    for m in re.finditer(r'<input[^>]+type=["\']hidden["\'][^>]*>', html, re.I):
        tag = m.group(0)
        n = re.search(r'name=["\']([^"\']+)["\']', tag, re.I)
        v = re.search(r'value=["\']([^"\']*)["\']', tag, re.I)
        if n:
            out[n.group(1)] = v.group(1) if v else ""
    return out


def _inputs(html: str) -> list:
    out = []
    for m in re.finditer(r"<(input|select|textarea)[^>]*>", html, re.I):
        tag = m.group(0)
        n = re.search(r'name=["\']([^"\']+)["\']', tag, re.I)
        if not n:
            continue
        t = re.search(r'type=["\']([^"\']+)["\']', tag, re.I)
        out.append({"name": n.group(1), "type": (t.group(1).lower() if t else "text"),
                    "tag": m.group(1).lower()})
    return out


def _find(html: str, keys) -> str:
    """Field ka ASLI naam (case same rakho — warna board ka POST fail hota hai)."""
    for k in keys:
        for m in re.finditer(r'name=["\']([^"\']+)["\']', html, re.I):
            nm = m.group(1)
            if k in nm.lower() and not nm.startswith("__"):
                return nm
    return ""


def fetch_form(url: str):
    """Official form laao: captcha image + fields + action. Kuch na mile to wajah."""
    if not requests:
        return {"ok": False, "why": "requests nahi hai"}
    try:
        s = _sess()
        r = s.get(url, timeout=TIMEOUT, verify=False, allow_redirects=True)
        html = r.text or ""
        low = html.lower()
        if "digilocker" in low or "login" in low and "captcha" not in low:
            return {"ok": False, "why": "login", "url": r.url}
        if "captcha" not in low and "imgcode" not in low and "seccode" not in low:
            return {"ok": False, "why": "form_nahi", "url": r.url}
        # captcha image
        cap_src = ""
        for m in re.finditer(r'<img[^>]+>', html, re.I):
            tag = m.group(0)
            if any(k in tag.lower() for k in ("captcha", "imgcode", "seccode", "verify", "code")):
                src = re.search(r'src=["\']([^"\']+)["\']', tag, re.I)
                if src:
                    cap_src = src.group(1)
                    break
        if not cap_src:
            return {"ok": False, "why": "captcha_img_nahi", "url": r.url}
        if cap_src.startswith("//"):
            cap_src = "https:" + cap_src
        elif cap_src.startswith("/"):
            base = re.match(r"(https?://[^/]+)", r.url)
            cap_src = (base.group(1) if base else "") + cap_src
        elif not cap_src.startswith("http"):
            cap_src = r.url.rsplit("/", 1)[0] + "/" + cap_src
        img = s.get(cap_src, timeout=TIMEOUT, verify=False)
        if img.status_code != 200 or len(img.content) < 200:
            return {"ok": False, "why": "captcha_img_fail", "url": r.url}
        action = ""
        fm = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', html, re.I)
        if fm:
            action = fm.group(1)
        if not action or action.startswith("#"):
            action = r.url
        elif action.startswith("/"):
            base = re.match(r"(https?://[^/]+)", r.url)
            action = (base.group(1) if base else "") + action
        elif not action.startswith("http"):
            action = r.url.rsplit("/", 1)[0] + "/" + action.lstrip("./")
        fields = _hidden(html)
        cap_name = _find(html, _CAP_KEYS) or "txtimgcode"
        roll_name = _find(html, _ROLL_KEYS) or "txtRollNo"
        dob_name = _find(html, _DOB_KEYS)
        submit_name = _find(html, _SUBMIT_KEYS) or "btnSearch"
        return {"ok": True, "url": r.url, "action": action, "fields": fields,
                "cap_name": cap_name, "roll_name": roll_name, "dob_name": dob_name,
                "submit_name": submit_name, "img": img.content, "sess": s,
                "needs_dob": bool(dob_name)}
    except Exception as e:                                        # noqa: BLE001
        return {"ok": False, "why": str(e)[:60]}


def submit(form: dict, captcha: str, roll: str, dob: str = ""):
    """User ka captcha + roll official server par bhejo → result page."""
    if not (form or {}).get("ok"):
        return {"ok": False, "why": "form_nahi"}
    try:
        s = form["sess"]
        data = dict(form.get("fields") or {})
        data[form["cap_name"]] = captcha.strip()
        data[form["roll_name"]] = roll.strip()
        if form.get("dob_name") and dob:
            data[form["dob_name"]] = dob.strip()
        data.setdefault(form.get("submit_name") or "btnSearch", "Submit")
        r = s.post(form["action"], data=data, timeout=TIMEOUT, verify=False,
                   headers={"Referer": form.get("url") or form["action"]})
        html = r.text or ""
        low = html.lower()
        if any(k in low for k in ("invalid captcha", "wrong captcha", "captcha does not",
                                  "enter correct captcha", "incorrect captcha")):
            return {"ok": False, "why": "captcha_galat"}
        if any(k in low for k in ("not found", "no record", "invalid roll", "does not exist",
                                  "record not")):
            return {"ok": False, "why": "roll_nahi"}
        stu = parse_result(html)
        if stu.get("name") or stu.get("total"):
            return {"ok": True, "student": stu}
        return {"ok": False, "why": "parse", "html_len": len(html)}
    except Exception as e:                                        # noqa: BLE001
        return {"ok": False, "why": str(e)[:60]}


# parse_result ke label patterns
_LBL = {"name": ("name", "candidate", "student"), "father_name": ("father", "fname"),
        "mother_name": ("mother", "mname"), "school_name": ("school", "institute"),
        "roll_no": ("roll", "reg", "enroll", "index"), "dob": ("dob", "birth"),
        "total": ("total", "grand total", "marks obtained", "aggregate"),
        "result": ("result", "status", "outcome"), "division": ("division",)}


def parse_result(html: str) -> dict:
    """Result page se student dict (best-effort — boards ka format alag hota hai)."""
    stu = {}
    txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html or "",
                 flags=re.S | re.I)
    _HDRS = {"sub code", "subject", "subjects", "marks", "total", "grand total", "grade",
             "paper", "theory", "practical", "subject code", "max marks", "obtained",
             "marks obtained", "code", "result", "division"}
    cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip()
             for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", txt, re.I | re.S)]

    # (label → value) pairs — "Father's Name" jaise labels bhi pakdo
    def _tok(x):
        return [t for t in re.sub(r"[^a-z0-9]+", " ", x.lower()).split() if t]

    for i, c in enumerate(cells):
        low = c.lower().strip(" :.·-")
        if not low or low in _HDRS:
            continue
        _tk = _tok(c)
        for key, words in _LBL.items():
            if key in stu:
                continue
            if any(w in _tk or any(t.startswith(w) for t in _tk) for w in words):
                for j in (i + 1, i + 2):
                    if j < len(cells):
                        v = cells[j].strip()
                        if v and v.lower().strip(" :.·-") not in _HDRS and v != c:
                            stu[key] = v[:90]
                            break
                break

    # subjects: row me code/naam + marks
    subs = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", txt, re.I | re.S):
        cs = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip()
              for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.I | re.S)]
        cs = [c for c in cs if c]
        if len(cs) < 2:
            continue
        nums = [c for c in cs if re.fullmatch(r"\d{1,3}(\.\d+)?", c)]
        if not nums:
            continue
        texts = [c for c in cs if re.search(r"[A-Za-z]{3,}", c)
                 and c.lower().strip(" :.·-") not in _HDRS]
        if not texts:
            continue
        nm = max(texts, key=len)
        code = nums[0] if (len(nums) >= 2 and len(cs) >= 3 and len(nums[0]) <= 3) else ""
        marks = nums[-1]
        subs.append({"sub_name": nm[:40], "sub_code": code,
                     "sub_total": marks, "theory": marks})
    if subs:
        stu["subjects"] = subs

    # total label-row se bhi try (jaise "Total | | 271")
    if not stu.get("total"):
        for i, c in enumerate(cells):
            if c.lower().strip(" :.·-") in ("total", "grand total", "marks obtained"):
                for j in (i + 1, i + 2):
                    if j < len(cells) and re.fullmatch(r"\d{1,4}(\.\d+)?", cells[j]):
                        stu["total"] = cells[j]
                        break
    if not stu.get("total") and subs:
        try:
            stu["total"] = sum(float(str(x.get("sub_total") or 0)) for x in subs)
            if float(stu["total"]).is_integer():
                stu["total"] = str(int(stu["total"]))
            else:
                stu["total"] = str(stu["total"])
        except Exception:                                        # noqa: BLE001
            pass
    if not stu.get("result"):
        for i, c in enumerate(cells):
            if c.lower().strip(" :.·-") in ("result", "status", "outcome"):
                if i + 1 < len(cells) and cells[i + 1]:
                    stu["result"] = cells[i + 1][:40]
                    break
    return stu
