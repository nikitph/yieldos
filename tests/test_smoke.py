from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from yieldos.models import SimConfig
from yieldos.policies import yieldos_v02
from yieldos.policies import policy_suite
from yieldos.simulator import run_simulation
from yieldos.trace_io import load_burstgpt_trace, load_trace, write_trace_csv
from yieldos.workloads import available_profiles, generate_mixed_trace, generate_profile_trace


class SmokeTests(unittest.TestCase):
    def test_trace_generation_is_reproducible(self) -> None:
        a = generate_mixed_trace(20, seed=3)
        b = generate_mixed_trace(20, seed=3)
        self.assertEqual(a, b)

    def test_all_policies_complete_small_trace(self) -> None:
        trace = generate_mixed_trace(60, seed=5)
        config = SimConfig(max_time_ms=120_000)
        for policy in policy_suite():
            with self.subTest(policy=policy.name):
                result = run_simulation(trace, policy, config=config, seed=5)
                self.assertEqual(result.metrics.requests, 60)
                self.assertGreater(result.metrics.completed, 0)
                self.assertGreaterEqual(result.metrics.governed_goodput, 0)

    def test_profile_generation_and_trace_roundtrip(self) -> None:
        trace = generate_profile_trace("chat_heavy", requests=12, seed=9)
        self.assertEqual(len(trace), 12)
        self.assertIn("rag_heavy", available_profiles())
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.csv"
            write_trace_csv(trace, path)
            loaded = load_trace(path)
        self.assertEqual(trace, loaded)

    def test_policy_label_does_not_change_policy_rng(self) -> None:
        trace = generate_mixed_trace(80, seed=12)
        config = SimConfig(max_time_ms=180_000)
        a = yieldos_v02()
        b = yieldos_v02()
        object.__setattr__(b, "name", "same_policy_different_label")
        first = run_simulation(trace, a, config=config, seed=12).metrics
        second = run_simulation(trace, b, config=config, seed=12).metrics
        self.assertEqual(first.governed_goodput, second.governed_goodput)
        self.assertEqual(first.kv_value_preserved, second.kv_value_preserved)

    def test_burstgpt_loader(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "burstgpt.csv"
            path.write_text(
                "Timestamp,Model,Request tokens,Response tokens,Total tokens,Log Type\n"
                "5,ChatGPT,472,18,490,Conversation log\n"
                "45,GPT-4,1087,230,1317,API log\n",
                encoding="utf-8",
            )
            trace = load_burstgpt_trace(str(path), limit=2, time_scale=10)
        self.assertEqual(len(trace), 2)
        self.assertEqual(trace[0].arrival_time_ms, 0)
        self.assertEqual(trace[1].arrival_time_ms, 4000)
        self.assertEqual(trace[0].priority_class, "interactive")


if __name__ == "__main__":
    unittest.main()
