#!/usr/bin/env python3
"""Benchmark local reproducible y paquete portátil para Vivado en Windows."""

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
    "top": TOP, "part": "xc7a35tcpg236-1", "clock_period_ns": 100,
    "clock_mhz": 10, "flow": "out_of_context", "format": "A04",
    "seed": 1, "symbols": 1024, "samples": 2048,
    "input_available": True, "output_ready": True,
    "vectors": "local A04; A05 pendiente",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(command: list[str], log: Path) -> None:
    print(f"$ {' '.join(command)}", flush=True)
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(command, cwd=ROOT, stdout=output,
                                stderr=subprocess.STDOUT, check=False)
    if result.returncode:
        print("\n".join(log.read_text(errors="replace").splitlines()[-40:]))
        raise RuntimeError(f"{command[0]} falló ({result.returncode}); ver {log}")


def capture(command: list[str]) -> str:
    return subprocess.check_output(command, cwd=ROOT, stderr=subprocess.STDOUT,
                                   text=True).strip()


def resource_counts(stats: dict) -> dict:
    # El diseño está aplanado: contar sólo el top evita sumar módulos de biblioteca.
    cells = stats["modules"]["\\" + TOP]["num_cells_by_type"]
    unknown = [name for name in cells if name.startswith("$") and name != "$scopeinfo"]
    if unknown:
        raise ValueError(f"Celdas sin mapear: {unknown}")
    return {
        "LUT": sum(cells.get(f"LUT{i}", 0) for i in range(1, 7)),
        "FF": sum(n for name, n in cells.items() if name.startswith("FD")),
        "DSP48E1": cells.get("DSP48E1", 0),
        "RAMB18E1": cells.get("RAMB18E1", 0),
        "RAMB36E1": cells.get("RAMB36E1", 0),
        "CARRY4": cells.get("CARRY4", 0),
        "MUXF7": cells.get("MUXF7", 0), "MUXF8": cells.get("MUXF8", 0),
        "primitives": cells,
    }


def measurement_key(manifest: dict, metrics: dict, resources: dict) -> str:
    sources = {path: digest for path, digest in manifest["inputs_sha256"].items()
               if path.startswith(("rtl/", "model/", "config/", "tb/", "constraints/", "scripts/synth/"))}
    measurement = {"sources": sources, "config": manifest["config"],
                   "tools": manifest["tools"], "vectors": manifest["vectors_sha256"],
                   "metrics": metrics, "resources": resources}
    return hashlib.sha256(json.dumps(measurement, sort_keys=True).encode()).hexdigest()


def record_run(run_id: str, result: str, key: str, report: Path = REPORT) -> None:
    document = report.read_text(encoding="utf-8")
    marker = "<!-- serial-runs:end -->"
    if document.count(marker) != 1:
        raise ValueError("El registro PPA debe conservar el marcador de corridas seriales")
    measurement = f"<!-- serial-measurement:{key} -->"
    if measurement in document:
        return
    heading = f"### Frecuencia serial — corrida `{run_id}` (local)"
    if heading in document:
        raise ValueError(f"La corrida {run_id} ya está registrada")
    entry = re.sub(r"(?m)^(#+) ", r"##\1 ", result).strip()
    report.write_text(document.replace(marker, measurement + "\n" + entry + "\n\n" + marker), encoding="utf-8")


def summary(run_dir: Path, manifest: dict, metrics: dict, resources: dict,
            report_dir: Path = REPORT.parent) -> str:
    rows = "\n".join(f"| {name} | {value} |" for name, value in resources.items()
                     if name != "primitives")
    period = metrics["clock_period_ns"]
    timing = "\n".join((
        f"| Muestras aceptadas / verificadas | {metrics['input_samples']} / {metrics['output_samples']} |",
        f"| Bloques completos | {metrics['blocks']} |",
        f"| Latencia por muestra | {metrics['latency_cycles']} ciclos = {metrics['latency_cycles'] * period / 1000:g} µs |",
        f"| Intervalo entre bloques (8 muestras) | {metrics['block_cycles']} ciclos = {metrics['block_cycles'] * period / 1000:g} µs |",
        f"| Ventana de procesamiento, sin reset | {metrics['active_cycles']} ciclos = {metrics['activity_duration_ns'] / 1e6:g} ms |",
        f"| Throughput a 10 MHz | {metrics['throughput_samples_per_second']:.3f} muestras/s |",
    ))
    location = run_dir.relative_to(ROOT).as_posix()
    evidence = Path(os.path.relpath(run_dir, report_dir)).as_posix()
    guide = Path(os.path.relpath(ROOT / "docs/frecuencia/ppa.md", report_dir)).as_posix()
    analysis = Path(os.path.relpath(REPORT, report_dir)).as_posix()
    return f"""# Frecuencia serial — corrida `{run_dir.name}` (local)

**Estado: verificación local y mapeo lógico completados; PPA físico pendiente de Vivado.**

## Configuración y trazabilidad

| Dato | Valor |
|---|---|
| Corrida UTC | `{run_dir.name}` |
| Commit base | `{manifest['commit']}` |
| Cambios locales al iniciar | {'Sí; consultar estado y hashes del manifiesto' if manifest['git_status'] else 'No'} |
| Módulo | `{TOP}` completo |
| FPGA | Basys3 / Artix-7 `{CONFIG['part']}` |
| Reloj objetivo | 10 MHz / 100 ns |
| Implementación prevista | Out-of-context, estrategias por defecto |
| Formato | A04: entrada 2/F0, trabajo 12/F5, coeficientes 10/F8, salida 9/F7 |
| Estímulo | QPSK 2×, semilla 1, 1024 símbolos, 2048 muestras |
| Interfaz | Entrada disponible, salida siempre lista |
| Vectores | Modelo A04 local; formato común A05 pendiente |
| Yosys | `{manifest['tools']['yosys']}` |
| Icarus | `{manifest['tools']['iverilog']}` |

## Verificación y rendimiento funcional

Regresión `smoke` y comparación exacta de las 2048 salidas: **PASS**.
La simulación RTL usa 100 ns; la capacidad física de operar a ese período se comprueba en Vivado.

| Medición | Resultado |
|---|---|
{timing}

## Recursos preliminares — Yosys XC7

Conteo de primitivas del núcleo aplanado, sin buffers de entrada/salida ni de reloj.
Las LUT son la suma de LUT1…LUT6; no equivalen directamente a slices o CLB.

| Recurso | Cantidad |
|---|---|
{rows}

## Resultados físicos — Vivado

| Métrica | Estado |
|---|---|
| LUT / FF / DSP / BRAM implementados | Pendiente |
| WNS a 100 ns / caminos sin constraints | Pendiente |
| Fmax aproximada de caminos internos | Pendiente |
| Simulación temporal y anotación SAIF | Pendiente |
| Potencia dinámica / estática | Pendiente |
| Energía dinámica por muestra | Pendiente |
| Versión Vivado / condiciones térmicas | Pendiente |

Se exige WNS ≥ 0 a 100 ns. La estimación de Fmax es `1000/(100 − WNS_ns)` MHz,
usando caminos internos de setup del mismo reloj; no reemplaza otra implementación a esa frecuencia.
Energía dinámica por muestra = potencia dinámica / throughput de la ventana SAIF.

El [análisis de la base serial]({analysis}#análisis-base-serial) reúne el desglose
de ciclos y los criterios para elegir la próxima optimización.

## Evidencia

- Corrida: `{location}/`.
- [Manifiesto y hashes]({evidence}/manifest.json).
- [Métricas del benchmark]({evidence}/local_metrics.json).
- [Recursos y primitivas]({evidence}/resources.json).
- [Onda de los primeros cuatro bloques]({evidence}/first_blocks.vcd).
- Logs: `{location}/logs/`; incluyen regresión, compilación, simulación y síntesis.
- [Procedimiento local y Windows]({guide}).

Los archivos pesados y la copia original `summary.md` de esta corrida quedan en
`build/`. Los resultados de Vivado se incorporarán al registro común conservando
las corridas anteriores.
"""


def local() -> Path:
    for tool in ("iverilog", "vvp", "yosys", "git"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"Falta herramienta: {tool}")
    commit = capture(["git", "rev-parse", "HEAD"])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = ROOT / "build/ppa/frequency_serial" / f"{stamp}-{commit[:8]}"
    run_dir.mkdir(parents=True)
    logs = run_dir / "logs"
    logs.mkdir()
    document = REPORT.read_text(encoding="utf-8")
    _, diagnosis = document.split("<!-- serial-analysis:start -->")
    diagnosis, _ = diagnosis.split("<!-- serial-analysis:end -->")
    diagnosis = diagnosis.strip()
    (run_dir / "diagnosis.txt").write_text(diagnosis + "\n", encoding="utf-8")
    inputs = sorted({*ROOT.glob("rtl/frequency/*.sv"), *ROOT.glob("model/*.py"),
                     *ROOT.glob("scripts/*.py"), *ROOT.glob("tests/*.py"),
                     *ROOT.glob("config/*"), *ROOT.glob("scripts/ppa/vivado/*"),
                     ROOT / f"tb/frequency/{TB}.sv", ROOT / "scripts/ppa.py",
                     ROOT / "scripts/ppa_vectors.py", ROOT / "constraints/clk_10mhz.xdc",
                     REPORT,
                     ROOT / "scripts/synth/frequency_serial_xc7.ys"})
    manifest = {
        "commit": commit, "git_status": capture(["git", "status", "--short"]),
        "config": CONFIG, "status": "running",
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
        rtl = [str(p.relative_to(ROOT)) for p in sorted(ROOT.glob("rtl/frequency/*.sv"))]
        run(["iverilog", "-g2012", "-Wall", "-s", TB, "-o", str(run_dir / "benchmark.out"),
             *rtl, f"tb/frequency/{TB}.sv"], logs / "compile.log")
        run(["vvp", str(run_dir / "benchmark.out"),
             f"+VECTORS={run_dir / 'ppa_vectors.txt'}",
             f"+METRICS={run_dir / 'local_metrics.json'}",
             f"+VCD={run_dir / 'first_blocks.vcd'}"], logs / "benchmark.log")
        run(["yosys", "-p", "script scripts/synth/frequency_serial_xc7.ys; "
             f'tee -o {(run_dir / "cells.json").relative_to(ROOT)} stat -json -tech xilinx'],
            logs / "yosys.log")
        resources = resource_counts(json.loads((run_dir / "cells.json").read_text()))
        write_json(run_dir / "resources.json", resources)
        metrics = json.loads((run_dir / "local_metrics.json").read_text())
        if not metrics.get("passed") or metrics.get("output_samples") != CONFIG["samples"]:
            raise ValueError("El benchmark no confirmó las 2048 salidas")
        changed = [name for name, digest in manifest["inputs_sha256"].items()
                   if sha256(ROOT / name) != digest]
        if changed:
            raise RuntimeError(f"Fuentes cambiaron durante la corrida; repetir: {changed}")
        signals = ("clk", "rst", "activity_window", "in_valid", "in_ready", "in_last",
                   "in_i[1:0]", "in_q[1:0]", "out_valid", "out_ready", "out_last",
                   "out_i[8:0]", "out_q[8:0]")
        (run_dir / "first_blocks.gtkw").write_text(
            f'[dumpfile] "{run_dir / "first_blocks.vcd"}"\n'
            + "[timestart] 0\n[signals]\n"
            + "\n".join(f"{TB}.{s}" if s == "activity_window" else f"{TB}.dut.{s}"
                        for s in signals) + "\n")
        manifest["status"] = "local_pass"
        manifest["vectors_sha256"] = sha256(run_dir / "ppa_vectors.txt")
        result = summary(run_dir, manifest, metrics, resources)
        (run_dir / "summary.md").write_text(
            summary(run_dir, manifest, metrics, resources, run_dir), encoding="utf-8")
        record_run(run_dir.name, result, measurement_key(manifest, metrics, resources))
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
    files = {p.relative_to(ROOT).as_posix(): p for p in ROOT.glob("rtl/frequency/*.sv")}
    files.update({p.relative_to(ROOT).as_posix(): p for p in ROOT.glob("scripts/ppa/vivado/*")
                  if p.is_file()})
    files.update({f"tb/frequency/{TB}.sv": ROOT / f"tb/frequency/{TB}.sv",
                  "constraints/clk_10mhz.xdc": ROOT / "constraints/clk_10mhz.xdc",
                  "vectors/ppa_vectors.txt": run_dir / "ppa_vectors.txt",
                  "local_metrics.json": run_dir / "local_metrics.json",
                  "resources.json": run_dir / "resources.json",
                  "manifest.json": run_dir / "manifest.json",
                  "summary.md": run_dir / "summary.md",
                  "diagnosis.txt": run_dir / "diagnosis.txt",
                  "README.md": ROOT / "scripts/ppa/vivado/README.md"})
    if "scripts/ppa/vivado/run.bat" not in files:
        raise RuntimeError("Falta el lanzador Vivado")
    archive = run_dir / "frequency_serial_vivado.zip"
    content = {name: path.read_bytes() for name, path in files.items()}
    archived_summary = content["summary.md"].decode("utf-8")
    guide = Path(os.path.relpath(ROOT / "docs/frecuencia/ppa.md", run_dir)).as_posix()
    archived_summary = archived_summary.replace(f"]({guide})", "](README.md)")
    analysis = Path(os.path.relpath(REPORT, run_dir)).as_posix()
    archived_summary = archived_summary.replace(
        f"]({analysis}#análisis-base-serial)", "](diagnosis.txt)")
    archived_summary = archived_summary.replace(
        "[Onda de los primeros cuatro bloques](./first_blocks.vcd)",
        "Onda de los primeros cuatro bloques: conservada en la corrida local, fuera del ZIP")
    content["summary.md"] = archived_summary.encode("utf-8")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(content.items()):
            bundle.writestr(name, data)
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
    parser.add_argument("command", choices=("local", "package"))
    args = parser.parse_args()
    try:
        run_dir = local()
        if args.command == "package":
            package(run_dir)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
