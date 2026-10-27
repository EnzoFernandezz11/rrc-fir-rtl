"""A07: tabla PPA SKY130 desde la evidencia versionada y anexo Vivado desde summary.tsv."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.ppa_table import COLUMNS, SKY130_COLUMNS, import_run, sky130_table, table

SUMMARY = """metric\tvalue
part\txc7a35tcpg236-1
clock_period_ns\t100
internal_wns_ns\t91.5
internal_whs_ns\t0.12
fmax_estimate_mhz\t117.647
lut\t412
ff\t388
dsp\t0
bram_tiles\t0
output_samples\t2048
latency_cycles\t559
throughput_samples_per_second\t139130.4
dynamic_power_w\t0.002
static_power_w\t0.072
energy_dynamic_nj_per_sample\t14.375
timing_status\tPASS
saif_review\t2696 / 4391 filas de redes con fuente SAIF (S); revisar
"""


CORNERS = [f"{rc}_{pvt}" for rc in ("nom", "min", "max")
           for pvt in ("tt_025C_1v80", "ss_100C_1v60", "ff_n40C_1v95")]


def write_sky130(root: Path, name: str, period: float, ss_setup: float, fmax: float | None) -> None:
    run = root / name / "sky130"
    run.mkdir(parents=True)
    timing = {c: {"setup_ws_ns": ss_setup if "ss" in c else 3.0, "hold_ws_ns": 0.1,
                  "setup_violations": int(ss_setup < 0 and "ss" in c), "hold_violations": 0,
                  "max_slew_violations": 0, "max_cap_violations": 0,
                  "max_fanout_violations": 2 if c == "max_ss_100C_1v60" else 0,
                  "fmax_estimate_mhz": fmax and (fmax if "ss" in c else 2 * fmax)} for c in CORNERS}
    power = {"total_w": 0.0634, "total_energy_j": 6.43e-10}
    scenario = {"clock_period_ns": period, "timing": timing, "power": power}
    (run / "physical_metrics.json").write_text(json.dumps({
        "areas": {"final_cell_area_um2": 541302, "core_area_um2": 1432473.9},
        "scenarios": {"target": scenario, "common": {
            **scenario, "clock_period_ns": 100,
            "timing": {c: {**t, "setup_ws_ns": 50.0, "setup_violations": 0} for c, t in timing.items()}}}}))
    (run / "local_metrics.json").write_text(json.dumps(
        {"clock_period_ns": period, "latency_cycles": 26, "throughput_samples_per_second": 98746383.8}))
    (run / "manifest.json").write_text(json.dumps({"commit": "22dd3d09" + "0" * 32}))
    (run / "evidence.json").write_text(json.dumps({"scenario_directories": {"target": "target", "common": "target"}}))
    for c in CORNERS:
        (run / "sta/target" / c).mkdir(parents=True)
        (run / "sta/target" / c / "clock.rpt").write_text(
            f"clk period_min = 17.11 fmax = {58.45 if 'ss' in c else 99.0}\n")


class PpaTableTest(unittest.TestCase):
    def test_sky130_verdicts_from_nine_corners(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write_sky130(root, "frequency_optimized", 10, -3.28, 75.3)
            write_sky130(root, "frequency_serial", 100, 56.1, None)  # Fmax solo en clock.rpt
            lines = sky130_table({"time": 44.25, "frequency": 42.96}, {"frequency_optimized"}, root).splitlines()

        self.assertEqual(lines[0], "| " + " | ".join(SKY130_COLUMNS) + " |")
        rows = {line.split(" | ")[0].lstrip("| "): line for line in lines[2:]}
        fast, common = rows["frequency_optimized @ 100 MHz"], rows["frequency_optimized @ 10 MHz"]
        for expected in ("43.0 dB", "541 302 / 1 432 474 µm²", "FAIL: setup -3.28 ns (nom_ss_100C_1v60)",
                         "hold +0.10 ns", "FAIL: slew 0 / cap 0 / fanout 2", "75.3 MHz (nom_ss_100C_1v60)",
                         "26 ciclos (260 ns)", "98.75 Mmuestras/s (condicionado: setup/hold FAIL)",
                         "63.4 mW / 0.643 nJ/muestra", "`22dd3d09`",
                         "(frequency_optimized/sky130/evidence.json)"):
            self.assertIn(expected, fast)
        self.assertIn("26 ciclos (2600 ns)", common)
        self.assertIn("9.875 Mmuestras/s |", common)
        serial = rows["frequency_serial @ 10 MHz"]
        self.assertIn("PASS: setup +3.00 ns (nom_tt_025C_1v80)", serial)
        self.assertIn("58.5 MHz", serial)
        self.assertIn("| — |", serial)  # sin RTL registrado no hay SQNR
        self.assertEqual(rows["time_serial @ objetivo"].count("no medida"), 7)

    def test_sky130_rejects_inconsistent_verdict(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            write_sky130(root, "time_serial", 100, 50.0, 124.5)
            path = root / "time_serial/sky130/physical_metrics.json"
            data = json.loads(path.read_text())
            data["scenarios"]["target"]["setup_hold_pass"] = False
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "setup_hold_pass"):
                sky130_table({"time": 44.25, "frequency": 42.96}, set(), root)

    def test_measured_and_missing_variants(self):
        with TemporaryDirectory() as directory:
            run = Path(directory) / "frequency_serial" / "10mhz"
            run.mkdir(parents=True)
            (run / "summary.tsv").write_text(SUMMARY, encoding="utf-8")
            (run / "tool_versions.txt").write_text("Vivado v2023.2 (64-bit)\n", encoding="utf-8")
            (run / "source_manifest.json").write_text(json.dumps({"commit": "da7a05f2" + "0" * 32}))
            lines = table({"time": 44.25, "frequency": 42.96}, {"frequency_serial", "time_serial"}, Path(directory)).splitlines()

        self.assertEqual(lines[0], "| " + " | ".join(COLUMNS) + " |")
        rows = {line.split(" | ")[0].lstrip("| "): line for line in lines[2:]}
        self.assertEqual(len(rows), 6)
        freq = rows["frequency_serial @ 10 MHz"]
        for expected in ("`da7a05f2`", "10 MHz, timing PASS", "43.0 dB", "412 LUT / 388 FF / 0 DSP / 0 BRAM",
                         "117.6 MHz (WNS 91.500 ns)", "559 ciclos", "0.1391 Mmuestras/s",
                         "14.4 nJ/muestra", "SAIF 2696 / 4391 redes", "Vivado v2023.2",
                         "(frequency_serial/10mhz/)"):
            self.assertIn(expected, freq)
        self.assertEqual(rows["frequency_serial @ 100 MHz"].count("no medida"), 5)
        self.assertIn("44.2 dB", rows["time_serial @ 10 MHz"])
        self.assertEqual(rows["time_serial @ 10 MHz"].count("no medida"), 5)
        self.assertIn("| — |", rows["time_optimized @ 100 MHz"])  # sin RTL registrado no hay SQNR

    def test_zero_dynamic_power_is_a_bound(self):
        with TemporaryDirectory() as directory:
            run = Path(directory) / "time_serial" / "10mhz"
            run.mkdir(parents=True)
            (run / "summary.tsv").write_text(SUMMARY.replace("dynamic_power_w\t0.002", "dynamic_power_w\t0.000")
                                             .replace("throughput_samples_per_second\t139130.4",
                                                      "throughput_samples_per_second\t1000000"))
            (run / "tool_versions.txt").write_text("Vivado v2024.2 (64-bit)\n", encoding="utf-8")
            text = table({"time": 44.25, "frequency": 42.96}, set(), Path(directory))
        self.assertIn("< 0.5 nJ/muestra", text)

    def test_import_run(self):
        with TemporaryDirectory() as directory:
            src, dest = Path(directory) / "corrida", Path(directory) / "reports"
            src.mkdir()
            (src / "summary.tsv").write_text(SUMMARY.replace("clock_period_ns\t100", "clock_period_ns\t10"))
            (src / "configuration.txt").write_text("vectors=/pc/pkg/vectors/v.txt\nsource_root=/pc/pkg\n")
            (src / "big.dcp").write_text("x")
            (src / "run_status.txt").write_text("FAILED\n")
            with self.assertRaises(ValueError):
                import_run(src, "frequency_serial", dest)
            (src / "run_status.txt").write_text("SIMULATION_PASS TIMING_PASS POWER_SAIF_REVIEW_REQUIRED\n")
            run = import_run(src, "frequency_serial", dest)

            self.assertEqual(run, dest / "frequency_serial" / "100mhz")
            self.assertFalse((run / "big.dcp").exists())
            self.assertEqual((run / "configuration.txt").read_text(),
                             "vectors=vectors/v.txt\nsource_root=<paquete>\n")


if __name__ == "__main__":
    unittest.main()
