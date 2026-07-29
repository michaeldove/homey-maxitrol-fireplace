import unittest

from homey_test_support import load_app_module


class AppTests(unittest.IsolatedAsyncioTestCase):
    async def test_initialization_logs_success(self) -> None:
        module = load_app_module("app.py", "app")
        app = module.MertikFireplaceApp()

        await app.on_init()

        self.assertIn("Mertik Fireplace app initialized", app.logs)
