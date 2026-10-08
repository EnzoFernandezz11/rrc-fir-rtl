#!/usr/bin/env python3
"""A01: símbolos QPSK reproducibles y coeficientes RRCOS de 8 taps.

Los parámetros salen de config/project.json. La normalización (energía
unitaria) es provisional hasta que E02/D02 la confirme.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROJECT = json.loads((ROOT / "config/project.json").read_text(encoding="utf-8"))
CONFIRMED = PROJECT["confirmed"]
TAPS = CONFIRMED["coefficient_count"]
ROLLOFF = CONFIRMED["rolloff"]
SPS = CONFIRMED.get("samples_per_symbol", PROJECT.get("proposals", {}).get("samples_per_symbol", {}).get("value"))
if SPS is None:
    raise KeyError("samples_per_symbol")


def qpsk(count: int, seed: int) -> np.ndarray:
    """Símbolos ±1±1j. Columna 0 de bits → I, columna 1 → Q; bit 0 → +1, bit 1 → −1."""
    bits = np.random.default_rng(seed).integers(0, 2, size=(count, 2))
    return (1 - 2 * bits[:, 0]) + 1j * (1 - 2 * bits[:, 1])


def upsample(symbols: np.ndarray, sps: int = SPS) -> np.ndarray:
    """Inserta sps−1 ceros después de cada símbolo."""
    out = np.zeros(len(symbols) * sps, dtype=complex)
    out[::sps] = symbols
    return out


def rrc(t: np.ndarray, alpha: float = ROLLOFF) -> np.ndarray:
    """Pulso RRCOS en t (en períodos de símbolo), sin normalizar."""
    t = np.asarray(t, dtype=float)
    singular = np.isclose(np.abs(t), 1 / (4 * alpha))
    zero = t == 0
    ts = np.where(singular | zero, 0.1, t)  # valor cualquiera para no dividir por cero
    h = (np.sin(np.pi * ts * (1 - alpha)) + 4 * alpha * ts * np.cos(np.pi * ts * (1 + alpha))) / (
        np.pi * ts * (1 - (4 * alpha * ts) ** 2)
    )
    h[zero] = 1 - alpha + 4 * alpha / np.pi
    h[singular] = alpha / np.sqrt(2) * (
        (1 + 2 / np.pi) * np.sin(np.pi / (4 * alpha)) + (1 - 2 / np.pi) * np.cos(np.pi / (4 * alpha))
    )
    return h


def sample_times(taps: int = TAPS, sps: int = SPS) -> np.ndarray:
    """Grilla simétrica: con 8 taps a 2× da ±0,25…±1,75 Ts, sin tap central."""
    return (np.arange(taps) - (taps - 1) / 2) / sps


def rrc_taps(taps: int = TAPS, alpha: float = ROLLOFF, sps: int = SPS) -> np.ndarray:
    """h[0]…h[taps−1] con energía unitaria (Σh² = 1). h[0] multiplica a x[n] en y[n] = Σ h[k]·x[n−k]."""
    h = rrc(sample_times(taps, sps), alpha)
    return h / np.linalg.norm(h)


def impulse_response(h: np.ndarray, length: int) -> np.ndarray:
    """Salida del FIR ante δ[n]; referencia índice a índice para los modelos y el RTL."""
    delta = np.zeros(length)
    delta[0] = 1
    return np.convolve(delta, h)[:length]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--symbols", type=int, default=8)
    args = parser.parse_args()

    h = rrc_taps()
    print(f"RRCOS: {TAPS} taps, roll-off {ROLLOFF}, {SPS}x, energía unitaria (provisional)")
    print(" n   t/Ts      h[n] = respuesta al impulso")
    t = sample_times()
    for n, v in enumerate(impulse_response(h, TAPS + 2)):
        print(f"{n:2d} {f'{t[n]:+6.2f}' if n < TAPS else '     —'} {v:+.12f}")
    print(f"Σh = {h.sum():.12f}  Σ|h| = {np.abs(h).sum():.12f}")
    symbols = qpsk(args.symbols, args.seed)
    print(f"\nQPSK semilla {args.seed}: {symbols}")
    print(f"{SPS}x: {upsample(symbols)}")


if __name__ == "__main__":
    main()
