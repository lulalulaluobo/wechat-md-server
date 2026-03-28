import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings, load_runtime_config, save_runtime_config  # noqa: E402


class SettingsTests(unittest.TestCase):
    def test_runtime_config_migrates_flat_fields_and_initializes_admin_user(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / "runtime-config.json"
            runtime_path.write_text(
                '{"fns_base_url":"https://runtime.example.com","fns_token":"runtime-token","fns_vault":"runtime-vault"}',
                encoding="utf-8",
            )
            env = {"WECHAT_MD_RUNTIME_CONFIG_PATH": str(runtime_path)}
            with patch.dict(os.environ, env, clear=False):
                settings = get_settings()
                runtime_data = load_runtime_config(runtime_path)

        self.assertEqual(settings.fns_base_url, "https://runtime.example.com")
        self.assertEqual(settings.fns_token, "runtime-token")
        self.assertEqual(settings.fns_vault, "runtime-vault")
        self.assertEqual(runtime_data["auth"]["user"]["username"], "admin")
        self.assertIn("password_hash", runtime_data["auth"]["user"])
        self.assertIn("user_settings", runtime_data)
        self.assertEqual(runtime_data["user_settings"]["image_mode"], "wechat_hotlink")
        self.assertIn("image_storage", runtime_data["user_settings"])

    def test_password_hash_is_not_plaintext_admin(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / "runtime-config.json"
            env = {"WECHAT_MD_RUNTIME_CONFIG_PATH": str(runtime_path)}
            with patch.dict(os.environ, env, clear=False):
                runtime_data = load_runtime_config(runtime_path)

        password_hash = runtime_data["auth"]["user"]["password_hash"]
        self.assertNotEqual(password_hash, "admin")
        self.assertIn("$", password_hash)

    def test_save_runtime_config_persists_s3_image_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / "runtime-config.json"
            env = {"WECHAT_MD_RUNTIME_CONFIG_PATH": str(runtime_path)}
            with patch.dict(os.environ, env, clear=False):
                save_runtime_config(
                    {
                        "image_mode": "s3_hotlink",
                        "image_storage_endpoint": "https://s3.example.com",
                        "image_storage_region": "auto",
                        "image_storage_bucket": "bucket-a",
                        "image_storage_access_key_id": "key-1",
                        "image_storage_secret_access_key": "secret-1",
                        "image_storage_path_template": "wechat/{year}/{filename}",
                        "image_storage_public_base_url": "https://img.example.com",
                    }
                )
                settings = get_settings()
                runtime_data = load_runtime_config(runtime_path)

        self.assertEqual(settings.image_mode, "s3_hotlink")
        self.assertEqual(settings.image_storage_endpoint, "https://s3.example.com")
        self.assertEqual(settings.image_storage_public_base_url, "https://img.example.com")
        self.assertEqual(runtime_data["user_settings"]["image_mode"], "s3_hotlink")
        self.assertEqual(runtime_data["user_settings"]["image_storage"]["bucket"], "bucket-a")


if __name__ == "__main__":
    unittest.main()
