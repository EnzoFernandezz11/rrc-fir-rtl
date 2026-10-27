#!/usr/bin/env python3
"""A07: tabla PPA de las cuatro variantes (SKY130) y anexo FPGA (Vivado / Artix-7).

La tabla principal lee la evidencia SKY130 versionada en `reports/ppa/<variante>/sky130/`
(D05/D06, acuerdo del 26/10). Setup/hold y restricciones eléctricas se evalúan en los
nueve corners y se informan por separado; el throughput queda condicionado solo si
setup/hold falla, porque D05 define el cumplimiento del reloj por setup/hold.

En el anexo FPGA, cada corrida medida tiene su carpeta `reports/ppa/<variante>/<reloj>mhz/` con los
reportes chicos que deja el flujo Vivado de C02 (`scripts/ppa/vivado/run.tcl`).
Una fila sin carpeta figura como «no medida» (verificacion-y-ppa.md#ppa). Las
seriales se miden a 10 MHz (oficial) y a 100 MHz (dato adicional, #49).

    python3 -m scripts.ppa_table --import <corrida> <variante>   # copia la corrida
    python3 -m scripts.ppa_table                                  # escribe reports/ppa/tabla.md
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PPA_DIR = ROOT / "reports/ppa"
ROWS = (("time_serial", 10), ("time_serial", 100), ("time_optimized", 100),
        ("frequency_serial", 10), ("frequency_serial", 100), ("frequency_optimized", 100))
KEEP = ("summary.tsv", "configuration.txt", "tool_versions.txt", "source_manifest.json",
        "run_status.txt", "read_saif.rpt", "power.rpt", "utilization.rpt", "timing_summary.rpt")
# (variante, escenario): target es el reloj objetivo; common, 10 MHz para todas.
SKY130_ROWS = (("time_serial", "target"), ("time_optimized", "target"), ("time_optimized", "common"),
               ("frequency_serial", "target"), ("frequency_optimized", "target"),
               ("frequency_optimized", "common"))
SKY130_COLUMNS = ("variante", "SQNR", "área celdas / core", "setup/hold (peor corner)",
                  "eléctrico (máx. por corner)", "Fmax (peor corner)", "latencia", "throughput",
                  "potencia / energía", "evidencia")
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


def sky130_row(name: str, scenario: str, sqnr: dict[str, float], registered: set[str],
               ppa_dir: Path = PPA_DIR) -> list[str]:
    run = ppa_dir / name / "sky130"
    sqnr_cell = f"{sqnr[name.split('_')[0]]:.1f} dB" if name in registered else "—"
    if not (run / "physical_metrics.json").is_file():
        return [f"{name} @ objetivo", sqnr_cell, *["no medida"] * 7, "—"]
    load = lambda f: json.loads((run / f).read_text(encoding="utf-8"))
    physical, local, manifest = load("physical_metrics.json"), load("local_metrics.json"), load("manifest.json")
    s = physical["scenarios"][scenario]
    timing = s["timing"]
    if len(timing) != 9:
        raise ValueError(f"{name}/{scenario}: se esperaban 9 corners, hay {len(timing)}")
    worst = lambda key: min(timing.items(), key=lambda kv: kv[1][key])
    setup_corner, setup = worst("setup_ws_ns")
    hold_corner, hold = worst("hold_ws_ns")
    setup_hold = all(t["setup_violations"] == 0 and t["hold_violations"] == 0
                     and t["setup_ws_ns"] >= 0 and t["hold_ws_ns"] >= 0 for t in timing.values())
    electrical = {k: max(t[f"max_{k}_violations"] for t in timing.values()) for k in ("slew", "cap", "fanout")}
    # Las corridas más viejas no traen los veredictos; si los traen, deben coincidir.
    for key, value in (("setup_hold_pass", setup_hold), ("electrical_constraints_pass", not any(electrical.values()))):
        if s.get(key, value) != value:
            raise ValueError(f"{name}/{scenario}: {key} no coincide con los nueve corners")
    # La corrida C02 es anterior a guardar Fmax en el JSON; queda en el clock.rpt publicado.
    sta = load("evidence.json").get("scenario_directories", {}).get(scenario, scenario)
    fmaxes = {c: t["fmax_estimate_mhz"] or float(re.search(
        r"\bfmax\s*=\s*(\S+)", (run / "sta" / sta / c / "clock.rpt").read_text(encoding="utf-8"))[1])
        for c, t in timing.items()}
    fmax_corner = min(fmaxes, key=fmaxes.get)
    period = float(s["clock_period_ns"])
    # ponytail: el benchmark corre al reloj objetivo; a otro reloj se escala con el período,
    # porque latencia e intervalo están en ciclos.
    throughput = local["throughput_samples_per_second"] * float(local["clock_period_ns"]) / period
    power = s["power"]
    areas = physical["areas"]
    verdict = lambda ok: "PASS" if ok else "FAIL"
    return [
        f"{name} @ {1000 / period:g} MHz",
        sqnr_cell,
        f"{areas['final_cell_area_um2']:,.0f} / {areas['core_area_um2']:,.0f} µm²".replace(",", " "),
        f"{verdict(setup_hold)}: setup {setup['setup_ws_ns']:+.2f} ns ({setup_corner}), "
        f"hold {hold['hold_ws_ns']:+.2f} ns ({hold_corner})",
        f"{verdict(not any(electrical.values()))}: slew {electrical['slew']} / cap {electrical['cap']} / "
        f"fanout {electrical['fanout']}",
        f"{fmaxes[fmax_corner]:.1f} MHz ({fmax_corner})",
        f"{local['latency_cycles']} ciclo{'' if local['latency_cycles'] == 1 else 's'} "
        f"({local['latency_cycles'] * period:g} ns)",
        f"{throughput / 1e6:.4g} Mmuestras/s" + ("" if setup_hold else " (condicionado: setup/hold FAIL)"),
        f"{power['total_w'] * 1e3:.3g} mW / {power['total_energy_j'] * 1e9:.3g} nJ/muestra",
        f"`{manifest['commit'][:8]}`; [evidencia]({name}/sky130/evidence.json)",
    ]


def sky130_table(sqnr: dict[str, float], registered: set[str], ppa_dir: Path = PPA_DIR) -> str:
    lines = ["| " + " | ".join(SKY130_COLUMNS) + " |", "|" + "---|" * len(SKY130_COLUMNS)]
    lines += ["| " + " | ".join(sky130_row(n, s, sqnr, registered, ppa_dir)) + " |" for n, s in SKY130_ROWS]
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
    registered = {t["name"] for t in load_targets()}
    out.write_text(
        "# Tabla PPA\n\n"
        "Generada con `python3 -m scripts.ppa_table`; no editar a mano.\n\n"
        "## SKY130 HD (comparación principal)\n\n"
        "Método común D05/D06 (acuerdo del 26/10): OpenLane 2 + SKY130 HD hasta STA post-ruteo con SPEF "
        "en nueve corners PVT/RC; potencia OpenSTA con VCD funcional de la netlist final, SPEF nominal y "
        "Liberty TT/25 °C/1,8 V; benchmark QPSK 2×, semilla 1, 2048 muestras. Cada fila sale de "
        "`reports/ppa/<variante>/sky130/` (ver `evidence.json`, con la corrida de origen y SHA256). "
        "El reloj objetivo es 10 MHz para las seriales y 100 MHz para las optimizadas; las optimizadas "
        "a 10 MHz son el escenario común, para separar la mejora de la arquitectura de la del reloj.\n\n"
        "Setup/hold PASS exige slack no negativo y cero violaciones en los nueve corners; se muestra el "
        "peor slack de cada chequeo con su corner. Las restricciones eléctricas (slew, capacitancia, "
        "fanout; máximo de violaciones entre corners) tienen veredicto propio. Fmax es la estimación "
        "registro a registro del peor corner. El throughput se marca condicionado cuando setup/hold "
        "falla. SQNR mínima del modelo fijo de cada rama, semillas 0–4 × 1024 símbolos (A04), solo "
        "para variantes registradas en `config/rtl_targets.json`. La actividad funcional sin retardos "
        "no captura todos los glitches.\n\n"
        + sky130_table(sqnr, registered)
        + "\n## Anexo: referencia FPGA (Vivado / Artix-7)\n\n"
        "Corridas medidas antes del acuerdo SKY130; se conservan para contrastar tendencias entre FPGA "
        "y ASIC. Sus LUT, timing y potencia no se convierten a cifras ASIC. Cada fila sale de "
        "`reports/ppa/<variante>/<reloj>mhz/summary.tsv` (flujo Vivado de C02). El reloj oficial es "
        "10 MHz para las seriales y 100 MHz para las optimizadas; las seriales a 100 MHz son un dato "
        "adicional para separar la mejora de la arquitectura de la del reloj (#49). SQNR mínima del modelo fijo "
        "de cada rama, semillas 0–4 × 1024 símbolos (A04), solo para variantes registradas en "
        "`config/rtl_targets.json` (coinciden palabra por palabra con ese modelo). La potencia estática es del dispositivo "
        "completo. Vivado informa la dinámica con resolución de 1 mW, así que la energía por muestra "
        "de corridas con pocos mW de dinámica no distingue diferencias menores a ±0,5 mW; además, "
        "la cobertura SAIF es parcial (redes anotadas / total). frequency_optimized se midió además con "
        "`set_input_delay` T/2 y `set_output_delay` 0 (ver su `clock.xdc`) y su SAIF sale de la netlist "
        "implementada sin SDF, porque la simulación SDF da salidas obsoletas en CARRY4 (#56); esa actividad "
        "no tiene glitches, así que su potencia dinámica puede estar algo subestimada.\n\n"
        + table(sqnr, registered),
        encoding="utf-8",
    )
    print(f"Tabla: {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
