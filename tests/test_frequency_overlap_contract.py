"""Comprueba la reconstrucción por FFT con 50 % de solapamiento de E01.

La DFT de referencia usa solo la biblioteca estándar. Los coeficientes de prueba
son ejemplos independientes de la tabla definitiva del filtro en frecuencia.
"""

import cmath
import math
import unittest

from model.stimuli import generate_qpsk, interpolate_2x


N = 16
HOP = 8


def transform(values, inverse=False):
    assert len(values) == N
    sign = 1 if inverse else -1
    scale = 1 / N if inverse else 1
    return [
        scale
        * sum(
            values[n] * cmath.exp(sign * 2j * math.pi * k * n / N)
            for n in range(N)
        )
        for k in range(N)
    ]


def frequency_filter(signal, taps):
    """Overlap-save: 8 muestras previas + 8 nuevas; conservar las últimas 8."""
    if len(taps) != 8:
        raise ValueError("El contrato exige exactamente 8 coeficientes")
    spectrum = transform(list(taps) + [0j] * (N - len(taps)))
    result = []
    for start in range(0, len(signal), HOP):
        block = [
            signal[index] if 0 <= index < len(signal) else 0j
            for index in range(start - HOP, start + HOP)
        ]
        input_spectrum = transform(block)
        circular = transform(
            [input_spectrum[k] * spectrum[k] for k in range(N)],
            inverse=True,
        )
        result.extend(circular[HOP : HOP + min(HOP, len(signal) - start)])
    return result


def direct_filter(signal, taps):
    """Ecuación causal independiente de la DFT y de los límites de bloque."""
    return [
        sum(tap * signal[n - k] for k, tap in enumerate(taps) if n >= k)
        for n in range(len(signal))
    ]


def illustrative_rrc_taps():
    """Ejemplo beta=0.5, 2×, ocho taps simétricos; NO es la tabla de E02.

    Se muestrea t/T=(k-3.5)/2 y se normaliza a energía unitaria.
    Esta rejilla no toca las singularidades t=0 ni t=±T/(4*beta).
    Solo sirve para comprobar reconstrucción, no calidad de conformado.
    """
    beta = 0.5
    taps = []
    for k in range(8):
        t = (k - 3.5) / 2
        numerator = (
            math.sin(math.pi * t * (1 - beta))
            + 4 * beta * t * math.cos(math.pi * t * (1 + beta))
        )
        taps.append(numerator / (math.pi * t * (1 - (4 * beta * t) ** 2)))
    norm = math.sqrt(sum(tap * tap for tap in taps))
    return [tap / norm for tap in taps]


class FrequencyOverlapContractTest(unittest.TestCase):
    def assert_matches_direct(self, signal, taps):
        actual = frequency_filter(signal, taps)
        expected = direct_filter(signal, taps)
        self.assertEqual(len(actual), len(signal))
        for index, (got, want) in enumerate(zip(actual, expected)):
            self.assertLess(abs(got - want), 1e-10, f"muestra {index}")

    def test_rrc_with_qpsk_2x_full_partial_and_empty_frames(self):
        taps = illustrative_rrc_taps()
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

    def test_independent_frame_does_not_inherit_history(self):
        taps = illustrative_rrc_taps()
        frequency_filter(interpolate_2x(generate_qpsk(5, seed=17)), taps)
        quiet_frame = [0j] * 10
        self.assertEqual(frequency_filter(quiet_frame, taps), quiet_frame)

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
