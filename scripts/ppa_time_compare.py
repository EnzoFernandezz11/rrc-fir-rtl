"""Tablas y Mermaid B02/B04 a partir de evidencia JSON; no ejecuta síntesis.

Adaptación de scripts/ppa_compare.py (rama e/c04-rtl-optimized, f1fe770) a las
variantes temporales: el throughput sostenido es por muestra (II), no por bloque de ocho.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess

from scripts.ppa_time import ROOT, REPORT, LIBRARY, evidence_dir, sha256, sustained_sps, write_json

# clave, etiqueta, unidad, preferencia. None: no representa una mejora por sí sola.
METRICS = [
    ("input_samples", "Muestras aceptadas", "muestras", None),
    ("output_samples", "Muestras exactas", "muestras", None),
    ("clock_mhz", "Reloj configurado", "MHz", None),
    ("latency_cycles", "Latencia", "ciclos", "min"),
    ("block_cycles", "Intervalo entre muestras (II)", "ciclos", "min"),
    ("active_cycles", "Ciclos activos del benchmark", "ciclos", "min"),
    ("latency_ns", "Latencia temporal", "ns", "min"),
    ("sustained_sps", "Throughput sostenido", "muestras/s", "max"),
    ("effective_sps", "Throughput efectivo", "muestras/s", "max"),
    ("cells", "Celdas de síntesis", "celdas", "min"),
    ("flip_flops", "Flip-flops de síntesis", "FF", "min"),
    ("combinational_cells", "Celdas combinacionales de síntesis", "celdas", "min"),
    ("cell_area_um2", "Área de celdas de síntesis", "µm²", "min"),
    ("final_cell_area_um2", "Área final de celdas", "µm²", "min"),
    ("core_area_um2", "Área del núcleo", "µm²", "min"),
    ("die_area_um2", "Área del die", "µm²", "min"),
    ("internal_w", "Potencia interna", "W", "min"),
    ("switching_w", "Potencia de conmutación", "W", "min"),
    ("dynamic_w", "Potencia dinámica", "W", "min"),
    ("leakage_w", "Leakage del núcleo", "W", "min"),
    ("total_w", "Potencia total", "W", "min"),
    ("dynamic_energy_j", "Energía dinámica por muestra", "J/muestra", "min"),
    ("total_energy_j", "Energía total por muestra", "J/muestra", "min"),
    ("activity_coverage_pct", "Pines con actividad VCD/reloj/constante", "%", "max"),
]


def score_pair(a: float, b: float, preference: str) -> list[float]:
    if not all(math.isfinite(x) and x >= 0 for x in (a, b)):
        raise ValueError("El radar requiere valores finitos no negativos")
    if a == b:
        return [100.0, 100.0]
    if preference == "max":
        return [100 * x / max(a, b) for x in (a, b)]
    if preference != "min":
        raise ValueError("Preferencia radar desconocida")
    return [100.0 if x == 0 else 100 * min(a, b) / x for x in (a, b)]


def load_run(directory: Path, target: str) -> dict:
    directory = directory.resolve()
    m = json.loads((directory / "manifest.json").read_text())
    if m["status"] not in ("local_pass", "physical_complete"):
        raise ValueError(f"Corrida incompleta: {directory}")
    if m["config"].get("target") != target:
        raise ValueError(f"Se esperaba {target}: {directory}")
    if m["library"]["name"] != LIBRARY:
        raise ValueError("La comparación requiere SKY130 HD TT")
    for name, digest in m.get("artifacts_sha256", {}).items():
        artifact = (directory / name).resolve()
        if not artifact.is_relative_to(directory):
            raise ValueError(f"Artefacto fuera de corrida: {name}")
        if sha256(artifact) != digest:
            raise ValueError(f"Artefacto alterado: {name}")
    if sha256(directory / "ppa_vectors.txt") != m["vectors_sha256"]:
        raise ValueError(f"Vectores alterados: {directory}")
    if sha256(directory / (m["library"]["name"] + ".lib")) != m["library"]["sha256"]:
        raise ValueError(f"Liberty alterada: {directory}")
    rtl = json.loads((directory / "local_metrics.json").read_text())
    gate = json.loads((directory / "gate_metrics.json").read_text())
    if not rtl.get("passed") or not gate.get("passed") or rtl["output_samples"] != 2048 or rtl["input_samples"] != 2048:
        raise ValueError(f"Benchmark incompleto: {directory}")
    if gate != rtl:
        raise ValueError(f"Netlist y RTL difieren: {directory}")
    v = {**json.loads((directory / "resources.json").read_text()), **rtl}
    period = rtl["clock_period_ns"]
    v.update(clock_mhz=1000 / period, latency_ns=rtl["latency_cycles"] * period,
             sustained_sps=sustained_sps(rtl["block_cycles"], period),
             effective_sps=rtl["throughput_samples_per_second"])
    physical = None
    if m["status"] == "physical_complete":
        physical = json.loads((directory / "physical_metrics.json").read_text())
        for scenario in physical.get("scenarios", {}).values():
            power = scenario.get("power", {})
            if "dynamic_w" not in power and "internal_w" in power and "switching_w" in power:
                power["dynamic_w"] = power["internal_w"] + power["switching_w"]
        v.update(physical["areas"])
        v.update(physical["scenarios"]["target"]["power"])
    for key, _, _, _ in METRICS:
        v.setdefault(key, None)
        x = v.get(key)
        if x is not None and (isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)):
            raise ValueError(f"Métrica no finita o inválida: {key}")
    evidence = {name: sha256(directory / name) for name in
                ("manifest.json", "local_metrics.json", "gate_metrics.json", "resources.json")}
    if physical:
        evidence["physical_metrics.json"] = sha256(directory / "physical_metrics.json")
    return {"directory": directory, "manifest": m, "values": v, "physical": physical, "evidence": evidence}


def check_compatible(a: dict, b: dict) -> None:
    ma, mb = a["manifest"], b["manifest"]
    if ma["status"] != mb["status"]:
        raise ValueError("No comparar etapas distintas: completar ambas corridas físicas o usar ambas lógicas")
    if ma["library"]["sha256"] != mb["library"]["sha256"] or ma["tools"] != mb["tools"]:
        raise ValueError("Biblioteca o versiones de herramientas incompatibles")
    for field in ("technology", "format", "seed", "symbols", "samples", "input_available", "output_ready"):
        if ma["config"].get(field) != mb["config"].get(field):
            raise ValueError(f"Configuración incompatible: {field}")
    if ma["vectors_sha256"] != mb["vectors_sha256"]:
        raise ValueError("Benchmark incompatible")
    if a["physical"] and ma["physical_method"] != mb["physical_method"]:
        raise ValueError("Métodos físicos incompatibles")


def fmt(value: float | None) -> str:
    if value is None:
        return "No medida"
    if value == 0:
        return "0"
    if abs(value) < .001 or abs(value) >= 1e7:
        return f"{value:.6g}"
    return f"{value:.6f}".rstrip("0").rstrip(".")


def bar(label: str, unit: str, a: float, b: float) -> str:
    if unit in ("W", "J/muestra"):
        factor, unit = (1e3, "mW") if unit == "W" else (1e9, "nJ/muestra")
        a, b = a * factor, b * factor
    low, high = min(0, a, b), max(0, a, b)
    if high == low:
        high = 1
    return (f'xychart-beta\n    title "{label}"\n    x-axis ["B02", "B04"]\n'
            f'    y-axis "{unit}" {low:.12f} --> {high * 1.05 if high > 0 else 0:.12f}\n'
            f'    bar [{a:.12f}, {b:.12f}]\n')


def corner_chart(scenario: str, metric: str, a: dict, b: dict) -> str | None:
    corners = list(a)
    aa, bb = [a[c].get(metric) for c in corners], [b[c].get(metric) for c in corners]
    if any(x is None for x in aa + bb):
        return None
    labels = [c.split("_")[0] + "-" + c.split("_")[1].upper() for c in corners]
    low, high = min(0, *aa, *bb), max(0, *aa, *bb)
    high = high * 1.05 if high > low else 1
    unit = "MHz" if metric.endswith("mhz") else "ns"
    return ("---\nconfig:\n  themeVariables:\n    xyChart:\n      plotColorPalette: '#2563eb, #ea580c'\n---\n"
            f'xychart-beta\n    title "{metric}: {scenario}"\n'
            + '    x-axis [' + ", ".join(f'"{x}"' for x in labels) + "]\n"
            + f'    y-axis "{unit}" {low:.12f} --> {high:.12f}\n'
            + "    line [" + ", ".join(f"{x:.12f}" for x in aa) + "]\n"
            + "    line [" + ", ".join(f"{x:.12f}" for x in bb) + "]\n")


def radar(title: str, keys: list[str], av: dict, bv: dict) -> str | None:
    specs = {key: (label, preference) for key, label, _, preference in METRICS}
    keys = [key for key in keys if av.get(key) is not None and bv.get(key) is not None]
    if len(keys) < 3:
        return None
    scores = [score_pair(av[key], bv[key], specs[key][1]) for key in keys]
    labels = {"cell_area_um2": "Área síntesis", "flip_flops": "FF", "latency_cycles": "Latencia",
              "block_cycles": "II", "final_cell_area_um2": "Área final", "latency_ns": "Latencia",
              "effective_sps": "Throughput", "total_energy_j": "Energía/muestra"}
    axes = ", ".join(f'a{i}["{labels.get(key, specs[key][0])}"]' for i, key in enumerate(keys))
    return ("---\nconfig:\n  theme: base\n  themeVariables:\n    cScale0: '#2563eb'\n"
            "    cScale1: '#ea580c'\n    fontSize: 18px\n    radar:\n      curveOpacity: 0.25\n      axisLabelFontSize: 16px\n      legendFontSize: 16px\n"
            "  radar:\n    width: 900\n    height: 700\n    axisScaleFactor: 1\n"
            "    marginTop: 60\n    marginBottom: 60\n    marginLeft: 100\n    marginRight: 100\n"
            "    curveTension: 0\n---\n"
            f"radar-beta\n    title {title}\n    axis {axes}\n"
            + '    curve b02["B02"]{' + ", ".join(f"{x[0]:.5f}" for x in scores) + "}\n"
            + '    curve b04["B04"]{' + ", ".join(f"{x[1]:.5f}" for x in scores) + "}\n"
            + "    min 0\n    max 100\n    ticks 5\n    showLegend true\n")


def scenario_status(scenario: dict) -> tuple[bool, bool, bool]:
    """Return setup/hold, electrical/constraints and global status, including legacy rows."""
    timing = scenario.get("timing", {})
    rows = list(timing.values())
    setup = scenario.get("setup_hold_pass")
    if setup is None and rows:
        setup = all(r.get("setup_ws_ns", -1) >= 0 and r.get("hold_ws_ns", -1) >= 0
                    and r.get("setup_violations", 1) == 0 and r.get("hold_violations", 1) == 0
                    for r in rows)
    electrical = scenario.get("electrical_constraints_pass")
    if electrical is None and rows:
        electrical = all(r.get("constraint_warnings", 1) == 0 and r.get("unconstrained_endpoints", 1) == 0
                         and r.get("unannotated_routed_nets", 1) == 0
                         and r.get("max_slew_violations", 1) == 0 and r.get("max_cap_violations", 1) == 0
                         and r.get("max_fanout_violations", 1) == 0 for r in rows)
    setup, electrical = bool(setup), bool(electrical)
    return setup, electrical, bool(scenario.get("timing_pass", setup and electrical))


def rebase_links(text: str, old_base: Path, new_base: Path) -> str:
    """Reescribe los enlaces relativos de Markdown para leerlos desde otra carpeta."""
    def rebase(match: re.Match) -> str:
        target = match.group(1)
        if re.match(r"[a-z]+:|#|/", target):
            return match.group(0)
        return "](" + Path(os.path.relpath(old_base / target, new_base)).as_posix() + ")"
    return re.sub(r"\]\(([^)\s]+)\)", rebase, text)


def comparison_document(a: dict, b: dict, output: Path, render: bool = False,
                        link_base: Path = REPORT.parent) -> tuple[str, dict]:
    check_compatible(a, b)
    av, bv = a["values"], b["values"]
    charts = {}
    link = lambda p: Path(os.path.relpath(p, link_base)).as_posix()
    text = ("## Comparación B02 / B04\n\n"
            f"Corridas: [B02]({link(a.get('published', a['directory']) / 'manifest.json')}) / "
            f"[B04]({link(b.get('published', b['directory']) / 'manifest.json')}). "
            "Benchmark: QPSK 2×, semilla 1, 2048 muestras exactas.\n\n"
            "Las diferencias porcentuales son (B04/B02 − 1) × 100; "
            "un signo positivo no siempre significa mejora.\n\n")
    physical = a["physical"] is not None
    text += ("Medición física; revisar PASS/FAIL por corner antes de interpretar las tasas.\n\n"
             if physical else "Síntesis lógica y ciclos RTL. Los relojes de 10/100 MHz son supuestos, "
             "**sin timing físico demostrado**. Potencia y energía no medidas.\n\n")
    text += "| Métrica | Unidad | B02 | B04 | Cambio B04/B02 | Condición / procedencia |\n|---|---|---:|---:|---:|---|\n"
    for key, label, unit, _ in METRICS:
        x, y = av.get(key), bv.get(key)
        delta = "—" if x is None or y is None or x == 0 else fmt(100 * (y / x - 1)) + " %"
        source = ("Objetivos propios, 10/100 MHz; hipotético si timing FAIL" if key in
                  ("clock_mhz", "latency_ns", "sustained_sps", "effective_sps") else
                  "Netlist final / SPEF / VCD, TT; objetivos propios" if key.endswith(("_w", "_j")) else
                  "physical_metrics.json" if key.startswith(("final_", "core_", "die_", "activity_"))
                  else "local_metrics.json / resources.json")
        text += f"| {label} | {unit} | {fmt(x)} | {fmt(y)} | {delta} | {source} |\n"

    def add_chart(name: str, code: str) -> str:
        charts[name] = code
        source_path = output / (name + ".mmd")
        source_path.write_text(code, encoding="utf-8")
        fence = chr(96) * 3
        result = f"\n{fence}mermaid\n{code}{fence}\n\n[Fuente Mermaid]({link(source_path)})"
        if render:
            svg = source_path.with_suffix(".svg")
            subprocess.run(["npm", "exec", "--yes", "--package=@mermaid-js/mermaid-cli@11.6.0",
                            "--", "mmdc", "-i", str(source_path), "-o", str(svg),
                            "-p", str(ROOT / "scripts/ppa/openlane/puppeteer.json")], check=True)
            result += f" · [SVG compatible]({link(svg)})"
        return result + "\n"

    text += ("\n### Radares normalizados\n\n100 es el mejor valor **de esta pareja** en cada eje. "
             "Más afuera es mejor. Beneficios: 100 × valor/máximo; costos: 100 × mínimo/valor. "
             "Empate en cero: ambos 100; costo cero frente a costo positivo: 100 frente a 0. "
             "La superficie no es una puntuación global. Valores originales en la tabla.\n")
    code = radar("Arquitectura y síntesis",
                 ["cell_area_um2", "flip_flops", "latency_cycles", "block_cycles"], av, bv)
    if code:
        text += add_chart("radar-arquitectura", code)
    else:
        text += "\nRadar pendiente: se requieren al menos tres métricas comparables.\n"
    text += "\n### Barras: objetivos propios\n\nCada gráfico usa una unidad; menor costo favorece la variante más pequeña.\n"
    for key, label, unit, _ in METRICS:
        if key in ("input_samples", "output_samples", "clock_mhz"):
            continue
        x, y = av.get(key), bv.get(key)
        if x is not None and y is not None:
            text += add_chart(key, bar(label, unit, x, y))
            text += f"\n| {unit} | B02 | B04 |\n|---|---:|---:|\n| {label} | {fmt(x)} | {fmt(y)} |\n"
    text += "\n### Reloj común: 10 MHz\n\n"
    common = []
    common_scenarios = [r["physical"]["scenarios"].get("common", {}) for r in (a, b)] if physical else []
    if physical and all(common_scenarios):
        for run, m in zip((a, b), common_scenarios):
            common.append({**run["values"], **m.get("power", {}),
                           "latency_ns": run["values"]["latency_cycles"] * 100,
                           "effective_sps": 2048e7 / run["values"]["active_cycles"]
                           if run["values"].get("active_cycles") else None,
                           "sustained_sps": sustained_sps(run["values"]["block_cycles"], 100)
                           if run["values"].get("block_cycles") else None})
        text += "Potencia común medida por variante (TT/25 °C/1,8 V), aunque el estado global no habilite gráficas:\n\n"
        text += "| Métrica | Unidad | B02 | B04 |\n|---|---|---:|---:|\n"
        for key in ("internal_w", "switching_w", "dynamic_w", "leakage_w", "total_w",
                    "dynamic_energy_j", "total_energy_j"):
            x, y = common[0].get(key), common[1].get(key)
            unit = "W" if key.endswith("_w") else "J/muestra"
            text += f"| {key} | {unit} | {fmt(x)} | {fmt(y)} |\n"
    if not physical or not all(scenario_status(r["physical"]["scenarios"].get("common", {}))[2] for r in (a, b)):
        text += "Pendiente: ambas implementaciones deben demostrar timing a 10 MHz. No se grafican datos físicos supuestos.\n"
    else:
        text += "Mismo layout de cada variante y reloj común; potencia funcional sin retardos, TT/25 °C/1,8 V.\n"
        code = radar("PPA físico a 10 MHz", ["final_cell_area_um2", "latency_ns", "effective_sps", "total_energy_j"], *common)
        if code:
            text += add_chart("radar-ppa-comun", code)
        for key, label, unit, _ in METRICS:
            if key in ("latency_ns", "effective_sps", "sustained_sps") or key.endswith(("_w", "_j")):
                x, y = common[0].get(key), common[1].get(key)
                if x is not None and y is not None:
                    text += add_chart("common-" + key, bar(label + " a 10 MHz", unit, x, y))
                    text += f"\nB02: {fmt(x)} {unit}; B04: {fmt(y)} {unit}.\n"
    if physical:
        text += "\n### Timing por corner\n\n"
        for scenario in ("target", "common"):
            if not all(scenario in r["physical"]["scenarios"] for r in (a, b)):
                continue
            aa, bb = [r["physical"]["scenarios"][scenario] for r in (a, b)]
            statuses = [scenario_status(x) for x in (aa, bb)]
            text += f"\nEscenario {scenario}: B02 setup/hold **{'PASS' if statuses[0][0] else 'FAIL'}**, eléctrico/restricciones **{'PASS' if statuses[0][1] else 'FAIL'}**, global **{'PASS' if statuses[0][2] else 'FAIL'}**; B04 setup/hold **{'PASS' if statuses[1][0] else 'FAIL'}**, eléctrico/restricciones **{'PASS' if statuses[1][1] else 'FAIL'}**, global **{'PASS' if statuses[1][2] else 'FAIL'}**.\n\n"
            text += "| Estado | B02 | B04 |\n|---|---|---|\n"
            for label, index in (("Setup/hold", 0), ("Eléctrico/restricciones", 1), ("Global", 2)):
                text += f"| {label} | {'PASS' if statuses[0][index] else 'FAIL'} | {'PASS' if statuses[1][index] else 'FAIL'} |\n"
            text += "\n"
            text += "| Corner | Métrica | B02 | B04 |\n|---|---|---:|---:|\n"
            if aa["timing"].keys() != bb["timing"].keys():
                raise ValueError("Corners incompatibles")
            for corner in aa["timing"]:
                for key, x in aa["timing"][corner].items():
                    text += f"| {corner} | {key} | {fmt(x)} | {fmt(bb['timing'][corner][key])} |\n"
            text += "\nEscenarios discretos de proceso/interconexión: **B02 azul**, **B04 naranja**. Las líneas no interpolan corners físicos nuevos.\n"
            for key in ("setup_ws_ns", "hold_ws_ns", "setup_tns_ns", "hold_tns_ns", "fmax_estimate_mhz"):
                code = corner_chart(scenario, key, aa["timing"], bb["timing"])
                if code:
                    text += add_chart(f"{scenario}-{key}", code)
    return text, {"b02": str(a["directory"]), "b04": str(b["directory"]),
                  "stage": "physical" if physical else "logical", "values": {"B02": av, "B04": bv},
                  "evidence_sha256": {"B02": a.get("evidence"), "B04": b.get("evidence")},
                  "charts": list(charts), "renderer": "@mermaid-js/mermaid-cli@11.6.0" if render else None}


def compare(b02: Path, b04: Path, render: bool = False, report: Path = REPORT) -> Path:
    a, b = load_run(b02, "time_serial"), load_run(b04, "time_optimized")
    check_compatible(a, b)
    original = report.read_text()
    for run, arch in ((a, "serial"), (b, "optimized")):
        start, end = f"<!-- {arch}-runs:start -->", f"<!-- {arch}-runs:end -->"
        if original.count(start) != 1 or original.count(end) != 1 or original.index(start) > original.index(end):
            raise ValueError(f"Marcadores de corrida inválidos: {arch}")
        section = original.split(start)[1].split(end)[0]
        # Adaptación: enlazar la copia versionada, que debe ser de esta misma corrida.
        published = evidence_dir(run["manifest"]["config"]["target"], report)
        if json.loads((published / "evidence.json").read_text())["run"] != run["directory"].name:
            raise ValueError(f"La evidencia publicada no es de {run['directory'].name}: {published}")
        run["published"] = published
        if run["directory"].name not in section:
            raise ValueError(f"La corrida {run['directory'].name} no es la publicada para {arch}")
    identity = hashlib.sha256(json.dumps([r["evidence"] for r in (a, b)], sort_keys=True).encode()).hexdigest()[:16]
    # Adaptación: build/ no se versiona; la comparación vive junto al reporte.
    output = report.parent / "time_comparison"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    result, data = comparison_document(a, b, output, render, link_base=report.parent)
    write_json(output / "comparison.json", {**data, "identity": identity})
    # Adaptación: el mismo texto va en time.md y en time_comparison/; cada copia enlaza desde su carpeta.
    (output / "comparison.md").write_text(rebase_links(result, report.parent, output))
    start, end = "<!-- comparison:start -->", "<!-- comparison:end -->"
    replacement = f"{start}\n\n{result}\n{end}"
    if start in original:
        if original.count(start) != 1 or original.count(end) != 1 or original.index(end) < original.index(start):
            raise ValueError("Marcadores de comparación inválidos")
        updated = re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: replacement, original, flags=re.S)
    else:
        marker = "## Referencia histórica preservada"
        if marker not in original:
            raise ValueError("Falta frontera de referencia histórica")
        updated = original.replace(marker, replacement + "\n\n" + marker, 1)
    temporary = report.with_suffix(".md.tmp")
    temporary.write_text(updated, encoding="utf-8")
    temporary.replace(report)
    print(f"Comparación: {output}")
    return output
