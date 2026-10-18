#!/usr/bin/env python3
"""B03: modelo ciclo a ciclo de la arquitectura sistólica del FIR temporal.

Simula las ecuaciones y el handshake de docs/arquitectura-rtl-tiempo-optimizada.md:
sumas parciales s_k ← h_q[k]·x + s_{k+1} que avanzan solo con la aceptación de
entrada, registro de salida con backpressure y limpieza de las s_k al aceptar
`last`. Compara cada resultado entregado con las columnas `yt` y `last` de los
vectores A05, mide L e II y comprueba que ninguna suma parcial sale de 9 bits con
signo. Verifica la propuesta de B03, no el RTL de B04.

`python3 -m model.fir_time_systolic` corre los vectores smoke y, si existe,
build/vectors/qpsk_s1.txt; también acepta rutas como argumentos.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from model.fixed_point import Format, coefficients
from model.qpsk_rrc import ROOT
from model.vectors import read

W_ACC = 9
SMOKE = ("impulso", "ceros", "extremos_tiempo", "extremos_frecuencia", "bordes")


def simular(cols: dict, pausas: bool, semilla: int = 1) -> tuple[int, set[int], set[int]]:
    """Devuelve (ciclos, valores de L, valores de II); AssertionError si algo no coincide."""
    h = [int(v) for v in coefficients(Format())]
    n_tot = len(cols["n"])
    rnd = random.Random(semilla)
    lim = 1 << (W_ACC - 1)
    s = {"i": [0] * 8, "q": [0] * 8}  # s[1..7]; s[0] sin usar
    y = {"i": 0, "q": 0}
    out_valid = out_last = 0
    n_in = n_out = ciclo = 0
    t_acepta: list[int] = []
    t_valido: list[int] = []
    while n_out < n_tot:
        ciclo += 1
        if ciclo > 40 * n_tot + 100:
            raise AssertionError(f"timeout con {n_out} de {n_tot} resultados")
        in_valid = n_in < n_tot and not (pausas and rnd.random() < 0.25)
        out_ready = not (pausas and rnd.random() < 0.33)
        in_ready = (not out_valid) or out_ready
        if out_valid and len(t_valido) == n_out:
            t_valido.append(ciclo)
        # Flanco: primero la salida presentada, después la aceptación de entrada.
        if out_valid and out_ready:
            esperado = (int(cols["yt_i"][n_out]), int(cols["yt_q"][n_out]), int(cols["last"][n_out]))
            if (y["i"], y["q"], out_last) != esperado:
                raise AssertionError(f"índice {n_out}: esperado {esperado}, obtenido {(y['i'], y['q'], out_last)}")
            n_out += 1
        if in_valid and in_ready:
            last = int(cols["last"][n_in])
            for c in "iq":
                x = int(cols[f"x_{c}"][n_in])
                p = [hk * x for hk in h]
                y[c] = p[0] + s[c][1]
                nuevo = [0] * 8
                if not last:  # con last, las sumas parciales pasan a 0 (regla 5)
                    for k in range(1, 7):
                        nuevo[k] = p[k] + s[c][k + 1]
                    nuevo[7] = p[7]
                for v in nuevo + [y[c]]:
                    if not -lim <= v < lim:
                        raise AssertionError(f"valor {v} fuera de {W_ACC} bits con signo")
                s[c] = nuevo
            t_acepta.append(ciclo)
            out_last = last
            out_valid = 1
            n_in += 1
        elif out_valid and out_ready:
            out_valid = 0
    L = {t_valido[n] - t_acepta[n] for n in range(n_tot)}
    II = {t_acepta[n] - t_acepta[n - 1] for n in range(1, n_tot)}
    return ciclo, L, II


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("archivos", nargs="*", type=Path, help="vectores A05 (por defecto, smoke y regresión)")
    args = parser.parse_args()
    archivos = args.archivos or [ROOT / "vectors" / f"{n}.txt" for n in SMOKE]
    regresion = ROOT / "build/vectors/qpsk_s1.txt"
    if not args.archivos and regresion.is_file():
        archivos.append(regresion)
    for ruta in archivos:
        cols = read(ruta)
        ciclos, L, II = simular(cols, pausas=False)
        simular(cols, pausas=True)
        nombre = ruta.resolve().relative_to(ROOT) if ruta.resolve().is_relative_to(ROOT) else ruta
        print(f"OK {nombre}: {len(cols['n'])} muestras; ideal L={sorted(L)} II={sorted(II)} en {ciclos} ciclos; con pausas también coincide")


if __name__ == "__main__":
    main()
