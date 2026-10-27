"""Flujo SKY130 temporal: targets, throughput por muestra y publicación de corridas."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.ppa_time import (LIBRARY, REPORT, ROOT, evidence_dir, evidence_links, publish_evidence,
                              record_run, sha256, sustained_sps, target_settings)
from scripts.ppa_time_compare import comparison_document, load_run
from scripts.ppa_time_physical import split_vcd, write_power_sdc


class PpaTimeTest(unittest.TestCase):
    def test_targets_use_time_benches_and_own_clocks(self):
        serial, optimized = target_settings("time_serial"), target_settings("time_optimized")
        self.assertEqual((serial["top"], serial["bench"], serial["clock_period_ns"]),
                         ("fir_time_serial", "tb_fir_time_ppa", 100))
        self.assertEqual((optimized["top"], optimized["bench"], optimized["clock_period_ns"]),
                         ("fir_time_systolic", "tb_fir_time_systolic_ppa", 10))
        for config in (serial, optimized):
            self.assertTrue(Path(config["bench_path"]).is_file())
            self.assertTrue(all(Path(source).is_file() for source in config["sources"]))
        with self.assertRaisesRegex(ValueError, "no soportado"):
            target_settings("frequency_serial")

    def test_sustained_throughput_is_per_sample(self):
        # B02: II = 10 a 10 MHz; B04: II = 1 a 100 MHz.
        self.assertAlmostEqual(sustained_sps(10, 100), 1e6)
        self.assertAlmostEqual(sustained_sps(1, 10), 1e8)

    def test_report_has_markers_for_both_variants(self):
        text = REPORT.read_text(encoding="utf-8")
        for marker in ("serial-runs", "optimized-runs", "comparison"):
            self.assertEqual(text.count(f"<!-- {marker}:start -->"), 1)
            self.assertEqual(text.count(f"<!-- {marker}:end -->"), 1)

    def test_new_run_replaces_previous_and_invalidates_comparison(self):
        with tempfile.TemporaryDirectory() as raw:
            report = Path(raw) / "report.md"
            report.write_text("<!-- serial-runs:start -->old<!-- serial-runs:end -->\n"
                              "<!-- optimized-runs:start -->b04<!-- optimized-runs:end -->\n"
                              "<!-- comparison:start -->old graph<!-- comparison:end -->\nFIN")
            record_run("new", "# New", "hash", report)
            text = report.read_text()
            # Los títulos de la corrida bajan dos niveles para quedar dentro de su sección.
            self.assertIn("<!-- serial-measurement:hash -->\n### New", text)
            self.assertNotIn("old", text.split("<!-- serial-runs:end -->")[0])
            self.assertIn("b04", text)
            self.assertIn("pendiente de regenerar", text)
            self.assertTrue(text.endswith("FIN"))
            with self.assertRaisesRegex(ValueError, "marcadores"):
                record_run("new", "# New", "hash", report, architecture="missing")

    def test_published_evidence_is_light_and_replaces_previous_copy(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            run_dir, report = root / "build/run-1", root / "reports/ppa/time.md"
            sta = run_dir / "runs/target/54-openroad-stapostpnr/nom_tt_025C_1v80"
            sta.mkdir(parents=True)
            for name in ("manifest.json", "physical_metrics.json", "target/metrics.json",
                         "target/power.sdc", "target/raw.vcd", "mapped.v"):
                (run_dir / name).parent.mkdir(parents=True, exist_ok=True)
                (run_dir / name).write_text(name)
            for name in ("checks.rpt", "clock.rpt", "max.rpt", "sta.log"):
                (sta / name).write_text(name)
            stale = root / "reports/ppa/time_optimized/sky130/old.json"
            stale.parent.mkdir(parents=True)
            stale.write_text("anterior")
            published = publish_evidence(run_dir, "time_optimized", report)
            self.assertEqual(published, evidence_dir("time_optimized", report))
            copied = json.loads((published / "evidence.json").read_text())
            self.assertEqual(copied["run"], "run-1")
            self.assertEqual(sorted(copied["sha256"]), [
                "manifest.json", "physical_metrics.json",
                "runs/target/54-openroad-stapostpnr/nom_tt_025C_1v80/checks.rpt",
                "runs/target/54-openroad-stapostpnr/nom_tt_025C_1v80/clock.rpt",
                "target/metrics.json", "target/power.sdc"])
            self.assertFalse(stale.exists())
            # Los enlaces sólo nombran archivos presentes en la copia.
            links = evidence_links(published, report.parent, (("Manifiesto", "manifest.json"),
                                                              ("Netlist", "mapped.v")))
            self.assertEqual(links, "- [Manifiesto](time_optimized/sky130/manifest.json).\n")

    def test_power_sdc_only_changes_clock_period(self):
        # La potencia del escenario común reutiliza el SDC del layout objetivo.
        with tempfile.TemporaryDirectory() as raw:
            source, output = Path(raw) / "target.sdc", Path(raw) / "power.sdc"
            source.write_text("create_clock -name clk -period 10.0000 [get_ports {clk}]\n"
                              "set_input_delay 2.0000 -clock [get_clocks {clk}] [get_ports {rst}]\n")
            write_power_sdc(source, output, 100)
            self.assertEqual(output.read_text(),
                             "create_clock -name clk -period 100.0000 [get_ports {clk}]\n"
                             "set_input_delay 2.0000 -clock [get_clocks {clk}] [get_ports {rst}]\n")

    def test_comparison_uses_per_sample_throughput_and_time_labels(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            runs = []
            for target, block_cycles in (("time_serial", 10), ("time_optimized", 1)):
                directory = root / target
                directory.mkdir()
                (directory / "ppa_vectors.txt").write_text("benchmark")
                (directory / f"{LIBRARY}.lib").write_text("liberty")
                metrics = {"passed": True, "input_samples": 2048, "output_samples": 2048,
                           "clock_period_ns": 100, "latency_cycles": 3, "block_cycles": block_cycles,
                           "active_cycles": 2048 * block_cycles, "throughput_samples_per_second": 1e6}
                for name in ("local_metrics.json", "gate_metrics.json"):
                    (directory / name).write_text(json.dumps(metrics))
                (directory / "resources.json").write_text(json.dumps(
                    {"cells": 10, "flip_flops": 4, "combinational_cells": 6, "cell_area_um2": 10}))
                (directory / "manifest.json").write_text(json.dumps({
                    "status": "local_pass", "config": {"target": target}, "tools": {},
                    "library": {"name": LIBRARY, "sha256": sha256(directory / f"{LIBRARY}.lib")},
                    "vectors_sha256": sha256(directory / "ppa_vectors.txt")}))
                runs.append(load_run(directory, target))
            self.assertEqual([r["values"]["sustained_sps"] for r in runs], [1e6, 1e7])
            text, data = comparison_document(*runs, root)
            self.assertIn("## Comparación B02 / B04", text)
            self.assertIn("| Throughput sostenido | muestras/s | 1000000 | 1e+07 | 900 % |", text)
            self.assertEqual(set(data["values"]), {"B02", "B04"})

    def test_full_activity_benchmark_reaches_last_sample_for_both_targets(self):
        # Con entrada nula la salida esperada es cero: alcanza para recorrer las 2048 muestras.
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            vectors = directory / "vectors.txt"
            vectors.write_text("2048\n" + "0 0 0 0\n" * 2048)
            for target in ("time_serial", "time_optimized"):
                cfg = target_settings(target)
                executable, vcd, metrics = (directory / n for n in ("sim.out", "activity.vcd", "metrics.json"))
                subprocess.run(["iverilog", "-g2012", "-s", cfg["bench"], "-o", str(executable),
                                *cfg["sources"], cfg["bench_path"]], cwd=ROOT, check=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(["vvp", str(executable), f"+VECTORS={vectors}", f"+POWER_VCD={vcd}",
                                f"+METRICS={metrics}", f"+PERIOD_NS={cfg['clock_period_ns']}"],
                               cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=30)
                m = json.loads(metrics.read_text())
                parts = directory / f"{target}-parts"
                parts.mkdir()
                meta = split_vcd(vcd, parts, m["activity_start_ns"], m["activity_duration_ns"],
                                 cfg["bench"] + "/dut", segments=8,
                                 clock_period_ns=cfg["clock_period_ns"])
                self.assertEqual(m["output_samples"], 2048)
                self.assertEqual(len(meta["segments"]), 8)
                self.assertEqual(sum(s["duration_ns"] for s in meta["segments"]),
                                 m["active_cycles"] * cfg["clock_period_ns"])
                self.assertTrue(all(s["sha256"] == sha256(s["path"]) for s in meta["segments"]))


if __name__ == "__main__":
    unittest.main()
