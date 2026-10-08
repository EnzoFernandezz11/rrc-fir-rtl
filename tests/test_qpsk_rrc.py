"""A01: QPSK reproducible y coeficientes RRCOS."""

import unittest

import numpy as np

from model.qpsk_rrc import TAPS, impulse_response, qpsk, rrc, rrc_taps, sample_times, upsample


class QpskChecks(unittest.TestCase):
    def test_same_seed_same_symbols(self):
        np.testing.assert_array_equal(qpsk(64, seed=7), qpsk(64, seed=7))
        self.assertFalse(np.array_equal(qpsk(64, seed=7), qpsk(64, seed=8)))

    def test_symbols_are_plus_minus_one(self):
        s = qpsk(1000, seed=1)
        self.assertTrue(set(s.real) == set(s.imag) == {-1.0, 1.0})

    def test_upsample_inserts_zeros(self):
        np.testing.assert_array_equal(upsample(np.array([1 + 1j, -1 - 1j]), 2), [1 + 1j, 0, -1 - 1j, 0])


class RrcChecks(unittest.TestCase):
    def test_eight_symmetric_unit_energy_taps(self):
        h = rrc_taps()
        self.assertEqual(len(h), TAPS)
        np.testing.assert_allclose(h, h[::-1])
        self.assertAlmostEqual(float(np.sum(h**2)), 1.0)
        np.testing.assert_allclose(sample_times(), [-1.75, -1.25, -0.75, -0.25, 0.25, 0.75, 1.25, 1.75])

    def test_special_points_are_continuous(self):
        # t = 0 y t = ±1/(4α) usan fórmulas aparte; deben coincidir con el límite.
        for t in (0.0, 0.5, -0.5):
            np.testing.assert_allclose(rrc([t]), rrc([t + 1e-7]), rtol=1e-5)

    def test_impulse_response_is_taps(self):
        h = rrc_taps()
        ir = impulse_response(h, TAPS + 3)
        np.testing.assert_allclose(ir[:TAPS], h)
        np.testing.assert_array_equal(ir[TAPS:], 0)


if __name__ == "__main__":
    unittest.main()
