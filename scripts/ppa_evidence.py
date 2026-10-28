"""Publica la evidencia pequeña de una corrida física sin ejecutar EDA."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from scripts.ppa import REPORT, ROOT, sha256, write_json
from scripts.ppa_physical import CORNERS


def published_directory(run_dir: Path, target: str, report_dir: Path = REPORT.parent) -> Path:
    destination = report_dir / target / "sky130"
    index = destination / "evidence.json"
    if index.is_file():
        evidence = json.loads(index.read_text())
        if (evidence["source_run"] == run_dir.name
                and evidence["files_sha256"]["manifest.json"] == sha256(run_dir / "manifest.json")):
            return destination
    return run_dir


def publish_evidence(run_dir: Path, report_dir: Path = REPORT.parent,
                     openlane_root: Path = Path.home() / "openlane2") -> Path:
    run_dir = run_dir.resolve()
    manifest = json.loads((run_dir / "manifest.json").read_text())
    target = manifest["config"]["target"]
    if target not in ("frequency_serial", "frequency_optimized"):
        raise ValueError(f"Variante de frecuencia desconocida: {target}")
    if manifest["status"] != "physical_complete":
        raise ValueError("Se requiere una corrida física completa, incluso si timing es FAIL")
    physical = json.loads((run_dir / "physical_metrics.json").read_text())
    destination = report_dir / target / "sky130"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not (destination / "evidence.json").is_file():
        raise ValueError(f"Destino sin índice de evidencia: {destination}")
    sources, generated, aliases = {}, {}, {}
    with tempfile.TemporaryDirectory(prefix=".sky130-", dir=destination.parent) as raw:
        staging = Path(raw) / "new"
        staging.mkdir()

        def copy(source: Path, name: str) -> None:
            relative = source.relative_to(run_dir).as_posix() if source.is_relative_to(run_dir) else None
            expected = manifest.get("artifacts_sha256", {}).get(relative)
            if expected and sha256(source) != expected:
                raise ValueError(f"Artefacto alterado: {source}")
            output = staging / name
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, output)
            sources[name] = str(source)

        for name in ("manifest.json", "physical_metrics.json", "local_metrics.json",
                     "gate_metrics.json", "resources.json", "openlane-target.json"):
            copy(run_dir / name, name)
        for name in ("openlane-common.json", "resource_summary.json", "validation.json",
                     "reproduce.txt", "source_run/rehash.json"):
            if (run_dir / name).is_file():
                copy(run_dir / name, name)
        provenance = manifest.get("resume_provenance", {})
        if provenance.get("reused_physical_layout"):
            copy(Path(provenance["source_run"]) / "manifest.json", "source_run/manifest.json")
        diagnostic = provenance.get("common_sta_vs_power_sdc", {}).get("timing_sta", {}).get("diagnostic_path")
        if diagnostic:
            copy(ROOT / diagnostic, "diagnostics/" + Path(diagnostic).name)
        for scenario in ("target", "common"):
            metrics = physical["scenarios"][scenario]
            if set(metrics["timing"]) != set(CORNERS):
                raise ValueError(f"Faltan los nueve corners en {scenario}")
            if scenario == "common" and not (run_dir / scenario).is_dir():
                original = physical["scenarios"]["target"]
                if (metrics["state"], metrics["clock_period_ns"]) != (original["state"], original["clock_period_ns"]):
                    raise ValueError("Escenario common sin evidencia propia ni alias target válido")
                aliases[scenario] = "target"
                continue
            aliases[scenario] = scenario
            state_file = Path(metrics["state"])
            state = json.loads(state_file.read_text())
            copy(state_file, f"sta/{scenario}/state_out.json")
            copy(Path(state["sdc"]), f"sta/{scenario}/resolved.sdc")
            for name in ("metrics.json", "power.log", "benchmark.log"):
                copy(run_dir / scenario / name, f"{scenario}/{name}")
            power_sdc = run_dir / scenario / "power.sdc"
            if not power_sdc.is_file():
                # La corrida C02 original leyó el SDC resuelto directamente.
                script = run_dir / scenario / "power.tcl"
                match = re.search(r"^read_sdc \{([^\n{}]+)\}$", script.read_text(), re.M)
                if not match:
                    raise ValueError(f"Falta identificar el SDC de potencia: {scenario}")
                power_sdc = Path(match[1])
                copy(script, f"{scenario}/power.tcl")
            copy(power_sdc, f"{scenario}/power.sdc")
            for corner in CORNERS:
                folder = state_file.parent / corner
                prefix = f"sta/{scenario}/{corner}"
                for name in ("checks.rpt", "clock.rpt", "ws.max.rpt", "ws.min.rpt",
                             "wns.max.rpt", "wns.min.rpt", "tns.max.rpt", "tns.min.rpt"):
                    copy(folder / name, f"{prefix}/{name}")
                for env in folder.glob("_env_*.tcl"):
                    copy(env, f"{prefix}/{env.name}")
                # El encabezado conserva el SDC realmente leído por STA y sus valores.
                log = folder / "sta.log"
                header = []
                with log.open() as stream:
                    for line in stream:
                        if line.startswith("%OL_CREATE_REPORT"):
                            break
                        header.append(line)
                name = f"{prefix}/sta-constraints.log"
                (staging / name).write_text("".join(header))
                generated[name] = {"source": str(log), "selection": "header before first report"}
                template = re.search(r"Reading design constraints file at '([^']+)'", "".join(header))
                if not template:
                    raise ValueError(f"Falta identificar el SDC usado por STA: {scenario}/{corner}")
                template_path = Path(template[1])
                name = f"{prefix}/sta.sdc"
                if template_path.is_file():
                    copy(template_path, name)
                elif template_path.name == "base.sdc":
                    revision = manifest["physical_method"]["openlane_revision"]
                    recovered = subprocess.run(
                        ["git", "-C", str(openlane_root), "show", f"{revision}:openlane/scripts/base.sdc"],
                        check=True, capture_output=True).stdout
                    (staging / name).write_bytes(recovered)
                    expected = provenance.get("common_sta_vs_power_sdc", {}).get("timing_sta", {}).get("template_sha256")
                    if expected and sha256(staging / name) != expected:
                        raise ValueError("El SDC recuperado difiere del hash registrado")
                    generated[name] = {"source": str(template_path), "openlane_revision": revision,
                                       "selection": "base.sdc recovered from recorded Git revision"}
                else:
                    raise FileNotFoundError(template_path)
        files = {p.relative_to(staging).as_posix(): sha256(p)
                 for p in sorted(staging.rglob("*")) if p.is_file()}
        write_json(staging / "evidence.json", {
            "source_run": run_dir.name, "source_directory": str(run_dir),
            "files_sha256": files, "source_files": sources, "derived_files": generated,
            "scenario_directories": aliases,
            "excluded": ["VCD", "netlists", "SPEF", "SDF", "ODB", "Liberty", "full STA path logs"],
        })
        previous = Path(raw) / "previous"
        if destination.exists():
            destination.rename(previous)
        try:
            staging.rename(destination)
        except OSError:
            if previous.exists():
                previous.rename(destination)
            raise
    return destination
