import asyncio
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules import imei_lookup
from modules import osint_hub
from modules.render_health import webhook_url_from_env, webhook_url_usable

try:
    from modules.osint_tools import lookup_phone_info
except ImportError:
    lookup_phone_info = None


class ImeiLookupTests(unittest.TestCase):
    def setUp(self):
        imei_lookup.clear_cache()

    def test_base_uses_canonical_hub_and_adds_api_path(self):
        with patch.dict(os.environ, {"IMEI_API_BASE": "https://osint-api-hub.onrender.com"}, clear=False):
            self.assertEqual(imei_lookup.api_base(), "https://osint-api-hub.onrender.com/api")

    def test_full_imei_is_validated_locally_but_only_tac_is_sent(self):
        captured = {}
        original_get = imei_lookup._get

        def fake_get(url, params, tmo=imei_lookup.TIMEOUT):
            captured["url"] = url
            captured["params"] = dict(params)
            return {
                "tac": "35301011",
                "brand": "APPLE",
                "model": "iPhone 12 mini",
                "reporting_body": "BABT",
                "note": "Local TAC match",
            }, None

        imei_lookup._get = fake_get
        try:
            result = imei_lookup.fetch_imei_details("353010111111110", use_cache=False)
        finally:
            imei_lookup._get = original_get

        self.assertTrue(result["ok"])
        self.assertTrue(captured["params"]["imei"].startswith("35301011"))
        self.assertEqual(result["tac"], "35301011")
        self.assertEqual(imei_lookup.specs_dict(result)["device_name"], "Apple iPhone 12 mini")
        self.assertEqual(imei_lookup.specs_dict(result)["tac"], "35301011")

    def test_provider_error_never_echoes_a_full_imei(self):
        full_imei = "353010111111110"
        result = imei_lookup.parse_imei_payload({"error": "temporary provider error"}, full_imei)
        self.assertFalse(result["ok"])
        self.assertEqual(result["tac"], full_imei[:8])
        self.assertNotIn(full_imei, json.dumps(result))

    def test_local_validation_error_does_not_echo_full_imei(self):
        full_imei = "12345678901234"  # invalid length: validation must stop before any network request
        result = imei_lookup.fetch_imei_details(full_imei, use_cache=False)
        self.assertFalse(result["ok"])
        self.assertEqual(result["tac"], full_imei[:8])
        self.assertNotIn(full_imei, json.dumps(result))

    def test_legacy_provider_schema_does_not_return_serial_fields(self):
        payload = {
            "result": {
                "header": {
                    "brand": "SAMSUNG",
                    "model": "Galaxy Tab A9+",
                    "photo": "https://example.test/device.jpg",
                    "url": "https://example.test/specs",
                },
                "items": [
                    {"role": "header", "title": "Display"},
                    {"role": "item", "title": "Size", "content": "11 inches"},
                    {"role": "item", "title": "IMEI", "content": "123456789012345"},
                    {"role": "item", "title": "Serial Number", "content": "ABC123"},
                ],
            }
        }
        result = imei_lookup.parse_imei_payload(payload, "35301011")
        self.assertTrue(result["ok"])
        output = json.dumps(imei_lookup.specs_dict(result))
        self.assertNotIn("123456789012345", output)
        self.assertNotIn("ABC123", output)
        self.assertEqual(imei_lookup.specs_dict(result)["url"], "https://example.test/specs")

    def test_private_lookups_are_disabled_without_network_calls(self):
        self.assertTrue(osint_hub.num_info_report("9876543210")["disabled"])
        self.assertTrue(osint_hub.aadhaar_family_report("123456789012")["disabled"])
        with patch.dict(os.environ, {"VEHICLE_PROVIDER_AUTHORIZED": "0", "VEHICLE_API_BASE": ""}, clear=False):
            self.assertFalse(osint_hub.is_configured())
            self.assertTrue(osint_hub.vehicle_report_v2("BR00XX0000")["fallback"])


class RenderWebhookConfigTests(unittest.TestCase):
    """v49.4: default POLLING hai — webhook sirf WEBHOOK_MODE=on par.

    Pehle bot RENDER_EXTERNAL_URL se khud webhook on kar deta tha. Render ke free
    plan par deploy ke waqt DNS ready nahi hota tha, isliye Telegram
    "Bad webhook: failed to resolve host" deta tha aur bot crash ho jata tha.
    """

    def test_default_mode_is_polling(self):
        self.assertEqual(webhook_url_from_env({"WEBHOOK_URL": "https://x.onrender.com"}), "")

    def test_explicit_webhook_url_wins_and_is_normalized(self):
        self.assertEqual(
            webhook_url_from_env({
                "WEBHOOK_MODE": "on",
                "WEBHOOK_URL": "https://utility-duniya-bot.onrender.com/",
                "RENDER_EXTERNAL_URL": "https://fallback.onrender.com",
            }),
            "https://utility-duniya-bot.onrender.com",
        )

    def test_render_external_url_is_webhook_fallback_in_on_mode(self):
        self.assertEqual(
            webhook_url_from_env({"WEBHOOK_MODE": "on", "WEBHOOK_URL": "",
                                  "RENDER_EXTERNAL_URL": "https://bot.onrender.com/"}),
            "https://bot.onrender.com",
        )

    def test_render_blueprint_keeps_polling_default(self):
        render_yaml = (Path(__file__).resolve().parents[1] / "render.yaml").read_text(encoding="utf-8")
        self.assertIn("- key: WEBHOOK_MODE\n        value: polling", render_yaml)
        # WEBHOOK_URL me hard-coded value nahi honi chahiye (warna deploy crash)
        self.assertNotIn("- key: WEBHOOK_URL\n        value: https://utility-duniya-bot.onrender.com", render_yaml)

    def test_webhook_url_usable_rejects_bad_hosts(self):
        ok, _why = webhook_url_usable("")
        self.assertFalse(ok)
        ok2, why2 = webhook_url_usable("https://bad_host.onrender.com")
        self.assertFalse(ok2)
        self.assertIn("underscore", why2)
        ok3, _why3 = webhook_url_usable("https://utility-duniya-bot.onrender.com")
        self.assertTrue(ok3)


class SafePhoneInfoTests(unittest.TestCase):
    @unittest.skipIf(lookup_phone_info is None, "phonenumbers dependency is not installed")
    def test_phone_info_card_has_no_external_links(self):
        # v49.13: user ka order — info tool me koi bahar wala link nahi.
        # Official safety links alag safety card (number_safety_info) me rehte hain.
        result = lookup_phone_info("+12025550123")
        self.assertTrue(result["ok"])
        self.assertEqual(result["links"], [])

    def test_safety_card_has_no_links_only_helpline_text(self):
        # v49.14: user ka order — safety card me bhi koi link nahi, sirf helpline numbers (text)
        from modules.osint_tools import number_safety_info
        sf = number_safety_info("+919876543210")
        self.assertTrue(sf["ok"])
        self.assertEqual(sf["links"], [])
        advice = " ".join(sf["advice"])
        self.assertIn("1930", advice)
        self.assertIn("155260", advice)
        self.assertNotIn("http", advice.lower())
        self.assertNotIn(".gov.in", advice.lower())


try:
    from tornado.testing import AsyncHTTPTestCase
    import telegram.ext._updater as updater_module
    from modules.render_health import install_webhook_health_routes

    class WebhookHealthTests(AsyncHTTPTestCase):
        @classmethod
        def setUpClass(cls):
            install_webhook_health_routes()
            super().setUpClass()

        def get_app(self):
            return updater_module.WebhookAppClass("/webhook/test-secret", None, asyncio.Queue(), None)

        def test_render_paths_return_200(self):
            for path in ("/", "/health", "/health/"):
                response = self.fetch(path)
                self.assertEqual(response.code, 200, path)
                self.assertIn(b'"status": "ok"', response.body)
            self.assertEqual(self.fetch("/health", method="HEAD").code, 200)
except ImportError:  # local minimal test environments may omit webhook extras
    WebhookHealthTests = None


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ImeiLookupTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(RenderWebhookConfigTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(SafePhoneInfoTests))
    if WebhookHealthTests is not None:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(WebhookHealthTests))
    unittest.TextTestRunner(verbosity=2).run(suite)
