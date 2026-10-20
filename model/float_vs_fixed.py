#!/usr/bin/env python3
"""I02: punto flotante contra punto fijo en cada conjunto de datos de A05 y en las semillas QPSK de A04.

`python3 -m model.float_vs_fixed` imprime, por caso y rama, el error contra el FIR temporal
flotante en LSB de salida (Q2.7) y la SQNR de D07. En `ceros` la referencia es nula y la SQNR
no está definida: se informa solo el error.
"""
from __future__ import annotations

import numpy as np

from model import fixed_point as fp
from model.fir_time import fir_time
from model.qpsk_rrc import qpsk, rrc_taps, upsample
from model.vectors import cases


def datasets() -> dict[str, list[np.ndarray]]:
    data = dict(cases())
    data.update({f"qpsk_s{s}": [upsample(qpsk(fp.SYMBOLS, s))] for s in fp.SEEDS})
    return data


def compare(frames: list[np.ndarray], fmt: fp.Format = fp.Format()) -> dict[str, dict[str, float]]:
    """Por rama: error máximo y RMS en LSB por componente, y SQNR (nan si la referencia es nula)."""
    h = rrc_taps()
    ref = np.concatenate([fir_time(x, h) for x in frames])
    res = {}
    for branch, model in (("tiempo", fp.fir_time_fxp), ("frecuencia", fp.fir_frequency_fxp)):
        y = np.concatenate([model(x, fmt) for x in frames]) / 2**fmt.out
        err = np.r_[(y - ref).real, (y - ref).imag] * 2**fmt.out
        res[branch] = {
            "max_lsb": float(np.abs(err).max()),
            "rms_lsb": float(np.sqrt(np.mean(err**2))),
            "sqnr_db": fp.sqnr_db(y, ref) if np.any(ref) else float("nan"),
        }
    return res


def main() -> None:
    print(f"{'caso':<20} {'muestras':>8}   {'tiempo: máx  rms  SQNR':>24}   {'frecuencia: máx  rms  SQNR':>28}")
    for name, frames in datasets().items():
        r = compare(frames)
        cells = "   ".join(f"{r[b]['max_lsb']:9.2f} {r[b]['rms_lsb']:5.2f} {r[b]['sqnr_db']:6.1f}"
                           for b in ("tiempo", "frecuencia"))
        print(f"{name:<20} {sum(map(len, frames)):>8}   {cells}")


if __name__ == "__main__":
    main()
