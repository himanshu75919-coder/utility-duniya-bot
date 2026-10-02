# -*- coding: utf-8 -*-
"""
Clip Maker (v43)
================
Ek video → 4-7 chhote clips (25-60 sec), "best moments" ya "equal parts", 16:9 ya 9:16.

Bina AI (deterministic):
  🔊 loudness peaks   → ffmpeg astats se 0.5 sec ka RMS  (cheering, hasi, shouting, goal)
  🎬 scene changes    → ffmpeg scene detect (keyframes par, fast)  (action, cuts, edits)
  🎯 score            → window ke andar loudness + scene hits; top windows = clips

Limits (Render free/small safe):
  CLIP_MAX_MINUTES = 15   (video isse bada → saaf error, kuch banega nahi)
  CLIP_COUNT = 6          (kitne clips)
  CLIP_LEN = 35           (target clip length seconds; 18-60 ke beech)
  CLIP_VERTICAL = 540x960 (9:16), normal = 480p
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time

try:
    from modules.desi_tools import ffmpeg_path, ffprobe_duration
except Exception:                                     # standalone test ke liye
    def ffmpeg_path() -> str:
        return os.environ.get("FFMPEG_BIN", "ffmpeg")

    def ffprobe_duration(path: str) -> float:
        return 0.0

MAX_MINUTES = float(os.environ.get("CLIP_MAX_MINUTES", "15"))
CLIP_COUNT = max(3, min(int(os.environ.get("CLIP_COUNT", "6")), 8))
TARGET_LEN = max(18.0, min(float(os.environ.get("CLIP_LEN", "35")), 60.0))
MIN_LEN = 15.0
MIN_VIDEO = 20.0                        # isse chhota video = saaf error
MIN_SCORE_GAP = 3.0                    # do clips ke beech kam se kam gap
MAX_CLIP_MB = 45.0                     # Telegram par bhejne layak
VERT_W, VERT_H = 540, 960
NORM_H = 480
SCENE_THRESH = 0.30


# ---------------------------------------------------------------- helpers
def _ff(args: list, timeout: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run([ffmpeg_path()] + args, capture_output=True, timeout=timeout)


def _tmpdir() -> str:
    return tempfile.mkdtemp(prefix="clips_")


def parse_ffmpeg_probe(text: str) -> dict:
    """ffmpeg -i ka stderr → duration / size / audio."""
    dur, w, h, has_audio = 0.0, 0, 0, False
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text or "")
    if m:
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    m = re.search(r"Video:.*?,\s*(\d{2,5})x(\d{2,5})", text or "")
    if m:
        w, h = int(m.group(1)), int(m.group(2))
    if re.search(r"Audio:\s", text or ""):
        has_audio = True
    return {"duration": round(dur, 1), "width": w, "height": h, "has_audio": has_audio}


def probe_info(path: str) -> dict:
    try:
        cp = _ff(["-hide_banner", "-i", path], timeout=120)
    except Exception:
        return {"duration": 0.0, "width": 0, "height": 0, "has_audio": False}
    info = parse_ffmpeg_probe((cp.stderr or b"").decode("utf-8", "ignore"))
    if not info["duration"]:
        info["duration"] = round(ffprobe_duration(path) or 0.0, 1)
    return info


def fmt_t(sec: float) -> str:
    sec = max(0, int(sec))
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


# ---------------------------------------------------------------- analysis
def audio_rms(path: str, win_sec: float = 0.5) -> list:
    """[(time, dB)] — 0.5 sec ke windows me loudness. -inf (silence) → -70."""
    sr = 8000
    samples = max(400, int(sr * win_sec))
    af = (f"aresample={sr},asetnsamples={samples},astats=metadata=1:reset=1,"
          f"ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-")
    try:
        cp = _ff(["-hide_banner", "-nostdin", "-i", path, "-vn", "-af", af, "-f", "null", "-"], timeout=900)
        txt = (cp.stdout or b"").decode("utf-8", "ignore") + (cp.stderr or b"").decode("utf-8", "ignore")
    except Exception:
        return []
    vals = []
    for m in re.finditer(r"RMS_level=(-?[\d.]+|-inf)", txt):
        s = m.group(1)
        db = -70.0 if s == "-inf" else float(s)
        vals.append(max(-70.0, min(0.0, db)))
    return [(round(i * win_sec, 2), v) for i, v in enumerate(vals)]


def scene_times(path: str, thresh: float = SCENE_THRESH) -> list:
    """Scene change ke seconds (keyframes par detect — fast)."""
    try:
        cp = _ff(["-hide_banner", "-nostdin", "-skip_frame", "nokey", "-i", path, "-an",
                  "-vf", f"scale=160:-2,select='gt(scene,{thresh})',metadata=print:file=-",
                  "-f", "null", "-"], timeout=600)
        txt = (cp.stdout or b"").decode("utf-8", "ignore") + (cp.stderr or b"").decode("utf-8", "ignore")
    except Exception:
        return []
    return [round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", txt)]


def _loud(rms: list) -> list:
    """dB → 0..60 score (silence 0)."""
    return [max(0.0, v + 70.0) for _t, v in rms] if rms else []


def _smooth(vals: list, k: int = 3) -> list:
    if not vals:
        return []
    out = []
    for i in range(len(vals)):
        a, b = max(0, i - k // 2), min(len(vals), i + k // 2 + 1)
        out.append(sum(vals[a:b]) / (b - a))
    return out


def pick_best(rms: list, scenes: list, duration: float, count: int = CLIP_COUNT,
              target_len: float = TARGET_LEN) -> list:
    """Loudness + scene se best windows. Return: [{start, dur, score, rank}]"""
    if duration <= 0:
        return []
    count = max(1, count)
    count = min(count, max(1, int(duration // MIN_LEN)))          # itne clips to bante hi hain
    # target se chhota video → clip length ko utna hi rakho jitna fit ho (warna clips kam pad jaate hain)
    L = max(MIN_LEN, min(target_len, duration / count))
    L = min(L, max(MIN_LEN, duration))

    loud = _loud(rms)
    win = 0.5
    smoothed = _smooth(loud)
    if not smoothed:                       # audio nahi / khaali → scene-only ya equal
        cands = [{"start": s, "dur": L, "score": 0.0} for s in _even_starts(duration, count, L)]
    else:
        mean = sum(smoothed) / len(smoothed)
        var = sum((x - mean) ** 2 for x in smoothed) / max(1, len(smoothed))
        std = var ** 0.5
        thr = mean + max(0.6 * std, 2.0)
        peaks = []
        for i, v in enumerate(smoothed):
            if v < thr:
                continue
            lo, hi = max(0, i - 6), min(len(smoothed), i + 7)
            if v >= max(smoothed[lo:hi]):
                t = i * win
                if not peaks or (t - peaks[-1][0]) > max(8.0, L * 0.6):
                    peaks.append((t, v))
        cands = []
        for t, v in peaks:
            start = max(0.0, min(t - 0.35 * L, max(0.0, duration - L)))
            sc = _window_score(smoothed, scenes, start, L, win)
            cands.append({"start": round(start, 2), "dur": round(L, 2), "score": round(sc, 2), "peak": round(t, 2)})
        if len(cands) < count:              # kaafi peaks nahi mile → bache slots evenly bharo
            have = sorted(c["start"] for c in cands)
            for s in _even_starts(duration, count, L):
                if all(abs(s - h) > MIN_SCORE_GAP for h in have):
                    cands.append({"start": round(s, 2), "dur": round(L, 2),
                                  "score": round(_window_score(smoothed, scenes, s, L, win), 2)})

    # score desc → greedy (overlap nahi, par back-to-back allowed) → top `count`
    cands.sort(key=lambda c: -c["score"])
    picked = []
    for c in cands:
        if len(picked) >= count:
            break
        if all(c["start"] + c["dur"] <= p["start"] + 0.05
               or p["start"] + p["dur"] <= c["start"] + 0.05 for p in picked):
            picked.append(c)
    for i, c in enumerate(sorted(picked, key=lambda x: x["start"]), 1):
        c["idx"] = i
    rank = {id(c): r for r, c in enumerate(sorted(picked, key=lambda x: -x["score"]), 1)}
    for c in picked:
        c["rank"] = rank[id(c)]
    return sorted(picked, key=lambda x: x["start"])


def _window_score(smoothed: list, scenes: list, start: float, L: float, win: float) -> float:
    a, b = int(start / win), int((start + L) / win) + 1
    part = smoothed[max(0, a):max(1, b)]
    loud_part = sum(part) / max(1, len(part)) + (max(part) if part else 0) * 0.5
    sc = sum(1 for t in scenes if start <= t <= start + L)
    return loud_part + sc * 4.0


def _even_starts(duration: float, count: int, L: float) -> list:
    if count <= 0:
        return []
    step = max(L, duration / count)
    starts, s = [], 0.0
    while s + MIN_LEN <= duration and len(starts) < count:
        starts.append(min(s, max(0.0, duration - L)))
        s += step
    return starts


def equal_split(duration: float, count: int = CLIP_COUNT, scenes: list = None) -> list:
    """Poora video barabar hisso me (scene cut par snap ho to aur saaf lagta hai)."""
    count = max(1, count)
    chunk = duration / count
    if chunk < MIN_LEN:
        count = max(1, int(duration // MIN_LEN) or 1)
        chunk = duration / count
    scenes = sorted(scenes or [])
    out = []
    for i in range(count):
        start = i * chunk
        end = min(duration, (i + 1) * chunk) if i < count - 1 else duration
        if scenes and 0 < i:
            near = [t for t in scenes if abs(t - start) <= 2.5]
            if near:
                start = min(near, key=lambda t: abs(t - start))
        out.append({"start": round(start, 2), "dur": round(max(2.0, end - start), 2),
                    "score": 0.0, "idx": i + 1})
    return out


# ---------------------------------------------------------------- cutting
def candidates_for_ai(src: str, count: int = 12) -> list:
    """AI ko dikhane ke liye candidate windows (energy + cuts) — sirf suggestion, final AI chunta hai."""
    try:
        info = probe_info(src)
        dur = float(info.get("duration") or 0)
        if dur < MIN_VIDEO:
            return []
        rms = audio_rms(src)
        scenes = scene_times(src)
        cands = pick_best(rms, scenes, dur, count=count)
        rms_map = dict(rms)
        out = []
        for i, c in enumerate(sorted(cands, key=lambda x: x["start"])):
            hits = 0
            t = c["start"]
            step = max(0.5, c["dur"] / 20.0)
            while t < c["start"] + c["dur"]:
                if rms_map.get(round(t, 1), -99) > -22:
                    hits += 1
                t += step
            sc = c.get("score", 0)
            try:
                sc = float(sc)
            except Exception:
                sc = 0.0
            out.append({"idx": i + 1, "start": c["start"], "end": c["start"] + c["dur"],
                        "dur": c["dur"], "score": round(sc, 2), "loud": hits,
                        "scenes": sum(1 for st in scenes if c["start"] <= st <= c["start"] + c["dur"])})
        out.sort(key=lambda x: -x["score"])
        return out
    except Exception:
        return []


def make_clip(src: str, out: str, start: float, dur: float, vertical: bool = False,
              has_audio: bool = True, quality: str = "normal") -> dict:
    """Ek clip kaato (re-encode — accurate cut + Telegram-friendly size)."""
    vf = (f"scale=-2:{VERT_H},crop={VERT_W}:{VERT_H}"
          if vertical else f"scale='min(1280,iw)':-2")
    if quality == "small":
        vf = (f"scale=-2:{int(VERT_H * 0.6)},crop={int(VERT_W * 0.6)}:{int(VERT_H * 0.6)}"
              if vertical else "scale='min(854,iw)':-2")
    crf = "27" if quality == "small" else "25"
    args = ["-hide_banner", "-nostdin", "-y",
            "-ss", f"{max(0.0, start):.2f}", "-t", f"{max(1.0, dur):.2f}", "-i", src]
    if vf:
        args += ["-vf", vf]
    args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", crf,
             "-maxrate", "1600k", "-bufsize", "3200k", "-pix_fmt", "yuv420p",
             "-movflags", "+faststart"]
    if has_audio:
        args += ["-c:a", "aac", "-b:a", "96k", "-ac", "2"]
    else:
        args += ["-an"]
    args += [out]
    try:
        cp = _ff(args, timeout=600)
    except Exception as e:
        return {"ok": False, "error": f"cut failed: {str(e)[:80]}"}
    if not os.path.exists(out) or os.path.getsize(out) < 8000:
        err = (cp.stderr or b"").decode("utf-8", "ignore")[-160:]
        return {"ok": False, "error": f"cut failed: {err}"}
    size_mb = os.path.getsize(out) / 1048576
    if size_mb > MAX_CLIP_MB:              # bahut bada → chhota banao
        small = out.replace(".mp4", "_s.mp4")
        make_clip(src, small, start, dur, vertical, has_audio, quality="small")
        if os.path.exists(small) and os.path.getsize(small) / 1048576 < size_mb:
            os.replace(small, out)
            size_mb = os.path.getsize(out) / 1048576
    pinfo = probe_info(out)
    return {"ok": True, "path": out, "size_mb": round(size_mb, 2),
            "width": pinfo.get("width") or (VERT_W if vertical else 0),
            "height": pinfo.get("height") or (VERT_H if vertical else NORM_H),
            "duration": round(pinfo.get("duration") or dur, 1)}


# ---------------------------------------------------------------- main
def analyze(src: str, mode: str = "smart", vertical: bool = False, count: int = CLIP_COUNT,
            ai_moments: list = None, ai_engine: str = "") -> dict:
    """Video file → clips (files ban jaate hain, send bot karega)."""
    if not shutil.which(ffmpeg_path()) and not os.path.exists(ffmpeg_path()):
        return {"ok": False, "error": "ffmpeg is not available on the server."}
    if not os.path.exists(src):
        return {"ok": False, "error": "Video file not found."}
    info = probe_info(src)
    dur = info.get("duration") or 0.0
    if dur < MIN_VIDEO:
        return {"ok": False, "error": f"Video is only {int(dur)} seconds long — need at least "
                                     f"{int(MIN_VIDEO)} seconds to make clips."}
    if dur > MAX_MINUTES * 60:
        return {"ok": False, "too_long": True, "duration": round(dur, 1),
                "error": f"Video is {int(dur // 60)} min long. Limit is {int(MAX_MINUTES)} min "
                         f"(server limit) — send a shorter part."}
    rms = audio_rms(src)
    scenes = scene_times(src)
    if ai_moments:
        # 🤖 AI ke chune hue moments (v44) — score ke hisaab se rank
        clips = []
        for i, m in enumerate(ai_moments):
            s0 = max(0.0, min(float(m.get("start", 0)), max(0.0, dur - 5)))
            e0 = min(dur, float(m.get("end", s0 + TARGET_LEN)))
            if e0 - s0 < MIN_LEN:
                e0 = min(dur, s0 + MIN_LEN)
            clips.append({"idx": i + 1, "start": round(s0, 2), "dur": round(e0 - s0, 2),
                          "score": float(m.get("score", 0) or 0),
                          "title": m.get("title") or "", "why": m.get("reason") or ""})
        order = sorted(range(len(clips)), key=lambda i: -clips[i]["score"])
        for rank, i in enumerate(order):
            clips[i]["rank"] = rank + 1
    elif mode == "smart":
        clips = pick_best(rms, scenes, dur, count=count)
        want = min(count, max(1, int(dur // MIN_LEN)))
        L = TARGET_LEN
        while len(clips) < want and L > MIN_LEN + 1:      # thoda chhota karke dobara
            L = max(MIN_LEN, L * 0.75)
            clips = pick_best(rms, scenes, dur, count=count, target_len=L)
    else:
        clips = equal_split(dur, count=count, scenes=scenes)
    if not clips:
        return {"ok": False, "error": "Could not find any clip in this video."}
    outdir = _tmpdir()
    made = []
    for c in clips:
        out = os.path.join(outdir, f"clip_{c['idx']:02d}.mp4")
        r = make_clip(src, out, c["start"], c["dur"], vertical=vertical,
                      has_audio=info.get("has_audio", True))
        if not r.get("ok"):
            continue
        r.update({"start": c["start"], "dur": c["dur"], "idx": c["idx"], "score": c.get("score", 0),
                  "rank": c.get("rank", c["idx"]), "title": c.get("title") or "",
                  "why": c.get("why") or ""})
        made.append(r)
    if not made:
        return {"ok": False, "error": "Clips could not be made (encoding failed) — try again."}
    return {"ok": True, "clips": made, "outdir": outdir, "count": len(made),
            "mode": mode, "vertical": vertical, "info": info, "ai_engine": ai_engine,
            "loud_peaks": len([1 for _t, v in rms if v > -25]),
            "scenes": len(scenes), "took_sec": None}


def cleanup(outdir: str) -> None:
    try:
        if outdir and os.path.isdir(outdir):
            shutil.rmtree(outdir, ignore_errors=True)
    except Exception:
        pass


# ---------------------------------------------------------------- sources
def download_direct(url: str, dest: str, max_mb: float = 46.0, timeout: int = 240) -> dict:
    """Direct video link (.mp4/.mkv/...) → file."""
    import requests
    try:
        with requests.get(url, stream=True, timeout=timeout,
                          headers={"User-Agent": "Mozilla/5.0 (ClipMaker)"}) as r:
            if r.status_code != 200:
                return {"ok": False, "error": f"Link gave HTTP {r.status_code}."}
            ctype = (r.headers.get("Content-Type") or "").lower()
            if ctype and not any(x in ctype for x in ("video", "octet-stream", "mp4", "mpeg")):
                return {"ok": False, "error": "This link is not a video file (need a direct .mp4 link)."}
            size, cap = 0, int(max_mb * 1048576)
            with open(dest, "wb") as f:
                for chunk in r.iter_content(262144):
                    if not chunk:
                        continue
                    size += len(chunk)
                    if size > cap:
                        return {"ok": False, "error": f"File is bigger than {int(max_mb)}MB — send a shorter video."}
                    f.write(chunk)
        return {"ok": True, "path": dest, "size_mb": round(size / 1048576, 2)}
    except Exception as e:
        return {"ok": False, "error": f"Download failed: {str(e)[:90]}"}


def is_direct_video_url(url: str) -> bool:
    u = (url or "").lower().split("?")[0]
    return u.startswith("http") and u.endswith((".mp4", ".mkv", ".mov", ".webm", ".m4v", ".3gp"))


def is_youtube_url(url: str) -> bool:
    u = (url or "").lower()
    return bool(re.search(r"(youtube\.com|youtu\.be|youtube-nocookie\.com)", u))


def ytdlp_available() -> bool:
    if os.environ.get("CLIP_YTDLP", "1") == "0":
        return False
    try:
        import yt_dlp  # noqa: F401
        return True
    except Exception:
        return shutil.which("yt-dlp") is not None


def _yt_friendly(err: str) -> str:
    """yt-dlp ka gandha error → user ke liye saaf line (link/kachra hata kar)."""
    e = re.sub(r"https?://\S+", "", str(err or ""))
    e = re.sub(r"\s{2,}", " ", e).strip(" .;,-")
    low = e.lower()
    if "sign in to confirm" in low or "not a bot" in low or "cookies" in low:
        return ("YouTube is blocking server downloads (its bot-check). "
                "YouTube link se download abhi possible nahi.")
    if "429" in low or "too many requests" in low:
        return "YouTube server ne rate-limit lagaya (429). Thodi der baad try karo."
    if "reload" in low or "player response" in low or "requested format" in low:
        return "YouTube ne is video ka format change kar diya — server se download nahi ho paya."
    if "private" in low or "unavailable" in low or "removed" in low:
        return "Ye video private / deleted / region-locked lagta hai."
    if "long" in low:
        return e[:160]
    return e[:160] or "Download failed."


def youtube_download(url: str, dest_dir: str, max_minutes: float = MAX_MINUTES,
                     max_mb: float = 400.0, quiet: bool = False) -> dict:
    """YouTube/Direct link → file (yt-dlp). Client fallback chain + cookies (env se)."""
    if not ytdlp_available():
        return {"ok": False, "no_ytdlp": True,
                "error": "YouTube download is not available on the server right now. "
                         "Send the video file itself, or a direct .mp4 link."}
    import yt_dlp
    base = {
        "format": "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]/b",
        "outtmpl": os.path.join(dest_dir, "src.%(ext)s"),
        "quiet": True, "no_warnings": True, "noprogress": True, "noplaylist": True,
        "max_filesize": int(max_mb * 1048576),
        "retries": 2, "fragment_retries": 2, "socket_timeout": 45,
        "merge_output_format": "mp4",
    }
    ck = os.environ.get("YTDLP_COOKIES_FILE", "")
    if ck and os.path.exists(ck):
        base["cookiefile"] = ck
    if os.environ.get("YTDLP_PROXY"):
        base["proxy"] = os.environ["YTDLP_PROXY"]

    # pehle user ka setting, phir apne aap client badal-badal ke try (v44)
    clients = []
    env_client = (os.environ.get("YTDLP_CLIENT") or "").strip()
    if env_client:
        clients.append([c.strip() for c in env_client.split(",") if c.strip()])
    clients += [["android_vr"], ["tv"], ["ios"], ["web_safari"], ["android"], []]
    seen, tried = set(), []
    last_err = ""
    for cl in clients:
        key = tuple(cl)
        if key in seen:
            continue
        seen.add(key)
        opts = dict(base)
        if cl:
            opts["extractor_args"] = {"youtube": {"player_client": cl}}
        tag = ",".join(cl) or "default"
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                meta = ydl.extract_info(url, download=True)
            if meta and meta.get("duration") and float(meta["duration"]) > max_minutes * 60:
                return {"ok": False, "too_long": True, "duration": float(meta["duration"]),
                        "error": f"This video is {int(float(meta['duration']) // 60)} min long — "
                                 f"limit is {int(max_minutes)} min."}
            files = [os.path.join(dest_dir, f) for f in os.listdir(dest_dir) if f.startswith("src.")]
            if not files:
                raise RuntimeError("no file came")
            return {"ok": True, "path": files[0], "size_mb": round(os.path.getsize(files[0]) / 1048576, 2),
                    "engine": f"yt-dlp ({tag})"}
        except Exception as e:                       # noqa: BLE001
            last_err = str(e)
            tried.append(tag)
            for f in os.listdir(dest_dir):           # adhura file saaf karo
                if f.startswith("src."):
                    try:
                        os.remove(os.path.join(dest_dir, f))
                    except Exception:
                        pass
            continue
    return {"ok": False, "tried": tried, "error": _yt_friendly(last_err)}


def caption_for(clip: dict, total: int, vertical: bool) -> str:
    """Clip ka caption (chhota — user ne chhote text maange the)."""
    stars = "⭐" * max(1, 4 - int(clip.get("rank", 9)))
    kind = "📱 9:16" if vertical else "🖥️ 16:9"
    line1 = f"🎬 <b>Clip {clip.get('idx')}/{total}</b> {stars} · {kind}\n"
    if clip.get("title"):
        line1 = f"🎬 <b>Clip {clip.get('idx')}/{total}</b> {stars} · {kind}\n🤖 <i>{_clip_esc(clip.get('title'))}</i>\n"
    return (line1 +
            f"<code>{fmt_t(clip.get('start', 0))}</code> · {int(clip.get('dur', 0))}s · "
            f"{clip.get('size_mb', 0)}MB")


def _clip_esc(t: str) -> str:
    return (str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))[:60]


def best_of_best(clips: list, k: int = 3) -> list:
    """Score ke hisaab se top clips (bot inko 'best' mark karta hai)."""
    return sorted([c for c in clips if c.get("score")], key=lambda c: -c["score"])[:k]


def help_card() -> str:
    return ("🎬 <b>CLIP MAKER</b>\n"
            "Video → 4-7 short clips (25-60 sec). 🤖 AI + loud moments + scene changes se best parts.\n"
            "📌 Limit: 15 min tak ka video · file 20MB tak (Telegram) ya direct .mp4 link\n"
            "⚠️ Use only your own video or a video you are allowed to reuse.")
