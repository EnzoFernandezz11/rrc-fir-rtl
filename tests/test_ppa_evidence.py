import json
from pathlib import Path
import tempfile
import unittest

from scripts.ppa import sha256, write_json
from scripts.ppa_evidence import publish_evidence, published_directory
from scripts.ppa_physical import CORNERS


class PpaEvidenceTest(unittest.TestCase):
    def test_publication_is_small_traceable_and_preserves_previous_on_failure(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            run = root / "run"
            run.mkdir()
            target = "frequency_serial"
            manifest = {"status": "physical_complete", "config": {"target": target}}
            write_json(run / "manifest.json", manifest)
            for name in ("local_metrics.json", "gate_metrics.json", "resources.json", "openlane-target.json"):
                write_json(run / name, {})
            state_dir = run / "runs/target/54-openroad-stapostpnr"
            state_dir.mkdir(parents=True)
            sdc = run / "resolved.sdc"
            sdc.write_text("create_clock -period 100 [get_ports clk]\n")
            write_json(state_dir / "state_out.json", {"sdc": str(sdc)})
            for corner in CORNERS:
                folder = state_dir / corner
                folder.mkdir()
                for name in ("checks.rpt", "clock.rpt", "ws.max.rpt", "ws.min.rpt",
                             "wns.max.rpt", "wns.min.rpt", "tns.max.rpt", "tns.min.rpt"):
                    (folder / name).write_text("STA report\n")
                (folder / "sta.log").write_text(
                    f"Reading design constraints file at '{sdc}'…\n%OL_CREATE_REPORT min.rpt\nlarge report\n")
                (folder / "design.sdf").write_text("excluded")
            scenario = run / "target"
            scenario.mkdir()
            for name in ("power.log", "benchmark.log"):
                (scenario / name).write_text("complete log\n")
            write_json(scenario / "metrics.json", {"passed": True})
            (scenario / "power.tcl").write_text(f"read_sdc {{{sdc}}}\n")
            (scenario / "raw.vcd").write_text("excluded")
            row = {"state": str(state_dir / "state_out.json"), "clock_period_ns": 100,
                   "timing": {corner: {} for corner in CORNERS}, "timing_pass": False}
            metrics = {"scenarios": {"target": row, "common": row}}
            write_json(run / "physical_metrics.json", metrics)
            reports = root / "reports"
            published = publish_evidence(run, reports)
            index = json.loads((published / "evidence.json").read_text())
            self.assertEqual(index["scenario_directories"], {"target": "target", "common": "target"})
            self.assertEqual(published_directory(run, target, reports), published)
            self.assertEqual((published / "target/power.sdc").read_bytes(), sdc.read_bytes())
            self.assertEqual((published / "target/power.log").read_bytes(), (scenario / "power.log").read_bytes())
            self.assertFalse(list(published.rglob("*.vcd")))
            self.assertFalse(list(published.rglob("*.sdf")))
            for name, digest in index["files_sha256"].items():
                self.assertEqual(sha256(published / name), digest)
            before = (published / "evidence.json").read_bytes()
            publish_evidence(run, reports)
            self.assertEqual((published / "evidence.json").read_bytes(), before)
            (state_dir / CORNERS[0] / "checks.rpt").unlink()
            with self.assertRaises(FileNotFoundError):
                publish_evidence(run, reports)
            self.assertEqual((published / "evidence.json").read_bytes(), before)
            manifest["status"] = "failed"
            write_json(run / "manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "completa"):
                publish_evidence(run, reports)
            self.assertEqual(published_directory(run, target, reports), run)
