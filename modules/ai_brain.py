# -*- coding: utf-8 -*-
"""
🧠 AI BRAIN (v44) — Clip Maker ke liye advanced AI layer.

Do provider support (jo key mile wahi chalta hai, dono ho to Gemini pehle):

  • Google **Gemini** (video + audio samajhta hai)
      GEMINI_API_KEY  → model: GEMINI_MODEL   (default gemini-2.5-flash)
      Video ke frames + audio ka sample bhejta hai → moments choose karta hai.

  • **Groq** (fast + free tier)
      GROQ_API_KEY    → GROQ_MODEL            (default llama-3.3-70b-versatile)
      Whisper (GROQ_WHISPER_MODEL, default whisper-large-v3-turbo) se poora
      transcript + timestamps nikalta hai, phir loudness ke saath mila kar
      best windows chunta hai.

  • Key na ho → AI layer chup-chaap OFF; Clip Maker apne classic
      (loud + scene) engine se chalta hai — bot kabhi crash nahi karta.

Sab public functions dict return karte hain: {"ok": True/False, ...} — kabhi raise nahi.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import tempfile

import requests

try:
    from modules import clip_maker as cm
except Exception:                                     # pragma: no cover
    import clip_maker as cm                           # type: ignore

UA = {"User-Agent": "ToolVault-AIBrain/1.0"}

# ----- keywords jo "mazedaar moment" batate hain (transcript scoring ke liye) -----
HYPE_WORDS = [
    "haha", "hahaha", "laugh", "laughter", "applause", "clap", "cheer", "wow", "woww",
    "omg", "oh my god", "what", "kya", "arre", "arey", "bhai", "yaar", "dar", "dhamaka",
    "goal", "six", "four", "out", "chakka", "khatarnaak", "gajab", "zabardast", "mast",
    "shabash", "wah", "ooooo", "aaaa", "no way", "insane", "crazy", "boom", "bam",
    "सच", "अरे", "वाह", "हाहा", "क्या", "भाई", "गजब", "जबरदस्त", "शाबाश",
]


# =====================================================================
# Provider detection
# =====================================================================
def gemini_key() -> str:
    return (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()


def groq_key() -> str:
    return (os.environ.get("GROQ_API_KEY") or "").strip()


def gemini_model() -> str:
    return (os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash").strip()


def groq_model() -> str:
    return (os.environ.get("GROQ_MODEL") or "llama-3.3-70b-versatile").strip()


def whisper_model() -> str:
    return (os.environ.get("GROQ_WHISPER_MODEL") or "whisper-large-v3-turbo").strip()


def ai_off_by_env() -> bool:
    return (os.environ.get("AI_MODE") or "auto").strip().lower() in ("off", "0", "false", "no")


def ai_available() -> bool:
    if ai_off_by_env() or os.environ.get("AI_MOCK") == "1":
        return not ai_off_by_env()
    return bool(gemini_key() or groq_key())


def ai_label() -> str:
    if not ai_available():
        return "classic"
    if gemini_key():
        return f"Gemini {gemini_model()}"
    if groq_key():
        return f"Groq {groq_model()}"
    if os.environ.get("AI_MOCK") == "1":
        return "AI (mock · test mode)"
    return "classic"


def provider_name() -> str:
    if gemini_key():
        return "gemini"
    if groq_key():
        return "groq"
    if os.environ.get("AI_MOCK") == "1":
        return "mock"
    return "none"


# =====================================================================
# ffmpeg helpers (video → frames + chhota audio namuna)
# =====================================================================
def _ffmpeg() -> str:
    return cm.ffmpeg_path()


def _run(args: list, timeout: int = 300) -> bool:
    try:
        p = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
        return p.returncode == 0
    except Exception:
        return False


def extract_audio(video: str, dest: str, start: float = 0.0, dur: float = None,
                  bitrate: str = "16k") -> bool:
    """Mono 16kHz mp3 — AI ko bhejne layak chhota (1 min ≈ 120KB)."""
    a = [_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error"]
    if start > 0:
        a += ["-ss", f"{start:.2f}"]
    a += ["-i", video]
    if dur:
        a += ["-t", f"{dur:.2f}"]
    a += ["-vn", "-ac", "1", "-ar", "16000", "-b:a", bitrate, dest]
    return _run(a) and os.path.exists(dest) and os.path.getsize(dest) > 1000


def grab_frame(video: str, ts: float, dest: str, width: int = 480) -> bool:
    a = [_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0.0, ts):.2f}",
         "-i", video, "-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "6", dest]
    return _run(a, timeout=90) and os.path.exists(dest) and os.path.getsize(dest) > 400


def _b64(path: str) -> str:
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def _data_url(path: str, mime: str) -> str:
    return f"data:{mime};base64,{_b64(path)}"


# =====================================================================
# HTTP helpers
# =====================================================================
def _post_json(url: str, payload: dict, headers: dict, timeout: int = 120) -> dict:
    try:
        r = requests.post(url, json=payload, headers={**UA, **headers}, timeout=timeout)
        if r.status_code >= 400:
            return {"ok": False, "error": f"HTTP {r.status_code}: {_clean(r.text)[:200]}"}
        return {"ok": True, "json": r.json()}
    except Exception as e:
        return {"ok": False, "error": _clean(str(e))[:200]}


def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", str(t or "")).strip()


def _json_from_text(txt: str) -> dict:
    """Model ke jawab me se JSON nikaalo (```json fences bhi chalega)."""
    t = str(txt or "").strip()
    t = re.sub(r"^```(?:json)?|```$", "", t, flags=re.M).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", t)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return {}
    return {}


# =====================================================================
# Gemini — video (frames) + audio ek saath
# =====================================================================
def gemini_generate(parts: list, timeout: int = 150) -> dict:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{gemini_model()}:generateContent?key={gemini_key()}")
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0.25, "responseMimeType": "application/json"},
    }
    res = _post_json(url, payload, {"Content-Type": "application/json"}, timeout=timeout)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}
    try:
        cand = (res["json"].get("candidates") or [])[0]
        txt = "".join(p.get("text", "") for p in cand["content"]["parts"])
        return {"ok": True, "data": _json_from_text(txt), "raw": txt}
    except Exception as e:
        return {"ok": False, "error": f"bad reply: {_clean(str(e))[:120]}"}


# =====================================================================
# Groq — Whisper transcript + Llama (text)
# =====================================================================
def groq_transcribe(audio_path: str, timeout: int = 240) -> dict:
    """Whisper se transcript + segments (start/end) — laugh/applause markers ke saath."""
    if not groq_key():
        return {"ok": False, "error": "no groq key"}
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    try:
        with open(audio_path, "rb") as fh:
            r = requests.post(
                url,
                headers={**UA, "Authorization": f"Bearer {groq_key()}"},
                files={"file": (os.path.basename(audio_path), fh, "audio/mpeg")},
                data={"model": whisper_model(), "response_format": "verbose_json",
                      "temperature": "0"},
                timeout=timeout)
        if r.status_code >= 400:
            return {"ok": False, "error": f"HTTP {r.status_code}: {_clean(r.text)[:160]}"}
        j = r.json()
        segs = [{"start": float(s.get("start") or 0), "end": float(s.get("end") or 0),
                 "text": _clean(s.get("text"))} for s in (j.get("segments") or [])]
        return {"ok": True, "text": _clean(j.get("text")), "segments": segs}
    except Exception as e:
        return {"ok": False, "error": _clean(str(e))[:160]}


def groq_chat_json(prompt: str, timeout: int = 90) -> dict:
    if not groq_key():
        return {"ok": False, "error": "no groq key"}
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": groq_model(),
        "temperature": 0.25,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You are a professional short-video editor. Always answer with JSON only."},
            {"role": "user", "content": prompt},
        ],
    }
    res = _post_json(url, payload, {"Content-Type": "application/json",
                                    "Authorization": f"Bearer {groq_key()}"}, timeout=timeout)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}
    try:
        txt = res["json"]["choices"][0]["message"]["content"]
        return {"ok": True, "data": _json_from_text(txt), "raw": txt}
    except Exception as e:
        return {"ok": False, "error": f"bad reply: {_clean(str(e))[:120]}"}


# =====================================================================
# Moments plan — dono providers ke liye ek hi interface
# =====================================================================
def _candidate_lines(cands: list) -> str:
    out = []
    for c in cands[:18]:
        out.append(f"  {c['start']:.0f}-{c['end']:.0f}s (energy {c.get('score', 0):.2f}, "
                   f"{c.get('scenes', 0)} cuts)")
    return "\n".join(out)


def _keyword_hits(text: str) -> int:
    low = (text or "").lower()
    return sum(low.count(w) for w in HYPE_WORDS)


def _title_from_text(t: str, limit: int = 46) -> str:
    t = _clean(t)
    t = re.sub(r"\[[^\]]*\]", "", t).strip(" .,-")
    if not t:
        return ""
    if len(t) > limit:
        t = t[:limit].rsplit(" ", 1)[0] + "…"
    return t


def _clean_moments(items: list, duration: float, count: int, min_len: float) -> list:
    """AI ke jawab ko saaf karo: bounds, overlap, min length, max count."""
    out = []
    for it in items or []:
        try:
            s = float(it.get("start", it.get("from", 0)))
            e = float(it.get("end", it.get("to", 0)))
        except Exception:
            continue
        if e <= s:
            continue
        s = max(0.0, min(s, max(0.0, duration - 5)))
        e = min(duration, e)
        if e - s < min_len:                      # bahut chhota → aage badhao
            e = min(duration, s + min_len)
        if e - s < 6:
            continue
        try:
            sc = float(it.get("score", 0) or 0)
        except Exception:
            sc = 0.0
        out.append({"start": round(s, 2), "end": round(e, 2), "score": sc,
                    "title": _title_from_text(str(it.get("title") or "")),
                    "reason": _title_from_text(str(it.get("reason") or ""), 90)})
    out.sort(key=lambda c: (-c["score"], c["start"]))
    picked = []
    for c in out:
        if any(not (c["end"] <= p["start"] + 0.4 or c["start"] >= p["end"] - 0.4) for p in picked):
            continue
        picked.append(c)
        if len(picked) >= count:
            break
    picked.sort(key=lambda c: c["start"])
    return picked


def plan_moments(video: str, duration: float, count: int = 6, min_len: float = 15.0,
                 target_len: float = 35.0, candidates: list = None,
                 progress=None) -> dict:
    """
    Video → AI ke chune hue best moments.
    Returns {"ok":True,"moments":[{start,end,score,title,reason}],"engine":label,"transcript":n}
    """
    if os.environ.get("AI_MOCK") == "1":
        mocks = []
        step = max(min_len, duration / max(1, count + 1))
        for i in range(min(count, max(1, int(duration // max(min_len, 8))))):
            s = round(i * step, 2)
            mocks.append({"start": s, "end": round(min(duration, s + target_len), 2),
                          "score": 9 - i, "title": f"AI moment {i + 1}", "reason": "mock"})
        return {"ok": True, "moments": mocks, "engine": "AI (mock)", "transcript": 0}

    providers = []
    gerr = ""
    if gemini_key():
        providers.append("gemini")
    if groq_key():
        providers.append("groq")
    if not providers:
        return {"ok": False, "error": "AI key set nahi hai"}

    tmp = tempfile.mkdtemp(prefix="aib_")
    try:
        if progress:
            progress("🧠 AI video dekh raha hai…")
        cands = candidates or cm.candidates_for_ai(video, count=max(count + 6, 12))
        cand_txt = _candidate_lines(cands)

        if "gemini" in providers:
            # ---- frames (poori video se) + audio (top moment ke aas-paas) ----
            parts = []
            n_frames = int(os.environ.get("AI_FRAMES", "12"))
            used_frames = 0
            for i in range(n_frames):
                ts = duration * (i + 0.5) / n_frames
                fp = os.path.join(tmp, f"f{i:02d}.jpg")
                if grab_frame(video, ts, fp):
                    parts.append({"inline_data": {"mime_type": "image/jpeg", "data": _b64(fp)}})
                    used_frames += 1
            if progress:
                progress(f"🖼️ {used_frames} frames + audio AI ko bhej raha hoon…")
            top = cands[:2] if cands else []
            audio_parts = 0
            for i, c in enumerate(top):
                ap = os.path.join(tmp, f"a{i}.mp3")
                if extract_audio(video, ap, start=max(0.0, c["start"] - 5),
                                 dur=min(150.0, max(60.0, c["end"] - c["start"] + 20))):
                    parts.append({"inline_data": {"mime_type": "audio/mp3", "data": _b64(ap)}})
                    audio_parts += 1
            prompt = (
                f"You are a professional short-video editor. Video length is {duration:.1f} seconds.\n"
                f"Pick the {count} BEST moments for short clips (each {int(min_len)}-{int(target_len + 20)} seconds).\n"
                "What makes a great clip: real laughs, cheering/applause, shouting, dramatic music hits, "
                "sudden action/motion, surprises, emotional peaks, funny reactions. Avoid: boring talking, "
                "logos, intros, black/silent frames, repeated content.\n"
                "The images are frames from the video in order; the audio samples come from the loudest parts.\n"
                f"Extra hint — energy analysis of candidate windows (seconds: energy/cuts):\n{cand_txt}\n\n"
                "Answer ONLY with JSON: {\"moments\":[{\"start\":sec,\"end\":sec,\"score\":1-10,"
                "\"title\":\"short label in English (max 6 words)\",\"reason\":\"why this moment\"}]}. "
                "Seconds must be numbers inside 0..duration, moments must NOT overlap, sort by score."
            )
            parts.insert(0, {"text": prompt})
            res = gemini_generate(parts)
            if res.get("ok"):
                data = res.get("data") or {}
                mm = _clean_moments(data.get("moments") or data.get("clips") or [], duration, count, min_len)
                if mm:
                    return {"ok": True, "moments": mm, "engine": f"AI · {ai_label()}",
                            "frames": used_frames, "audio": audio_parts, "transcript": 0}
            gerr = res.get("error", "")

        if "groq" in providers:
            # ---- Whisper se transcript → hype moments + loudness = final score ----
            ap = os.path.join(tmp, "full.mp3")
            if extract_audio(video, ap, dur=min(duration, float(cm.MAX_MINUTES) * 60), bitrate="12k"):
                if progress:
                    progress("🎧 AI transcript bana raha hai (Whisper)…")
                tr = groq_transcribe(ap)
                if tr.get("ok"):
                    segs = tr.get("segments") or []
                    # segment index → candidates ke andar boost
                    boosted = []
                    for c in cands:
                        hits = 0
                        texts = []
                        for s in segs:
                            if s["end"] >= c["start"] and s["start"] <= c["end"]:
                                hits += _keyword_hits(s["text"])
                                if s["text"]:
                                    texts.append(s["text"])
                        sc = float(c.get("score", 0)) + 3.0 * min(hits, 4)
                        boosted.append({**c, "score": sc, "hits": hits,
                                        "text": _title_from_text(" ".join(texts))})
                    boosted.sort(key=lambda x: -x["score"])
                    # overlap-free top N
                    picked, used = [], []
                    for c in boosted:
                        if any(not (c["end"] <= u[0] or c["start"] >= u[1]) for u in used):
                            continue
                        picked.append(c)
                        used.append((c["start"], c["end"]))
                        if len(picked) >= count:
                            break
                    picked.sort(key=lambda x: x["start"])
                    if picked:
                        # Llama se sirf titles (chhota, sasta request)
                        tp = ("Give a short English label (max 6 words) for each video moment. "
                              "Reply JSON {\"titles\":[\"...\"]} in the same order.\n"
                              + json.dumps([c.get("text") or f"moment at {int(c['start'])}s"
                                            for c in picked], ensure_ascii=False))
                        titles = (groq_chat_json(tp).get("data") or {}).get("titles") or []
                        moments = []
                        for i, c in enumerate(picked):
                            t = _title_from_text(str(titles[i])) if i < len(titles) else (c.get("text") or "")
                            moments.append({"start": c["start"], "end": c["end"], "score": c["score"],
                                            "title": t, "reason": f"{c.get('hits', 0)} hype words"})
                        return {"ok": True, "moments": moments, "engine": f"AI · {ai_label()}",
                                "frames": 0, "audio": 1, "transcript": len(segs)}
                    return {"ok": False, "error": "AI ko is video me moments nahi mile."}
                return {"ok": False, "error": "Transcript failed: " + str(tr.get("error"))[:120]}

        if gemini_key() and gerr:
            return {"ok": False, "error": f"Gemini: {gerr}"}
        return {"ok": False, "error": "AI could not analyse this video."}
    except Exception as e:                                  # noqa: BLE001
        return {"ok": False, "error": _clean(str(e))[:160]}
    finally:
        cm.cleanup(tmp)


# =====================================================================
# Status card (admin /aistatus)
# =====================================================================
def status_card() -> str:
    provider = provider_name()
    lines = ["🧠 <b>AI BRAIN — status</b>", "━━━━━━━━━━━━━━━━━━━━━━"]
    if provider == "gemini":
        lines += ["• Provider: <b>Google Gemini</b> ✅", f"• Model: <code>{gemini_model()}</code>",
                  "• Video: frames + audio samajhta hai ✅",
                  f"• Groq (backup): {'✅ set' if groq_key() else '— not set'}"]
    elif provider == "groq":
        lines += ["• Provider: <b>Groq</b> ✅", f"• Model: <code>{groq_model()}</code>",
                  f"• Whisper: <code>{whisper_model()}</code> ✅",
                  "• Tip: <code>GEMINI_API_KEY</code> add karo to video (frames+audio) bhi AI dekhega"]
    elif provider == "mock":
        lines += ["• Provider: <b>MOCK</b> (testing only)"]
    else:
        lines += ["• Provider: ❌ <b>none</b> — AI layer OFF (classic loud+scene engine chalega)",
                  "",
                  "Render → Environment me ek key add karo:",
                  "• <code>GEMINI_API_KEY</code> = Google AI Studio se (free) → video+audio samajhta hai",
                  "• ya <code>GROQ_API_KEY</code> = Groq console se (free) → Whisper transcript se scoring",
                  "• <code>AI_MODE=off</code> se kabhi band kar sakte ho"]
    lines += [f"• AI_MODE: <code>{os.environ.get('AI_MODE', 'auto')}</code>"]
    return "\n".join(lines)


def live_test() -> dict:
    """Chhota live request — key chal rahi hai ya nahi."""
    if os.environ.get("AI_MOCK") == "1":
        return {"ok": True, "say": "mock ok", "engine": "AI (mock)"}
    try:
        if gemini_key():
            r = gemini_generate([{"text": 'Reply JSON only: {"say":"ok"}'}], timeout=40)
            if r.get("ok"):
                return {"ok": True, "say": str((r.get("data") or {}).get("say") or "ok"),
                        "engine": ai_label()}
            return {"ok": False, "error": str(r.get("error"))[:180]}
        if groq_key():
            r = groq_chat_json('Reply JSON only: {"say":"ok"}', timeout=40)
            if r.get("ok"):
                return {"ok": True, "say": str((r.get("data") or {}).get("say") or "ok"),
                        "engine": ai_label()}
            return {"ok": False, "error": str(r.get("error"))[:180]}
        return {"ok": False, "error": "Koi AI key set nahi hai"}
    except Exception as e:                                   # noqa: BLE001
        return {"ok": False, "error": _clean(str(e))[:180]}
