import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app  # noqa: E402


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_get_config(self):
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("default_output_dir", data)
        self.assertIn("r2_config_exists", data)

    def test_convert_success(self):
        fake_result = {"title": "示例", "markdown_file": r"D:\obsidian\00_Inbox\01_示例\示例.md"}
        with patch("app.api.routes.run_pipeline", return_value=fake_result):
            response = self.client.post("/api/convert", json={"url": "https://mp.weixin.qq.com/s/example"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(response.json()["result"]["title"], "示例")

    def test_batch_from_text(self):
        with patch("app.api.routes.job_store.create_batch_job") as mocked:
            mocked.return_value = {
                "job_id": "job-1",
                "total": 2,
                "output_dir": r"D:\obsidian\00_Inbox",
            }
            response = self.client.post(
                "/api/batch",
                data={"urls_text": "https://mp.weixin.qq.com/s/a\nhttps://mp.weixin.qq.com/s/b"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["job_id"], "job-1")
        self.assertEqual(response.json()["deduped_count"], 2)

    def test_batch_from_file(self):
        with patch("app.api.routes.job_store.create_batch_job") as mocked:
            mocked.return_value = {
                "job_id": "job-file",
                "total": 1,
                "output_dir": r"D:\obsidian\00_Inbox",
            }
            response = self.client.post(
                "/api/batch",
                files={"file": ("links.txt", b"https://mp.weixin.qq.com/s/file-example", "text/plain")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["job_id"], "job-file")


if __name__ == "__main__":
    unittest.main()
