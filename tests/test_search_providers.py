import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.search.sogou_weixin import search_sogou_weixin  # noqa: E402


class SearchProviderTests(unittest.TestCase):
    def test_sogou_weixin_parses_public_html(self):
        html = """
        <html><body>
          <div class="news-box">
            <ul class="news-list">
              <li>
                <div class="txt-box">
                  <h3><a target="_blank" href="https://mp.weixin.qq.com/s/abc">AI <em>编程</em>工作流实践</a></h3>
                  <p class="txt-info">摘要 <em>片段</em></p>
                  <div class="s-p">
                    <a class="account">某公众号</a>
                    <span class="s2">2026-05-01</span>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </body></html>
        """
        response = Mock(status_code=200, text=html)
        response.raise_for_status.return_value = None

        with patch("app.search.sogou_weixin.requests.get", return_value=response):
            results = search_sogou_weixin("AI 编程工作流", limit=10)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "AI 编程工作流实践")
        self.assertEqual(results[0]["url"], "https://mp.weixin.qq.com/s/abc")
        self.assertEqual(results[0]["source_name"], "某公众号")
        self.assertEqual(results[0]["published_at"], "2026-05-01")
        self.assertEqual(results[0]["snippet"], "摘要 片段")
        self.assertEqual(results[0]["provider"], "sogou_weixin")

    def test_sogou_weixin_empty_html_returns_empty_results(self):
        response = Mock(status_code=200, text="<html><body></body></html>")
        response.raise_for_status.return_value = None

        with patch("app.search.sogou_weixin.requests.get", return_value=response):
            results = search_sogou_weixin("无结果", limit=10)

        self.assertEqual(results, [])

    def test_sogou_weixin_request_error_is_clear(self):
        with patch("app.search.sogou_weixin.requests.get", side_effect=RuntimeError("network down")):
            with self.assertRaisesRegex(RuntimeError, "搜狗微信搜索失败"):
                search_sogou_weixin("AI", limit=10)


if __name__ == "__main__":
    unittest.main()
