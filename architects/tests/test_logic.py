"""
Unit tests for core logic components: ManagedMem, APIUsageGuard, and LLMUtilitySuite.
Includes a real API integration test class.
"""

import unittest
import os
import shutil
import tempfile
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from architects.helpers.managed_mem import ManagedMem
from ui_ux_team.blue_ui.app import api_usage_guard
from architects.helpers.api_utils import LLMUtilitySuite
from ui_ux_team.blue_ui.app.secure_api_key import read_api_key, set_runtime_api_key, RUNTIME_SOURCE_DOTENV
from ui_ux_team.blue_ui import settings as app_settings


class TestManagedMem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patcher = patch("architects.helpers.managed_mem.user_config_dir", return_value=Path(self.temp_dir))
        self.patcher.start()
        ManagedMem._instance = None
        self.mem = ManagedMem()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.temp_dir)

    def test_set_get(self):
        self.mem.settr("test_key", "test_value")
        self.assertEqual(self.mem.gettr("test_key"), "test_value")

    def test_persistence(self):
        self.mem.settr("persist_key", 123)
        self.mem.flush(wait=True)
        ManagedMem._instance = None
        new_mem = ManagedMem()
        self.assertEqual(new_mem.gettr("persist_key"), 123)


class TestAPIUsageGuard(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.p1 = patch("ui_ux_team.blue_ui.config.settings_store.user_config_dir", return_value=Path(self.temp_dir))
        self.p1.start()
        from ui_ux_team.blue_ui.config import set_setting
        set_setting("api_usage_state_month_spend_usd", 0.0)
        set_setting("api_usage_state_minute_count", 0)
        set_setting("api_usage_state_day_count", 0)

    def tearDown(self):
        self.p1.stop()
        shutil.rmtree(self.temp_dir)

    def test_reserve_request(self):
        allowed, reason = api_usage_guard.reserve_request("test_scope")
        self.assertTrue(allowed)
        self.assertEqual(reason, "")

    def test_record_usage(self):
        cost = api_usage_guard.record_usage(scope="test", model_name="gemini-2.5-flash", usage={"total_token_count": 1000000})
        self.assertGreater(cost, 0)
        state = api_usage_guard.current_usage_state()
        self.assertAlmostEqual(state["month_spend_usd"], cost, places=5)


class TestLLMUtilitySuite(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_key"
        self.client_patcher = patch("architects.helpers.api_utils.GenAIClient")
        self.mock_client_cls = self.client_patcher.start()
        self.mock_client = self.mock_client_cls.return_value
        LLMUtilitySuite._instance = None
        self.suite = LLMUtilitySuite(api_key=self.api_key)

    def tearDown(self):
        self.client_patcher.stop()

    def test_generate_text_mock(self):
        self.mock_client.generate_content.return_value = {"text": "mocked response"}
        res = self.suite.generate_text("hi")
        self.assertEqual(res, "mocked response")

    def test_chat_message_mock(self):
        mock_session = MagicMock()
        mock_session.send_message.return_value = {"text": "hello from AI"}
        res = LLMUtilitySuite.send_chat_message(mock_session, "hello")
        self.assertEqual(res, "hello from AI")


class TestLLMRealAPI(unittest.TestCase):
    """
    Integration test using a REAL API call.
    Only runs if an API key is available.
    """
    def setUp(self):
        # 1. Try Keyring
        self.api_key, _ = read_api_key()
        
        # 2. Try .env fallback
        if not self.api_key:
            self.api_key, _ = app_settings.read_dotenv_api_key()
            if self.api_key:
                set_runtime_api_key(self.api_key, source=RUNTIME_SOURCE_DOTENV)

        if not self.api_key:
            self.skipTest("No API key found in keyring or .env - skipping real API test.")

        # Reset singleton for real call
        LLMUtilitySuite._instance = None
        self.suite = LLMUtilitySuite(api_key=self.api_key)

    def test_real_ping_pong(self):
        # Use flash-lite for speed and to minimize quota usage
        print("\n[Real API Test] Sending 'ping' to Gemini (Flash Lite)...")
        res = self.suite.generate_text("Respond with exactly 'pong'", model_name="models/gemini-2.5-flash-lite")
        print(f"[Real API Test] Received: '{res}'")
        self.assertIn("pong", res.lower())

    def test_all_curated_models(self):
        """Iterate through all curated models and ensure they respond."""
        from ui_ux_team.blue_ui.widgets.model_settings_form import CHAT_MODELS, TRANSCRIPT_MODELS
        
        all_to_test = list(CHAT_MODELS.values()) + list(TRANSCRIPT_MODELS.values())
        unique_models = list(set(all_to_test))
        
        print(f"\n[Real API Test] Verifying {len(unique_models)} curated models...")
        
        for model_id in unique_models:
            print(f"  -> Testing {model_id}...")
            try:
                # Test basic generation with a system prompt to verify config normalization
                sys_prompt = "You are a helpful assistant."
                res = self.suite.generate_text("hi", model_name=model_id, system_prompt=sys_prompt)
                self.assertTrue(len(res) > 0, f"Model {model_id} returned empty string")
                print(f"     ✅ Response received.")
            except Exception as e:
                if "429" in str(e):
                    print(f"     ⚠️ Quota Exhausted (429) for {model_id}")
                else:
                    self.fail(f"Model {model_id} failed with error: {e}")


if __name__ == "__main__":
    unittest.main()
