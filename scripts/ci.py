#!/usr/bin/env python3
"""Comandos de CI reproducibles en local y GitHub Actions."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from validate_project import ROOT, load_project, load_targets

LOG_DIR = ROOT / "build/ci-logs"


def run(command: list[str], log_name: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = LOG_DIR / log_name
    print(f"$ {' '.join(command)}", flush=True)
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            command,
            cwd=ROOT,
            stdout=output,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    if result.returncode:
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
        print(f"ERROR: comando falló; últimas líneas de {log.relative_to(ROOT)}:")
        print("\n".join(lines[-60:]))
        raise RuntimeError(f"{command[0]} terminó con código {result.returncode}")
    print(f"OK: {log.relative_to(ROOT)}")


def smoke() -> None:
    load_project()
    targets = load_targets()
    run([sys.executable, "-m", "compileall", "-q", "scripts", "tests", "model"], "python-compile.log")
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], "python-tests.log")
    if not targets:
        print("ETAPA 0: no hay RTL registrado; smoke validó contrato y herramientas Python, no vector matching")
        return
    for target in targets:
        output = ROOT / "build" / f"{target['name']}.out"
        output.parent.mkdir(parents=True, exist_ok=True)
        run(
            [
                "iverilog", "-g2012", "-Wall", "-s", target["testbench_top"],
                "-o", str(output), *target["sources"], target["testbench"],
            ],
            f"{target['name']}-compile.log",
        )
        run(["vvp", str(output)], f"{target['name']}-sim.log")
    print(f"Smoke: {len(targets)} variante(s) compiladas y simuladas")


def full() -> None:
    load_project()
    targets = load_targets()
    scripts = [target for target in targets if target.get("synth_script")]
    if not scripts:
        print("ETAPA 0: no hay scripts de síntesis registrados; full aún no mide PPA")
        return
    for target in scripts:
        run(["yosys", "-s", target["synth_script"]], f"{target['name']}-synth.log")
    skipped = len(targets) - len(scripts)
    print(f"Síntesis: {len(scripts)} variante(s); {skipped} sin script (pendientes)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "full", "has-targets", "has-synth"))
    args = parser.parse_args()
    try:
        if args.command == "smoke":
            smoke()
        elif args.command == "full":
            full()
        elif args.command == "has-targets":
            return 0 if load_targets() else 1
        elif args.command == "has-synth":
            return 0 if any(t.get("synth_script") for t in load_targets()) else 1
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
