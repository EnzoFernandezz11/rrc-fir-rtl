"""Modelo flotante de E01: overlap-save de 16 puntos y avance de ocho.

La transformada usa una DFT directa de biblioteca estándar para representar
FFT16/IFFT16; no modela su arquitectura, rendimiento ni cuantización RTL.
Los coeficientes definitivos se reciben como argumento (E02).
"""

import cmath
import math


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
    """Filtra una trama completa con ocho taps en orden causal h[0]…h[7].

    signal contiene muestras complejas (interpolar antes si se parte de símbolos).
    Devuelve len(signal) muestras: historial inicial cero y sin cola final.
    Cada llamada es una trama independiente; no admite fragmentos de un flujo
    continuo conservando estado. Es un modelo flotante sin latencia de reloj.
    """
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

