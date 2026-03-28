import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.auth import verify_password  # noqa: E402
from app.config import load_runtime_config  # noqa: E402


class ResetAdminCliTests(unittest.TestCase):
    def test_cli_rejects_missing_password_and_random_flag(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / "runtime-config.json"
            env = os.environ.copy()
            env.update(
                {
                    "WECHAT_MD_RUNTIME_CONFIG_PATH": str(runtime_path),
                    "WECHAT_MD_APP_MASTER_KEY": "test-master-key",
                    "WECHAT_MD_ADMIN_PASSWORD": "admin",
                }
            )

            result = subprocess.run(
                [sys.executable, "-m", "app.cli.reset_admin_password"],
                cwd=PROJECT_ROOT,
                env=env,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must provide --password or --random", result.stderr)

    def test_cli_rejects_conflicting_password_and_random_flag(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / "runtime-config.json"
            env = os.environ.copy()
            env.update(
                {
                    "WECHAT_MD_RUNTIME_CONFIG_PATH": str(runtime_path),
                    "WECHAT_MD_APP_MASTER_KEY": "test-master-key",
                    "WECHAT_MD_ADMIN_PASSWORD": "admin",
                }
            )

            result = subprocess.run(
                [sys.executable, "-m", "app.cli.reset_admin_password", "--password", "x", "--random"],
                cwd=PROJECT_ROOT,
                env=env,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot use --password and --random together", result.stderr)

    def test_cli_resets_admin_password_with_explicit_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / "runtime-config.json"
            env = os.environ.copy()
            env.update(
                {
                    "WECHAT_MD_RUNTIME_CONFIG_PATH": str(runtime_path),
                    "WECHAT_MD_APP_MASTER_KEY": "test-master-key",
                    "WECHAT_MD_ADMIN_USERNAME": "admin",
                    "WECHAT_MD_ADMIN_PASSWORD": "admin",
                }
            )
            with patch.dict(os.environ, env, clear=False):
                load_runtime_config(runtime_path)

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "app.cli.reset_admin_password",
                    "--username",
                    "rooter",
                    "--password",
                    "offline-secret",
                ],
                cwd=PROJECT_ROOT,
                env=env,
                capture_output=True,
                text=True,
            )

            with patch.dict(os.environ, env, clear=False):
                runtime_data = load_runtime_config(runtime_path)

        self.assertEqual(result.returncode, 0)
        self.assertIn("password reset successful", result.stdout)
        self.assertIn("username: rooter", result.stdout)
        self.assertEqual(runtime_data["auth"]["user"]["username"], "rooter")
        self.assertTrue(verify_password("offline-secret", runtime_data["auth"]["user"]["password_hash"]))

    def test_cli_can_generate_random_password(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_path = Path(temp_dir) / "runtime-config.json"
            env = os.environ.copy()
            env.update(
                {
                    "WECHAT_MD_RUNTIME_CONFIG_PATH": str(runtime_path),
                    "WECHAT_MD_APP_MASTER_KEY": "test-master-key",
                    "WECHAT_MD_ADMIN_PASSWORD": "admin",
                }
            )
            with patch.dict(os.environ, env, clear=False):
                load_runtime_config(runtime_path)

            result = subprocess.run(
                [sys.executable, "-m", "app.cli.reset_admin_password", "--random"],
                cwd=PROJECT_ROOT,
                env=env,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("generated password:", result.stdout)


if __name__ == "__main__":
    unittest.main()
