"""El conteo XC7 no debe incluir las celdas internas de la biblioteca Yosys."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.ppa import TOP, measurement_key, record_run, resource_counts


class PpaResourcesTest(unittest.TestCase):
    def test_top_only_and_separate_resources(self):
        stats = {"modules": {
            "\\" + TOP: {"num_cells_by_type": {
                "LUT2": 3, "LUT6": 4, "FDRE": 5, "FDSE": 2,
                "DSP48E1": 1, "RAMB18E1": 2, "CARRY4": 9, "MUXF7": 7,
                "$scopeinfo": 6,
            }},
            "\\LUT6": {"num_cells_by_type": {"$lut": 200}},
        }}
        result = resource_counts(stats)
        self.assertEqual((result["LUT"], result["FF"], result["DSP48E1"]), (7, 7, 1))
        self.assertEqual((result["RAMB18E1"], result["RAMB36E1"]), (2, 0))
        self.assertEqual((result["CARRY4"], result["MUXF7"], result["MUXF8"]), (9, 7, 0))
        stats["modules"]["\\" + TOP]["num_cells_by_type"]["$mul"] = 1
        with self.assertRaisesRegex(ValueError, "sin mapear"):
            resource_counts(stats)

    def test_record_runs_preserves_history_and_optimized_analysis(self):
        with TemporaryDirectory() as directory:
            report = Path(directory) / "frequency.md"
            original = "# PPA\n\n## Corridas seriales\n\n<!-- serial-runs:end -->\n\n## Frecuencia optimizada\n\nAnálisis a conservar.\n"
            report.write_text(original, encoding="utf-8")
            for run_id in ("first", "second"):
                record_run(run_id, f"# Frecuencia serial — corrida `{run_id}` (local)\n\n## Medidas\n\nDatos {run_id}.\n", run_id, report)
            result = report.read_text(encoding="utf-8")
            self.assertIn("Datos first.", result)
            self.assertIn("Datos second.", result)
            self.assertIn("## Frecuencia optimizada\n\nAnálisis a conservar.", result)
            self.assertLess(result.index("Datos second."), result.index("## Frecuencia optimizada"))
            with self.assertRaisesRegex(ValueError, "ya está registrada"):
                record_run("first", "duplicate", "different-key", report)
            self.assertEqual(report.read_text(encoding="utf-8"), result)
            record_run("repeat", "Ejecución equivalente", "first", report)
            self.assertEqual(report.read_text(encoding="utf-8"), result)
            report.write_text("Historial sin marcador", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "marcador"):
                record_run("third", "new entry", "third", report)
            self.assertEqual(report.read_text(encoding="utf-8"), "Historial sin marcador")

    def test_measurement_identity_ignores_documentation_but_tracks_rtl_and_results(self):
        manifest = {"inputs_sha256": {"rtl/top.sv": "rtl-v1", "reports/ppa/frequency.md": "docs-v1"},
                    "config": {"clock_mhz": 10}, "tools": {"yosys": "0.52"},
                    "vectors_sha256": "vectors-v1"}
        key = measurement_key(manifest, {"block_cycles": 575}, {"LUT": 1507})
        manifest["inputs_sha256"]["reports/ppa/frequency.md"] = "docs-v2"
        self.assertEqual(key, measurement_key(manifest, {"block_cycles": 575}, {"LUT": 1507}))
        self.assertNotEqual(key, measurement_key(manifest, {"block_cycles": 550}, {"LUT": 1507}))
        manifest["inputs_sha256"]["rtl/top.sv"] = "rtl-v2"
        self.assertNotEqual(key, measurement_key(manifest, {"block_cycles": 575}, {"LUT": 1507}))


if __name__ == "__main__":
    unittest.main()
