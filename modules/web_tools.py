# -*- coding: utf-8 -*-
"""
Web Scraper — v53.0 (PRO REWRITE)
=================================
📄 Kisi bhi PUBLIC page ka **asli article text** (title + author + date + clean body).

v52.3 me kya galat tha (live test se prove hua):
  Wikipedia "Telegram (software)" par **22,515 words** aaye the — usme article ke alawa
  navigation, sidebar, "See also", 300+ references, footnotes, external links,
  categories aur copyright notice sab tha.
  Wajah: code sirf semantic tags hatata tha —
      soup(["script","style","noscript","svg","header","footer","nav","aside","form","iframe"])
  par zyadatar sites (khaas kar Indian news/blog) me ye tags hote hi nahi; sab `<div>`
  me hota hai. To `find("article")` fail → `find("body")` → **poora kachra**.

v53.0 ab kya karta hai (readability-style extraction, koi nayi dependency nahi):
  • **Paragraph scoring** — har candidate block ko score milta hai:
      + text length, + comma count (real prose me commas hote hain),
      + sentence count, + <p> tag bonus
      − link density (nav/menu/reference blocks me link-text ratio high hota hai)
  • **Boilerplate detection** — nav/menu/sidebar/footer/cookie/ad/share/class-based
    patterns + reference-list ("[1]", "[edit]", "Jump to") remove.
  • **Sibling expansion** — top-scoring container ke aas-paas ke similar blocks bhi
    le leta hai (article aksar kai sibling divs me failta hai).
  • **Metadata** — title, author, publish-date, site-name, language, hero image
    (Open Graph + JSON-LD + meta tags, teeno se).
  • **Reading time** + word/paragraph counts.
  • **Markdown output** — headings/bold/list/links preserve, taaki .txt file padhne
    layak ho (pehle ek lambi deewar thi).
  • **SSRF-guarded** + `core.net` se pooled/retry/size-capped fetch.
  • **TTL cache** — same URL 15 min tak dobara fetch nahi.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from modules.core.cache import TTLCache, cached_call
from modules.core.net import NetError, http_get, is_safe_url
from modules.core.telemetry import tracked as _tracked

log = logging.getLogger("ud.scraper")

__all__ = [
    "scrape_public_text", "extract_readable", "web_cache_snapshot",
    "reading_time_min", "html_to_markdown",
]

_UA = os.environ.get(
    "SCRAPER_UA",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
)
_TIMEOUT = float(os.environ.get("SCRAPER_TIMEOUT", "20"))
MAX_BYTES = int(os.environ.get("SCRAPER_MAX_MB", "4")) * 1024 * 1024
_CACHE_TTL = int(os.environ.get("SCRAPER_CACHE_TTL", "900"))
_FAIL_TTL = 60
_MIN_WORDS = int(os.environ.get("SCRAPER_MIN_WORDS", "40"))

_cache = TTLCache(maxsize=int(os.environ.get("SCRAPER_CACHE_SIZE", "256")),
                  default_ttl=_CACHE_TTL)


def web_cache_snapshot() -> dict:
    return _cache.snapshot()


# --------------------------------------------------------------- boilerplate
# Class/id patterns jo almost hamesha chrome (nav/menu/ad/footer) hote hain.
_BAD_PAT = re.compile(
    r"(?i)\b(comment|combx|disqus|extra|foot|header|menu|remark|rss|shoutbox|"
    r"sidebar|sponsor|ad-|advert|promo|banner|breadcrumb|social|share|sharing|"
    r"related|recommend|widget|cookie|consent|newsletter|subscribe|login|signin|"
    r"signup|register|nav|navbar|navigation|toolbar|pagination|pager|toc|"
    r"tags?-|categories|breadcrumb|masthead|site-?branding|jump-?to|"
    r"edit-?section|mw-?editsection|reflist|references|see-?also|external-?links|"
    r"print-?footer|footer|copyright|byline-?tools|article-?tools)\b")

# Poore block jo sirf reference/link-list hote hain
_REF_BLOCK_PAT = re.compile(
    r"(?i)\b(references|bibliography|external links|further reading|see also|"
    r"sources|notes|citations|footnotes)\b")

_NOISE_TAGS = ["script", "style", "noscript", "svg", "template", "iframe", "object",
               "embed", "canvas", "form", "button", "input", "select", "textarea",
               "figcaption"]

# Wikipedia/portal specific junk
_JUNK_LINE_PAT = re.compile(
    r"^\s*(\[\d+\]|\[\s*edit\s*\]|\[\s*citation needed\s*\]|"
    r"Jump to (navigation|search|content)|From Wikipedia, the free encyclopedia|"
    r"Retrieved \d|^\^|doi:\d|ISBN\s|Edit \|)"
    , re.I)

# ⚠️ Backmatter headings — inme se koi bhi paragraph milte hi article KHATAM.
# Live audit: Wikipedia "Telegram (software)" ke 231 paragraphs me se 188-231
# sab references + maintenance categories the ("CS1: unfit URL", "All pages
# needing factual verification", ...). 19% junk.
_BACKMATTER_HEADINGS = re.compile(
    r"^\s*(?:#{0,4}\s*)?(?:\d+(?:\.\d+)*[\s.)-]*)?"
    r"(see\s+also|references|bibliography|external\s+links|further\s+reading|"
    r"notes|sources|citations|footnotes|works\s+cited|works\s+consulted|"
    r"general\s+references|related\s+(?:pages|articles)|categories|"
    r"appendix|glossary|index|comments|reader\s+comments|"
    r"(?:more\s+)?(?:from|around|related)\s+(?:the\s+)?(?:web|news)|"
    r"share\s+(?:this|on)|follow\s+us|newsletter|sign\s+up|"
    r"popular\s+(?:posts|stories)|recommended|you\s+may\s+also\s+like|"
    r"trending|most\s+read|top\s+stories)\s*[:\-—–]?\s*$", re.I)

# Wikipedia maintenance/hidden categories — kabhi content nahi hote
_MAINT_CAT_PAT = re.compile(
    r"(?i)^(all\s+)?(wikipedia\s+)?(articles?|pages?|all\s+pages?)\b.{0,60}"
    r"(needing|requiring|with\s+unsourced|that\s+may\s+contain|"
    r"in\s+need\s+of|lacking|to\s+be\s+|containing|from\s+\w+\s+\d{4}\b)|"
    r"^cs1\s*[:\-]|^pages?\s+using\s+(sister|wikidata|magic)|"
    r"^all\s+(wikipedia|articles|pages)|^webarchive\s+template|"
    r"^use\s+(dmy|mdy)\s+dates|^articles?\s+with|^short\s+description\s+is", re.I)

# Reference-list paragraphs: citation jaisi shape (saal + title + publisher)
_CITATION_PAT = re.compile(
    r"(?i)(\b(?:19|20)\d{2}\b.{0,40}[\"“].{0,80}[\"”])|"
    r"(\bretrieved\b\s+\d{1,2}\s+\w+\s+\d{4})|(\barchived\s+from\b\s+the\s+original)|"
    r"(\b(?:pp|vol|no)\.\s*\d)|(\{\{cite\b)|(isbn\s*[\d\-x]+)|(doi[:\s]*10\.)", re.I)

# Newsletter / subscription / cookie CTAs — article nahi, chrome.
# (Live audit: blog.google ke end me "Check your inbox to confirm your
#  subscription." + privacy-policy line aa rahi thi.)
_CTA_PAT = re.compile(
    r"(?i)^\s*(?:"
    # --- newsletter / subscription ---
    r"check your inbox|confirm your (?:e-?mail|subscription)|"
    r"you can also subscribe|subscribe to (?:our|the)|sign ?up(?:\s|\b)|"
    r"get (?:the )?(?:latest|our|top)\b.{0,40}(?:news|stories|updates|inbox)|"
    r"join .{0,30}(?:newsletter|mailing list)|"
    r"(?:news|delivered) (?:to )?your inbox|"
    # --- form / signup widget artifacts ---
    r"done\.?\s+just one step more|just one step more\.?|"
    r"thank you (?:for|!)|(?:almost|nearly) (?:done|finished|there)|"
    r"please check your (?:e-?mail|inbox)|we(?:'ve| have) sent (?:you|a)|"
    r"(?:something went wrong|please try again)|"
    r"this (?:field|e-?mail) is (?:required|invalid)|invalid (?:e-?mail|email) address|"
    # --- legal / footer boilerplate ---
    r"unsubscribe\b|manage your (?:preferences|subscription)|"
    r"privacy policy\b|terms of (?:use|service)|cookie policy\b|"
    r"all rights reserved|(?:you are|we are) receiving this|"
    r"your (?:e-?mail|information|data) (?:will be|address)|"
    r"we (?:will|may) (?:send|share|use) your|"
    r"by (?:signing up|subscribing|continuing|using this site)|"
    r"you may opt out|this (?:is an|e-?mail was) automatically generated|"
    r"please do not (?:reply|respond)|"
    # --- social / promo chrome ---
    r"follow us on|share this (?:article|story|page|post)|"
    r"report (?:an error|a typo)|corrections?\s*[:?]?\s*$|"
    r"(?:read|see) (?:more|also|full (?:article|story))\b|"
    r"(?:accept|manage) (?:all )?cookies"
    r")"
    # ⚠️ v53.0 fix: pehle yahan `.{0,90}$` tha — matlab trigger ke BAAD poori
    # line 90 chars me khatam honi chahiye. Isse lambi footer lines jaise
    # "Unsubscribe | Privacy Policy | © 2026 Acme Inc. All rights reserved."
    # match hi nahi hoti thin. Line ki lambai ab `_strip_backmatter` ka
    # word-count check (<=30 words) sambhalta hai, regex nahi.
    r".*$", re.I)


def reading_time_min(words: int) -> int:
    """Average Indian reading speed (~200 wpm) par kitne minute lagenge."""
    if not words:
        return 0
    return max(1, round(words / 200.0))


# --------------------------------------------------------------- fetch
def _fetch(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Page fetch karo → (html, error). SSRF-guarded + size-capped."""
    safe, why = is_safe_url(url)
    if not safe:
        return None, f"Ye URL safe nahi hai — {why or 'block ho gaya'}."
    try:
        r = http_get(url, headers={"User-Agent": _UA,
                                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                   "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8"},
                     timeout=_TIMEOUT, max_bytes=MAX_BYTES, retries=1, ssrf_check=False)
    except NetError as e:
        if e.kind == "toobig":
            return None, f"Page bahut bada hai ({MAX_BYTES // (1024*1024)} MB limit)."
        if e.kind == "timeout":
            return None, "Page slow hai — time limit ke andar nahi khula. 1 minute baad try karo."
        if e.kind == "blocked":
            return None, f"Ye URL block hai — {e.message}"
        return None, f"Page open nahi hua: {e.message[:80]}"
    except Exception as e:                                          # noqa: BLE001
        return None, f"Page open nahi hua: {str(e)[:70]}"

    if r.status_code in (401, 403):
        return None, f"Page ne access deny kiya (HTTP {r.status_code}) — login/paywall wali site lagti hai."
    if r.status_code == 404:
        return None, "Ye page nahi mila (HTTP 404). URL check karo."
    if r.status_code >= 500:
        return None, f"Server error (HTTP {r.status_code}). Thodi der baad try karo."
    if r.status_code >= 400:
        return None, f"Page ne HTTP {r.status_code} diya."

    ctype = (r.headers.get("content-type") or "").lower()
    if "html" not in ctype and "text" not in ctype and "xml" not in ctype:
        return None, ("Ye HTML page nahi hai (image/PDF/video/file lagta hai).\n"
                      "📄 Kisi <b>article / blog / news page</b> ka link bhejo.")
    enc = r.encoding or "utf-8"
    try:
        return r.content.decode(enc, errors="replace"), None
    except Exception:                                               # noqa: BLE001
        return r.content.decode("utf-8", errors="replace"), None


# --------------------------------------------------------------- metadata
def _meta_content(soup: BeautifulSoup, **attrs) -> str:
    t = soup.find("meta", attrs=attrs)
    if t and t.get("content"):
        return str(t["content"]).strip()
    return ""


def _json_ld(soup: BeautifulSoup) -> Dict[str, Any]:
    """JSON-LD blocks se article metadata nikalo (NewsArticle/BlogPosting)."""
    out: Dict[str, Any] = {}
    for tag in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        raw = tag.string or tag.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except Exception:                                           # noqa: BLE001
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if not isinstance(it, dict):
                continue
            graph = it.get("@graph")
            if isinstance(graph, list):
                items.extend(x for x in graph if isinstance(x, dict))
                continue
            t = str(it.get("@type") or "")
            if not re.search(r"(?i)article|posting|blog|news|webpage", t):
                continue
            for k_src, k_dst in (("headline", "title"), ("name", "title"),
                                 ("author", "author"), ("datePublished", "date"),
                                 ("dateModified", "date_modified"),
                                 ("publisher", "publisher"), ("description", "description"),
                                 ("image", "image"), ("articleBody", "body"),
                                 ("wordCount", "word_count"), ("inLanguage", "language")):
                v = it.get(k_src)
                if v is None:
                    continue
                if isinstance(v, dict):
                    v = v.get("name") or v.get("url") or v.get("headline") or ""
                elif isinstance(v, list):
                    first = v[0] if v else None
                    if isinstance(first, dict):
                        v = first.get("name") or first.get("url") or ""
                    else:
                        v = first or ""
                if v and not out.get(k_dst):
                    out[k_dst] = str(v).strip()
    return out


def _extract_meta(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    """Title / author / date / site / image / lang — teeno sources se."""
    ld = _json_ld(soup)
    host = urlparse(url).netloc.replace("www.", "")

    title = (ld.get("title")
             or _meta_content(soup, property="og:title")
             or _meta_content(soup, name="twitter:title"))
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        h1 = soup.find("h1")
        title = h1.get_text(" ", strip=True) if h1 else ""
    # site name se suffix hatao ("... - Times of India")
    site = (ld.get("publisher") or _meta_content(soup, property="og:site_name")
            or _meta_content(soup, name="application-name") or host)
    if title and site and site not in host:
        for sep in (" | ", " – ", " - ", " :: ", " » "):
            if title.endswith(sep + site):
                title = title[: -len(sep + site)].strip()
                break

    author = ld.get("author") or _meta_content(soup, name="author") \
        or _meta_content(soup, property="article:author") or _meta_content(soup, name="twitter:creator")
    date = (ld.get("date") or _meta_content(soup, property="article:published_time")
            or _meta_content(soup, name="date") or _meta_content(soup, name="pubdate")
            or _meta_content(soup, itemprop="datePublished"))
    desc = (ld.get("description") or _meta_content(soup, property="og:description")
            or _meta_content(soup, name="description") or _meta_content(soup, name="twitter:description"))
    image = ld.get("image") or _meta_content(soup, property="og:image") \
        or _meta_content(soup, name="twitter:image")
    lang = (ld.get("language") or (soup.html.get("lang") if soup.html else "")
            or _meta_content(soup, **{"http-equiv": "content-language"})
            or _meta_content(soup, property="og:locale"))
    if image and not str(image).startswith("http"):
        image = urljoin(url, str(image))

    return {"title": re.sub(r"\s+", " ", title or "").strip()[:200] or host,
            "author": re.sub(r"\s+", " ", author or "").strip()[:80],
            "date": re.sub(r"\s+", " ", date or "").strip()[:40],
            "site": re.sub(r"\s+", " ", site or "").strip()[:60],
            "description": re.sub(r"\s+", " ", desc or "").strip()[:300],
            "image": str(image or "").strip()[:400],
            "language": str(lang or "").strip()[:12]}


# --------------------------------------------------------------- readability
def _link_density(el: Tag) -> float:
    """Block ke text me se kitna hissa link text hai (0..1). Nav/menu me ~1.0 hota hai."""
    total = len(el.get_text(" ", strip=True))
    if not total:
        return 1.0
    link = sum(len(a.get_text(" ", strip=True)) for a in el.find_all("a"))
    return min(1.0, link / total)


def _score_block(el: Tag) -> float:
    """Ek candidate content block ka score (readability-style)."""
    txt = el.get_text(" ", strip=True)
    words = txt.split()
    n = len(words)
    if n < 15:
        return -1.0

    score = 0.0
    score += min(n / 12.0, 22.0)                 # lamba prose = accha
    score += min(txt.count(",") * 0.9, 14.0)     # commas = real sentences
    # sentence-ish count (danda/period/question)
    sents = len(re.findall(r"[.!?।]\s", txt)) + 1
    score += min(sents * 0.8, 10.0)

    # <p> children bonus
    ps = el.find_all("p", recursive=False)
    score += min(len(ps) * 2.0, 8.0)

    # tag bonus/penalty
    name = (el.name or "").lower()
    if name in ("article", "main"):
        score += 22.0
    elif name == "section":
        score += 4.0
    elif name in ("div",):
        score += 0.0
    elif name in ("td", "li", "ul", "ol", "table"):
        score -= 8.0
    elif name in ("aside", "nav", "header", "footer", "form"):
        score -= 30.0

    # class/id signal
    cls = " ".join([*(el.get("class") or []), str(el.get("id") or ""),
                    str(el.get("role") or "")])
    if _BAD_PAT.search(cls):
        score -= 28.0
    if re.search(r"(?i)\b(article|post|entry|content|story|body|text|prose|blog|main)\b", cls):
        score += 16.0

    # link density — sabse strong signal
    ld = _link_density(el)
    score -= ld * 55.0
    if ld > 0.6:
        score -= 25.0

    # paragraph density (prose blocks me <p> zyada hote hain)
    p_words = sum(len(p.get_text(" ", strip=True).split()) for p in el.find_all("p"))
    if n:
        score += (p_words / n) * 12.0

    return score


_CANDIDATE_TAGS = ("article", "main", "section", "div", "td", "body")


def _candidates(soup: BeautifulSoup) -> List[Tuple[float, Tag]]:
    scored: List[Tuple[float, Tag]] = []
    for el in soup.find_all(_CANDIDATE_TAGS):
        # already-scored ancestor ke andar ka chhota block skip (double counting)
        if _BAD_PAT.search(" ".join([*(el.get("class") or []), str(el.get("id") or "")])):
            continue
        if el.find_parent(["article", "main"]) is not None and el.name in ("div", "section", "td"):
            # article/main ke andar ke divs ko alag se score nahi karte — parent hi jeetega
            if el.name != "article":
                continue
        if _REF_BLOCK_PAT.search(el.get_text(" ", strip=True)[:80]):
            continue
        s = _score_block(el)
        if s > 0:
            scored.append((s, el))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def _clean_text_block(el: Tag) -> List[str]:
    """Block se clean paragraphs ki list banao (junk lines hata ke)."""
    out: List[str] = []
    # seedhe <p> mil jayein to wahi best; warna line-wise
    ps = el.find_all(["p", "h2", "h3", "h4", "li"])
    if not ps:
        raw = el.get_text("\n")
        chunks = [raw]
    else:
        chunks = []
        for p in ps:
            # nested list-item ke andar ke p ko skip
            if p.name == "li" and p.find(["p", "li"]):
                continue
            t = p.get_text(" ", strip=True)
            if p.name in ("h2", "h3", "h4") and t:
                chunks.append("## " + t)
            elif t:
                chunks.append(t)
    for c in chunks:
        c = re.sub(r"[ \t]+", " ", c).strip()
        if not c or len(c.split()) < 3:
            continue
        if _JUNK_LINE_PAT.match(c):
            continue
        if re.fullmatch(r"[\W_]+", c):
            continue
        out.append(c)
    return out


def extract_readable(html: str, url: str = "") -> Dict[str, Any]:
    """HTML → clean article. Returns dict with text/markdown/paragraphs/meta."""
    soup = BeautifulSoup(html, "html.parser")

    # comments + noise tags hatao
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for t in soup(_NOISE_TAGS):
        t.decompose()
    # semantic chrome (jab site ne sahi tags use kiye hon)
    for t in soup(["header", "footer", "nav", "aside"]):
        # header ke andar ka h1 title hota hai — wo metadata me already le liya
        t.decompose()
    # hidden elements
    for t in soup.find_all(attrs={"hidden": True}):
        t.decompose()
    for t in soup.find_all(style=re.compile(r"(?i)display\s*:\s*none")):
        t.decompose()
    # reference/list blocks
    for t in soup.find_all(class_=_REF_BLOCK_PAT):
        t.decompose()
    for t in soup.find_all(id=_REF_BLOCK_PAT):
        t.decompose()

    meta = _extract_meta(soup, url)

    cands = _candidates(soup)
    best: Optional[Tag] = None
    if cands:
        best = cands[0][1]
        # sibling expansion: best ke parent ke bhai-behen jo bhi decent score rakhte hain
        parent = best.parent
        if parent is not None and parent.name not in ("html", "[document]"):
            top_score = cands[0][0]
            extra: List[Tag] = []
            for sib in parent.find_all(_CANDIDATE_TAGS, recursive=False):
                if sib is best:
                    continue
                s = _score_block(sib)
                if s >= top_score * 0.22 and s > 12:
                    extra.append(sib)
            if extra:
                # best + siblings ko ek virtual container me treat karo
                blocks: List[str] = []
                for el in [best, *extra]:
                    blocks.extend(_clean_text_block(el))
                paragraphs = _dedupe(blocks)
                container = "siblings"
            else:
                paragraphs = _clean_text_block(best)
                container = best.name or "div"
        else:
            paragraphs = _clean_text_block(best)
            container = best.name or "div"
    else:
        body = soup.body or soup
        paragraphs = _clean_text_block(body)
        container = "body-fallback"

    paragraphs = _strip_backmatter(paragraphs)
    text = "\n\n".join(paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    words = len(text.split())

    return {
        "text": text,
        "paragraphs": paragraphs,
        "words": words,
        "chars": len(text),
        "para_count": len(paragraphs),
        "reading_min": reading_time_min(words),
        "container": container,
        "score": round(cands[0][0], 1) if cands else 0.0,
        "meta": meta,
        "json_ld_body": bool(meta.get("body")),
    }


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        k = re.sub(r"\W+", "", x.lower())[:120]
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(x)
    return out


def _strip_backmatter(paras: List[str]) -> List[str]:
    """Article ke peeche ka kachra kaato (references / categories / "share this").

    Teen signals:
      1. **Backmatter heading** — "References", "See also", "External links",
         "Categories", "Share this" jaisa standalone heading milte hi wahan se
         aage sab kaat do. (Live audit: Wikipedia Telegram page ke 231 paras me
         se 44 pure references + maintenance categories the.)
      2. **Citation tail** — lagaatar 3+ paragraphs citation-jaisi shape ke hon
         (saal + "quoted title" / "Retrieved 12 May 2024" / ISBN / doi) to wahan
         se kaat do. Ye tab kaam aata hai jab heading text me ghul gaya ho.
      3. **Short maintenance lines** — "CS1: unfit URL", "All pages needing
         factual verification" jaisi chhoti lines end se hatao.

    Hamesha kam-az-kam 25% content bacha rehte hain (over-trim se bachne ke liye),
    aur agar kuch bhi bachta hi nahi to original wapas.
    """
    if not paras:
        return paras
    n = len(paras)
    floor = max(3, int(n * 0.25))     # itne paragraphs hamesha bachenge

    # ---- signal 1: explicit backmatter heading ----
    cut = n
    for i, p in enumerate(paras):
        if i < floor:
            continue
        head = re.sub(r"^\s*(#{1,6}|\d+(?:\.\d+)*[\s.)-]*)\s*", "", p.strip())
        if len(head.split()) <= 7 and _BACKMATTER_HEADINGS.match(head):
            cut = i
            break

    # ---- signal 2: citation tail (3+ lagaatar citation-shaped paras) ----
    if cut > floor:
        run = 0
        for i in range(floor, min(cut, n)):
            p = paras[i]
            is_cit = bool(_CITATION_PAT.search(p)) or _MAINT_CAT_PAT.match(p.strip())
            # chhote lines jo citation-ish hon (author. "title". Publisher. Year.)
            if is_cit and len(p.split()) < 60:
                run += 1
            else:
                run = 0
            if run >= 3:
                cut = min(cut, i - run + 1)
                break

    out = paras[:max(floor, cut)]

    # ---- signal 3: end ki chhoti maintenance / CTA lines hatao ----
    while out and len(out) > floor:
        last = out[-1].strip()
        last = re.sub(r"^\s*(?:#{1,6}|\d+(?:\.\d+)*[\s.)-]*)\s*", "", last)
        words = last.split()
        if (_MAINT_CAT_PAT.match(last)
                or _CTA_PAT.match(last)
                or (len(words) <= 12 and _CITATION_PAT.search(last))
                or _JUNK_LINE_PAT.match(last)
                or re.fullmatch(r"[\W_]+", last)):
            out.pop()
            continue
        break

    # ---- signal 4: beech me ghuse hue CTA/newsletter lines bhi hatao ----
    # (signup form aksar article ke andar embed hota hai, end me nahi)
    # Note: heading paras "## Get the latest news..." ki shape me hote hain,
    # isliye match se pehle markdown/numbering prefix strip karo.
    cleaned = []
    for p in out:
        bare = re.sub(r"^\s*(?:#{1,6}|\d+(?:\.\d+)*[\s.)-]*)\s*", "", p.strip())
        if _CTA_PAT.match(bare) and len(bare.split()) <= 30:
            continue
        cleaned.append(p)
    out = cleaned if cleaned else out

    return out if out else paras


# --------------------------------------------------------------- markdown
def html_to_markdown(html: str, url: str = "") -> str:
    """Poora page nahi — sirf extracted article ko simple markdown me badlo.

    (Telegram .txt file me padhne layak format: headings, bullets, bold.)
    """
    ex = extract_readable(html, url)
    m = ex["meta"]
    lines: List[str] = []
    lines.append("# " + (m["title"] or "Article"))
    byline = []
    if m.get("author"):
        byline.append("✍️ " + m["author"])
    if m.get("date"):
        byline.append("📅 " + m["date"])
    if m.get("site"):
        byline.append("🌐 " + m["site"])
    if byline:
        lines.append("*" + " · ".join(byline) + "*")
    if url:
        lines.append("<" + url + ">")
    if m.get("description"):
        lines.append("> " + m["description"])
    lines.append("")
    lines.append(f"**{ex['words']} words · ~{ex['reading_min']} min read**")
    lines.append("")
    lines.append("---")
    lines.append("")
    for p in ex["paragraphs"]:
        if p.startswith("## "):
            lines.append("")
            lines.append(p)
            lines.append("")
        elif re.match(r"^([-•*]\s|—\s)", p):
            lines.append("- " + re.sub(r"^([-•*]|—)\s*", "", p))
        else:
            lines.append(p)
            lines.append("")
    md = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


# --------------------------------------------------------------- public API
@_tracked("webscraper")
def scrape_public_text(target: str, use_cache: bool = True,
                       markdown: bool = False) -> Dict[str, Any]:
    """Public URL ka readable article text nikalo (SSRF-guarded, cached).

    Returns {"ok":True,"title","text","words",...} ya {"ok":False,"error":...}
    Backward-compatible: `title`/`desc`/`text`/`words`/`url` wahi keys hain jo
    v52.3 me thi, taaki bot.py ka purana code toote nahi.
    """
    url = re.sub(r"\s+", "", (target or "").strip())
    if not url:
        return {"ok": False,
                "error": ("Koi website link bhejo.\n"
                          "📌 Jaise: <code>https://en.wikipedia.org/wiki/Telegram_(software)</code>")}
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    if len(url) > 1800:
        return {"ok": False, "error": "URL bahut lamba hai."}
    ok, why = is_safe_url(url)
    if not ok:
        return {"ok": False, "error": f"Ye URL safe nahi hai — {why or 'block ho gaya'}"}

    def _work():
        html, err = _fetch(url)
        if err:
            return {"ok": False, "error": err, "url": url}
        try:
            ex = extract_readable(html, url)
        except Exception as e:                                      # noqa: BLE001
            log.debug("extract fail %s: %s", url, str(e)[:100])
            return {"ok": False, "error": "Page parse nahi ho paya. Doosra page try karo.",
                    "url": url}
        if ex["words"] < _MIN_WORDS:
            return {"ok": False, "url": url,
                    "error": ("Page khul gaya par <b>readable article text nahi mila</b> "
                              f"({ex['words']} words).\n"
                              "━━━━━━━━━━━━━━━━━━━━━━\n"
                              "Ye tab hota hai jab page:\n"
                              "• JavaScript se banta ho (SPA / React app)\n"
                              "• Login/paywall ke peeche ho\n"
                              "• Sirf photos/video ho, text na ho\n\n"
                              "📌 Kisi <b>news article ya blog post</b> ka link try karo.")}
        m = ex["meta"]
        out = {
            "ok": True,
            "url": url,
            # --- v52.3 compatible keys ---
            "title": m["title"],
            "desc": m["description"],
            "text": ex["text"],
            "words": ex["words"],
            # --- v53.0 naye fields ---
            "author": m["author"],
            "date": m["date"],
            "site": m["site"],
            "image": m["image"],
            "language": m["language"],
            "paragraphs": ex["paragraphs"],
            "para_count": ex["para_count"],
            "reading_min": ex["reading_min"],
            "chars": ex["chars"],
            "container": ex["container"],
            "score": ex["score"],
        }
        if markdown:
            out["markdown"] = html_to_markdown(html, url)
        return out

    if not use_cache:
        return _work()
    val, _hit = cached_call(_cache, f"scrape:{url}", _work, ttl=_CACHE_TTL,
                            fail_ttl=_FAIL_TTL, is_failure=lambda v: not v.get("ok"))
    return val
