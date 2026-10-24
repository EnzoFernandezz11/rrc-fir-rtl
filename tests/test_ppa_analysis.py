"""Comparabilidad, normalización, actividad completa y rechazo de evidencia parcial."""

import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.ppa import LIBRARY, ROOT, record_run, sha256, target_settings
from scripts.ppa_compare import check_compatible, compare, comparison_document, load_run, score_pair
from scripts.ppa_physical import CORNERS, nominal_spef, parse_power, physical_areas, timing_metrics, trim_vcd


class PpaAnalysisTest(unittest.TestCase):
    def test_radar_direction_zeros_and_missing_dimensions(self):
        self.assertEqual(score_pair(10, 20, "min"), [100, 50])
        self.assertEqual(score_pair(10, 20, "max"), [50, 100])
        self.assertEqual(score_pair(0, 20, "min"), [100, 0])
        self.assertEqual(score_pair(0, 0, "min"), [100, 100])
        with self.assertRaises(ValueError):
            score_pair(-1, 1, "min")
        with self.assertRaises(ValueError):
            score_pair(float("nan"), 1, "max")

    def pair(self, root):
        manifest = {"status": "local_pass", "library": {"sha256": "lib"},
                    "tools": {"yosys": "0.52"}, "config": {"technology": "SKY130"},
                    "vectors_sha256": "vectors"}
        a = {"directory": root / "c02", "manifest": manifest, "physical": None,
             "values": {"cell_area_um2": 100, "flip_flops": 10, "latency_cycles": 559,
                        "block_cycles": 575, "output_samples": 2048}}
        b = copy.deepcopy(a)
        b["directory"] = root / "c04"
        b["values"].update(cell_area_um2=1000, flip_flops=100, latency_cycles=26, block_cycles=8)
        return a, b

    def test_missing_power_is_not_zero_and_incompatible_tools_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            a, b = self.pair(directory)
            text, data = comparison_document(a, b, directory)
            self.assertIn("No medida", text)
            self.assertIn("sin timing físico demostrado", text)
            self.assertIn("radar-arquitectura", data["charts"])
            self.assertNotIn("radar-ppa-comun", data["charts"])
            self.assertFalse((directory / "total_w.mmd").exists())
            b["manifest"]["tools"]["yosys"] = "other"
            with self.assertRaisesRegex(ValueError, "incompatibles"):
                check_compatible(a, b)

    def test_new_run_invalidates_comparison_and_preserves_history(self):
        with tempfile.TemporaryDirectory() as raw:
            report = Path(raw) / "report.md"
            report.write_text("<!-- serial-runs:start -->old<!-- serial-runs:end -->\n"
                              "<!-- comparison:start -->old graph<!-- comparison:end -->\nHISTORY")
            record_run("new", "# New", "hash", report)
            self.assertIn("pendiente de regenerar", report.read_text())
            self.assertNotIn("old graph", report.read_text())
            self.assertTrue(report.read_text().endswith("HISTORY"))

    def evidence_pair(self, root):
        paths = []
        for target, name in (("frequency_serial", "c02"), ("frequency_optimized", "c04")):
            p = root / name
            p.mkdir()
            (p / "ppa_vectors.txt").write_text("benchmark")
            (p / (LIBRARY + ".lib")).write_text("liberty")
            m = {"status": "local_pass", "config": {"target": target}, "tools": {"yosys": "test"},
                 "library": {"name": LIBRARY, "sha256": sha256(p / (LIBRARY + ".lib"))},
                 "vectors_sha256": sha256(p / "ppa_vectors.txt")}
            metrics = {"passed": True, "input_samples": 2048, "output_samples": 2048,
                       "clock_period_ns": 100, "latency_cycles": 559, "block_cycles": 575,
                       "active_cycles": 147200, "throughput_samples_per_second": 139130.434782609}
            for filename in ("local_metrics.json", "gate_metrics.json"):
                (p / filename).write_text(json.dumps(metrics))
            (p / "resources.json").write_text(json.dumps({"cells": 4474, "flip_flops": 610,
                 "combinational_cells": 3864, "cell_area_um2": 38448.1248}))
            m["artifacts_sha256"] = {"resources.json": sha256(p / "resources.json")}
            (p / "manifest.json").write_text(json.dumps(m))
            paths.append(p)
        return paths

    def test_tampered_evidence_and_failed_comparison_do_not_publish(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            a, b = self.evidence_pair(root)
            self.assertEqual(load_run(a, "frequency_serial")["values"]["cells"], 4474)
            (b / "resources.json").write_text("{}")
            report = root / "report.md"
            original = ("<!-- serial-runs:start -->c02<!-- serial-runs:end -->\n"
                        "<!-- optimized-runs:start -->c04<!-- optimized-runs:end -->\nHISTORY")
            report.write_text(original)
            with self.assertRaisesRegex(ValueError, "alterado"):
                compare(a, b, report=report)
            self.assertEqual(report.read_text(), original)
            m = json.loads((a / "manifest.json").read_text())
            m["artifacts_sha256"] = {"../outside": "digest"}
            (a / "manifest.json").write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError, "fuera"):
                load_run(a, "frequency_serial")

    def test_activity_crop_rebases_preserves_initial_state_and_rejects_truncation(self):
        header = ("$timescale 1ns $end\n$scope module tb $end\n$scope module dut $end\n"
                  "$var wire 1 ! clk $end\n$var wire 2 \" data [1:0] $end\n"
                  "$upscope $end\n$upscope $end\n$enddefinitions $end\n")
        with tempfile.TemporaryDirectory() as raw:
            source, output = Path(raw) / "raw.vcd", Path(raw) / "power.vcd"
            source.write_text(header + "#0\n$dumpvars\n0!\nb00 \"\n$end\n"
                              "#10\n1!\n#15\n0!\nb11 \"\n#20\n1!\n#25\n0!\n")
            meta = trim_vcd(source, output, 10, 10, "tb/dut")
            text = output.read_text()
            self.assertIn("#0\n$dumpvars\n0!\nb00 \"\n$end\n#0\n1!", text)
            self.assertIn("#5\n0!\nb11 \"", text)
            self.assertTrue(text.endswith("#10\n"))
            self.assertEqual(meta["nets"], ["clk", "data[0]", "data[1]"])
            with self.assertRaisesRegex(ValueError, "truncado"):
                trim_vcd(source, output, 10, 100, "tb/dut")
            with self.assertRaisesRegex(ValueError, "scope"):
                trim_vcd(source, output, 10, 10, "wrong/dut")

    def test_power_window_energy_and_name_coverage(self):
        self.assertEqual(nominal_spef({"spef": {"nom_*": "nom.spef", "min_*": "min.spef"}}), Path("nom.spef"))
        with self.assertRaises(ValueError):
            nominal_spef({"spef": {"min_*": "min.spef"}})
        coverage = {"start_ns": 1000, "duration_ns": 1000, "sha256": "activity"}
        metrics = {"activity_duration_ns": 1000, "output_samples": 100}
        result = parse_power("Annotated 90 pin activities.\nPPA_POWER 0.001 0.002 0.0001 0.0031\nPPA_COVERAGE 100 0\nPPA_INTERNAL_EXCLUDED 2\n", metrics, coverage)
        self.assertAlmostEqual(result["dynamic_energy_j"], 3e-11)
        self.assertAlmostEqual(result["total_energy_j"], 3.1e-11)
        self.assertEqual(result["activity_coverage_pct"], 100)
        self.assertEqual(result["excluded_liberty_internal_pins"], 2)
        with self.assertRaisesRegex(ValueError, "corresponde"):
            parse_power("Annotated 90 pin activities.\nPPA_POWER 0.001 0.002 0.0001 0.0031\nPPA_COVERAGE 99 1\nPPA_INTERNAL_EXCLUDED 2\n", metrics, coverage)
        with self.assertRaisesRegex(ValueError, "Falta"):
            parse_power("report_power incomplete", metrics, coverage)

    def test_physical_area_uses_micron_bounding_boxes_not_synthesis_area(self):
        metrics = {"design__instance__area": 1800, "design__core__bbox": "5 5 55 55",
                   "design__die__bbox": [0, 0, 60, 60]}
        self.assertEqual(physical_areas(metrics),
                         {"final_cell_area_um2": 1800, "core_area_um2": 2500, "die_area_um2": 3600})
        metrics["design__core__bbox"] = "5 5 5 55"
        with self.assertRaisesRegex(ValueError, "vacío"):
            physical_areas(metrics)

    def test_all_timing_corners_required_and_failure_is_a_result(self):
        metrics = {}
        for corner in CORNERS:
            for suffix in ("setup__ws", "hold__ws", "setup__wns", "hold__wns",
                           "setup__tns", "hold__tns", "setup_vio__count", "hold_vio__count"):
                metrics[f"timing__{suffix}__corner:{corner}"] = 0
            for suffix in ("max_cap_violation__count", "max_slew_violation__count", "max_fanout_violation__count"):
                metrics[f"design__{suffix}__corner:{corner}"] = 0
            metrics[f"timing__setup_r2r__ws__corner:{corner}"] = 2
            metrics[f"timing__unannotated_net_filtered__count__corner:{corner}"] = 0
        with tempfile.TemporaryDirectory() as raw:
            reports = Path(raw)
            for corner in CORNERS:
                (reports / corner).mkdir()
                (reports / corner / "checks.rpt").write_text("check_setup -verbose -unconstrained_endpoints\n")
            rows, passed = timing_metrics({"metrics": metrics}, 10, reports)
            self.assertEqual(len(rows), 9)
            self.assertTrue(passed)
            self.assertEqual(rows[CORNERS[0]]["fmax_estimate_mhz"], 125)
            checks = reports / CORNERS[0] / "checks.rpt"
            checks.write_text(checks.read_text() + "Warning: There are 2 unconstrained endpoints.\n")
            with self.assertRaisesRegex(ValueError, "incompletos"):
                timing_metrics({"metrics": metrics}, 10, reports)
            checks.write_text("check_setup -verbose -unconstrained_endpoints\n")
            metrics[f"timing__unannotated_net_filtered__count__corner:{CORNERS[0]}"] = 1
            with self.assertRaisesRegex(ValueError, "incompletos"):
                timing_metrics({"metrics": metrics}, 10, reports)
            metrics[f"timing__unannotated_net_filtered__count__corner:{CORNERS[0]}"] = 0
            metrics[f"timing__setup__ws__corner:{CORNERS[1]}"] = -1
            self.assertFalse(timing_metrics({"metrics": metrics}, 10, reports)[1])
            del metrics[f"timing__hold__ws__corner:{CORNERS[-1]}"]
            with self.assertRaisesRegex(ValueError, "incompleto"):
                timing_metrics({"metrics": metrics}, 10, reports)

    def test_full_activity_benchmark_reaches_last_sample_for_both_targets(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            vectors = directory / "vectors.txt"
            vectors.write_text("2048\n" + "0 0 0 0\n" * 2048)
            for target in ("frequency_serial", "frequency_optimized"):
                cfg = target_settings(target)
                executable, vcd, metrics = (directory / n for n in ("sim.out", "activity.vcd", "metrics.json"))
                subprocess.run(["iverilog", "-g2012", "-s", cfg["bench"], "-o", str(executable),
                                *cfg["sources"], cfg["bench_path"]], cwd=ROOT, check=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["vvp", str(executable), f"+VECTORS={vectors}",
                                f"+POWER_VCD={vcd}", f"+METRICS={metrics}"], cwd=ROOT, check=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                m = json.loads(metrics.read_text())
                trimmed = directory / "trimmed.vcd"
                meta = trim_vcd(vcd, trimmed, m["activity_start_ns"], m["activity_duration_ns"], cfg["bench"] + "/dut")
                self.assertEqual(m["output_samples"], 2048)
                self.assertEqual(meta["duration_ns"], m["active_cycles"] * cfg["clock_period_ns"])
                self.assertEqual(meta["sha256"], sha256(trimmed))


if __name__ == "__main__":
    unittest.main()
