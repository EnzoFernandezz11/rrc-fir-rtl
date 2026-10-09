"""A02: modelo flotante temporal."""

import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np

from model.fir_time import cases, export, fir_time
from model.qpsk_rrc import rrc_taps


def direct_sum(x, h):
    """Referencia independiente: la ecuación del contrato, término a término."""
    return [sum(h[k] * x[n - k] for k in range(len(h)) if n - k >= 0) for n in range(len(x))]


class FirTimeChecks(unittest.TestCase):
    def setUp(self):
        self.h = rrc_taps()
        self.cases = cases(seed=1, symbols=32)

    def test_impulse_returns_taps(self):
        y = fir_time(self.cases["impulso"], self.h)
        np.testing.assert_allclose(y[:8], self.h)
        np.testing.assert_array_equal(y[8:], 0)

    def test_zeros_return_zeros(self):
        np.testing.assert_array_equal(fir_time(self.cases["ceros"], self.h), 0)

    def test_qpsk_matches_direct_sum(self):
        x = self.cases["qpsk_s1"]
        y = fir_time(x, self.h)
        self.assertEqual(len(y), len(x))
        np.testing.assert_allclose(y, direct_sum(x, self.h), atol=1e-15)

    def test_real_taps_keep_i_and_q_separate(self):
        x = self.cases["qpsk_s1"]
        y = fir_time(x, self.h)
        np.testing.assert_allclose(y.real, fir_time(x.real, self.h).real, atol=1e-15)
        np.testing.assert_allclose(y.imag, fir_time(x.imag, self.h).real, atol=1e-15)

    def test_peak_within_sum_of_abs_taps(self):
        y = fir_time(self.cases["qpsk_s1"], self.h)
        bound = np.abs(self.h).sum() + 1e-12
        self.assertLessEqual(np.abs(y.real).max(), bound)
        self.assertLessEqual(np.abs(y.imag).max(), bound)

    def test_export_round_trips_with_indices(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = export(Path(tmp), seed=1, symbols=4)
            self.assertEqual([p.name for p in paths], ["impulso.csv", "ceros.csv", "qpsk_s1.csv"])
            with paths[2].open(newline="") as f:
                rows = list(csv.DictReader(f))
        x = cases(seed=1, symbols=4)["qpsk_s1"]
        y = fir_time(x, self.h)
        self.assertEqual([int(r["n"]) for r in rows], list(range(len(x))))
        np.testing.assert_array_equal([complex(float(r["y_i"]), float(r["y_q"])) for r in rows], y)


if __name__ == "__main__":
    unittest.main()
