"""Comprueba que la CI no omita variantes registradas por error."""

import copy
import unittest

from scripts.validate_project import ROOT, load_project, validate_project, validate_targets


class ScaffoldChecks(unittest.TestCase):
    def test_formal_requirements_are_preserved(self):
        project = load_project()
        self.assertEqual(project["confirmed"]["coefficient_count"], 8)
        changed = copy.deepcopy(project)
        changed["confirmed"]["coefficient_count"] = 7
        with self.assertRaises(ValueError):
            validate_project(changed)

    def test_missing_registered_rtl_fails_validation(self):
        manifest = {
            "schema_version": 1,
            "targets": [{
                "name": "time_serial",
                "domain": "time",
                "architecture": "serial",
                "rtl_top": "fir_time_serial",
                "testbench_top": "tb_fir_time_serial",
                "sources": ["rtl/time/missing.sv"],
                "testbench": "tb/time/missing.sv",
            }],
        }
        with self.assertRaises(ValueError):
            validate_targets(manifest, ROOT)

    def test_duplicate_target_names_fail(self):
        manifest = {
            "schema_version": 1,
            "targets": [
                {
                    "name": "same", "domain": "time", "architecture": "serial",
                    "rtl_top": "example", "testbench_top": "tb_example",
                    "sources": ["scripts/ci.py"], "testbench": "scripts/ci.py",
                },
                {"name": "same", "domain": "time", "architecture": "serial"},
            ],
        }
        with self.assertRaisesRegex(ValueError, "duplicado"):
            validate_targets(manifest, ROOT)


if __name__ == "__main__":
    unittest.main()
