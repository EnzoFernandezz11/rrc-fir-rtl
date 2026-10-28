import json
import tempfile
import unittest
from pathlib import Path

from scripts.ppa import LIBRARY, sha256
from scripts.ppa_compare import comparison_document, load_run, scenario_status


class PpaCompareStatusTest(unittest.TestCase):
    def test_legacy_power_derives_dynamic_metric_without_changing_source_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            runs = []
            for target, name in (("frequency_serial", "c02"), ("frequency_optimized", "c04")):
                directory = root / name
                directory.mkdir()
                (directory / "ppa_vectors.txt").write_text("benchmark")
                (directory / f"{LIBRARY}.lib").write_text("liberty")
                manifest = {"status": "physical_complete", "config": {"target": target},
                            "tools": {"yosys": "test"}, "library": {"name": LIBRARY},
                            "vectors_sha256": sha256(directory / "ppa_vectors.txt"),
                            "physical_method": "test", "artifacts_sha256": {}}
                manifest["library"]["sha256"] = sha256(directory / f"{LIBRARY}.lib")
                metrics = {"passed": True, "input_samples": 2048, "output_samples": 2048,
                           "clock_period_ns": 100, "latency_cycles": 5, "block_cycles": 6,
                           "active_cycles": 12, "throughput_samples_per_second": 1e6}
                for filename in ("local_metrics.json", "gate_metrics.json"):
                    (directory / filename).write_text(json.dumps(metrics))
                resources = directory / "resources.json"
                resources.write_text(json.dumps({"cell_area_um2": 10, "flip_flops": 4,
                                                 "combinational_cells": 6, "cells": 10}))
                manifest["artifacts_sha256"] = {"resources.json": sha256(resources)}
                power = {"internal_w": 0.002, "switching_w": 0.003, "leakage_w": 0.0001,
                         "total_w": 0.0051, "dynamic_energy_j": 1e-9, "total_energy_j": 1.1e-9}
                row = {"setup_ws_ns": 1, "hold_ws_ns": 1, "setup_violations": 0, "hold_violations": 0,
                       "constraint_warnings": 0, "unconstrained_endpoints": 0, "unannotated_routed_nets": 0,
                       "max_slew_violations": 0, "max_cap_violations": 0, "max_fanout_violations": 0}
                physical = {"areas": {"final_cell_area_um2": 11}, "scenarios": {}}
                for scenario in ("target", "common"):
                    physical["scenarios"][scenario] = {"timing": {"tt_025c_1v80": row}, "timing_pass": True,
                                                       "power": dict(power)}
                physical_path = directory / "physical_metrics.json"
                physical_path.write_text(json.dumps(physical))
                original = physical_path.read_bytes()
                (directory / "manifest.json").write_text(json.dumps(manifest))
                run = load_run(directory, target)
                self.assertEqual(run["values"]["dynamic_w"], 0.005)
                self.assertNotIn("dynamic_w", json.loads(original)["scenarios"]["target"]["power"])
                self.assertEqual(physical_path.read_bytes(), original)
                runs.append(run)
            text, data = comparison_document(*runs, root)
            self.assertIn("| Potencia dinámica | W | 0.005 | 0.005 |", text)
            self.assertIn("dynamic_w", data["charts"])
            self.assertEqual(sha256(runs[0]["directory"] / "physical_metrics.json"),
                             runs[0]["evidence"]["physical_metrics.json"])

    def test_status_legacy_derives_setup_and_electrical_separately(self):
        self.assertEqual(scenario_status({"timing": {"tt": {
            "setup_ws_ns": 0.2, "hold_ws_ns": 0.1, "setup_violations": 0, "hold_violations": 0,
            "constraint_warnings": 1, "unconstrained_endpoints": 0, "unannotated_routed_nets": 0,
            "max_slew_violations": 0, "max_cap_violations": 0, "max_fanout_violations": 0}}}),
                         (True, False, False))

    def test_document_preserves_common_power_but_no_common_charts_on_global_fail(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest = {"status": "physical_complete", "library": {"sha256": "lib"}, "tools": {"yosys": "0.52"},
                        "config": {"technology": "SKY130", "format": "x", "seed": 1, "symbols": 1,
                                   "samples": 2048, "input_available": 1, "output_ready": 1},
                        "vectors_sha256": "vectors", "physical_method": "test"}
            def run(name, setup, electrical, global_pass):
                row = {"setup_ws_ns": .2, "hold_ws_ns": .1, "setup_violations": 0, "hold_violations": 0,
                       "constraint_warnings": 0 if electrical else 1, "unconstrained_endpoints": 0,
                       "unannotated_routed_nets": 0, "max_slew_violations": 0, "max_cap_violations": 0,
                       "max_fanout_violations": 0, "fmax_estimate_mhz": 80}
                if not setup:
                    row.update(setup_ws_ns=-.1, setup_violations=2)
                scenarios = {}
                for scenario in ("target", "common"):
                    scenarios[scenario] = {"timing": {"tt_025c_1v80": row}, "timing_pass": global_pass,
                                           "power": {"total_w": .01, "total_energy_j": .001}}
                return {"directory": root / name, "manifest": dict(manifest), "physical": {"scenarios": scenarios},
                        "values": {"cell_area_um2": 10, "flip_flops": 4, "latency_cycles": 5,
                                   "block_cycles": 6, "final_cell_area_um2": 11}}
            a, b = run("c02", True, False, False), run("c04", False, True, False)
            text, data = comparison_document(a, b, root)
            self.assertIn("Setup/hold", text)
            self.assertIn("Eléctrico/restricciones", text)
            self.assertIn("| Setup/hold | PASS | FAIL |", text)
            self.assertIn("| total_w | W | 0.01 | 0.01 |", text)
            self.assertNotIn("radar-ppa-comun", data["charts"])
            self.assertNotIn("common-total_w", data["charts"])


if __name__ == "__main__":
    unittest.main()
