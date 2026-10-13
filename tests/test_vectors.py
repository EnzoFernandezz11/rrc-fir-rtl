"""A05: los vectores de vectors/ están al día y respetan el formato."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from model.fir_time import fir_time
from model.fixed_point import Format, sqnr_db, widths
from model.qpsk_rrc import rrc_taps
from model.vectors import OUT, cases, read, regression, render


class VectorChecks(unittest.TestCase):
    def test_files_match_generator(self):
        expected = {f"{name}.txt": render(frames) for name, frames in cases().items()}
        self.assertEqual(sorted(p.name for p in OUT.glob("*.txt")), sorted(expected))
        for name, text in expected.items():
            with self.subTest(name):
                self.assertEqual((OUT / name).read_text(encoding="utf-8"), text,
                                 "vectores desactualizados: correr python3 -m model.vectors")

    def test_format_ranges_and_frames(self):
        bits = widths(Format())["salida"][0]
        lim = 1 << (bits - 1)
        for path in OUT.glob("*.txt"):
            with self.subTest(path.name):
                d = read(path)
                np.testing.assert_array_equal(d["n"], np.arange(len(d["n"])))
                self.assertEqual(d["last"][-1], 1)
                self.assertTrue(set(np.r_[d["x_i"], d["x_q"]]) <= {-1, 0, 1})
                y = np.r_[d["yt_i"], d["yt_q"], d["yf_i"], d["yf_q"]]
                self.assertTrue(-lim <= y.min() and y.max() < lim)
                self.assertLessEqual(np.abs(np.r_[d["yt_i"] - d["yf_i"], d["yt_q"] - d["yf_q"]]).max(), 2)

    def test_qpsk_vector_meets_sqnr(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "qpsk.txt"
            path.write_text(render(next(iter(regression().values()))), encoding="utf-8")
            d = read(path)
        ref = fir_time(d["x_i"] + 1j * d["x_q"], rrc_taps())
        scale = 2 ** Format().out
        self.assertGreaterEqual(sqnr_db((d["yt_i"] + 1j * d["yt_q"]) / scale, ref), 40)
        self.assertGreaterEqual(sqnr_db((d["yf_i"] + 1j * d["yf_q"]) / scale, ref), 40)


if __name__ == "__main__":
    unittest.main()
