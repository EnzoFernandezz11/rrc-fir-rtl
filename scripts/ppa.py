#!/usr/bin/env python3
"""Medición ASIC SKY130, comparación Mermaid y referencia FPGA para Vivado."""

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
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOP = "fir_frequency_serial"
TB = "tb_fir_frequency_ppa"
REPORT = ROOT / "reports/ppa/frequency.md"
CONFIG = {
    "top": TOP, "technology": "SKY130", "clock_period_ns": 100,
    "clock_mhz": 10, "flow": "standard_cell_synthesis", "format": "A04",
    "seed": 1, "symbols": 1024, "samples": 2048,
    "input_available": True, "output_ready": True,
    "vectors": "modelo fijo A04; regresión A05",
}

LIBRARY = "sky130_fd_sc_hd__tt_025C_1v80"


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


def summary(run_dir: Path, manifest: dict, metrics: dict, resources: dict,
            report_dir: Path = REPORT.parent) -> str:
    config = manifest["config"]
    label = "optimizada" if config.get("target") == "frequency_optimized" else "serial"
    period = metrics["clock_period_ns"]
    sustained = 8e9 / (metrics["block_cycles"] * period)
    evidence = Path(os.path.relpath(run_dir, report_dir)).as_posix()
    guide = Path(os.path.relpath(ROOT / "docs/frecuencia/ppa.md", report_dir)).as_posix()
    return f"""# Frecuencia {label} — corrida `{run_dir.name}` (SKY130)

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
| Formatos I/Q | Entrada 2/F0; trabajo 12/F5; constantes 10/F8; salida 9/F7 |
| Benchmark | QPSK 2×, semilla 1, 1024 símbolos, 2048 muestras; sin pausas |
| Yosys | `{manifest['tools']['yosys']}` |
| Icarus | `{manifest['tools']['iverilog']}` |

## Resultados actuales

| Medición | Resultado |
|---|---:|
| Muestras aceptadas / exactas | {metrics['input_samples']} / {metrics['output_samples']} |
| Latencia | {metrics['latency_cycles']} ciclos |
| Intervalo por bloque de ocho muestras | {metrics['block_cycles']} ciclos |
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
El área es la suma de áreas
Liberty de las instancias mapeadas, no el área final de un chip. Los bancos se
mapean a lógica y registros; no se incluyen macros SRAM. La síntesis no impone
un objetivo de retardo a ABC: no demuestra 10/100 MHz ni produce WNS/Fmax.
Las tasas en muestras/s suponen el reloj indicado; los ciclos se miden en RTL.

Pendientes ASIC: STA con restricciones de reloj/E/S, setup/hold, implementación
física con parasíticos y potencia con actividad representativa. Una corrida
Vivado posterior mide FPGA y se informa como referencia separada.

## Evidencia reproducible

- [Manifiesto, versiones y hashes]({evidence}/manifest.json).
- [Métricas RTL]({evidence}/local_metrics.json) y [celdas/área por tipo]({evidence}/resources.json).
- [Métricas de netlist]({evidence}/gate_metrics.json) y [log del benchmark de netlist]({evidence}/logs/gate_benchmark.log).
- [Estadística Yosys original]({evidence}/cells.json) y [netlist SKY130]({evidence}/mapped.v).
- [Script de la corrida]({evidence}/synthesis.ys) y [biblioteca utilizada]({evidence}/{LIBRARY}.lib).
- [Log de síntesis]({evidence}/logs/yosys.log) y [benchmark]({evidence}/logs/benchmark.log).
- [Regresión Python]({evidence}/logs/regression/python-tests.log) y [regresión C02/C04]({evidence}/logs/regression/).
- [Onda de los primeros cuatro bloques]({evidence}/first_blocks.vcd).
- [Procedimiento]({guide}).

Sólo esta última corrida exitosa ocupa la sección; las anteriores permanecen en `build/ppa/`.
"""


def target_settings(name: str) -> dict:
    if name not in ("frequency_serial", "frequency_optimized"):
        raise ValueError(f"Target PPA no soportado: {name}")
    targets = json.loads((ROOT / "config/rtl_targets.json").read_text())["targets"]
    target = next((t for t in targets if t["name"] == name), None)
    if target is None:
        raise ValueError(f"Target no registrado: {name}")
    optimized = name == "frequency_optimized"
    return {**CONFIG, "target": name, "top": target["rtl_top"],
            "bench": "tb_fir_frequency_optimized_ppa" if optimized else TB,
            "bench_path": ("tb/frequency_optimized/tb_fir_frequency_optimized_ppa.sv"
                           if optimized else f"tb/frequency/{TB}.sv"),
            "sources": target["sources"], "architecture": target["architecture"],
            "constraint": f"constraints/clk_{100 if optimized else 10}mhz.xdc",
            "clock_period_ns": 10 if optimized else 100,
            "clock_mhz": 100 if optimized else 10,
            "vectors": "modelo fijo A04; regresión A05"}


def local(target: str = "frequency_serial", liberty: str | None = None,
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
    document = REPORT.read_text(encoding="utf-8")
    _, diagnosis = document.split("<!-- serial-analysis:start -->")
    diagnosis, _ = diagnosis.split("<!-- serial-analysis:end -->")
    diagnosis = diagnosis.strip()
    (run_dir / "diagnosis.txt").write_text(diagnosis + "\n", encoding="utf-8")
    inputs = sorted({*ROOT.glob("rtl/*/*.sv"), *ROOT.glob("tb/*/*.sv"),
                     *ROOT.glob("scripts/synth/*.ys"), *ROOT.glob("vectors/*.txt"),
                     *ROOT.glob("model/*.py"),
                     *ROOT.glob("scripts/*.py"), *ROOT.glob("scripts/ppa/openlane/*"), *ROOT.glob("tests/*.py"),
                     *ROOT.glob("config/*"), *ROOT.glob("scripts/ppa/vivado/*"),
                     ROOT / config["bench_path"], ROOT / "scripts/ppa.py",
                     ROOT / "scripts/ppa_vectors.py", ROOT / config["constraint"],
                     REPORT,
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
        run([sys.executable, "-m", "scripts.ppa_vectors", str(run_dir / "ppa_vectors.txt")],
            logs / "vectors.log")
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
        result = summary(run_dir, manifest, metrics, resources)
        (run_dir / "summary.md").write_text(
            summary(run_dir, manifest, metrics, resources, run_dir), encoding="utf-8")
        if publish:
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


def package(run_dir: Path) -> Path:
    manifest = json.loads((run_dir / "manifest.json").read_text())
    config = manifest["config"]
    if manifest["status"] != "local_pass":
        raise ValueError("Solo se empaquetan corridas locales verificadas")
    files = {name: ROOT / name for name in config["sources"]}
    files.update({p.relative_to(ROOT).as_posix(): p for p in ROOT.glob("scripts/ppa/vivado/*")
                  if p.is_file()})
    files.update({config["bench_path"]: ROOT / config["bench_path"],
                  config["constraint"]: ROOT / config["constraint"],
                  "vectors/ppa_vectors.txt": run_dir / "ppa_vectors.txt",
                  "local_metrics.json": run_dir / "local_metrics.json",
                  "resources.json": run_dir / "resources.json",
                  "manifest.json": run_dir / "manifest.json",
                  "summary.md": run_dir / "summary.md",
                  "diagnosis.txt": run_dir / "diagnosis.txt",
                  "README.md": ROOT / "scripts/ppa/vivado/README.md"})
    if "scripts/ppa/vivado/run.bat" not in files:
        raise RuntimeError("Falta el lanzador Vivado")
    archive = run_dir / f"{config['target']}_vivado.zip"
    for name, path in files.items():
        expected = manifest["inputs_sha256"].get(name)
        if expected is not None and sha256(path) != expected:
            raise ValueError(f"Fuente modificada desde benchmark: {name}")
    if sha256(run_dir / "ppa_vectors.txt") != manifest["vectors_sha256"]:
        raise ValueError("Vectores modificados desde benchmark")
    content = {name: path.read_bytes() for name, path in files.items()}
    metrics = json.loads((run_dir / "local_metrics.json").read_text())
    command = (f'scripts\\ppa\\vivado\\run.bat -Top {config["top"]} '
               f'-Bench {config["bench"]} -PeriodNs {config["clock_period_ns"]} '
               f'-LatencyCycles {metrics["latency_cycles"]} '
               f'-BlockCycles {metrics["block_cycles"]} '
               f'-ActiveCycles {metrics["active_cycles"]} -Vectors vectors/ppa_vectors.txt')
    content["README.md"] = ("# Referencia FPGA de esta variante\n\n"
                            "Los resultados locales de resources.json/summary.md son ASIC SKY130; "
                            "Vivado medirá Artix-7 de forma independiente.\n\n"
                            "Desde la raíz del ZIP, en consola Vivado:\n\n"
                            + "```bat\n" + command + "\n```\n\n"
                            + content["README.md"].decode("utf-8")).encode("utf-8")
    archived_summary = content["summary.md"].decode("utf-8")
    if "## Evidencia reproducible" in archived_summary:
        archived_summary = archived_summary.split("## Evidencia reproducible")[0] + """## Evidencia incluida

- [Manifiesto](manifest.json), [métricas RTL](local_metrics.json) y [área ASIC](resources.json).
- [Instrucciones Vivado](README.md) y [análisis](diagnosis.txt).

La netlist, biblioteca, métricas de netlist, logs y ondas ASIC permanecen en la
corrida local identificada por el título; este ZIP contiene las fuentes para FPGA.
"""
    content["summary.md"] = archived_summary.encode("utf-8")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(content.items()):
            # Fecha ZIP fija: SOURCE_DATE_EPOCH de Nix puede quedar antes de 1980.
            bundle.writestr(zipfile.ZipInfo(name), data, compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None or set(bundle.namelist()) != set(files):
            raise RuntimeError("Falló validación del ZIP")
        for name, data in content.items():
            if bundle.read(name) != data:
                raise RuntimeError(f"Contenido ZIP diferente: {name}")
    manifest = json.loads((run_dir / "manifest.json").read_text())
    manifest["package"] = {"path": archive.name, "bytes": archive.stat().st_size,
                           "sha256": sha256(archive)}
    write_json(run_dir / "manifest.json", manifest)
    print(f"Paquete: {archive} ({archive.stat().st_size:,} bytes)")
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("local", "package", "physical", "compare", "publish-evidence"))
    parser.add_argument("--run-dir", type=Path, help="Corrida física existente para publicar evidencia")
    parser.add_argument("--target", choices=("frequency_serial", "frequency_optimized"),
                        default="frequency_serial")
    parser.add_argument("--liberty", help="Ruta a SKY130 HD TT 25C 1v80; también SKY130_LIB")
    parser.add_argument("--c02", type=Path, help="Corrida completa C02 para comparar")
    parser.add_argument("--c04", type=Path, help="Corrida completa C04 para comparar")
    parser.add_argument("--openlane-root", type=Path, default=Path.home() / "openlane2")
    parser.add_argument("--render", action="store_true", help="Exportar SVG con Mermaid CLI 11.6.0")
    args = parser.parse_args()
    try:
        if args.command == "publish-evidence":
            from scripts.ppa_evidence import publish_evidence
            if args.run_dir is None:
                raise ValueError("publish-evidence requiere --run-dir")
            print(f"Evidencia: {publish_evidence(args.run_dir, openlane_root=args.openlane_root)}")
        elif args.command == "compare":
            from scripts.ppa_compare import compare
            if args.c02 is None or args.c04 is None:
                raise ValueError("compare requiere --c02 y --c04")
            compare(args.c02, args.c04, render=args.render)
        elif args.command == "physical":
            from scripts.ppa_physical import physical
            physical(args.target, args.openlane_root, args.liberty)
        else:
            run_dir = local(args.target, args.liberty)
            if args.command == "package":
                package(run_dir)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
