#!/usr/bin/env python3
"""A05: exporta los vectores de prueba de ambas ramas desde los modelos fijos de A04.

Un archivo de texto por caso en vectors/, una línea por muestra de entrada:

    n last x_i x_q yt_i yt_q yf_i yf_q

Enteros decimales con signo, separados por un espacio. `x_*` en Q2.0, `yt_*` e
`yf_*` en el formato de salida de A04 (entero / 2**fraction_bits). `yt` es la
salida esperada de la rama temporal y `yf` la de frecuencia; cada RTL se compara
palabra por palabra con la suya. `last = 1` cierra una trama; cada trama empieza
con historial cero. `python3 -m model.vectors` regenera sin edición manual los casos
smoke en vectors/ (versionados) y la regresión QPSK en build/vectors/.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from model import fixed_point as fp
from model.qpsk_rrc import ROOT, qpsk, upsample

OUT = ROOT / "vectors"
BUILD = ROOT / "build/vectors"  # regresiones grandes, sin versionar
QPSK_SEED, QPSK_SYMBOLS = 1, 1024  # vector de regresión y de actividad SAIF (D06)


def worst_case_frames() -> list[np.ndarray]:
    """Una trama de 16 muestras por etapa del motor: la ventana QPSK que lleva `work` a su máximo.

    La segunda ventana de la trama es exactamente esas 16 muestras (8 de historial + 8 nuevas).
    """
    f = fp.Format()
    _, (Hr, Hi), (Wr, Wi) = fp.constants(f)
    trace: list = []
    fp._engine(np.eye(16), np.zeros((16, 16)), fp.Format(f.coef, f.out, f.work, 0, 0),
               (Hr / 2**f.spectrum, Hi / 2**f.spectrum), (Wr / 2**f.twiddle, Wi / 2**f.twiddle), None, trace)
    frames = []
    for cr, ci in trace:  # cr[n, nodo]: coeficiente de la entrada n en el nodo
        node = (np.abs(cr) + np.abs(ci)).sum(axis=0).argmax()
        si, sq = np.sign(cr[:, node]), -np.sign(ci[:, node])  # maximiza Re del nodo
        si, sq = np.where(si == 0, 1, si), np.where(sq == 0, 1, sq)
        frames.append(si + 1j * sq)
    return frames


def time_extremes() -> np.ndarray:
    """Lleva la salida temporal a +Σ|h_q| y −Σ|h_q| en I y Q."""
    s = np.sign(fp.coefficients(fp.Format()))[::-1]  # x[n−k] = sign(h_q[k])
    return np.r_[s, -s] * (1 + 1j)


def cases() -> dict[str, list[np.ndarray]]:
    """Casos smoke del contrato: impulso, ceros, extremos y límites de bloque."""
    impulse = np.zeros(32, complex)
    impulse[0] = 1 - 1j
    lengths = list(range(1, 18)) + [24, 25]  # parciales 1…7, bloque justo, bordes 8/16/24
    starts = np.cumsum([0] + lengths)
    edge_data = upsample(qpsk(starts[-1] // 2 + 1, 7))
    return {
        "impulso": [impulse],
        "ceros": [np.zeros(32, complex)],
        "extremos_tiempo": [time_extremes()],
        "extremos_frecuencia": worst_case_frames(),
        "bordes": [edge_data[a:b] for a, b in zip(starts, starts[1:])],
    }


def regression() -> dict[str, list[np.ndarray]]:
    return {f"qpsk_s{QPSK_SEED}": [upsample(qpsk(QPSK_SYMBOLS, QPSK_SEED))]}


def render(frames: list[np.ndarray]) -> str:
    rows, n = [], 0
    for x in frames:
        xi, xq = fp.to_int(x)
        yt, yf = fp.fir_time_fxp(x), fp.fir_frequency_fxp(x)
        for k in range(len(x)):
            cols = (n, int(k == len(x) - 1), xi[k], xq[k], yt[k].real, yt[k].imag, yf[k].real, yf[k].imag)
            rows.append(" ".join(str(int(c)) for c in cols))
            n += 1
    return "\n".join(rows) + "\n"


def read(path: Path) -> dict[str, np.ndarray]:
    """Lector de referencia: columnas como arrays enteros."""
    data = np.loadtxt(path, dtype=np.int64, ndmin=2)
    names = ("n", "last", "x_i", "x_q", "yt_i", "yt_q", "yf_i", "yf_q")
    return dict(zip(names, data.T))


def export() -> list[Path]:
    paths = []
    for out, group in ((OUT, cases()), (BUILD, regression())):
        out.mkdir(parents=True, exist_ok=True)
        for name, frames in group.items():
            path = out / f"{name}.txt"
            path.write_text(render(frames), encoding="utf-8")
            paths.append(path)
    return paths


if __name__ == "__main__":
    for p in export():
        print(p.relative_to(ROOT))
