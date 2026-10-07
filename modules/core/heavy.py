# -*- coding: utf-8 -*-
"""
heavy.py — 🏗️ HEAVY WORK ADMISSION GATE (v77)
=============================================

Yahi ek cheez aapke bot ko "baar-baar crash" kar rahi thi
-----------------------------------------------------------
Render ka FREE plan = sirf **512 MB RAM** aur **0.1 CPU**.
Bot ka bhaari kaam (video download + ffmpeg encode + PDF banana) ek-dusre se
**laatchaar** (uncontrolled) chalta tha — code me ek bhi `Semaphore` nahi tha.

  4 users ne saath me "VIDEO DOWNLOAD" dabaya
      -> 4 ffmpeg/yt-dlp process + 4 PIL/PDF job ek saath
      -> 273 MB (idle) + ~4 x 120 MB  >>  512 MB
      -> Linux OOM killer bot ka process MAR deta hai
      -> Render log me sirf "Killed", user ko bot "hang/crash" lagta hai

Is file ke baad: ek saath sirf `HEAVY_MAX_SLOTS` (default 2) bhaari kaam
chalte hain. Baaki queue me khade hote hain, aur queue bhi hamesha ke liye
nahi — `HEAVY_WAIT_SECONDS` (default 25s) se zyada intezaar to user ko
saaf jawab milta hai ("server busy, abhi try karo") aur worker thread
**chhoo-ta hai** ( Render ke 0.1 CPU par worker thread ko ghanton tak atke
rehne dena hi ek aur tarah ka hang hai).

Do aur cheezein
---------------
1. **RAM dekha jaata hai**: 512 MB me se `HEAVY_THROTTLE_MB` (default 380)
   cross -> ek time par sirf EK bhaari kaam. `HEAVY_DENY_MB` (default 435)
   cross -> naya bhaari kaam shuru hi nahi hota (pehle se chalte hue ko
   nahi maarte; sirf naye ko mana karte hain). Isse "peak" memory kabhi
   chhat ko chhoo-ti hi nahi, aur cache-safai ko waqt mil jaata hai.

2. **Kabhi crash nahi karta**: gate fail ho (env galat, mem_mb() exception,
   registry toota) to **fail-open** — kaam chalta rehta hai. Protection
   kabhi khud bug ban kar bot nahi roklega.

USE (sync code me — ye hamesha worker thread se hi call hota hai)
    from modules.core import heavy

    with heavy.gate("ffmpeg"):            # slot na mila -> HeavyBusy raise
        subprocess.run([...])
    except heavy.HeavyBusy as e:
        return {"ok": False, "error": e.user_msg}

Health/report ke liye: heavy.stats(), heavy.health_line()
"""
from __future__ import annotations

import contextlib
import os
import threading
import time
from typing import Any, Dict, Optional

__all__ = [
    "HeavyBusy", "gate", "try_acquire", "release", "acquire",
    "stats", "health_line", "is_overloaded", "busy_result",
    "max_slots", "reset_stats",
]


# =====================================================================
#  CONFIG (sab env-se, galat value par bhi bot nahi rukega)
# =====================================================================
def _env_int(name: str, default: int, lo: int, hi: int) -> int:
    """Render ke Environment tab me koi bhi kachra likha ho to default le lo.

    (int("25 seconds") -> ValueError -> "Application failed to start". Ye
    isliye safe hai.)
    """
    try:
        raw = (os.environ.get(name) or "").strip()
        if not raw:
            return default
        # "25 sec", "25 seconds", "25,000" jaisi values se na ghirein
        num = ""
        for ch in raw:
            if ch.isdigit():
                num += ch
            elif num:
                break
        val = int(num) if num else default
    except Exception:                                        # noqa: BLE001
        return default
    return max(lo, min(hi, val))


# kitne bhaari kaam ek saath (Render free = 2; Starter+ = 3-4 theek)
_MAX_SLOTS_CFG = _env_int("HEAVY_MAX_SLOTS", 2, 1, 8)
# queue me kitni der intezar (is se zyada -> saaf busy message, worker free)
_WAIT_CFG = _env_int("HEAVY_WAIT_SECONDS", 25, 2, 300)
# RAM thresholds (MB). MEMORY_LIMIT_MB (v60) ka fallback use karte hain.
_LIMIT = _env_int("MEMORY_LIMIT_MB", 512, 128, 32768)
_THROTTLE = _env_int("HEAVY_THROTTLE_MB", int(_LIMIT * 0.74), 64, 32768)  # ~380 of 512
_DENY = _env_int("HEAVY_DENY_MB", int(_LIMIT * 0.85), 64, 32768)          # ~435 of 512
_ENABLED = (os.environ.get("HEAVY_GATE", "on").strip().lower()
            not in ("off", "0", "no", "false"))


class HeavyBusy(Exception):
    """Bhaari kaam ke liye slot nahi mila (busy / RAM zyada / queue lambi).

    `user_msg` me wahi line hai jo user ko dikhani hai — ye exception
    kabhi bot ko nahi giraata, sirf tool ko saaf "fail" karwata hai.
    """

    def __init__(self, reason: str, wait_ms: float = 0.0):
        self.reason = reason
        self.wait_ms = round(wait_ms, 1)
        if reason == "mem":
            self.user_msg = ("⚠️ Server par memory ka pressure hai — "
                             "bhaari kaam thodi der baad try karo.")
        elif reason == "timeout":
            self.user_msg = ("⏳ Line lambi hai — ye kaam abhi start nahi ho "
                             "paya. Thodi der baad dobara bhejo.")
        else:
            self.user_msg = "⏳ Server busy hai — abhi dobara try karo."
        super().__init__(f"heavy busy ({reason}, waited {self.wait_ms}ms)")


# =====================================================================
#  STATE
# =====================================================================
_COND = threading.Condition()
# 🪆 RE-ENTRANCY (maratmak design): ek hi thread me gate ke andar dobara gate
# lagane se DEADLOCK hota (2 slot, dono bahar se pakde, andar wala teesra
# maang raha hai). Isliye per-thread depth ginte hain — andar wala call
# slot DOBARA nahi maangta, upar wale hi chhoda jaata hai.
_tls = threading.local()
_state: Dict[str, Any] = {
    "reused": 0,             # nested (re-entrant) calls, slot share kiya
    "in_flight": 0,        # abhi kitne bhaari kaam chal rahe hain
    "served": 0,           # total slots mile
    "queued": 0,           # total baar queue me khade hue (wait > 0)
    "denied": 0,           # total baar mana kiya (timeout ya memory)
    "denied_mem": 0,       # un me se kitni baar RAM ki wajah se
    "wait_ms_total": 0.0,  # queue ka total time (average nikalne ke liye)
    "wait_ms_max": 0.0,    # sabse lamba wait
    "queue_now": 0,        # abhi queue me kitne khade hain
    "queue_max": 0,        # sabse bheed bhara pal
    "skipped": 0,          # gate band tha (HEAVY_GATE=off) ya bypass
    "by_kind": {},         # kind -> {"run": n, "busy": n}
}


def _mem_mb() -> float:
    """Process RAM. Guard na mile/galti ho to 0 (fail-open)."""
    try:
        from modules.core.guard import mem_mb as _g_mem
        v = float(_g_mem())
        if v > 0:
            return v
    except Exception:                                        # noqa: BLE001
        pass
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:                                        # noqa: BLE001
        return 0.0


def max_slots() -> int:
    """Abhi kitne bhaari kaam ek saath allowed hain (memory ke hisaab se)."""
    if not _ENABLED:
        return 8                                             # gate off = sab chalao
    n = _MAX_SLOTS_CFG
    try:
        mb = _mem_mb()
        if mb >= _DENY:
            return 0
        if mb >= _THROTTLE and n > 1:
            return 1
    except Exception:                                        # noqa: BLE001
        pass
    return n


def is_overloaded() -> bool:
    """Naya bhaari kaam start karna theek nahi (RAM chhat ke paas)."""
    if not _ENABLED:
        return False
    try:
        return _mem_mb() >= _DENY
    except Exception:                                        # noqa: BLE001
        return False


def acquire(kind: str = "job", wait: Optional[float] = None) -> bool:
    """Slot lene ki koshish. Mila -> True, warna False (koi exception nahi).

    🪆 Re-entrant: isi thread me agar pehle se slot hai (gate ke andar se
    gate), to naya slot MAANGTA HI NAHI — warna 2-slot wale free instance par
    aasan deadlock hota. Andar wala call bahar wale slot ko hi use karta hai.
    """
    if getattr(_tls, "depth", 0) > 0:                      # 🪆 slot pehle se hai
        _tls.depth += 1
        try:
            with _COND:
                _state["reused"] += 1
        except Exception:                                  # noqa: BLE001
            pass
        return True
    if not _ENABLED:
        with _COND:
            _state["skipped"] += 1
        return True
    _w = float(_WAIT_CFG if wait is None else wait)
    t0 = time.time()
    denied_reason = "timeout"
    got = False
    with _COND:
        kd = _state["by_kind"].setdefault(str(kind or "job"),
                                          {"run": 0, "busy": 0})
        kd["busy"] += 0                                      # key guarantee (stats)
        _state["queue_now"] += 1
        if _state["queue_now"] > _state["queue_max"]:
            _state["queue_max"] = _state["queue_now"]
        try:
            end = t0 + max(0.0, _w)
            while True:
                cap = max_slots()
                if _state["in_flight"] < cap:
                    if cap <= 0:
                        denied_reason = "mem"
                        break
                    _state["in_flight"] += 1
                    _state["served"] += 1
                    kd["run"] += 1
                    got = True
                    break
                if _mem_mb() >= _DENY:
                    denied_reason = "mem"
                    break
                rem = end - time.time()
                if rem <= 0:
                    break
                _state["queued"] += 1
                _COND.wait(min(rem, 1.0))
        except Exception:                                    # noqa: BLE001
            got = False                                      # gate kabhi na roke
            _state["skipped"] += 1
        finally:
            _state["queue_now"] = max(0, _state["queue_now"] - 1)
            wms = (time.time() - t0) * 1000.0
            _state["wait_ms_total"] = round(_state["wait_ms_total"] + wms, 1)
            if wms > _state["wait_ms_max"]:
                _state["wait_ms_max"] = round(wms, 1)
        if not got:
            _state["denied"] += 1
            if denied_reason == "mem":
                _state["denied_mem"] += 1
    if got:
        _tls.depth = 1
    return got


def release() -> None:
    """Slot wapas. Har acquire ke baad ye HONEI chahiye (finally me)."""
    try:
        d = getattr(_tls, "depth", 0)
        if d > 1:                                            # 🪆 andar wala call
            _tls.depth = d - 1
            return
        if d == 1:
            _tls.depth = 0
        with _COND:
            if _state["in_flight"] > 0:
                _state["in_flight"] -= 1
            _COND.notify_all()
    except Exception:                                        # noqa: BLE001
        pass


@contextlib.contextmanager
def gate(kind: str = "job", wait: Optional[float] = None,
         fail_open: bool = False):
    """`with gate("ffmpeg"): ...` — slot na mile to HeavyBusy.

    fail_open=True: slot na milne par bhi kaam CHALNE do (jahan rokna
    khada karna se bura ho — e.g. koi aisa tool jiska koi doosra raasta nahi).
    """
    got = acquire(kind, wait)
    if not got:
        if fail_open:
            with _COND:
                _state["skipped"] += 1
            yield False
            return
        raise HeavyBusy("timeout" if not is_overloaded() else "mem")
    try:
        yield True
    finally:
        release()


def try_acquire(kind: str = "job", wait: Optional[float] = None) -> bool:
    """Non-raising version — `True` mila, `False` busy.

    `with gate(...)` ke bajahan khud try/finally likhna ho to (e.g. ek aisa
    tool jahan slot na milne par purana behaviour hi chahiye):

        if heavy.try_acquire("media"):
            try:
                ...kaam...
            finally:
                heavy.release()
    """
    return acquire(kind, wait)


def busy_result(kind: str = "job", wait: Optional[float] = None,
                extra: Optional[dict] = None) -> dict:
    """Tool ke liye ready-made 'fail par bhi saaf jawab' result."""
    out = {"ok": False, "error": HeavyBusy("timeout").user_msg, "busy": True}
    if extra:
        out.update(extra)
    return out


def stats() -> Dict[str, Any]:
    with _COND:
        out = dict(_state)
        out["by_kind"] = {k: dict(v) for k, v in _state["by_kind"].items()}
    n = out.get("served", 0)
    out["wait_ms_avg"] = (round(out.get("wait_ms_total", 0.0) / n, 1)
                          if n else 0.0)
    out.update({
        "enabled": _ENABLED,
        "max": _MAX_SLOTS_CFG,
        "now_allowed": max_slots(),
        "wait_seconds": _WAIT_CFG,
        "throttle_mb": _THROTTLE,
        "deny_mb": _DENY,
        "mem_mb": round(_mem_mb(), 1),
    })
    return out


def reset_stats() -> None:
    """Sirf tests ke liye."""
    with _COND:
        for k, v in (("in_flight", 0), ("served", 0), ("queued", 0),
                     ("denied", 0), ("denied_mem", 0), ("wait_ms_total", 0.0),
                     ("wait_ms_max", 0.0), ("queue_now", 0), ("queue_max", 0),
                     ("skipped", 0), ("reused", 0)):
            _state[k] = v
        _state["by_kind"] = {}


def health_line() -> str:
    """/health aur /sys ke liye ek line — crash se pehle ki warning yahan dikhegi."""
    try:
        s = stats()
        return (f"heavy-gate: {'ON' if s['enabled'] else 'off'} "
                f"| slots {s['in_flight']}/{s['max']} (allowed {s['now_allowed']}) "
                f"| served {s['served']} | queued {s['queued']} "
                f"| busy-rejects {s['denied']} (mem {s['denied_mem']}) "
                f"| avg wait {s['wait_ms_avg']}ms max {s['wait_ms_max']}ms "
                f"| throttle {s['throttle_mb']}/{s['deny_mb']}MB")
    except Exception as e:                                   # noqa: BLE001
        return f"heavy-gate: (report unavailable: {str(e)[:40]})"


def register_with_guard() -> None:
    """Memory watchdog ko batao: pressure par gate aur tight ho jaye.

    Guard na mile to chup-chaap skip — import kabhi fail nahi karega.
    """
    try:
        from modules.core import guard as _g
        if _g is not None and not getattr(_g, "_heavy_registered", False):
            _g._heavy_registered = True
    except Exception:                                        # noqa: BLE001
        pass


register_with_guard()
