"""Comparabilidad, normalización, actividad completa y rechazo de evidencia parcial."""

import copy
import json
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from scripts.ppa import LIBRARY, ROOT, record_run, sha256, target_settings
from scripts.ppa_compare import check_compatible, compare, comparison_document, load_run, score_pair
from scripts.ppa_physical import (CORNERS, nominal_spef, parse_power, physical_areas,
                                  combine_segment_power, physical_summary, profiled_run,
                                  timing_metrics, split_vcd, write_power_sdc)


def has_linux_gnu_time():
    if not Path("/proc/meminfo").is_file() or not shutil.which("/usr/bin/time"):
        return False
    try:
        result = subprocess.run(["/usr/bin/time", "--version"], capture_output=True,
                                text=True, timeout=2)
        return result.returncode == 0 and "GNU" in result.stdout
    except (OSError, subprocess.TimeoutExpired):
        return False


HAS_LINUX_GNU_TIME = has_linux_gnu_time()


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

    def test_comparison_publishes_chart_sources_with_valid_relative_links(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            a, b = self.evidence_pair(root)
            report = root / "reports/frequency.md"
            report.parent.mkdir()
            report.write_text("<!-- serial-runs:start -->c02<!-- serial-runs:end -->\n"
                              "<!-- optimized-runs:start -->c04<!-- optimized-runs:end -->\n"
                              "## Referencia histórica preservada\n")
            output = compare(a, b, report=report)
            self.assertTrue(output.is_relative_to(report.parent))
            for document in (report, output / "comparison.md"):
                links = re.findall(r"\]\(([^)]+)\)", document.read_text())
                self.assertTrue(links)
                for link in links:
                    self.assertTrue((document.parent / link).exists(), (document, link))

    def test_activity_split_rebases_preserves_initial_state_and_rejects_truncation(self):
        header = ("$timescale 1ns $end\n$scope module tb $end\n$scope module dut $end\n"
                  "$var wire 1 ! clk $end\n$var wire 2 \" data [1:0] $end\n"
                  "$upscope $end\n$upscope $end\n$enddefinitions $end\n")
        with tempfile.TemporaryDirectory() as raw:
            source, output = Path(raw) / "raw.vcd", Path(raw) / "parts"
            output.mkdir()
            source.write_text(header + "#0\n$dumpvars\n0!\nb00 \"\n$end\n"
                              "#10\n1!\n#15\n0!\nb11 \"\n#20\n1!\n#25\n0!\n")
            meta = split_vcd(source, output, 10, 10, "tb/dut", segments=2)
            first, second = (Path(part["path"]).read_text() for part in meta["segments"])
            self.assertIn("#0\n$dumpvars\n0!\nb00 \"\n$end\n#0\n1!", first)
            self.assertTrue(first.endswith("#5\n"))
            self.assertIn("#0\n$dumpvars\n1!\nb00 \"\n$end\n#0\n0!\nb11 \"", second)
            self.assertTrue(second.endswith("#5\n"))
            self.assertEqual(meta["nets"], ["clk", "data[0]", "data[1]"])
            with self.assertRaisesRegex(ValueError, "truncado"):
                split_vcd(source, output, 10, 100, "tb/dut", segments=2)
            with self.assertRaisesRegex(ValueError, "scope"):
                split_vcd(source, output, 10, 10, "wrong/dut", segments=2)

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
        combined = combine_segment_power([
            ({"internal_w": 1, "switching_w": 0, "leakage_w": 0, "total_w": 1,
              "dynamic_energy_j": 2, "total_energy_j": 3}, 3),
            ({"internal_w": 3, "switching_w": 0, "leakage_w": 0, "total_w": 3,
              "dynamic_energy_j": 5, "total_energy_j": 7}, 1),
        ], 4)
        self.assertEqual(combined["total_w"], 1.5)
        self.assertEqual(combined["dynamic_w"], combined["internal_w"] + combined["switching_w"])
        self.assertAlmostEqual(combined["total_w"], combined["dynamic_w"] + combined["leakage_w"])
        self.assertEqual(combined["dynamic_energy_j"], 7)
        with self.assertRaisesRegex(ValueError, "difiere"):
            combine_segment_power([], 1)
        with self.assertRaisesRegex(ValueError, "corresponde"):
            parse_power("Annotated 90 pin activities.\nPPA_POWER 0.001 0.002 0.0001 0.0031\nPPA_COVERAGE 99 1\nPPA_INTERNAL_EXCLUDED 2\n", metrics, coverage)
        with self.assertRaisesRegex(ValueError, "Falta"):
            parse_power("report_power incomplete", metrics, coverage)

    def test_power_parser_preserves_opensta_diagnostics(self):
        with self.assertRaisesRegex(ValueError, "vcd period 10 differs from SDC period 100"):
            parse_power("Warning: vcd period 10 differs from SDC period 100", {}, {})
        with self.assertRaisesRegex(ValueError, "Error: cannot read VCD"):
            parse_power("Error: cannot read VCD", {}, {})

    @unittest.skipUnless(HAS_LINUX_GNU_TIME, "Requiere Linux y GNU time en /usr/bin/time")
    def test_profiled_run_keeps_resource_report(self):
        with tempfile.TemporaryDirectory() as raw:
            log = Path(raw) / "benchmark.log"
            usage = profiled_run(["python3", "-c", "import os; print(os.environ['LC_ALL']); print(os.environ['TMPDIR'])"], log)
            self.assertEqual(usage.name, "benchmark.resource.txt")
            self.assertIn("Maximum resident set size", usage.read_text())
            self.assertIn("MemAvailable", (Path(raw) / "benchmark.monitor.jsonl").read_text())
            self.assertEqual(log.read_text().splitlines(), ["C", str(ROOT / "build/tmp")])
            started = time.monotonic()
            with self.assertRaises(subprocess.TimeoutExpired):
                profiled_run(["python3", "-c", "import time; time.sleep(30)"], log, timeout=.2)
            self.assertLess(time.monotonic() - started, 3)
            self.assertIn('"abort_reason": "TimeoutExpired"',
                          (Path(raw) / "benchmark.monitor.jsonl").read_text())

    @unittest.skipUnless(HAS_LINUX_GNU_TIME, "Requiere Linux y GNU time en /usr/bin/time")
    def test_profiled_run_cleans_process_group_on_keyboard_interrupt(self):
        with tempfile.TemporaryDirectory() as raw:
            log = Path(raw) / "interrupt.log"
            with patch("scripts.ppa_physical.subprocess.Popen") as popen, \
                    patch("scripts.ppa_physical.os.killpg") as killpg:
                process = popen.return_value
                process.pid = 24680
                process.poll.return_value = None
                process.wait.side_effect = [KeyboardInterrupt, 0, 0]
                with self.assertRaises(KeyboardInterrupt):
                    profiled_run(["sta", "-exit", "power.tcl"], log)
                killpg.assert_called_once_with(24680, signal.SIGTERM)

    def test_power_sdc_changes_only_validated_clock_period(self):
        with tempfile.TemporaryDirectory() as raw:
            source, destination = Path(raw) / "resolved.sdc", Path(raw) / "power.sdc"
            source.write_text("set_input_delay 2 -clock clk [all_inputs]\n"
                              "create_clock -name clk -period 100.0000 [get_ports clk]\n")
            write_power_sdc(source, destination, 10)
            self.assertEqual(destination.read_text(),
                             "set_input_delay 2 -clock clk [all_inputs]\n"
                             "create_clock -name clk -period 10.0000 [get_ports clk]\n")
            source.write_text("set_input_delay 2 -clock clk [all_inputs]\n")
            with self.assertRaisesRegex(ValueError, "período"):
                write_power_sdc(source, destination, 10)

    def test_physical_summary_handles_legacy_status_and_lists_corner_timing(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            (directory / "target").mkdir()
            (directory / "target/metrics.json").write_text(json.dumps({
                "latency_cycles": 5, "block_cycles": 8, "active_cycles": 20,
                "throughput_samples_per_second": 1000,
            }))
            timing_row = {"setup_ws_ns": 1.0, "hold_ws_ns": .2, "setup_violations": 0,
                          "hold_violations": 0, "max_slew_violations": 0,
                          "max_cap_violations": 1, "max_fanout_violations": 0,
                          "constraint_warnings": 0, "unconstrained_endpoints": 0,
                          "unannotated_routed_nets": 0, "fmax_estimate_mhz": 125.0}
            power = {key: 1e-3 for key in ("internal_w", "switching_w", "leakage_w",
                                             "total_w", "dynamic_energy_j", "total_energy_j")}
            scenario = {"clock_period_ns": 100, "timing": {CORNERS[0]: timing_row},
                        "timing_pass": False, "power": power}
            (directory / "openlane-target.json").write_text("{}")
            result = {"areas": {"final_cell_area_um2": 100, "core_area_um2": 200,
                                 "die_area_um2": 300},
                      "scenarios": {"target": scenario, "common": copy.deepcopy(scenario)}}
            manifest = {"config": {"target": "frequency_optimized"},
                        "resume_provenance": {"reused_physical_layout": True,
                                               "source_run": str(directory / "source-run")}}
            report = physical_summary(directory, manifest, result)
            self.assertIn("no hizo placement ni routing nuevos", report)
            self.assertIn("simulación funcional de la netlist y el análisis de potencia", report)
            self.assertIn("| PASS | FAIL | FAIL |", report)
            self.assertIn(CORNERS[0], report)
            self.assertIn("125.00", report)
            self.assertIn("0.002", report)
            self.assertNotIn("dynamic_w", power)
            self.assertIn("openlane-target.json", report)
            self.assertNotIn("openlane-common.json", report)
            self.assertIn("escenario common comparte la corrida target", report)
            self.assertRegex(report, r"\[Actividad y potencia common\]\([^)]*/target/\)")
            self.assertNotIn("/common/", report)
            scenario.update(setup_hold_pass=True, electrical_constraints_pass=False)
            self.assertIn("| PASS | FAIL | FAIL |", physical_summary(directory, manifest, result))

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
            rows, passed, setup_hold_pass, electrical_pass = timing_metrics({"metrics": metrics}, 10, reports)
            self.assertEqual(len(rows), 9)
            self.assertTrue(passed)
            self.assertTrue(setup_hold_pass)
            self.assertTrue(electrical_pass)
            self.assertEqual(rows[CORNERS[0]]["fmax_estimate_mhz"], 125)
            metrics[f"timing__setup_r2r__ws__corner:{CORNERS[0]}"] = float("inf")
            clock = reports / CORNERS[0] / "clock.rpt"
            clock.write_text("report_clock_min_period\nclk period_min = 6.90 fmax = 144.90\n")
            rows, _, _, _ = timing_metrics({"metrics": metrics}, 10, reports)
            self.assertEqual(rows[CORNERS[0]]["fmax_estimate_mhz"], 144.90)
            clock.write_text("report_clock_min_period\nclk period_min = 6.90\n")
            rows, _, _, _ = timing_metrics({"metrics": metrics}, 10, reports)
            self.assertAlmostEqual(rows[CORNERS[0]]["fmax_estimate_mhz"], 1000 / 6.9)
            checks = reports / CORNERS[0] / "checks.rpt"
            checks.write_text(checks.read_text() + "Warning: There are 2 unconstrained endpoints.\n")
            with self.assertRaisesRegex(ValueError, "incompletos"):
                timing_metrics({"metrics": metrics}, 10, reports)
            checks.write_text("check_setup -verbose -unconstrained_endpoints\n")
            metrics[f"timing__unannotated_net_filtered__count__corner:{CORNERS[0]}"] = 1
            with self.assertRaisesRegex(ValueError, "incompletos"):
                timing_metrics({"metrics": metrics}, 10, reports)
            metrics[f"timing__unannotated_net_filtered__count__corner:{CORNERS[0]}"] = 0
            metrics[f"design__max_cap_violation__count__corner:{CORNERS[0]}"] = 1
            _, passed, setup_hold_pass, electrical_pass = timing_metrics({"metrics": metrics}, 10, reports)
            self.assertFalse(passed)
            self.assertTrue(setup_hold_pass)
            self.assertFalse(electrical_pass)
            metrics[f"design__max_cap_violation__count__corner:{CORNERS[0]}"] = 0
            metrics[f"timing__setup__ws__corner:{CORNERS[1]}"] = -1
            _, passed, setup_hold_pass, electrical_pass = timing_metrics({"metrics": metrics}, 10, reports)
            self.assertFalse(passed)
            self.assertFalse(setup_hold_pass)
            self.assertTrue(electrical_pass)
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
                parts = directory / target
                parts.mkdir()
                meta = split_vcd(vcd, parts, m["activity_start_ns"], m["activity_duration_ns"],
                                 cfg["bench"] + "/dut", segments=8,
                                 clock_period_ns=cfg["clock_period_ns"])
                self.assertEqual(m["output_samples"], 2048)
                self.assertEqual(meta["duration_ns"], m["active_cycles"] * cfg["clock_period_ns"])
                self.assertEqual(len(meta["segments"]), 8)
                self.assertAlmostEqual(sum(part["duration_ns"] for part in meta["segments"]), meta["duration_ns"])
                self.assertTrue(all(Path(part["path"]).is_file() for part in meta["segments"]))


if __name__ == "__main__":
    unittest.main()
