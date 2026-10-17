"""Exporta el benchmark PPA local A04: QPSK 2x, semilla 1, 1024 símbolos."""

import argparse
from pathlib import Path

import numpy as np

from model.fixed_point import Format, fir_frequency_fxp, widths
from model.qpsk_rrc import PROJECT, qpsk, upsample


def export(path: Path) -> None:
    fmt = Format()
    if widths(fmt)["salida"] != (9, 7) or (fmt.work, fmt.twiddle, fmt.spectrum) != (5, 8, 8):
        raise ValueError("El benchmark requiere los formatos A04 del RTL serial")
    x = upsample(qpsk(1024, seed=1), sps=2)
    y = fir_frequency_fxp(x, fmt, PROJECT["decisions"]["coefficients"])
    values = np.column_stack((x.real, x.imag, y.real, y.imag))
    assert len(x) == len(y) == 2048 and np.array_equal(values, values.astype(np.int64))
    assert np.all(np.abs(values[:, :2]) <= 1) and np.all((values[:, 2:] >= -256) & (values[:, 2:] < 256))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"{len(x)}\n")
        np.savetxt(stream, values, fmt="%d")
    print(f"{path}: {len(x)} muestras, QPSK 2x, seed=1, A04")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    export(parser.parse_args().output)
