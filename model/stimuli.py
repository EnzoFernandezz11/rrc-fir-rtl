"""Fuentes reutilizables para pruebas Python; no define mapeo de bits ni RTL."""

import random


def generate_qpsk(symbol_count, *, seed=0):
    """Genera símbolos con I/Q = ±1 sin conocer bloques FFT ni coeficientes.

    Usa un generador local con semilla, sin normalizar por sqrt(2).
    A01/E02 definirán el mapeo de bits del generador definitivo.
    """
    if symbol_count < 0:
        raise ValueError("La cantidad de símbolos no puede ser negativa")
    rng = random.Random(seed)
    return [
        complex(rng.choice((-1, 1)), rng.choice((-1, 1)))
        for _ in range(symbol_count)
    ]


def upsample_2x(symbols):
    """Inserta un cero después de cada símbolo, incluido el último: S → 2S."""
    return [sample for symbol in symbols for sample in (symbol, 0j)]
