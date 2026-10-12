#!/usr/bin/env python3
"""A04: modelos de punto fijo bit-true, SQNR y barrido de anchos.

Cada valor fijo es un entero con F bits fraccionarios (valor real = entero / 2**F).
Los cortes redondean «mitad hacia arriba»: (v + 2**(s−1)) >> s, que en RTL es un
sumador y un desplazamiento aritmético. Ningún nodo satura: los anchos salen de
cotas analíticas del peor caso y los modelos levantan OverflowError si un valor
no entra, así que no hay overflow oculto.

- `fir_time_fxp`: FIR temporal; productos y acumulador exactos, un solo corte a la salida.
- `fir_frequency_fxp`: motor de C01 (#39): carga bit reversal, 32 mariposas DIT,
  16 productos por H, 6 intercambios, IFFT con W conjugado y escala 1/16 a la salida.
  Cortes tras cada producto complejo (W·B y X·H) y a la salida.

`python3 -m model.fixed_point` corre el barrido e imprime la evidencia.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from model.fir_time import fir_time
from model.qpsk_rrc import PROJECT, qpsk, rrc_taps, upsample

N, HOP = 16, 8
# Tabla de operaciones de C01 §2.4: (addr_a, addr_b, w_index), etapas m = 2, 4, 8, 16.
BUTTERFLIES = [(b + j, b + j + m // 2, j * N // m) for m in (2, 4, 8, 16) for b in range(0, N, m) for j in range(m // 2)]
BITREV = [int(f"{i:04b}"[::-1], 2) for i in range(N)]
SWAPS = [(i, BITREV[i]) for i in range(N) if i < BITREV[i]]


FRACTION_BITS = PROJECT["decisions"]["fixed_point_format"]["fraction_bits"]


@dataclass(frozen=True)
class Format:
    """Bits fraccionarios de cada nodo; los anchos totales se derivan con `widths`."""

    coef: int = FRACTION_BITS["coef"]          # h_q, compartidos por ambas ramas
    out: int = FRACTION_BITS["out"]            # salida común I/Q
    work: int = FRACTION_BITS["work"]          # banco work del motor en frecuencia
    twiddle: int = FRACTION_BITS["twiddle"]    # W
    spectrum: int = FRACTION_BITS["spectrum"]  # H


def quantize(v, frac: int) -> np.ndarray:
    """Redondeo mitad hacia arriba a `frac` bits; para constantes calculadas offline."""
    return np.floor(np.asarray(v, dtype=float) * 2**frac + 0.5).astype(np.int64)


def rshift_round(v: np.ndarray, s: int) -> np.ndarray:
    if s < 0:
        raise ValueError("el corte no puede agregar bits fraccionarios")
    return v if s == 0 else (v + (1 << (s - 1))) >> s


def bits_for(bound: float) -> int:
    """Bits enteros con signo para cubrir [−bound, bound]."""
    return int(np.floor(np.log2(bound))) + 2 if bound >= 1 else 1


def check(name: str, v: np.ndarray, width: int) -> None:
    lim = 1 << (width - 1)
    if v.size and (v.min() < -lim or v.max() >= lim):
        raise OverflowError(f"{name}: valor fuera de {width} bits con signo")


def to_int(x) -> tuple[np.ndarray, np.ndarray]:
    """Entrada E02: I/Q en {−1, 0, +1}, 2 bits con signo y 0 fraccionarios."""
    x = np.asarray(x, dtype=complex)
    xi, xq = np.rint(x.real).astype(np.int64), np.rint(x.imag).astype(np.int64)
    if not (np.array_equal(xi, x.real) and np.array_equal(xq, x.imag)) or np.abs(np.r_[xi, xq]).max(initial=0) > 1:
        raise ValueError("la entrada debe tener I/Q en {−1, 0, +1}")
    return xi, xq


def coefficients(fmt: Format, h=None) -> np.ndarray:
    return quantize(rrc_taps() if h is None else h, fmt.coef)


def constants(fmt: Format, h=None):
    """h_q, H_q = Q(DFT16([h_q, 0…0])) y W_q, como C01 §2.2."""
    h_q = coefficients(fmt, h)
    H = np.fft.fft(np.r_[h_q / 2**fmt.coef, np.zeros(N - len(h_q))])
    W = np.exp(-2j * np.pi * np.arange(N // 2) / N)
    return h_q, (quantize(H.real, fmt.spectrum), quantize(H.imag, fmt.spectrum)), (quantize(W.real, fmt.twiddle), quantize(W.imag, fmt.twiddle))


def widths(fmt: Format, h=None) -> dict[str, tuple[int, int]]:
    """(bits totales, bits fraccionarios) por nodo, a partir de cotas del peor caso."""
    h_q, (Hr, Hi), (Wr, Wi) = constants(fmt, h)
    acc = np.abs(h_q).sum()  # |Σ h_q·x| con x en {−1, 0, +1}
    work = work_bound(fmt, h) * 2**fmt.work
    return {
        "entrada": (2, 0),
        "coeficiente": (bits_for(np.abs(h_q).max()), fmt.coef),
        "acumulador": (bits_for(acc), fmt.coef),
        "salida": (bits_for(acc / 2**fmt.coef * 2**fmt.out + 1), fmt.out),
        "work": (bits_for(work), fmt.work),
        "twiddle": (bits_for(np.abs(np.r_[Wr, Wi]).max()), fmt.twiddle),
        "espectro": (bits_for(np.abs(np.r_[Hr, Hi]).max()), fmt.spectrum),
    }


def fir_time_fxp(x, fmt: Format = Format(), h=None) -> np.ndarray:
    """FIR temporal bit-true; devuelve la salida entera (F = fmt.out) como complejo de enteros."""
    w = widths(fmt, h)
    h_q = coefficients(fmt, h)
    out = []
    for comp in to_int(x):
        acc = np.convolve(comp, h_q)[: len(comp)] if len(comp) else comp
        check("acumulador", acc, w["acumulador"][0])
        y = rshift_round(acc, fmt.coef - fmt.out)
        check("salida", y, w["salida"][0])
        out.append(y)
    return out[0] + 1j * out[1]


def windows(xi: np.ndarray, xq: np.ndarray):
    """Ventanas de 16 (8 de historial + 8 nuevas, relleno con ceros) y cantidad p de salidas."""
    n = len(xi)
    blocks = -(-n // HOP)
    pad = lambda v: np.r_[np.zeros(HOP, np.int64), v, np.zeros(blocks * HOP - n, np.int64)]
    idx = np.arange(blocks)[:, None] * HOP + np.arange(N)
    return pad(xi)[idx], pad(xq)[idx], n


def _engine(wr, wi, fmt: Format, H, W, check_width: int | None, trace=None):
    """Motor de C01 sobre todas las ventanas a la vez (filas independientes)."""
    wr, wi = wr[:, BITREV], wi[:, BITREV]  # work[bitrev(r)] = ventana[r]
    rnd = (lambda v, s: rshift_round(v, s)) if check_width else (lambda v, s: v / 2**s)

    def stage_check(name):
        if check_width:
            check(name, np.r_[wr.ravel(), wi.ravel()], check_width)
        if trace is not None:
            trace.append((wr.copy(), wi.copy()))

    def transform(w_r, w_i, name):
        nonlocal wr, wi
        for s in range(4):
            for a, b, k in BUTTERFLIES[8 * s : 8 * s + 8]:
                tr = rnd(w_r[k] * wr[:, b] - w_i[k] * wi[:, b], fmt.twiddle)
                ti = rnd(w_r[k] * wi[:, b] + w_i[k] * wr[:, b], fmt.twiddle)
                ar, ai = wr[:, a].copy(), wi[:, a].copy()
                wr[:, a], wi[:, a], wr[:, b], wi[:, b] = ar + tr, ai + ti, ar - tr, ai - ti
            stage_check(f"{name} etapa {s + 1}")

    Wr, Wi = W
    transform(Wr, Wi, "FFT")
    Hr, Hi = H
    wr, wi = rnd(wr * Hr - wi * Hi, fmt.spectrum), rnd(wr * Hi + wi * Hr, fmt.spectrum)
    stage_check("producto")
    for i, j in SWAPS:
        wr[:, [i, j]], wi[:, [i, j]] = wr[:, [j, i]], wi[:, [j, i]]
    transform(Wr, -Wi, "IFFT")
    return wr[:, HOP:], wi[:, HOP:]


def fir_frequency_fxp(x, fmt: Format = Format(), h=None) -> np.ndarray:
    """Filtro en frecuencia bit-true; salida entera (F = fmt.out) como complejo de enteros."""
    w = widths(fmt, h)
    _, H, W = constants(fmt, h)
    xi, xq = to_int(x)
    if not len(xi):
        return np.zeros(0, complex)
    wr, wi, n = windows(xi << fmt.work, xq << fmt.work)
    yr, yi = _engine(wr, wi, fmt, H, W, w["work"][0])
    shift = fmt.work + 4 - fmt.out  # escala 1/16 de la IFFT y corte a la salida
    yr, yi = rshift_round(yr.ravel()[:n], shift), rshift_round(yi.ravel()[:n], shift)
    check("salida", np.r_[yr, yi], w["salida"][0])
    return yr + 1j * yi


def work_bound(fmt: Format, h=None) -> float:
    """Máximo |I| o |Q| de cada etapa del banco work, con I/Q de entrada en {−1, 0, +1}.

    Cada nodo es lineal en la ventana: v = Σ c_n·x_n. Con x_n = x_i + j·x_q,
    |Re v| y |Im v| ≤ Σ (|Re c_n| + |Im c_n|). Se evalúa con las constantes
    cuantizadas y se suma 1 de margen por el error acumulado de redondeo.
    """
    _, (Hr, Hi), (Wr, Wi) = constants(fmt, h)
    H = (Hr / 2**fmt.spectrum, Hi / 2**fmt.spectrum)
    W = (Wr / 2**fmt.twiddle, Wi / 2**fmt.twiddle)
    eye = np.eye(N)
    trace: list = []
    _engine(eye.copy(), np.zeros((N, N)), Format(fmt.coef, fmt.out, fmt.work, 0, 0), H, W, None, trace)
    # Filas = impulso en cada posición de la ventana: columna = nodo.
    return max((np.abs(r) + np.abs(i)).sum(axis=0).max() for r, i in trace) + 1


def sqnr_db(y_fxp: np.ndarray, y_ref: np.ndarray) -> float:
    """D07: 10·log10(Σ|y_ref|² / Σ|y_fxp − y_ref|²), I/Q juntas, todas las muestras."""
    return float(10 * np.log10(np.sum(np.abs(y_ref) ** 2) / np.sum(np.abs(y_fxp - y_ref) ** 2)))


SEEDS = (0, 1, 2, 3, 4)
SYMBOLS = 1024


def evaluate(fmt: Format, seeds=SEEDS, symbols=SYMBOLS) -> dict[str, float]:
    """SQNR mínima entre semillas por rama y diferencia máxima entre ramas en LSB."""
    h = rrc_taps()
    res = {"tiempo": np.inf, "frecuencia": np.inf, "dif_lsb": 0.0}
    for seed in seeds:
        x = upsample(qpsk(symbols, seed))
        ref = fir_time(x, h)
        yt, yf = fir_time_fxp(x, fmt), fir_frequency_fxp(x, fmt)
        res["tiempo"] = min(res["tiempo"], sqnr_db(yt / 2**fmt.out, ref))
        res["frecuencia"] = min(res["frecuencia"], sqnr_db(yf / 2**fmt.out, ref))
        res["dif_lsb"] = max(res["dif_lsb"], np.abs(np.r_[(yt - yf).real, (yt - yf).imag]).max())
    return res


def sweep() -> None:
    """Evidencia de A04: barridos con un nodo variable y el resto en el formato elegido."""
    fmt = Format()
    print(f"SQNR mínima (dB) en semillas {SEEDS} × {SYMBOLS} símbolos; formato elegido: {fmt}")
    print("\nRama temporal: coef × salida (salida ≤ coef)")
    print("coef\\out" + "".join(f"{o:>7}" for o in range(5, 10)))
    for c in range(5, 10):
        cells = [f"{evaluate(Format(c, o, 12, 12, 12), seeds=SEEDS[:2])['tiempo']:7.1f}" if o <= c else "      —" for o in range(5, 10)]
        print(f"{c:>8} " + "".join(cells))
    print("\nRama en frecuencia: un nodo por vez")
    for node in ("work", "twiddle", "spectrum"):
        cells = []
        for f in range(4, 10):
            r = evaluate(Format(**{**fmt.__dict__, node: f}), seeds=SEEDS[:2])
            cells.append(f"{f}:{r['frecuencia']:.1f}")
        print(f"{node:>9}  " + "  ".join(cells))
    r = evaluate(fmt)
    print(f"\nFormato elegido: tiempo {r['tiempo']:.1f} dB, frecuencia {r['frecuencia']:.1f} dB, "
          f"diferencia máx. entre ramas {r['dif_lsb']:.0f} LSB")
    print(f"Cota del banco work: {work_bound(fmt):.1f}")
    print("\nnodo          bits  frac")
    for name, (bits, frac) in widths(fmt).items():
        print(f"{name:<12} {bits:>5} {frac:>5}")


if __name__ == "__main__":
    sweep()
