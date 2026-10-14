#!/usr/bin/env python3
"""A07: tabla PPA de las cuatro variantes, trazable a las corridas Vivado.

Cada variante medida tiene su carpeta `reports/ppa/<variante>/` con los archivos
que deja el flujo Vivado de C02 (`scripts/ppa/vivado/run.tcl`): `summary.tsv`,
`configuration.txt`, `tool_versions.txt` y, si existe, `source_manifest.json`.
Una variante sin carpeta figura como «no medida» (verificacion-y-ppa.md#ppa).

    python3 -m scripts.ppa_table      # escribe reports/ppa/tabla.md
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PPA_DIR = ROOT / "reports/ppa"
VARIANTS = ("time_serial", "time_optimized", "frequency_serial", "frequency_optimized")
COLUMNS = ("variante", "commit", "configuración", "SQNR", "área", "Fmax", "latencia",
           "throughput", "potencia", "herramienta/log")


def read_summary(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8") as fh:
        return {row["metric"]: row["value"] for row in csv.DictReader(fh, delimiter="\t")}


def row(name: str, sqnr: dict[str, float], registered: set[str], ppa_dir: Path = PPA_DIR) -> list[str]:
    # ponytail: SQNR del modelo fijo de la rama; vale para el RTL solo si está
    # registrado, porque el banco común exige coincidencia exacta con ese modelo (A06).
    sqnr_cell = f"{sqnr[name.split('_')[0]]:.1f} dB" if name in registered else "—"
    run = ppa_dir / name
    if not (run / "summary.tsv").is_file():
        return [name, "—", "—", sqnr_cell, *["no medida"] * 5, "—"]
    m = read_summary(run / "summary.tsv")
    commit = "—"
    if (run / "source_manifest.json").is_file():
        commit = json.loads((run / "source_manifest.json").read_text(encoding="utf-8"))["commit"][:8]
    tool = (run / "tool_versions.txt").read_text(encoding="utf-8").splitlines()[0].strip()
    period = float(m["clock_period_ns"])
    return [
        name,
        f"`{commit}`",
        f"{m['part']}, OOC, {1000 / period:g} MHz, timing {m['timing_status']}",
        sqnr_cell,
        f"{m['lut']} LUT / {m['ff']} FF / {m['dsp']} DSP / {m['bram_tiles']} BRAM",
        f"{float(m['fmax_estimate_mhz']):.1f} MHz (WNS {float(m['internal_wns_ns']):.3f} ns)",
        f"{m['latency_cycles']} ciclos",
        f"{float(m['throughput_samples_per_second']) / 1e6:.4g} Mmuestras/s",
        f"{m['dynamic_power_w']} W din. / {m['static_power_w']} W est. / "
        f"{float(m['energy_dynamic_nj_per_sample']):.3g} nJ/muestra",
        f"{tool}; [corrida]({name}/)",
    ]


def table(sqnr: dict[str, float], registered: set[str], ppa_dir: Path = PPA_DIR) -> str:
    lines = ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    lines += ["| " + " | ".join(row(name, sqnr, registered, ppa_dir)) + " |" for name in VARIANTS]
    return "\n".join(lines) + "\n"


def main() -> int:
    from model.fixed_point import Format, evaluate
    from scripts.validate_project import load_targets

    r = evaluate(Format())
    sqnr = {"time": r["tiempo"], "frequency": r["frecuencia"]}
    out = PPA_DIR / "tabla.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "# Tabla PPA\n\n"
        "Generada con `python3 -m scripts.ppa_table`; no editar a mano. Cada fila sale de "
        "`reports/ppa/<variante>/summary.tsv` (flujo Vivado de C02). SQNR mínima del modelo fijo "
        "de cada rama, semillas 0–4 × 1024 símbolos (A04), solo para variantes registradas en "
        "`config/rtl_targets.json` (coinciden palabra por palabra con ese modelo). La potencia estática es del dispositivo "
        "completo; la dinámica requiere revisar la cobertura SAIF de cada corrida.\n\n"
        + table(sqnr, {t["name"] for t in load_targets()}),
        encoding="utf-8",
    )
    print(f"Tabla: {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
