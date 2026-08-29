"""The two rules that cost somebody their dashboard when they were wrong.

Standard library only, so this runs anywhere the app runs:

    python -m unittest discover tests

The auth tests need the app's runtime dependencies, which are in the image but
not necessarily on a laptop; they skip themselves rather than fail when those are
missing. The image carries the dependencies but not this directory, so to run them
against the published image, mount it in:

    docker run --rm --entrypoint python -v "$PWD/tests:/app/tests:ro" -w /app \
        deeponinc/dockprobe:latest -m unittest discover tests
"""
from __future__ import annotations

import importlib
import os
import unittest

try:
    from app import main as dockprobe
    HAVE_APP = True
except ImportError:  # pragma: no cover — a laptop without the runtime deps
    dockprobe = None
    HAVE_APP = False


class FakeClient:
    def __init__(self, host: str) -> None:
        self.host = host


class FakeRequest:
    """Enough of a Request for _check_auth: headers and a peer address."""

    def __init__(self, ip: str, authorization: str | None = None) -> None:
        self.client = FakeClient(ip)
        self.headers = {} if authorization is None else {"Authorization": authorization}
        self.method = "GET"


class CpuThresholdDefault(unittest.TestCase):
    """100% is one core, so a fixed number means different things per machine."""

    def setUp(self) -> None:
        self._saved = os.environ.get("CPU_THRESHOLD")

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop("CPU_THRESHOLD", None)
        else:
            os.environ["CPU_THRESHOLD"] = self._saved

    def _threshold(self) -> float:
        from app import config
        return importlib.reload(config).CPU_THRESHOLD

    def test_unset_scales_with_the_core_count(self) -> None:
        os.environ.pop("CPU_THRESHOLD", None)
        self.assertEqual(self._threshold(), 80.0 * (os.cpu_count() or 1))

    def test_empty_counts_as_unset(self) -> None:
        # compose passes the variable through whether or not anyone filled it in.
        os.environ["CPU_THRESHOLD"] = ""
        self.assertEqual(self._threshold(), 80.0 * (os.cpu_count() or 1))

    def test_an_explicit_value_is_left_alone(self) -> None:
        os.environ["CPU_THRESHOLD"] = "250"
        self.assertEqual(self._threshold(), 250.0)


@unittest.skipUnless(HAVE_APP, "app.main needs the runtime dependencies")
class FailedLoginCounting(unittest.TestCase):
    """Only a refused guess counts. The opening request of Basic auth is not one.

    Five in a minute blocks the address — the browser on the same desk included —
    and the dashboard asks for five things at once on its first refresh. Counting
    the header-less request meant one cold open was enough to lock the door.
    """

    def setUp(self) -> None:
        self.main = dockprobe
        self._auth = dockprobe._load_auth
        dockprobe._load_auth = lambda: ("admin", dockprobe._hash_pw("correct-horse"))
        dockprobe._fail_log.clear()

    def tearDown(self) -> None:
        self.main._load_auth = self._auth
        self.main._fail_log.clear()

    @staticmethod
    def _basic(user: str, password: str) -> str:
        import base64
        return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()

    def test_no_header_is_challenged_but_not_counted(self) -> None:
        for _ in range(10):
            response = self.main._check_auth(FakeRequest("10.0.0.9"))
            self.assertEqual(response.status_code, 401)
        self.assertEqual(len(self.main._fail_log["10.0.0.9"]), 0,
                         "opening a Basic exchange must not look like a failed login")

    def test_a_wrong_password_is_counted(self) -> None:
        for _ in range(3):
            self.main._check_auth(FakeRequest("10.0.0.9", self._basic("admin", "nope")))
        self.assertEqual(len(self.main._fail_log["10.0.0.9"]), 3)

    def test_enough_wrong_passwords_still_lock_the_address(self) -> None:
        for _ in range(self.main.RATE_MAX_FAILS):
            self.main._check_auth(FakeRequest("10.0.0.9", self._basic("admin", "nope")))
        response = self.main._check_auth(FakeRequest("10.0.0.9", self._basic("admin", "nope")))
        self.assertEqual(response.status_code, 429)

    def test_the_right_password_passes(self) -> None:
        request = FakeRequest("10.0.0.9", self._basic("admin", "correct-horse"))
        self.assertIsNone(self.main._check_auth(request))
        self.assertEqual(len(self.main._fail_log["10.0.0.9"]), 0)


if __name__ == "__main__":
    unittest.main()
