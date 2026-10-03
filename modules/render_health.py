# -*- coding: utf-8 -*-
"""Render health endpoints for the python-telegram-bot webhook server.

PTB's default webhook listener only registers the Telegram POST route, so Render
and UptimeRobot receive 404 on `/` and `/health`. This small compatibility hook
adds read-only health routes to the same Tornado application and port.
"""

from __future__ import annotations


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
