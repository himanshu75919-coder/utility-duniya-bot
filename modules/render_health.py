# -*- coding: utf-8 -*-
"""Render health endpoints for the python-telegram-bot webhook server.

PTB's default webhook listener only registers the Telegram POST route, so Render
and UptimeRobot receive 404 on `/` and `/health`. This small compatibility hook
adds read-only health routes to the same Tornado application and port.
"""

from __future__ import annotations

import os


def webhook_url_from_env(env=None) -> str:
    """Webhook URL — sirf jab WEBHOOK_MODE on ho (default: POLLING, sabse safe).

    Pehle yahi RENDER_EXTERNAL_URL se apne aap webhook on kar deta tha. Render ke
    free plan par deploy ke waqt DNS kabhi kabhi ready nahi hota -> Telegram
    "Bad webhook: failed to resolve host" deta hai aur bot crash ho jata tha.
    Ab: WEBHOOK_MODE=on + WEBHOOK_URL (ya RENDER_EXTERNAL_URL) ho to hi webhook.
    """
    values = os.environ if env is None else env
    mode = str(values.get("WEBHOOK_MODE") or "polling").strip().lower()
    if mode in ("off", "polling", "0", "false", "no"):
        return ""
    return str(values.get("WEBHOOK_URL") or values.get("RENDER_EXTERNAL_URL") or "").strip().rstrip("/")


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


def install_webhook_health_routes() -> None:
    """Add GET/HEAD `/` and `/health` routes to PTB's webhook app once."""
    import telegram.ext._updater as updater_module
    from tornado.web import RequestHandler

    base_app = updater_module.WebhookAppClass
    if getattr(base_app, "_utility_health_routes_installed", False):
        return

    class HealthHandler(RequestHandler):
        def _respond(self) -> None:
            self.set_header("Cache-Control", "no-store")
            self.set_header("X-Content-Type-Options", "nosniff")
            self.write({
                "status": "ok",
                "service": "utility-duniya-bot",
                "mode": "webhook",
                "powered_by": "@Supermannn_x",
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
