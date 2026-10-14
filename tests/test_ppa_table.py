"""A07: la tabla PPA lee summary.tsv del flujo Vivado y marca lo no medido."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.ppa_table import COLUMNS, table

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
saif_review\tREVISAR
"""


class PpaTableTest(unittest.TestCase):
    def test_measured_and_missing_variants(self):
        with TemporaryDirectory() as directory:
            run = Path(directory) / "frequency_serial"
            run.mkdir()
            (run / "summary.tsv").write_text(SUMMARY, encoding="utf-8")
            (run / "tool_versions.txt").write_text("Vivado v2023.2 (64-bit)\n", encoding="utf-8")
            (run / "source_manifest.json").write_text(json.dumps({"commit": "da7a05f2" + "0" * 32}))
            lines = table({"time": 44.25, "frequency": 42.96}, {"frequency_serial", "time_serial"}, Path(directory)).splitlines()

        self.assertEqual(lines[0], "| " + " | ".join(COLUMNS) + " |")
        rows = {line.split(" | ")[0].lstrip("| "): line for line in lines[2:]}
        self.assertEqual(len(rows), 4)
        freq = rows["frequency_serial"]
        for expected in ("`da7a05f2`", "10 MHz, timing PASS", "43.0 dB", "412 LUT / 388 FF / 0 DSP / 0 BRAM",
                         "117.6 MHz (WNS 91.500 ns)", "559 ciclos", "0.1391 Mmuestras/s",
                         "14.4 nJ/muestra", "Vivado v2023.2"):
            self.assertIn(expected, freq)
        self.assertIn("44.2 dB", rows["time_serial"])
        self.assertEqual(rows["time_serial"].count("no medida"), 5)
        self.assertIn("| — |", rows["time_optimized"])  # sin RTL registrado no hay SQNR


if __name__ == "__main__":
    unittest.main()
