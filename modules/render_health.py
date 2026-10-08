# -*- coding: utf-8 -*-
"""Render health endpoints for the python-telegram-bot webhook server.

PTB's default webhook listener only registers the Telegram POST route, so Render
and UptimeRobot receive 404 on `/` and `/health`. This small compatibility hook
adds read-only health routes to the same Tornado application and port.
"""

from __future__ import annotations

import os


def webhook_url_from_env(env=None) -> str:
    """Webhook URL — Render par default AUTO (WEBHOOK_MODE=off karo to POLLING).

    v59.9: ab AUTO hai — RENDER_EXTERNAL_URL (ya WEBHOOK_URL) mila to webhook.
    Kyun: POLLING me har deploy par 10-20 second do instance ek saath getUpdates
    karte hain -> Telegram "Conflict: terminated by other getUpdates request"
    -> us waqt bot jawab nahi deta. Webhook me Telegram khud update bhejta hai,
    getUpdates hota hi nahi -> Conflict kabhi nahi.

    Crash se bachav: webhook_url_usable() (DNS check) + webhook_preflight()
    (Telegram se setWebhook ek baar pooch lo) — dono fail ho to chup-chaap
    POLLING par chalta hai, bot band nahi hota. WEBHOOK_MODE=off = zabardasti
    polling.
    """
    values = os.environ if env is None else env
    mode = str(values.get("WEBHOOK_MODE") or "auto").strip().lower()
    # v59.9.1: "polling" bhi AUTO maana jaata hai — ye value Render dashboard me
    # purane blueprint (v46) se baithi thi, aur isi wajah se bot polling par hi
    # chal raha tha (har deploy par 10-20s Conflict). Zabardasti polling chahiye
    # to WEBHOOK_MODE=off likho — wahi ek rasta hai.
    if mode in ("off", "0", "false", "no"):
        return ""
    # v59.9.3: sirf ASLI http(s) URL maano. Agar WEBHOOK_URL me kuch aur likha ho
    # (jaise "on"/"yes"/"1" — galti se flag samajh kar), to usko chhod kar Render
    # ka apna RENDER_EXTERNAL_URL use karo. Pehle aisi value poori webhook band
    # kar deti thi (bot chup-chaap polling par chala jaata tha).
    def _url_like(raw) -> str:
        v = str(raw or "").strip().rstrip("/")
        v = v.strip("'\"").strip()
        return v if v.lower().startswith(("http://", "https://")) else ""

    # v81.1 — CRITICAL guard: bot code khud "/webhook/<secret>" jodta hai
    # (bot.py: full_url = WEBHOOK_URL.rstrip("/") + path). Agar env me koi
    # poora path likh de ("https://x.onrender.com/webhook/SECRET") to URL
    # DOUBLE ho jaata tha → Telegram ka har POST 404 → **bot ekdum chup**
    # (8 Oct 2026 ko yahi hua: 36 updates Telegram ke paas phans gaye).
    # Isliye yahan se hamesha sirf BASE URL hi jaayega.
    return _base_only(_url_like(values.get("WEBHOOK_URL"))
                      or _url_like(values.get("RENDER_EXTERNAL_URL")))


def _base_only(v: str) -> str:
    """"https://x.onrender.com/webhook/SECRET" → "https://x.onrender.com"
    (path ka pehla "/webhook" kahaan bhi ho, wahan se kaat do — base hi chahiye)."""
    v = str(v or "").strip().rstrip("/")
    i = v.lower().find("/webhook")
    if i > len("https://") - 1 and i > 0:
        v = v[:i]
    return v.rstrip("/")


def webhook_url_usable(url: str) -> tuple:
    """URL sach me chalega ya nahi — DNS + hostname check (crash se pehle pakdo).

    Returns (ok: bool, reason: str)
    """
    import socket as _socket
    from urllib.parse import urlparse

    u = str(url or "").strip()
    if not u:
        return False, "khaali URL"
    try:
        pr = urlparse(u)
    except Exception as e:                                   # noqa: BLE001
        return False, f"URL parse nahi hua ({e})"
    if pr.scheme not in ("http", "https"):
        return False, f"scheme '{pr.scheme}' — http/https hona chahiye"
    host = pr.hostname or ""
    if not host:
        return False, "hostname nahi mila"
    if "_" in host:
        return False, f"hostname me underscore hai ({host}) — DNS isse nahi samajhta"
    if "." not in host:
        return False, f"hostname adhoora lagta hai ({host})"
    try:
        _socket.getaddrinfo(host, 443 if pr.scheme == "https" else 80)
    except Exception as e:                                   # noqa: BLE001
        return False, f"DNS resolve nahi hua ({host}) — {e}"
    return True, ""


def webhook_preflight(url: str, path: str, token: str, secret_token=None,
                      timeout: float = 12.0) -> tuple:
    """Telegram khud is webhook ko maanta hai? (setWebhook ek baar try karo)

    Returns (ok: bool, reason: str). Isse pehle hi pata chal jaata hai ki
    webhook chalega ya nahi — phir polling par chup-chaap switch ho jaate hain,
    bot crash nahi hota. Token/path kabhi log me nahi jaate.
    """
    import json as _json
    import urllib.parse as _up
    import urllib.request as _ur

    base = str(url or "").strip().rstrip("/")
    if not base or not token:
        return False, "URL ya token nahi mila"
    full = base + (path if str(path).startswith("/") else "/" + str(path))
    payload = {"url": full, "drop_pending_updates": "true"}
    if secret_token:
        payload["secret_token"] = str(secret_token)
    try:
        req = _ur.Request(
            "https://api.telegram.org/bot" + str(token) + "/setWebhook",
            data=_up.urlencode(payload).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with _ur.urlopen(req, timeout=timeout) as r:
            body = _json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:                                        # noqa: BLE001
        return False, f"Telegram se baat nahi hui ({type(e).__name__})"
    if isinstance(body, dict) and body.get("ok"):
        return True, ""
    why = ""
    if isinstance(body, dict):
        why = str(body.get("description") or body.get("error_code") or "")
    return False, f"Telegram ne webhook maana nahi: {why[:90]}"


def install_webhook_health_routes(status_provider=None) -> None:
    """Add GET/HEAD `/` and `/health` routes to PTB's webhook app once.

    status_provider (optional) — callable jo HTML/text deta hai. Bot isse apni
    poori /health report (version, commit, crashes, keepalive) webhook mode me
    bhi dikhata hai — pehle webhook mode me sirf chhota JSON aata tha.
    """
    import telegram.ext._updater as updater_module
    from tornado.web import RequestHandler

    base_app = updater_module.WebhookAppClass
    if getattr(base_app, "_utility_health_routes_installed", False):
        return

    class HealthHandler(RequestHandler):
        def _respond(self) -> None:
            self.set_header("Cache-Control", "no-store")
            self.set_header("X-Content-Type-Options", "nosniff")
            if callable(status_provider):
                try:
                    self.set_header("Content-Type", "text/html; charset=utf-8")
                    self.write(status_provider())
                    return
                except Exception:                                 # noqa: BLE001
                    pass
            self.set_header("Content-Type", "application/json; charset=utf-8")
            self.write({
                "status": "ok",
                "service": "utility-duniya-bot",
                "mode": "webhook",
            })

        def get(self) -> None:
            self._respond()

        def head(self) -> None:
            self.set_status(200)
            self.set_header("Cache-Control", "no-store")
            self.finish()

    class HealthWebhookApp(base_app):
        _utility_health_routes_installed = True

        def __init__(self, webhook_path, bot, update_queue, secret_token=None):
            super().__init__(webhook_path, bot, update_queue, secret_token)
            self.add_handlers(r".*$", [
                (r"/", HealthHandler),
                (r"/health/?", HealthHandler),
            ])

    HealthWebhookApp.__name__ = "UtilityDuniyaHealthWebhookApp"
    updater_module.WebhookAppClass = HealthWebhookApp


# =====================================================================
#  v81.1 — WEBHOOK DELIVERY CHECK + SELF-HEAL
#  "Telegram ne URL maan liya" se kaam nahi chalna — updates PAUNCHCHE hain ya
#  nahi, wahi asli cheez hai. Ye do functions /health aur keepalive loop me
#  use hote hain. Dono KABHI exception nahi uthaate.
# =====================================================================
def _mask(txt: str, token: str = "", secret: str = "") -> str:
    """Token/secret kabhi log ya health me na dikhein."""
    t = str(txt or "")
    for k in (token, secret):
        k = str(k or "")
        if k:
            t = t.replace(k, "MASKED")
            if ":" in k:
                t = t.replace(k.split(":")[-1], "MASKED")
    return t


def webhook_delivery_state(token: str, timeout: float = 6.0, expected: str = "") -> dict:
    """getWebhookInfo se saccha haal.

    Returns {"ok": bool, "pending": int, "err": str, "dupes": int,
             "registered": bool, "match": bool|None}.
    dupes = URL me "/webhook/" kitni baar aaya (1 se zyada = double path = 404).
    expected diya ho to "match" = Telegram par wahi URL registered hai ya nahi.
    ⚠️ Registered URL me webhook SECRET hota hai — isliye wo is dict me KABHI nahi
    aata (health page public hai); sirf match ka result aata hai.
    """
    import json as _json
    import urllib.error as _ue
    import urllib.request as _ur
    out = {"ok": True, "pending": 0, "err": "", "dupes": 0, "registered": False,
           "match": None}
    if not token:
        out.update(ok=False, err="token nahi mila")
        return out
    try:
        req = _ur.Request("https://api.telegram.org/bot" + str(token) + "/getWebhookInfo",
                          headers={"User-Agent": "utility-duniya-bot/wh-check"})
        with _ur.urlopen(req, timeout=timeout) as r:
            body = _json.loads(r.read().decode("utf-8", "replace"))
    except _ue.HTTPError as e:
        try:
            why = _json.loads(e.read().decode("utf-8", "replace")).get("description", "")
        except Exception:                                        # noqa: BLE001
            why = f"HTTP {e.code}"
        out.update(ok=False, err=_mask(why or f"HTTP {e.code}", token))
        return out
    except Exception as e:                                       # noqa: BLE001
        out.update(ok=False, err=_mask(f"{type(e).__name__}", token))
        return out
    res = (body or {}).get("result") or {}
    url = str(res.get("url") or "")
    out["registered"] = bool(url)
    if expected:
        out["match"] = str(url).rstrip("/") == str(expected).strip().rstrip("/")
    out["pending"] = int(res.get("pending_update_count") or 0)
    out["dupes"] = max(0, url.lower().count("/webhook") - 1)
    out["err"] = _mask(str(res.get("last_error_message") or ""), token)
    out["ok"] = bool(out["registered"]) and not out["err"] and out["dupes"] == 0 \
        and out["match"] is not False
    return out


def webhook_needs_repair(state: dict, pending_limit: int = 5) -> bool:
    """Update Telegram ke paas phans rahe hain? (ya URL bigda hua hai?)"""
    if not isinstance(state, dict) or state.get("registered") is False:
        return True
    if int(state.get("dupes") or 0) > 0:
        return True                                   # double path = 100% broken
    if int(state.get("pending") or 0) >= int(pending_limit):
        return True
    return bool(str(state.get("err") or ""))


def webhook_repair(token: str, base_url: str, path: str, secret_token=None,
                   drop_pending: bool = False, timeout: float = 12.0) -> tuple:
    """deleteWebhook + setWebhook — khud theek kar lo (404/wrong path ke liye).

    Returns (ok: bool, why: str). Token/path kabhi return me na aayeen.
    """
    import json as _json
    import urllib.error as _ue
    import urllib.parse as _up
    import urllib.request as _ur
    base = str(base_url or "").strip().rstrip("/")
    if not base or not token or not path:
        return False, "base/token/path me se kuch khaali"
    full = base + (path if str(path).startswith("/") else "/" + str(path))
    if full.lower().count("/webhook") > 1:
        return False, "URL me /webhook do baar hai — base hi galat hai"

    def _call(method, **kw):
        data = _up.urlencode({k: ("true" if v is True else "false" if v is False else v)
                              for k, v in kw.items()}).encode() if kw else None
        req = _ur.Request("https://api.telegram.org/bot" + str(token) + "/" + method,
                          data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            with _ur.urlopen(req, timeout=timeout) as r:
                return _json.loads(r.read().decode("utf-8", "replace"))
        except _ue.HTTPError as e:
            try:
                return _json.loads(e.read().decode("utf-8", "replace"))
            except Exception:                                    # noqa: BLE001
                return {"ok": False, "description": f"HTTP {e.code}"}
        except Exception as e:                                   # noqa: BLE001
            return {"ok": False, "description": type(e).__name__}

    _call("deleteWebhook", drop_pending_updates=bool(drop_pending))
    payload = {"url": full, "drop_pending_updates": False, "max_connections": 40}
    if secret_token:
        payload["secret_token"] = str(secret_token)
    res = _call("setWebhook", **payload)
    if isinstance(res, dict) and res.get("ok"):
        return True, "webhook dobara set ho gaya ✅"
    why = str((res or {}).get("description") if isinstance(res, dict) else res)[:120]
    return False, _mask(why or "setWebhook fail", token)
