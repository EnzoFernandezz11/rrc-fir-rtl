#!/usr/bin/env python3
"""Medición ASIC SKY130 de las variantes temporales (B02/B04).

Adaptación del flujo de frecuencia de C02/C04 (scripts/ppa.py de la rama
e/c04-rtl-optimized): mismas herramientas, biblioteca, benchmark y método.
Cambian los targets, los vectores (dominio temporal), el reporte y el
throughput sostenido, que en tiempo es por muestra y no por bloque de ocho.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/ppa/time.md"
GUIDE = ROOT / "docs/ppa-tiempo.md"
TARGETS = ("time_serial", "time_optimized")
# Bancos PPA por target: el serial es el de A07, el optimizado el de B04.
BENCHES = {"time_serial": "tb_fir_time_ppa", "time_optimized": "tb_fir_time_systolic_ppa"}
CONFIG = {
    "technology": "SKY130", "flow": "standard_cell_synthesis", "format": "A04",
    "seed": 1, "symbols": 1024, "samples": 2048,
    "input_available": True, "output_ready": True,
    "vectors": "modelo fijo A04; dominio temporal",
}

LIBRARY = "sky130_fd_sc_hd__tt_025C_1v80"
# build/ no se versiona: el reporte enlaza una copia liviana de la última corrida
# en reports/ppa/<target>/sky130/. Quedan afuera VCD, netlists, SPEF, ODB, la
# Liberty y los reportes de caminos completos; se regeneran con el comando.
EVIDENCE = ("manifest.json", "local_metrics.json", "gate_metrics.json", "resources.json",
            "cells.json", "synthesis.ys", "logs/benchmark.log",
            "logs/gate_benchmark.log", "physical_metrics.json", "openlane-target.json",
            "openlane-common.json", "*/metrics.json", "*/power.sdc", "*/power.log",
            "runs/*/*-openroad-stapostpnr/summary.rpt", "runs/*/*-openroad-stapostpnr/*/*.rpt")
STA_REPORTS = {"summary.rpt", "checks.rpt", "clock.rpt", "power.rpt", "violator_list.rpt",
               "skew.max.rpt", "skew.min.rpt", "ws.max.rpt", "ws.min.rpt",
               "wns.max.rpt", "wns.min.rpt", "tns.max.rpt", "tns.min.rpt"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(command: list[str], log: Path, timeout: float | None = None) -> None:
    print(f"$ {' '.join(command)}", flush=True)
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(command, cwd=ROOT, stdout=output,
                                stderr=subprocess.STDOUT, check=False, timeout=timeout)
    if result.returncode:
        print("\n".join(log.read_text(errors="replace").splitlines()[-40:]))
        raise RuntimeError(f"{command[0]} falló ({result.returncode}); ver {log}")


def capture(command: list[str]) -> str:
    return subprocess.check_output(command, cwd=ROOT, stderr=subprocess.STDOUT,
                                   text=True).strip()


def sky130_library(raw: str | None = None) -> Path:
    selected = raw or os.environ.get("SKY130_LIB")
    if selected:
        path = Path(selected).expanduser().resolve()
    else:
        root = Path.home() / ".volare"
        suffix = f"sky130A/libs.ref/sky130_fd_sc_hd/lib/{LIBRARY}.lib"
        candidates = {p.resolve() for p in (root / "volare/sky130/versions").glob(f"*/{suffix}")}
        if (root / suffix).is_file():
            candidates.add((root / suffix).resolve())
        if len(candidates) != 1:
            raise ValueError("Indicar --liberty o SKY130_LIB: se requiere una biblioteca SKY130 HD TT única")
        path = candidates.pop()
    if not path.is_file() or path.name != f"{LIBRARY}.lib":
        raise ValueError(f"Se requiere el archivo {LIBRARY}.lib: {path}")
    return path


def liberty_flops(library: Path) -> set[str]:
    cells = re.split(r'\bcell\s*\(\s*"?([\w]+)"?\s*\)\s*\{', library.read_text())
    return {name for name, body in zip(cells[1::2], cells[2::2])
            if re.search(r"\bff\s*\(", body)}


def resource_counts(stats: dict, top: str, flop_types: set[str]) -> dict:
    # Contar sólo el top aplanado; los módulos de biblioteca no son instancias.
    module = stats["modules"]["\\" + top]
    cells = {name: count for name, count in module["num_cells_by_type"].items()
             if name != "$scopeinfo"}
    unknown = [name for name in cells if not name.startswith("sky130_fd_sc_hd__")]
    if unknown:
        raise ValueError(f"Celdas sin mapear a SKY130 HD: {unknown}")
    area = module.get("area")
    if not isinstance(area, (int, float)) or area <= 0:
        raise ValueError("Falta área de celdas válida en stat -liberty")
    total = sum(cells.values())
    flops = sum(count for name, count in cells.items()
                if name in flop_types)
    return {"cells": total, "flip_flops": flops,
            "combinational_cells": total - flops, "cell_area_um2": area,
            "cells_by_type": cells}


def measurement_key(manifest: dict, metrics: dict, resources: dict) -> str:
    sources = {path: digest for path, digest in manifest["inputs_sha256"].items()
               if path.startswith(("rtl/", "model/", "config/", "tb/", "constraints/", "scripts/synth/"))}
    measurement = {"sources": sources, "config": manifest["config"],
                   "tools": manifest["tools"], "vectors": manifest["vectors_sha256"],
                   "metrics": metrics, "resources": resources,
                   "liberty_sha256": manifest.get("library", {}).get("sha256")}
    return hashlib.sha256(json.dumps(measurement, sort_keys=True).encode()).hexdigest()


def record_run(run_id: str, result: str, key: str, report: Path = REPORT,
               architecture: str = "serial") -> None:
    document = report.read_text(encoding="utf-8")
    start = f"<!-- {architecture}-runs:start -->"
    end = f"<!-- {architecture}-runs:end -->"
    if document.count(start) != 1 or document.count(end) != 1:
        raise ValueError(f"El registro PPA debe conservar los marcadores de corridas {architecture}")
    left, right = document.index(start) + len(start), document.index(end)
    if right < left:
        raise ValueError("Marcadores de corridas fuera de orden")
    entry = re.sub(r"(?m)^(#+) ", r"##\1 ", result).strip()
    replacement = f"\n\n<!-- {architecture}-measurement:{key} -->\n{entry}\n\n"
    # Incluso una medición equivalente reemplaza la anterior: siempre la última corrida exitosa.
    # Una nueva medición invalida la pareja graficada, aunque la otra no cambie.
    if "<!-- comparison:start -->" in document:
        document = re.sub(r"(?s)(<!-- comparison:start -->).*?(<!-- comparison:end -->)",
                          r"\1\n\nComparación pendiente de regenerar con las últimas corridas.\n\n\2", document)
        left, right = document.index(start) + len(start), document.index(end)
    report.write_text(document[:left] + replacement + document[right:], encoding="utf-8")


def evidence_dir(target: str, report: Path = REPORT) -> Path:
    return report.parent / target / "sky130"


def publish_evidence(run_dir: Path, target: str, report: Path = REPORT) -> Path:
    """Copia el subconjunto versionable de la corrida; reemplaza la copia anterior."""
    destination = evidence_dir(target, report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # La copia nueva se arma aparte y sólo reemplaza a la anterior si quedó completa.
    with tempfile.TemporaryDirectory(prefix=".sky130-", dir=destination.parent) as raw:
        staging, previous = Path(raw) / "new", Path(raw) / "previous"
        copied = {}
        for pattern in EVIDENCE:
            for source in sorted(run_dir.glob(pattern)):
                if not source.is_file() or (source.suffix == ".rpt" and source.name not in STA_REPORTS):
                    continue
                name = source.relative_to(run_dir).as_posix()
                (staging / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, staging / name)
                copied[name] = sha256(source)
        if "manifest.json" not in copied:
            raise ValueError(f"Corrida sin manifiesto: {run_dir}")
        write_json(staging / "evidence.json", {"run": run_dir.name, "sha256": copied})
        if destination.exists():
            destination.rename(previous)
        try:
            staging.rename(destination)
        except OSError:
            if previous.exists():
                previous.rename(destination)
            raise
    return destination


def sustained_sps(block_cycles: int, period_ns: float) -> float:
    # En tiempo el "bloque" es una muestra: block_cycles es el II por muestra.
    return 1e9 / (block_cycles * period_ns)


def evidence_links(base: Path, report_dir: Path, items: tuple[tuple[str, str], ...]) -> str:
    # Sólo se enlaza lo que existe: la copia versionada no tiene todos los artefactos.
    link = Path(os.path.relpath(base, report_dir)).as_posix()
    return "".join(f"- [{label}]({link}/{name}).\n" for label, name in items
                   if (base / name.rstrip("/")).exists())


def summary(run_dir: Path, manifest: dict, metrics: dict, resources: dict,
            report_dir: Path = REPORT.parent, evidence: Path | None = None) -> str:
    config = manifest["config"]
    label = "optimizada (B04)" if config.get("target") == "time_optimized" else "serial (B02)"
    period = metrics["clock_period_ns"]
    sustained = sustained_sps(metrics["block_cycles"], period)
    links = evidence_links(evidence or run_dir, report_dir, (
        ("Manifiesto, versiones y hashes", "manifest.json"), ("Métricas RTL", "local_metrics.json"),
        ("Celdas/área por tipo", "resources.json"), ("Métricas de netlist", "gate_metrics.json"),
        ("Log del benchmark de netlist", "logs/gate_benchmark.log"),
        ("Estadística Yosys original", "cells.json"), ("Netlist SKY130", "mapped.v"),
        ("Script de la corrida", "synthesis.ys"), ("Biblioteca utilizada", f"{LIBRARY}.lib"),
        ("Log de síntesis", "logs/yosys.log"), ("Benchmark", "logs/benchmark.log"),
        ("Regresión", "logs/regression/"), ("Onda de las primeras 32 muestras", "first_blocks.vcd")))
    guide = Path(os.path.relpath(GUIDE, report_dir)).as_posix()
    return f"""# Tiempo {label} — corrida `{run_dir.name}` (SKY130)

**PASS RTL, síntesis ASIC y simulación funcional de netlist SKY130. Timing físico y potencia no medidos.**

| Configuración | Valor |
|---|---|
| Commit base | `{manifest['commit']}` |
| Cambios locales al iniciar | {'Sí; fuentes identificadas por hashes' if manifest['git_status'] else 'No'} |
| Top | `{config['top']}` |
| Tecnología / biblioteca | SKY130, 130 nm / `sky130_fd_sc_hd` |
| Corner | TT, 25 °C, 1,8 V |
| Liberty SHA256 | `{manifest['library']['sha256']}` |
| Flujo | Yosys aplanado + dfflibmap + ABC; sin placement ni routing |
| Reloj de simulación / objetivo | {1000/period:g} MHz / {period:g} ns; sin cierre temporal demostrado |
| Formatos I/Q | Entrada Q2.0; coeficientes Q1.7; salida Q2.7 (9 bits) |
| Benchmark | QPSK 2×, semilla 1, 1024 símbolos, 2048 muestras; sin pausas |
| Yosys | `{manifest['tools']['yosys']}` |
| Icarus | `{manifest['tools']['iverilog']}` |

## Resultados actuales

| Medición | Resultado |
|---|---:|
| Muestras aceptadas / exactas | {metrics['input_samples']} / {metrics['output_samples']} |
| Latencia | {metrics['latency_cycles']} ciclos |
| Intervalo entre muestras (II) | {metrics['block_cycles']} ciclos |
| Ciclos activos del benchmark | {metrics['active_cycles']} |
| Throughput sostenido al reloj supuesto | {sustained:.3f} muestras/s |
| Throughput efectivo al reloj supuesto | {metrics['throughput_samples_per_second']:.3f} muestras/s |
| Celdas estándar totales | {resources['cells']} |
| Flip-flops | {resources['flip_flops']} |
| Celdas combinacionales | {resources['combinational_cells']} |
| Área de celdas | {resources['cell_area_um2']:.6f} µm² |

La regresión común `smoke` pasó antes del benchmark. La netlist mapeada también
verificó las 2048 salidas y reprodujo exactamente las métricas RTL usando los
modelos funcionales SKY130, sin retardos ni SDF. Esta prueba no verifica timing.
El área es la suma de áreas Liberty de las instancias mapeadas, no el área final
de un chip. La síntesis no impone un objetivo de retardo a ABC: no demuestra
10/100 MHz ni produce WNS/Fmax. Las tasas en muestras/s suponen el reloj
indicado; los ciclos se miden en RTL.

Pendientes ASIC: STA con restricciones de reloj/E/S, setup/hold, implementación
física con parasíticos y potencia con actividad representativa.

## Evidencia reproducible

{links}- [Procedimiento]({guide}).

Sólo esta última corrida exitosa ocupa la sección; las anteriores permanecen en `build/ppa/`.
"""


def target_settings(name: str) -> dict:
    if name not in TARGETS:
        raise ValueError(f"Target PPA no soportado: {name}")
    targets = json.loads((ROOT / "config/rtl_targets.json").read_text())["targets"]
    target = next((t for t in targets if t["name"] == name), None)
    if target is None:
        raise ValueError(f"Target no registrado: {name}")
    # Reloj objetivo: 10 MHz (100 ns) la serial, 100 MHz (10 ns) la optimizada.
    optimized = name == "time_optimized"
    return {**CONFIG, "target": name, "top": target["rtl_top"],
            "bench": BENCHES[name], "bench_path": f"tb/time/{BENCHES[name]}.sv",
            "sources": target["sources"], "architecture": target["architecture"],
            "clock_period_ns": 10 if optimized else 100,
            "clock_mhz": 100 if optimized else 10}


def local(target: str = "time_serial", liberty: str | None = None,
          publish: bool = True) -> Path:
    library = sky130_library(liberty)
    models = [library.parent.parent / "verilog" / name
              for name in ("primitives.v", "sky130_fd_sc_hd.v")]
    for model in models:
        if not model.is_file():
            raise ValueError(f"Falta modelo funcional SKY130: {model}")
    config = target_settings(target)
    top, bench = config["top"], config["bench"]
    for tool in ("iverilog", "vvp", "yosys", "git"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"Falta herramienta: {tool}")
    commit = capture(["git", "rev-parse", "HEAD"])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = ROOT / "build/ppa" / target / f"{stamp}-{commit[:8]}"
    run_dir.mkdir(parents=True)
    logs = run_dir / "logs"
    logs.mkdir()
    inputs = sorted({*ROOT.glob("rtl/*/*.sv"), *ROOT.glob("tb/*/*.sv"),
                     *ROOT.glob("scripts/synth/*.ys"), *ROOT.glob("vectors/*.txt"),
                     *ROOT.glob("model/*.py"),
                     *ROOT.glob("scripts/*.py"), *ROOT.glob("scripts/ppa/openlane/*"), *ROOT.glob("tests/*.py"),
                     *ROOT.glob("config/*"),
                     ROOT / config["bench_path"], ROOT / "scripts/ppa_time.py",
                     ROOT / "scripts/ppa_vectors.py", REPORT,
                     ROOT / f"scripts/synth/{target}_sky130.ys"})
    manifest = {
        "commit": commit, "git_status": capture(["git", "status", "--short"]),
        "config": config, "status": "running",
        "library": {"name": LIBRARY, "path": str(library), "sha256": sha256(library)},
        "library_models": {p.name: {"path": str(p), "sha256": sha256(p)} for p in models},
        "tools": {"python": sys.version.split()[0], "numpy": version("numpy"),
                  "yosys": capture(["yosys", "-V"]).splitlines()[0],
                  "iverilog": capture(["iverilog", "-V"]).splitlines()[0],
                  "vvp": capture(["vvp", "-V"]).splitlines()[0]},
        "inputs_sha256": {p.relative_to(ROOT).as_posix(): sha256(p)
                          for p in inputs if p.is_file()},
    }
    write_json(run_dir / "manifest.json", manifest)
    try:
        smoke_started = (run_dir / "manifest.json").stat().st_mtime_ns
        run([sys.executable, "scripts/ci.py", "smoke"], logs / "smoke.log")
        (logs / "regression").mkdir()
        for log in (ROOT / "build/ci-logs").glob("*.log"):
            if log.stat().st_mtime_ns >= smoke_started:
                shutil.copy2(log, logs / "regression" / log.name)
        run([sys.executable, "-m", "scripts.ppa_vectors", str(run_dir / "ppa_vectors.txt"),
             "--domain", "time"], logs / "vectors.log")
        rtl = config["sources"]
        run(["iverilog", "-g2012", "-Wall", "-s", bench, "-o", str(run_dir / "benchmark.out"),
             *rtl, config["bench_path"]], logs / "compile.log")
        run(["vvp", str(run_dir / "benchmark.out"),
             f"+VECTORS={run_dir / 'ppa_vectors.txt'}",
             f"+METRICS={run_dir / 'local_metrics.json'}",
             f"+VCD={run_dir / 'first_blocks.vcd'}",
             f"+PERIOD_NS={config['clock_period_ns']}"], logs / "benchmark.log")
        library_copy = run_dir / library.name
        shutil.copy2(library, library_copy)
        mapped = run_dir / "mapped.v"
        stats = run_dir / "cells.json"
        synthesis = run_dir / "synthesis.ys"
        lib_arg = json.dumps(str(library_copy.relative_to(ROOT)))
        synthesis.write_text(
            f"script scripts/synth/{target}_sky130.ys\n"
            f"dffunmap\ndfflibmap -liberty {lib_arg}\nabc -liberty {lib_arg}\nopt_clean\n"
            f"delete t:$scopeinfo\nread_liberty -lib {lib_arg}\ncheck -assert -mapped\n"
            f"write_verilog -noattr -noexpr {mapped.relative_to(ROOT)}\n"
            f"tee -o {stats.relative_to(ROOT)} stat -json -liberty {lib_arg}\n",
            encoding="utf-8")
        run(["yosys", "-s", str(synthesis)], logs / "yosys.log")
        resources = resource_counts(json.loads(stats.read_text()), top, liberty_flops(library_copy))
        write_json(run_dir / "resources.json", resources)
        metrics = json.loads((run_dir / "local_metrics.json").read_text())
        if not metrics.get("passed") or metrics.get("output_samples") != config["samples"]:
            raise ValueError("El benchmark no confirmó las 2048 salidas")
        model_dir = run_dir / "library_models"
        model_dir.mkdir()
        for model in models:
            shutil.copy2(model, model_dir / model.name)
        run(["iverilog", "-g2012", "-DFUNCTIONAL", "-DUNIT_DELAY=", "-s", bench,
             "-o", str(run_dir / "gate.out"), config["bench_path"], str(mapped),
             *(str(model_dir / model.name) for model in models)], logs / "gate_compile.log")
        run(["vvp", str(run_dir / "gate.out"), f"+VECTORS={run_dir / 'ppa_vectors.txt'}",
             f"+METRICS={run_dir / 'gate_metrics.json'}",
             f"+PERIOD_NS={config['clock_period_ns']}"], logs / "gate_benchmark.log")
        gate_metrics = json.loads((run_dir / "gate_metrics.json").read_text())
        if gate_metrics != metrics:
            raise ValueError("Las métricas de la netlist SKY130 difieren del benchmark RTL")
        changed = [name for name, digest in manifest["inputs_sha256"].items()
                   if sha256(ROOT / name) != digest]
        if sha256(library) != manifest["library"]["sha256"] or sha256(library_copy) != manifest["library"]["sha256"]:
            changed.append(str(library))
        for model in models:
            expected = manifest["library_models"][model.name]["sha256"]
            if sha256(model) != expected or sha256(model_dir / model.name) != expected:
                changed.append(str(model))
        if changed:
            raise RuntimeError(f"Fuentes cambiaron durante la corrida; repetir: {changed}")
        signals = ("clk", "rst", "activity_window", "in_valid", "in_ready", "in_last",
                   "in_i[1:0]", "in_q[1:0]", "out_valid", "out_ready", "out_last",
                   "out_i[8:0]", "out_q[8:0]")
        (run_dir / "first_blocks.gtkw").write_text(
            f'[dumpfile] "{run_dir / "first_blocks.vcd"}"\n'
            + "[timestart] 0\n[signals]\n"
            + "\n".join(f"{bench}.{s}" if s == "activity_window" else f"{bench}.dut.{s}"
                        for s in signals) + "\n")
        manifest["status"] = "local_pass"
        manifest["vectors_sha256"] = sha256(run_dir / "ppa_vectors.txt")
        (run_dir / "summary.md").write_text(
            summary(run_dir, manifest, metrics, resources, run_dir), encoding="utf-8")
        if publish:
            write_json(run_dir / "manifest.json", manifest)
            published = publish_evidence(run_dir, target)
            result = summary(run_dir, manifest, metrics, resources, evidence=published)
            record_run(run_dir.name, result, measurement_key(manifest, metrics, resources),
                       architecture=config["architecture"])
    except Exception:
        manifest["status"] = "failed"
        raise
    finally:
        manifest["artifacts_bytes"] = {p.relative_to(run_dir).as_posix(): p.stat().st_size
                                      for p in sorted(run_dir.rglob("*"))
                                      if p.is_file() and p.name != "manifest.json"}
        write_json(run_dir / "manifest.json", manifest)
        print(f"Evidencia: {run_dir}")
    print(f"Resumen: {REPORT}")
    return run_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("local", "physical", "compare"))
    parser.add_argument("--target", choices=TARGETS, default="time_serial")
    parser.add_argument("--liberty", help="Ruta a SKY130 HD TT 25C 1v80; también SKY130_LIB")
    parser.add_argument("--b02", type=Path, help="Corrida completa B02 para comparar")
    parser.add_argument("--b04", type=Path, help="Corrida completa B04 para comparar")
    parser.add_argument("--openlane-root", type=Path, default=Path.home() / "openlane2")
    parser.add_argument("--render", action="store_true", help="Exportar SVG con Mermaid CLI 11.6.0")
    args = parser.parse_args()
    try:
        if args.command == "compare":
            from scripts.ppa_time_compare import compare
            if args.b02 is None or args.b04 is None:
                raise ValueError("compare requiere --b02 y --b04")
            compare(args.b02, args.b04, render=args.render)
        elif args.command == "physical":
            from scripts.ppa_time_physical import physical
            physical(args.target, args.openlane_root, args.liberty)
        else:
            local(args.target, args.liberty)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
