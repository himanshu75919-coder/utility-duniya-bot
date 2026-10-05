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

    return _url_like(values.get("WEBHOOK_URL")) or _url_like(values.get("RENDER_EXTERNAL_URL"))


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
