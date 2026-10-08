#!/usr/bin/env python3
"""A02: modelo flotante del FIR temporal y casos de referencia con índice.

Misma convención que `frequency_filter` de E01 (#28): historial inicial cero,
una salida por muestra de entrada y sin cola final, para comparar índice a
índice. Los CSV van a build/; el formato definitivo de vectores lo fija A05.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from model.qpsk_rrc import ROOT, qpsk, rrc_taps, upsample


def fir_time(x: np.ndarray, h: np.ndarray) -> np.ndarray:
    """y[n] = Σ h[k]·x[n−k] para n = 0…len(x)−1, con x[n<0] = 0."""
    return np.convolve(np.asarray(x, dtype=complex), h)[: len(x)]


def cases(seed: int = 1, symbols: int = 32) -> dict[str, np.ndarray]:
    """Estímulos mínimos del contrato de verificación: impulso, ceros y QPSK 2×."""
    n = 2 * symbols
    impulse = np.zeros(n, dtype=complex)
    impulse[0] = 1
    return {
        "impulso": impulse,
        "ceros": np.zeros(n, dtype=complex),
        f"qpsk_s{seed}": upsample(qpsk(symbols, seed)),
    }


def export(out: Path, seed: int = 1, symbols: int = 32) -> list[Path]:
    """Escribe un CSV por caso con columnas n, x_i, x_q, y_i, y_q."""
    out.mkdir(parents=True, exist_ok=True)
    h = rrc_taps()
    paths = []
    for name, x in cases(seed, symbols).items():
        y = fir_time(x, h)
        path = out / f"{name}.csv"
        np.savetxt(
            path,
            np.column_stack([np.arange(len(x)), x.real, x.imag, y.real, y.imag]),
            fmt=["%d", "%.17g", "%.17g", "%.17g", "%.17g"],
            delimiter=",",
            header="n,x_i,x_q,y_i,y_q",
            comments="",
        )
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--symbols", type=int, default=32)
    parser.add_argument("--out", type=Path, default=ROOT / "build/a02")
    args = parser.parse_args()
    for path in export(args.out, args.seed, args.symbols):
        print(path)


if __name__ == "__main__":
    main()
