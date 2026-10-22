"""Conteo ASIC, benchmarks y reemplazo seguro de la última corrida PPA."""

import unittest
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.ppa import TOP, measurement_key, record_run, resource_counts, target_settings, package, sha256, liberty_flops, sky130_library, LIBRARY
from scripts.validate_project import ROOT


class PpaResourcesTest(unittest.TestCase):
    def test_vivado_options_and_report_parsers(self):
        result = subprocess.run(
            ["tclsh", "scripts/ppa/vivado/selftest.tcl"], cwd=ROOT,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("PASS", result.stdout)

    def test_benchmark_clock_period_and_metrics(self):
        targets = json.loads((ROOT / "config/rtl_targets.json").read_text())["targets"]
        target = next(t for t in targets if t["name"] == "frequency_serial")
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            executable = directory / "ppa.out"
            compiled = subprocess.run(
                ["iverilog", "-g2012", "-s", "tb_fir_frequency_ppa", "-o", str(executable),
                 *target["sources"], "tb/frequency/tb_fir_frequency_ppa.sv"],
                cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout)
            vectors = directory / "zeros.txt"
            vectors.write_text("2048\n" + "0 0 0 0\n" * 2048)
            for period in (100, 12.5):
                with self.subTest(period=period):
                    metrics_path = directory / "metrics.json"
                    result = subprocess.run(
                        ["vvp", str(executable), f"+VECTORS={vectors}",
                         f"+METRICS={metrics_path}", f"+PERIOD_NS={period}"],
                        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout)
                    metrics = json.loads(metrics_path.read_text())
                    self.assertEqual(metrics["clock_period_ns"], period)
                    self.assertEqual(metrics["output_samples"], 2048)
                    self.assertEqual(metrics["active_cycles"], 147200)
                    self.assertEqual(metrics["latency_cycles"], 559)
                    self.assertEqual(metrics["block_cycles"], 575)
                    self.assertEqual(metrics["activity_start_ns"], 10 * period)
                    self.assertEqual(metrics["activity_duration_ns"], 147200 * period)
                    self.assertAlmostEqual(metrics["throughput_samples_per_second"],
                                           2048e9 / (147200 * period), places=6)

    def test_optimized_benchmark_and_export(self):
        config = target_settings("frequency_optimized")
        self.assertEqual(config["clock_period_ns"], 10)
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            executable = directory / "ppa.out"
            compiled = subprocess.run(
                ["iverilog", "-g2012", "-s", config["bench"], "-o", str(executable),
                 *config["sources"], config["bench_path"]], cwd=ROOT,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout)
            vectors = directory / "ppa_vectors.txt"
            vectors.write_text("2048\n" + "0 0 0 0\n" * 2048)
            metrics_path = directory / "local_metrics.json"
            for period in (10, 12.5):
                result = subprocess.run(
                    ["vvp", str(executable), f"+VECTORS={vectors}",
                     f"+METRICS={metrics_path}", f"+PERIOD_NS={period}"], cwd=ROOT,
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stdout)
                metrics = json.loads(metrics_path.read_text())
                self.assertEqual(metrics["clock_period_ns"], period)
                self.assertEqual(metrics["active_cycles"], 2074)
                self.assertEqual(metrics["latency_cycles"], 26)
                self.assertEqual(metrics["block_cycles"], 8)
                self.assertEqual(metrics["output_samples"], 2048)
                self.assertAlmostEqual(metrics["throughput_samples_per_second"], 2048e9/(2074*period), places=6)
                self.assertAlmostEqual(metrics["sustained_throughput_samples_per_second"], 1e9/period, places=6)
            # Package must select the optimized source set, clock and measured launch options.
            import zipfile
            manifest = {"config": config, "status": "local_pass", "commit": "abc1234",
                        "inputs_sha256": {name: sha256(ROOT/name) for name in config["sources"]},
                        "vectors_sha256": sha256(vectors)}
            (directory / "manifest.json").write_text(json.dumps(manifest))
            for name in ("resources.json", "summary.md", "diagnosis.txt"):
                (directory/name).write_text("{}")
            archive = package(directory)
            with zipfile.ZipFile(archive) as bundle:
                self.assertTrue(set(config["sources"]).issubset(bundle.namelist()))
                self.assertIn("constraints/clk_100mhz.xdc", bundle.namelist())
                self.assertIn("-Top fir_frequency_optimized", bundle.read("README.md").decode())
                self.assertIn("-LatencyCycles 26 -BlockCycles 8 -ActiveCycles 2074", bundle.read("README.md").decode())
            vectors.write_text("changed")
            with self.assertRaisesRegex(ValueError, "Vectores modificados"):
                package(directory)

    def test_top_only_and_separate_resources(self):
        flops = {"sky130_fd_sc_hd__dfxtp_1", "sky130_fd_sc_hd__sedfxtp_1"}
        stats = {"modules": {
            "\\" + TOP: {"area": 123.4, "num_cells_by_type": {
                "sky130_fd_sc_hd__dfxtp_1": 5, "sky130_fd_sc_hd__sedfxtp_1": 2,
                "sky130_fd_sc_hd__and2_1": 3, "$scopeinfo": 6,
            }},
            "\\sky130_fd_sc_hd__and2_1": {"num_cells_by_type": {"$and": 200}},
        }}
        result = resource_counts(stats, TOP, flops)
        self.assertEqual((result["cells"], result["flip_flops"], result["combinational_cells"]), (10, 7, 3))
        self.assertEqual(result["cell_area_um2"], 123.4)
        stats["modules"]["\\" + TOP]["num_cells_by_type"]["$mul"] = 1
        with self.assertRaisesRegex(ValueError, "sin mapear"):
            resource_counts(stats, TOP, flops)
        del stats["modules"]["\\" + TOP]["num_cells_by_type"]["$mul"]
        del stats["modules"]["\\" + TOP]["area"]
        with self.assertRaisesRegex(ValueError, "área"):
            resource_counts(stats, TOP, flops)

    def test_library_selection_and_sequential_cell_detection(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            suffix = f"sky130A/libs.ref/sky130_fd_sc_hd/lib/{LIBRARY}.lib"
            first = root / ".volare/volare/sky130/versions/v1" / suffix
            first.parent.mkdir(parents=True)
            first.write_text('cell ("sky130_fd_sc_hd__sedfxtp_1") { ff (IQ, IQ_N) {} }'
                             'cell (sky130_fd_sc_hd__and2_1) { pin (A) {} }')
            self.assertEqual(liberty_flops(first), {"sky130_fd_sc_hd__sedfxtp_1"})
            with patch("scripts.ppa.Path.home", return_value=root), patch.dict("os.environ", {}, clear=True):
                self.assertEqual(sky130_library(), first)
                second = root / ".volare/volare/sky130/versions/v2" / suffix
                second.parent.mkdir(parents=True)
                second.write_text(first.read_text())
                with self.assertRaisesRegex(ValueError, "única"):
                    sky130_library()
                self.assertEqual(sky130_library(str(first)), first)
                with patch.dict("os.environ", {"SKY130_LIB": str(second)}):
                    self.assertEqual(sky130_library(), second)
                    self.assertEqual(sky130_library(str(first)), first)
                with self.assertRaisesRegex(ValueError, "Se requiere"):
                    sky130_library(str(root / "missing.lib"))

    def test_record_run_replaces_only_its_section_even_for_equivalent_result(self):
        with TemporaryDirectory() as directory:
            report = Path(directory) / "frequency.md"
            prefix = "# PPA\n<!-- serial-runs:start -->"
            suffix = "<!-- serial-runs:end -->\nAnálisis optimizado.\nReferencia histórica Vivado.\n"
            report.write_text(prefix + "\nAnterior\n" + suffix)
            for run_id in ("first", "second"):
                record_run(run_id, f"# Corrida {run_id}\n\n## Medidas\nDatos {run_id}.", "same-key", report)
            result = report.read_text()
            self.assertNotIn("Datos first.", result)
            self.assertIn("Datos second.", result)
            self.assertTrue(result.startswith(prefix))
            self.assertTrue(result.endswith(suffix))
            self.assertIn("### Corrida second", result)
            for broken in ("Sin marcador", "<!-- serial-runs:end --><!-- serial-runs:start -->",
                           prefix + prefix + suffix):
                report.write_text(broken)
                with self.assertRaises(ValueError):
                    record_run("third", "new entry", "key", report)
                self.assertEqual(report.read_text(), broken)

    def test_optimized_run_preserves_serial_and_historical_reference(self):
        with TemporaryDirectory() as directory:
            report = Path(directory) / "frequency.md"
            prefix = "<!-- serial-runs:start -->Serial evidence\n<!-- serial-runs:end -->\nOptimized\n"
            original = prefix + "<!-- optimized-runs:start --><!-- optimized-runs:end -->\nVivado reference\n"
            report.write_text(original)
            record_run("new", "# Frecuencia optimizada\n\nResults", "key", report, architecture="optimized")
            document = report.read_text()
            self.assertTrue(document.startswith(prefix))
            self.assertTrue(document.endswith("\nVivado reference\n"))
            self.assertIn("<!-- optimized-measurement:key -->", document)
            self.assertLess(document.index("Optimized"), document.index("Results"))

    def test_measurement_identity_ignores_documentation_but_tracks_rtl_and_results(self):
        manifest = {"inputs_sha256": {"rtl/top.sv": "rtl-v1", "reports/ppa/frequency.md": "docs-v1"},
                    "config": {"clock_mhz": 10}, "tools": {"yosys": "0.52"},
                    "vectors_sha256": "vectors-v1", "library": {"sha256": "lib-v1"}}
        key = measurement_key(manifest, {"block_cycles": 575}, {"cells": 1507})
        manifest["inputs_sha256"]["reports/ppa/frequency.md"] = "docs-v2"
        self.assertEqual(key, measurement_key(manifest, {"block_cycles": 575}, {"cells": 1507}))
        self.assertNotEqual(key, measurement_key(manifest, {"block_cycles": 550}, {"cells": 1507}))
        manifest["library"]["sha256"] = "lib-v2"
        self.assertNotEqual(key, measurement_key(manifest, {"block_cycles": 575}, {"cells": 1507}))
        manifest["library"]["sha256"] = "lib-v1"
        manifest["inputs_sha256"]["rtl/top.sv"] = "rtl-v2"
        self.assertNotEqual(key, measurement_key(manifest, {"block_cycles": 575}, {"cells": 1507}))


if __name__ == "__main__":
    unittest.main()
