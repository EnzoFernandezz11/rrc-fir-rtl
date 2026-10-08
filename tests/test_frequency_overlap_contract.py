"""Comprueba la reconstrucción por FFT con 50 % de solapamiento de E01.

La referencia es la convolución directa. Los símbolos y la tabla RRC salen de
`model/qpsk_rrc.py` (A01/E02); el resto de los coeficientes son ejemplos.
"""

import unittest

from model.frequency import frequency_filter
from model.qpsk_rrc import qpsk, rrc_taps, upsample


def generate_qpsk(symbol_count, *, seed=0):
    return qpsk(symbol_count, seed).tolist()


def interpolate_2x(symbols):
    return upsample(symbols).tolist()


def direct_filter(signal, taps):
    """Ecuación causal independiente de la DFT y de los límites de bloque."""
    return [
        sum(tap * signal[n - k] for k, tap in enumerate(taps) if n >= k)
        for n in range(len(signal))
    ]


class FrequencyOverlapContractTest(unittest.TestCase):
    def assert_matches_direct(self, signal, taps):
        actual = frequency_filter(signal, taps)
        expected = direct_filter(signal, taps)
        self.assertEqual(len(actual), len(signal))
        for index, (got, want) in enumerate(zip(actual, expected)):
            self.assertLess(abs(got - want), 1e-10, f"muestra {index}")

    def test_rrc_with_qpsk_2x_full_partial_and_empty_frames(self):
        taps = rrc_taps().tolist()
        for seed in (0, 17, 42):
            for symbol_count in (0, 1, 2, 3, 4, 5, 7, 8, 9, 17, 25):
                with self.subTest(seed=seed, symbols=symbol_count):
                    symbols = generate_qpsk(symbol_count, seed=seed)
                    signal = interpolate_2x(symbols)
                    self.assertEqual(len(signal), 2 * symbol_count)
                    self.assert_matches_direct(signal, taps)

    def test_asymmetric_taps_and_all_partial_lengths(self):
        taps = [
            0.25 + 0.125j, -0.125 + 0.0625j, 0.5, 0.125 - 0.25j,
            -0.0625, 0.125j, 0.0625 - 0.125j, -0.125,
        ]
        qpsk = generate_qpsk(25, seed=17)
        for length in range(26):
            with self.subTest(length=length):
                self.assert_matches_direct(qpsk[:length], taps)

    def test_impulses_on_both_sides_of_block_boundary(self):
        taps = [complex(k + 1, -k / 8) for k in range(8)]
        for impulse_index in (0, 7, 8, 15, 16):
            signal = [0j] * 25
            signal[impulse_index] = 1 + 1j
            with self.subTest(impulse_index=impulse_index):
                self.assert_matches_direct(signal, taps)

    def test_last_tap_delay_preserves_indices_and_truncates_tail(self):
        signal = interpolate_2x(generate_qpsk(9, seed=42))
        actual = frequency_filter(signal, [0] * 7 + [1])
        expected = [0j] * 7 + signal[:-7]
        self.assertEqual(len(actual), len(expected))
        for got, want in zip(actual, expected):
            self.assertLess(abs(got - want), 1e-10)

    def test_reusable_source_and_interpolator(self):
        symbols = generate_qpsk(64, seed=17)
        self.assertEqual(symbols, generate_qpsk(64, seed=17))
        self.assertEqual(set(symbols), {1+1j, 1-1j, -1+1j, -1-1j})
        self.assertEqual(
            interpolate_2x([1+1j, -1+1j, -1-1j]),
            [1+1j, 0j, -1+1j, 0j, -1-1j, 0j],
        )


if __name__ == "__main__":
    unittest.main()
