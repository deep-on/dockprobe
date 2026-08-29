"""The GPU rule: it fires when it should, and stays quiet when it should not.

Standard library only, like its neighbour:

    python -m unittest discover tests
"""
from __future__ import annotations

import unittest

try:
    from app import config
    from app.alerting.detector import AnomalyDetector
    HAVE_APP = True
except ImportError:  # pragma: no cover - a laptop without the runtime deps
    config = None
    AnomalyDetector = None
    HAVE_APP = False


def _host(**overrides):
    """A host reading with nothing wrong in it, so each test changes one thing."""
    host = {"cpu_temp": 40.0, "gpu_temp": None, "gpu_util": None, "disk": []}
    host.update(overrides)
    return host


@unittest.skipUnless(HAVE_APP, "the app's runtime dependencies are not installed")
class GpuTemperature(unittest.TestCase):

    def setUp(self) -> None:
        self.detector = AnomalyDetector()

    def _run(self, host):
        return [a["type"] for a in self.detector.check([], host)]

    def test_no_gpu_raises_nothing(self) -> None:
        """A machine without a card reads None, and None is not hot."""
        self.assertNotIn("gpu_temp", self._run(_host(gpu_temp=None)))

    def test_a_warm_gpu_is_left_alone(self) -> None:
        self.assertNotIn("gpu_temp", self._run(_host(gpu_temp=config.GPU_TEMP_THRESHOLD - 0.1)))

    def test_the_threshold_itself_is_not_over_it(self) -> None:
        self.assertNotIn("gpu_temp", self._run(_host(gpu_temp=config.GPU_TEMP_THRESHOLD)))

    def test_a_hot_gpu_raises_one_alert(self) -> None:
        alerts = self.detector.check([], _host(gpu_temp=config.GPU_TEMP_THRESHOLD + 5))
        gpu = [a for a in alerts if a["type"] == "gpu_temp"]
        self.assertEqual(len(gpu), 1)
        self.assertIn("GPU temperature", gpu[0]["msg"])
        self.assertEqual(gpu[0]["target"], "gpu")

    def test_a_busy_gpu_is_not_an_alert(self) -> None:
        """100% utilisation is a GPU doing its job, not a fault."""
        self.assertNotIn("gpu_temp", self._run(_host(gpu_util=100.0, gpu_temp=60.0)))


if __name__ == "__main__":
    unittest.main()
