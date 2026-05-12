import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import bot_workers  # noqa: E402


class _FakeTelegramStop:
    def __init__(self, loops: int) -> None:
        self.loops = loops
        self.wait_calls = 0

    def is_set(self) -> bool:
        return self.wait_calls >= self.loops

    def wait(self, _: int) -> None:
        self.wait_calls += 1


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def post(self, url: str, **_: object) -> _FakeResponse:
        self.calls.append(url.rsplit("/", 1)[-1])
        if url.endswith("/getUpdates"):
            return _FakeResponse({"ok": True, "result": []})
        return _FakeResponse({"ok": True})


def test_telegram_polling_deletes_webhook_once_per_token() -> None:
    fake_session = _FakeSession()
    settings = SimpleNamespace(
        telegram_enabled=True,
        telegram_receive_mode="polling",
        telegram_bot_token="telegram-token",
        telegram_poll_interval=1,
        default_timeout=1,
    )

    with patch.object(bot_workers, "_telegram_stop", _FakeTelegramStop(loops=2)):
        with patch.object(bot_workers, "get_settings", return_value=settings):
            with patch.object(bot_workers.requests, "Session", return_value=fake_session):
                bot_workers._telegram_polling_loop()

    assert fake_session.calls == ["deleteWebhook", "getUpdates", "getUpdates"]
