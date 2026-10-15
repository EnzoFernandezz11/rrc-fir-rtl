"""C02: constantes y regresión extendida A03/A04, complementarias a A05."""

from pathlib import Path

import numpy as np

from model.fir_time import cases, fir_time
from model.fixed_point import (
    SEEDS, SYMBOLS, Format, _engine, constants, fir_frequency_fxp, fir_time_fxp, sqnr_db, widths,
)
from model.qpsk_rrc import PROJECT, ROOT, qpsk, rrc_taps, upsample


def stimuli():
    yield from cases(seed=1, symbols=32).items()
    for seed in (0, 17, 42, 1234):
        yield f"a03_qpsk_s{seed}", upsample(qpsk(256, seed))
    x = upsample(qpsk(20, 7))
    for length in range(41):
        yield f"a03_length_{length}", x[:length]
    for pos in range(24):
        x = np.zeros(24, complex)
        x[pos] = 1 - 1j
        yield f"a03_impulse_{pos}", x
    for value in (1 + 1j, 1 - 1j, -1 + 1j, -1 - 1j):
        yield f"extreme_{int(value.real)}_{int(value.imag)}", np.full(32, value)
    # A04: ventanas de signos que maximizan cada componente/nodo de las nueve etapas.
    fmt = Format()
    _, H, W = constants(fmt)
    trace = []
    _engine(np.eye(16), np.zeros((16, 16)), Format(fmt.coef, fmt.out, fmt.work, 0, 0),
            (H[0] / 2**fmt.spectrum, H[1] / 2**fmt.spectrum),
            (W[0] / 2**fmt.twiddle, W[1] / 2**fmt.twiddle), None, trace)
    for stage, (cr, ci) in enumerate(trace):
        for node in range(16):
            for component, (xr, xq) in enumerate(((cr[:, node], -ci[:, node]), (ci[:, node], cr[:, node]))):
                xr, xq = np.sign(xr), np.sign(xq)
                xr, xq = np.where(xr == 0, xq, xr), np.where(xq == 0, xr, xq)
                yield f"a04_worst_stage{stage}_node{node}_comp{component}", xr + 1j*xq
    for seed in SEEDS:
        yield f"a04_sqnr_s{seed}", upsample(qpsk(SYMBOLS, seed))


def export(path: Path = ROOT / "build/frequency_serial_vectors.txt") -> None:
    fmt = Format()
    w = widths(fmt)
    if fmt.twiddle != fmt.spectrum:
        raise ValueError("frequency_serial comparte el formato de H y W")
    h = PROJECT["decisions"]["coefficients"]
    taps, (hr, hi), (wr, wi) = constants(fmt, h)
    frames = list(stimuli())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as out:
        out.write(" ".join(str(v) for node in ("work", "twiddle", "salida") for v in w[node]) + "\n")
        for tap in taps:
            out.write(f"{tap}\n")
        for real, imag in zip(hr, hi):
            out.write(f"{real} {imag}\n")
        for real, imag in zip(wr, wi):
            out.write(f"{real} {imag}\n")
        out.write(f"{len(frames)}\n")
        for name, x in frames:
            y = fir_frequency_fxp(x, fmt, h)
            if name.startswith("a04_sqnr"):
                sqnr = sqnr_db(y / 2**fmt.out, fir_time(x, rrc_taps()))
                difference = y - fir_time_fxp(x, fmt, h)
                delta = np.abs(np.r_[difference.real, difference.imag]).max()
                if sqnr < PROJECT["confirmed"]["minimum_sqnr_db"] or delta > 2:
                    raise ValueError(f"{name}: SQNR={sqnr:.3f} dB, diferencia={delta} LSB")
                print(f"{name}: SQNR={sqnr:.3f} dB, diferencia entre ramas={delta:.0f} LSB")
            out.write(f"{name} {len(x)}\n")
            for sample, result in zip(x, y):
                out.write(f"{int(sample.real)} {int(sample.imag)} {int(result.real)} {int(result.imag)}\n")
    print(f"{path.relative_to(ROOT)}: {len(frames)} tramas, {sum(len(x) for _, x in frames)} muestras")


if __name__ == "__main__":
    export()
