"""Ejercita el lector A05 real del testbench con archivos temporales."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.validate_project import ROOT


class FrequencyVectorChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        cls.directory = Path(directory.name)
        cls.executable = cls.directory / "frequency.out"
        targets = json.loads((ROOT / "config/rtl_targets.json").read_text())["targets"]
        target = next(t for t in targets if t["name"] == "frequency_serial")
        compiled = subprocess.run(
            ["iverilog", "-g2012", "-s", target["testbench_top"], "-o", str(cls.executable),
             *target["sources"], target["testbench"]],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
        )
        if compiled.returncode:
            raise RuntimeError(compiled.stdout)

    def simulate(self, path):
        return subprocess.run(
            ["vvp", str(self.executable), f"+a05_file={path}"],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
        )

    def test_official_frames_with_and_without_pauses(self):
        result = self.simulate(ROOT / "vectors/bordes.txt")
        self.assertEqual(result.returncode, 0, result.stdout)
        for pauses in (0, 1):
            self.assertIn(f"202 muestras, 19 tramas, pausas={pauses}", result.stdout)

    def test_frequency_column_is_exact(self):
        path = self.directory / "columnas.txt"
        # En cero, yt deliberadamente distinto no debe afectar la comparación de yf.
        path.write_text("0 1 0 0 1 -1 0 0\n")
        result = self.simulate(path)
        self.assertEqual(result.returncode, 0, result.stdout)
        path.write_text("0 1 0 0 0 0 1 0\n")
        result = self.simulate(path)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("esperado (1,0), obtenido (0,0)", result.stdout)
        self.assertIn(str(path), result.stdout)

    def test_invalid_files_fail_with_location(self):
        cases = {
            "vacio": ("", "archivo vacio", 0),
            "incompleto": ("0 1 0 0 0 0 0\n", "ocho columnas", 0),
            "fila_partida": ("0 1 0 0\n0 0 0 0\n", "ocho columnas", 0),
            "extra": ("0 1 0 0 0 0 0 0 extra\n", "ocho columnas", 0),
            "indice": ("1 1 0 0 0 0 0 0\n", "indice discontinuo", 0),
            "entrada": ("0 1 -2 0 0 0 0 0\n", "fuera de rango", 0),
            "salida": ("0 1 0 0 0 0 256 0\n", "fuera de rango", 0),
            "last": ("0 2 0 0 0 0 0 0\n", "fuera de rango", 0),
            "desconocido": ("0 1 x 0 0 0 0 0\n", "valor desconocido", 0),
            "sin_last": ("0 0 0 0 0 0 0 0\n", "trama sin last", 0),
            "trama_larga": ("".join(f"{n} 0 0 0 0 0 0 0\n" for n in range(2049)),
                            "trama supera 2048", 2048),
        }
        for name, (content, message, index) in cases.items():
            with self.subTest(name=name):
                path = self.directory / f"{name}.txt"
                path.write_text(content)
                result = self.simulate(path)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(message, result.stdout)
                self.assertIn(f"A05 {path} indice {index}", result.stdout)
        path = self.directory / "ausente.txt"
        result = self.simulate(path)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(f"A05 {path} indice 0: no se pudo abrir", result.stdout)


if __name__ == "__main__":
    unittest.main()
