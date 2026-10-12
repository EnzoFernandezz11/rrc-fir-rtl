"""A03: correspondencia entre el FIR temporal (A02) y el de frecuencia (E01).

Ambos modelos reciben las mismas muestras y la tabla RRC de E02; la diferencia
esperada es solo redondeo flotante. `python3 -m tests.test_a03_time_vs_frequency`
imprime el error máximo por caso como evidencia; la tolerancia de punto fijo
la fija A04.
"""

import unittest

import numpy as np

from model.fir_time import cases, fir_time
from model.frequency import HOP, N, frequency_filter
from model.qpsk_rrc import qpsk, rrc_taps, upsample

TOL = 1e-12


def max_error(x: np.ndarray, h: np.ndarray) -> float:
    y_time = fir_time(x, h)
    y_freq = np.asarray(frequency_filter(x, h), dtype=complex)
    assert len(y_freq) == len(y_time) == len(x)
    return float(np.abs(y_freq - y_time).max(initial=0.0))


def evidence(h: np.ndarray) -> dict[str, float]:
    """Casos del contrato: A02, varias semillas, todos los bordes y trama larga."""
    rows = {name: max_error(x, h) for name, x in cases(seed=1, symbols=32).items()}
    for seed in (0, 17, 42, 1234):
        rows[f"qpsk_s{seed}_256sym"] = max_error(upsample(qpsk(256, seed)), h)
    x = upsample(qpsk(20, 7))
    # 0…40 cubre trama vacía, bloques parciales y fronteras en 8, 16, 24, 32 y 40.
    rows["largos_0..40"] = max(max_error(x[:n], h) for n in range(len(x) + 1))
    # Un impulso en i reaparece en i…i+7: cruza la frontera desde cada posición.
    rows["impulso_en_0..23"] = max(max_error(np.eye(3 * HOP)[i].astype(complex), h) for i in range(3 * HOP))
    return rows


class TimeVsFrequency(unittest.TestCase):
    def test_every_case_matches_within_float_rounding(self):
        for name, err in evidence(rrc_taps()).items():
            with self.subTest(name):
                self.assertLess(err, TOL)

    def test_block_size_matches_contract(self):
        self.assertEqual((N, HOP), (16, 8))


if __name__ == "__main__":
    h = rrc_taps()
    print(f"{'caso':<22} error máx |y_freq - y_time|")
    for name, err in evidence(h).items():
        print(f"{name:<22} {err:.3e}")
