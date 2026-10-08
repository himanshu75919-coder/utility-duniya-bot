# -*- coding: utf-8 -*-
"""
🐘 BIGFILE (v79) — 20 MB ki deewar todta hai (150 MB tak, safe tarike se)
============================================================================
Telegram **Bot API** ki 2 sakht haddain hain (hamara code nahi, Telegram ka rule):

  • bot koi bhi file **接收** (download) sirf **20 MB** tak kar sakta hai
  • bot koi bhi file **भेज** (upload) sirf **50 MB** tak kar sakta hai

Isliye user ne 66.5 MB ka WhatsApp zip bheja to bot bola "20MB limit".

Ilaja: **MTProto** (Telegram ka khula API). Wahi bot token, bas Bot API server
ke bajaye seedha Telegram ke data-center se baat — wahan 2 GB tak chalega.
Telethon se `client.start(bot_token=...)` karke same bot hi download/upload kar
leta hai. Bot ko koi naya account nahi chahiye, bas:

  TG_API_ID     (my.telegram.org → API development tools)
  TG_API_HASH   (wahi page)

Ye 2 env set NA ho to module chup-chaap "disabled" reheta hai aur bot ka
behaviour bilkul pehle jaisa rehta hai (20 MB message + 48 MB cap) — yani
deploy safe, zero risk.

RAM ka khayal (Render free = 512 MB, aur OOM hi hamara pichla crash tha):
badi file **hamesha disk par** utarti hai, aur 45 MB se upar ka payload tools
ko `MappedFile` (mmap) ke roop me jaata hai — yaani 150 MB file aate waqt bhi
Python ka RAM ~0 badhta hai.
"""
from __future__ import annotations

import logging
import mmap
import os
import tempfile
import threading
from typing import Any, Optional

log = logging.getLogger(__name__)

__all__ = [
    "enabled", "cap_in_mb", "cap_out_mb", "BOT_API_IN_MB", "BOT_API_OUT_MB",
    "MEM_SAFE_MB", "download_to_path", "MappedFile", "mt_send", "dl_limit_mb",
    "send_via_mt", "status",
]

# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------
BOT_API_IN_MB = 20          # Telegram Bot API: getFile ki hadd (hamara control nahi)
BOT_API_OUT_MB = 48         # Bot API upload ~50MB (buffer ke saath)
MEM_SAFE_MB = 45            # itne tak RAM me bytes theek hain; upar mmap


def _i(name: str, default: int, lo: int, hi: int) -> int:
    try:
        v = int(str(os.environ.get(name, "")).strip() or default)
    except Exception:                                       # noqa: BLE001
        v = default
    return max(lo, min(hi, v))


#: kitni badi file user se LENGE (MTProto on ho to)
MAX_IN_MB = _i("MAX_FILE_MB", 150, 20, 2000)
#: kitni badi file bot bhejega (MTProto on ho to)
MAX_OUT_MB = _i("MAX_SEND_MB", 150, 20, 2000)

_lock = threading.RLock()
_client = None
_client_err = ""


def _creds() -> tuple:
    try:
        api_id = int(str(os.environ.get("TG_API_ID", "")).strip() or 0)
    except Exception:                                       # noqa: BLE001
        api_id = 0
    api_hash = (os.environ.get("TG_API_HASH") or "").strip()
    token = (os.environ.get("BOT_TOKEN") or "").strip()
    return api_id, api_hash, token


def enabled() -> bool:
    """MTProto ready hai? (telethon + creds + ek baar client ban gaya)"""
    return _client_ready() is not None


def _client_ready():
    global _client, _client_err
    with _lock:
        if _client is not None:
            return _client
        api_id, api_hash, token = _creds()
        if not (api_id and api_hash and token):
            _client_err = "TG_API_ID/TG_API_HASH set nahi"
            return None
        try:
            from telethon import TelegramClient                # noqa: PLC0415
        except Exception as e:                                 # noqa: BLE001
            _client_err = f"telethon install nahi: {e}"
            return None
        try:
            # Telethon apna event loop khud choose karta hai — jis loop me uska
            # pehla `await` chalega, wahi uska loop. Yahan `asyncio.get_event_loop()`
            # se manually set karne se Python 3.12+ par (loop na ho) RuntimeError
            # aata tha, jiska matlab MTProto kabhi ready hi nahi hota = feature
            # chup-chaap mar jaata. Isliye loop ko haath nahi lagate.
            _client = TelegramClient(":memory:", api_id, api_hash)
            _client_err = ""
            return _client
        except Exception as e:                                 # noqa: BLE001
            _client_err = f"{type(e).__name__}: {str(e)[:80]}"
            return None


async def _started():
    """Client ko bot-token se login karo (eek hi baar). None = use nahi kar sakte."""
    c = _client_ready()
    if c is None:
        return None
    if getattr(c, "_du", False):
        return c
    _api_id, _api_hash, token = _creds()
    try:
        await c.start(bot_token=token)
        c._du = True            # type: ignore[attr-defined]  (bas ek baar login)
        log.info("🐘 bigfile: MTProto bot session ready (bade file ab chalega)")
        return c
    except Exception as e:                                     # noqa: BLE001
        global _client_err
        _client_err = f"login fail: {type(e).__name__}: {str(e)[:70]}"
        log.warning("🐘 bigfile MTProto login fail — %s", _client_err)
        return None


def status() -> dict:
    c = _client_ready()
    return {"ready": c is not None, "logged_in": bool(c and getattr(c, "_du", False)),
            "max_in_mb": MAX_IN_MB, "max_out_mb": MAX_OUT_MB,
            "note": _client_err or "ok"}


# ---------------------------------------------------------------------------
# caps jo tools poochhte hain
# ---------------------------------------------------------------------------
def cap_in_mb() -> int:
    """User se file lene ki hadd (MTProto on = MAX_FILE_MB, warna 20)."""
    return MAX_IN_MB if enabled() else BOT_API_IN_MB


def cap_out_mb() -> int:
    """Bot file bhej sakta hai kitni (MTProto on = MAX_SEND_MB, warna 48)."""
    return MAX_OUT_MB if enabled() else BOT_API_OUT_MB


def dl_limit_mb(default: int = BOT_API_OUT_MB) -> int:
    """Downloader ka max download size — MTProto on ho to badi file bhi."""
    return max(default, cap_out_mb()) if enabled() else default


# ---------------------------------------------------------------------------
# MappedFile — disk par file, par bytes jaisi dikhti hai (RAM nahi khata)
# ---------------------------------------------------------------------------
class MappedFile:
    """Chhota wrapper: `.getvalue()` memoryview deta hai aur `.path` asli file.

    Hamare tools (`open(pin,'wb').write(data)`, ffmpeg, PIL) ise seedha use kar
    lete hain, aur 150 MB file ke liye bhi Python RAM ~0 rehta hai.
    """

    __slots__ = ("path", "size", "_mm")

    def __init__(self, path: str, size: int):
        self.path = path
        self.size = size
        self._mm = None

    def _map(self):
        if self._mm is None:
            f = open(self.path, "rb")
            self._mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        return self._mm

    def getvalue(self):                       # tools isi ko bulate hain
        try:
            return memoryview(self._map())
        except Exception:                     # noqa: BLE001
            with open(self.path, "rb") as fh:
                return fh.read()

    def __len__(self):
        return self.size

    def read(self, n: int = -1) -> bytes:
        with open(self.path, "rb") as fh:
            return fh.read() if n is None or n < 0 else fh.read(n)

    def close(self):
        try:
            if self._mm is not None:
                self._mm.close()
        except Exception:                     # noqa: BLE001
            pass

    def unlink(self):
        self.close()
        try:
            os.remove(self.path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# download (user -> bot), disk par
# ---------------------------------------------------------------------------
async def download_to_path(message, suffix: str = "", max_mb: Optional[int] = None) -> dict:
    """`message` ki document/video file temp path par utaar do.

    Returns {ok, path, size, size_mb, mapped} ya {ok: False, reason}.
    Chhoti file (<= 45MB) ke liye mapped=False — caller bytes bhi padh sakta hai.
    """
    cap = max_mb if max_mb is not None else MAX_IN_MB
    c = await _started()
    if c is None:
        return {"ok": False, "reason": _client_err or "MTProto ready nahi",
                "need_env": "TG_API_ID + TG_API_HASH"}
    suffix = (suffix or "").lower()
    if suffix and not suffix.startswith("."):
        suffix = "." + suffix
    fd, path = tempfile.mkstemp(prefix="bigin_", suffix=suffix)
    os.close(fd)
    try:
        got = await c.download_media(message, file=path + ".part")
        src = got or (path + ".part")
        if not os.path.exists(src):
            return {"ok": False, "reason": "file download hoke mili nahi"}
        size = os.path.getsize(src)
        if size > cap * 1048576:
            try:
                os.remove(src)
            except OSError:
                pass
            return {"ok": False, "reason": f"file {size // 1048576} MB hai — hadd {cap} MB",
                    "too_big": True}
        os.replace(src, path)
        try:
            os.remove(path + ".part")
        except OSError:
            pass
        return {"ok": True, "path": path, "size": size,
                "size_mb": round(size / 1048576, 2),
                "mapped": size > MEM_SAFE_MB * 1048576}
    except Exception as e:                                     # noqa: BLE001
        for _p in (path, path + ".part"):
            try:
                os.remove(_p)
            except OSError:
                pass
        return {"ok": False, "reason": f"{type(e).__name__}: {str(e)[:110]}"}


# ---------------------------------------------------------------------------
# send (bot -> user), MTProto se (50MB se badi file)
# ---------------------------------------------------------------------------
async def mt_send(chat_id: int, data, *, kind: str = "auto", caption: str = "",
                  file_name: str = "", max_mb: Optional[int] = None) -> dict:
    """Badi file bhejo — Bot API ki 50MB hadd se upar.

    `data` bytes / BytesIO / path / MappedFile kuch bhi ho sakta hai.
    """
    cap = max_mb if max_mb is not None else MAX_OUT_MB
    c = await _started()
    if c is None:
        return {"ok": False, "reason": _client_err or "MTProto ready nahi"}
    tmp = ""
    try:
        if isinstance(data, MappedFile):
            payload = data.path
        elif isinstance(data, (bytes, bytearray, memoryview)):
            payload = bytes(data)
        elif hasattr(data, "getvalue"):
            payload = data.getvalue()
        elif isinstance(data, str):
            payload = data
        else:
            return {"ok": False, "reason": "unsupported data"}
        sz = os.path.getsize(payload) if isinstance(payload, str) else len(payload)
        if sz > cap * 1048576:
            return {"ok": False, "reason": f"file {sz // 1048576} MB — hadd {cap} MB",
                    "too_big": True}
        if not isinstance(payload, str):
            ext = os.path.splitext(file_name or "")[1] or (".mp4" if kind == "video"
                                                           else ".jpg" if kind == "photo" else ".bin")
            fd, tmp = tempfile.mkstemp(prefix="bigout_", suffix=ext)
            with os.fdopen(fd, "wb") as fh:
                fh.write(payload)
            payload = tmp
        kw: dict[str, Any] = {}
        if caption:
            kw["caption"] = caption[:1000]
        if file_name:
            kw["force_document"] = kind not in ("video", "audio", "voice")
        if kind == "video":
            kw["supports_streaming"] = True
        await c.send_file(int(chat_id), payload, **kw)
        return {"ok": True, "size_mb": round(sz / 1048576, 2), "engine": "mtproto"}
    except Exception as e:                                     # noqa: BLE001
        return {"ok": False, "reason": f"{type(e).__name__}: {str(e)[:110]}"}
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass


async def send_via_mt(update, chat_id: int, data, *, kind: str = "auto",
                      caption: str = "", file_name: str = "") -> dict:
    """Convenience: MTProto on ho aur file 48MB se badi ho to bhejo, warna skip."""
    if not enabled():
        return {"ok": False, "reason": "MTProto off"}
    sz = len(data) if hasattr(data, "__len__") else 0
    if sz and sz <= BOT_API_OUT_MB * 1048576:
        return {"ok": False, "reason": "chhoti file — Bot API se hi jaldi hai"}
    return await mt_send(chat_id, data, kind=kind, caption=caption, file_name=file_name)
