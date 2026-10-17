#!/usr/bin/env python3
"""A07: tabla PPA de las cuatro variantes, trazable a las corridas Vivado.

Cada corrida medida tiene su carpeta `reports/ppa/<variante>/<reloj>mhz/` con los
reportes chicos que deja el flujo Vivado de C02 (`scripts/ppa/vivado/run.tcl`).
Una fila sin carpeta figura como «no medida» (verificacion-y-ppa.md#ppa). Las
seriales se miden a 10 MHz (oficial) y a 100 MHz (dato adicional, #49).

    python3 -m scripts.ppa_table --import <corrida> <variante>   # copia la corrida
    python3 -m scripts.ppa_table                                  # escribe reports/ppa/tabla.md
"""

from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PPA_DIR = ROOT / "reports/ppa"
ROWS = (("time_serial", 10), ("time_serial", 100), ("time_optimized", 100),
        ("frequency_serial", 10), ("frequency_serial", 100), ("frequency_optimized", 100))
KEEP = ("summary.tsv", "configuration.txt", "tool_versions.txt", "source_manifest.json",
        "run_status.txt", "read_saif.rpt", "power.rpt", "utilization.rpt", "timing_summary.rpt")
COLUMNS = ("variante", "commit", "configuración", "SQNR", "área", "Fmax", "latencia",
           "throughput", "potencia", "herramienta/log")


def read_summary(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8") as fh:
        return {row["metric"]: row["value"] for row in csv.DictReader(fh, delimiter="\t")}


def import_run(src: Path, name: str, ppa_dir: Path = PPA_DIR) -> Path:
    """Copia los reportes de una corrida Vivado completa a reports/ppa/<variante>/<reloj>mhz/."""
    if name not in {n for n, _ in ROWS}:
        raise ValueError(f"Variante desconocida: {name}")
    status = (src / "run_status.txt").read_text(encoding="utf-8").strip()
    if not status.startswith("SIMULATION_PASS TIMING_PASS"):
        raise ValueError(f"Corrida incompleta ({status}): {src}")
    period = float(read_summary(src / "summary.tsv")["clock_period_ns"])
    dest = ppa_dir / name / f"{1000 / period:g}mhz"
    dest.mkdir(parents=True, exist_ok=True)
    for f in KEEP:
        if (src / f).is_file():
            shutil.copy2(src / f, dest / f)
    # Rutas absolutas de la PC que corrió Vivado → relativas al paquete.
    config = (dest / "configuration.txt").read_text(encoding="utf-8")
    root = next(line.split("=", 1)[1] for line in config.splitlines() if line.startswith("source_root="))
    config = config.replace(root + "/", "").replace(f"source_root={root}", "source_root=<paquete>")
    (dest / "configuration.txt").write_text(config, encoding="utf-8")
    return dest


def row(name: str, mhz: int, sqnr: dict[str, float], registered: set[str],
        ppa_dir: Path = PPA_DIR) -> list[str]:
    # ponytail: SQNR del modelo fijo de la rama; vale para el RTL solo si está
    # registrado, porque el banco común exige coincidencia exacta con ese modelo (A06).
    sqnr_cell = f"{sqnr[name.split('_')[0]]:.1f} dB" if name in registered else "—"
    label = f"{name} @ {mhz} MHz"
    run = ppa_dir / name / f"{mhz}mhz"
    if not (run / "summary.tsv").is_file():
        return [label, "—", "—", sqnr_cell, *["no medida"] * 5, "—"]
    m = read_summary(run / "summary.tsv")
    commit = "—"
    if (run / "source_manifest.json").is_file():
        commit = json.loads((run / "source_manifest.json").read_text(encoding="utf-8"))["commit"][:8]
    tool = (run / "tool_versions.txt").read_text(encoding="utf-8").splitlines()[0].strip()
    period = float(m["clock_period_ns"])
    energy = f"{float(m['energy_dynamic_nj_per_sample']):.3g} nJ/muestra"
    if float(m["dynamic_power_w"]) == 0:
        # Vivado redondea a 1 mW: 0.000 W solo acota la dinámica a < 0.5 mW.
        bound = 0.0005 / float(m["throughput_samples_per_second"]) * 1e9
        energy = f"< {bound:.2g} nJ/muestra"
    return [
        label,
        f"`{commit}`",
        f"{m['part']}, OOC, {1000 / period:g} MHz, timing {m['timing_status']}",
        sqnr_cell,
        f"{m['lut']} LUT / {m['ff']} FF / {m['dsp']} DSP / {m['bram_tiles']} BRAM",
        f"{float(m['fmax_estimate_mhz']):.1f} MHz (WNS {float(m['internal_wns_ns']):.3f} ns)",
        f"{m['latency_cycles']} ciclos",
        f"{float(m['throughput_samples_per_second']) / 1e6:.4g} Mmuestras/s",
        f"{m['dynamic_power_w']} W din. / {m['static_power_w']} W est. / "
        f"{energy} "
        f"(SAIF {m['saif_review'].split(' filas')[0]} redes)",
        f"{tool}; [corrida]({name}/{mhz}mhz/)",
    ]


def table(sqnr: dict[str, float], registered: set[str], ppa_dir: Path = PPA_DIR) -> str:
    lines = ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    lines += ["| " + " | ".join(row(name, mhz, sqnr, registered, ppa_dir)) + " |" for name, mhz in ROWS]
    return "\n".join(lines) + "\n"


def main() -> int:
    if sys.argv[1:2] == ["--import"]:
        print(f"Corrida: {import_run(Path(sys.argv[2]), sys.argv[3]).relative_to(ROOT)}")
        return 0
    from model.fixed_point import Format, evaluate
    from scripts.validate_project import load_targets

    r = evaluate(Format())
    sqnr = {"time": r["tiempo"], "frequency": r["frecuencia"]}
    out = PPA_DIR / "tabla.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "# Tabla PPA\n\n"
        "Generada con `python3 -m scripts.ppa_table`; no editar a mano. Cada fila sale de "
        "`reports/ppa/<variante>/<reloj>mhz/summary.tsv` (flujo Vivado de C02). El reloj oficial es "
        "10 MHz para las seriales y 100 MHz para las optimizadas; las seriales a 100 MHz son un dato "
        "adicional para separar la mejora de la arquitectura de la del reloj (#49). SQNR mínima del modelo fijo "
        "de cada rama, semillas 0–4 × 1024 símbolos (A04), solo para variantes registradas en "
        "`config/rtl_targets.json` (coinciden palabra por palabra con ese modelo). La potencia estática es del dispositivo "
        "completo. Vivado informa la dinámica con resolución de 1 mW, así que la energía por muestra "
        "de corridas con pocos mW de dinámica no distingue diferencias menores a ±0,5 mW; además, "
        "la cobertura SAIF es parcial (redes anotadas / total).\n\n"
        + table(sqnr, {t["name"] for t in load_targets()}),
        encoding="utf-8",
    )
    print(f"Tabla: {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
