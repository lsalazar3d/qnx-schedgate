import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from schedgate.analyze import inspect_tree
from schedgate.parse_spec import parse_yaml_lite_threads
from schedgate.sched import hyperbolic_bound_ok, liu_layland_bound, rate_monotonic_ok, utilization
from schedgate.model import ThreadSpec


class SchedMathTests(unittest.TestCase):
    def test_liu_layland_one_task_is_one(self):
        self.assertAlmostEqual(liu_layland_bound(1), 1.0)

    def test_liu_layland_two_tasks(self):
        self.assertAlmostEqual(liu_layland_bound(2), 2 * (math.sqrt(2) - 1), places=9)

    def test_good_budget_is_schedulable(self):
        threads = [
            ThreadSpec("a", "SCHED_FIFO", 21, 10_000_000, 1_200_000, "t"),
            ThreadSpec("b", "SCHED_RR", 10, 50_000_000, 2_000_000, "t"),
        ]
        self.assertAlmostEqual(utilization(threads), 0.12 + 0.04, places=9)
        ok, u, bound = rate_monotonic_ok(threads)
        self.assertTrue(ok)
        self.assertLess(u, bound)
        self.assertTrue(hyperbolic_bound_ok(threads))


class YamlTests(unittest.TestCase):
    def test_parses_fixture(self):
        text = (ROOT / "schedgate/fixtures/good/schedgate.yml").read_text()
        threads = parse_yaml_lite_threads(text, "good.yml")
        self.assertEqual([t.name for t in threads], ["pulse_loop", "logger"])
        self.assertEqual(threads[0].policy, "SCHED_FIFO")
        self.assertEqual(threads[0].period_ns, 10_000_000)


class TreeTests(unittest.TestCase):
    def test_good_tree_has_no_errors(self):
        report = inspect_tree(ROOT / "schedgate/fixtures/good")
        self.assertEqual(report.errors, [], [f.message for f in report.errors])
        self.assertTrue(report.schedulable)
        self.assertEqual(len(report.threads), 2)

    def test_bad_tree_catches_policy_capacity_and_ifs(self):
        report = inspect_tree(ROOT / "schedgate/fixtures/bad")
        codes = {f.code for f in report.findings}
        self.assertIn("other-on-deadline", codes)
        self.assertIn("wcet-exceeds-period", codes)
        self.assertIn("ifs-world-writable", codes)
        self.assertIn("make-host-gcc-only", codes)
        self.assertTrue(report.errors)

    def test_sample_project_is_clean(self):
        report = inspect_tree(ROOT / "samples/qnx-heartbeat")
        self.assertEqual(report.errors, [], [f.message for f in report.errors])
        self.assertTrue(report.schedulable)


class CliTests(unittest.TestCase):
    def test_cli_good_exit_zero(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "schedgate.py"), str(ROOT / "schedgate/fixtures/good")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SCHEDULABLE", result.stdout)

    def test_cli_bad_exit_one(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "schedgate.py"), str(ROOT / "schedgate/fixtures/bad")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
