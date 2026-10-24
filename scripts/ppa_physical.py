"""OpenLane 2 fijado, STA post-SPEF y potencia con actividad de netlist."""

from __future__ import annotations

import json
from fnmatch import fnmatchcase
import math
import os
from pathlib import Path
import re
import shutil
import subprocess

from scripts.ppa import (ROOT, REPORT, capture, local, record_run, run,
                         sha256, sky130_library, write_json)

OPENLANE_REV = "a7b0e6d"
PDK_REV = "0fe599b2afb6708d281543108caf8310912f54af"
CORNERS = [f"{rc}_{pvt}" for rc in ("nom", "min", "max")
           for pvt in ("tt_025C_1v80", "ss_100C_1v60", "ff_n40C_1v95")]
METHOD = {"flow": "OpenLane2-Classic-to-STAPostPNR", "openlane_revision": OPENLANE_REV,
          "pdk_revision": PDK_REV, "pdk": "sky130A", "scl": "sky130_fd_sc_hd",
          "core_util_pct": 35, "placement_density_pct": 45, "threads": 2,
          "corners": CORNERS, "synthesis_strategy": "AREA 0",
          "power": "functional-netlist-VCD-zero-delay-TT-nom-SPEF"}


def tcl_word(value: str | Path) -> str:
    # Braces no interpretan $, corchetes ni espacios. Rechazar saltos y braces.
    value = str(value)
    if any(c in value for c in "{}\n\r"):
        raise ValueError(f"Ruta/nombre Tcl no soportado: {value!r}")
    return "{" + value + "}"


def configuration(config: dict, sources: list[Path], period: float) -> dict:
    return {"DESIGN_NAME": config["top"], "VERILOG_FILES": [str(p) for p in sources],
            "CLOCK_PORT": "clk", "CLOCK_PERIOD": period,
            "STD_CELL_LIBRARY": "sky130_fd_sc_hd", "DEFAULT_CORNER": "nom_tt_025C_1v80",
            "STA_CORNERS": CORNERS, "TIMING_VIOLATION_CORNERS": ["*"],
            "FP_CORE_UTIL": 35, "PL_TARGET_DENSITY_PCT": 45,
            "SYNTH_STRATEGY": "AREA 0", "SYNTH_HIERARCHY_MODE": "flatten",
            "SYNTH_ABC_DFF": False, "DRT_THREADS": 2, "STA_THREADS": 2,
            "ERROR_ON_LINTER_WARNINGS": False}


def trim_vcd(source: Path, destination: Path, start_ns: float, duration_ns: float,
             scope: str) -> dict:
    """Recortar/rebasar en streaming: el OpenSTA fijado no tiene -begin_time."""
    header, stack, nets, states = [], [], set(), {}
    scale_ns, timestamp, emitted = None, 0, False
    start = end = None
    last_time = 0
    with source.open() as src, destination.open("w") as dst:
        for line in src:
            header.append(line)
            if line.startswith("$scope"):
                stack.append(line.split()[2])
            elif line.startswith("$upscope"):
                stack.pop()
            elif line.startswith("$var") and "/".join(stack) == scope:
                fields = line.split()
                if fields[1] not in ("wire", "reg"):
                    continue
                width, name = int(fields[2]), fields[4]
                if width == 1:
                    nets.add(name)
                else:
                    bounds = re.fullmatch(r"\[(-?\d+):(-?\d+)\]", fields[5])
                    if not bounds and fields[5] != "$end":
                        raise ValueError("Rango VCD no soportado")
                    lo, hi = sorted(map(int, bounds.groups())) if bounds else (0, width - 1)
                    nets.update(f"{name}[{i}]" for i in range(lo, hi + 1))
            if "$enddefinitions" in line:
                break
        joined = "".join(header)
        units = re.search(r"\$timescale\s+(\d+)\s*(s|ms|us|ns|ps|fs)\s+\$end", joined)
        if not units or not nets:
            raise ValueError("VCD sin timescale o scope DUT válido")
        scale_ns = int(units[1]) * {"s": 1e9, "ms": 1e6, "us": 1e3, "ns": 1, "ps": .001, "fs": .000001}[units[2]]
        start, end = round(start_ns / scale_ns), round((start_ns + duration_ns) / scale_ns)
        dst.write(joined)
        for line in src:
            value = line.strip()
            if value.startswith("#"):
                timestamp = int(value[1:])
                last_time = timestamp
                if timestamp >= start and not emitted:
                    dst.write("#0\n$dumpvars\n" + "".join(states.values()) + "$end\n")
                    emitted = True
                if timestamp > end:
                    break
                if emitted:
                    dst.write(f"#{timestamp - start}\n")
            elif value and not value.startswith("$"):
                fields = value.split()
                if value[0] in "bBrR":
                    identifier = fields[-1]
                elif value[0] in "01xXzZ":
                    identifier = value[1:]
                else:
                    raise ValueError(f"Valor VCD no soportado: {value[:100]}")
                if timestamp < start:
                    states[identifier] = line
                elif emitted:
                    dst.write(line)
        if not emitted or last_time < end:
            raise ValueError("VCD truncado: falta parte de la ventana activa")
        dst.write(f"#{end-start}\n")
    return {"start_ns": start_ns, "duration_ns": duration_ns, "nets": sorted(nets),
            "scope": scope, "time_origin": "active-window-start", "sha256": sha256(destination)}


def timing_metrics(state: dict, period: float, reports: Path) -> tuple[dict, bool]:
    metrics = state["metrics"]
    result = {}
    for corner in CORNERS:
        row = {}
        for key, metric in [
            ("setup_ws_ns", "timing__setup__ws"), ("hold_ws_ns", "timing__hold__ws"),
            ("setup_wns_ns", "timing__setup__wns"), ("hold_wns_ns", "timing__hold__wns"),
            ("setup_tns_ns", "timing__setup__tns"), ("hold_tns_ns", "timing__hold__tns"),
            ("setup_violations", "timing__setup_vio__count"), ("hold_violations", "timing__hold_vio__count"),
            ("max_slew_violations", "design__max_slew_violation__count"),
            ("max_cap_violations", "design__max_cap_violation__count"),
            ("max_fanout_violations", "design__max_fanout_violation__count"),
            ("unannotated_routed_nets", "timing__unannotated_net_filtered__count"),
        ]:
            x = metrics.get(f"{metric}__corner:{corner}")
            if not isinstance(x, (float, int)) or not math.isfinite(x):
                raise ValueError(f"STA incompleto: {metric}, {corner}")
            row[key] = x
        slack = metrics.get(f"timing__setup_r2r__ws__corner:{corner}")
        row["fmax_estimate_mhz"] = (1000 / (period - slack)
                                           if isinstance(slack, (int, float)) and math.isfinite(slack)
                                           and 0 < period - slack < 1e20 else None)
        checks = (reports / corner / "checks.rpt").read_text()
        marker = "check_setup -verbose -unconstrained_endpoints"
        if marker not in checks:
            raise ValueError(f"Falta check_setup completo: {corner}")
        diagnostics = checks.split(marker, 1)[1]
        row["constraint_warnings"] = len(re.findall(r"(?im)^\s*(?:Warning|Error)\b", diagnostics))
        counts = re.findall(r"(\d+) unconstrained endpoints?", diagnostics)
        row["unconstrained_endpoints"] = sum(map(int, counts))
        if row["constraint_warnings"] or row["unconstrained_endpoints"] or row["unannotated_routed_nets"]:
            raise ValueError(f"Restricciones/parásitos incompletos: {corner}; ver checks.rpt")
        result[corner] = row
    passed = all(r["setup_ws_ns"] >= 0 and r["hold_ws_ns"] >= 0
                 and r["setup_violations"] == 0 and r["hold_violations"] == 0
                 and r["constraint_warnings"] == 0 and r["unconstrained_endpoints"] == 0
                 and r["unannotated_routed_nets"] == 0
                 and r["max_slew_violations"] == 0 and r["max_cap_violations"] == 0
                 and r["max_fanout_violations"] == 0
                 for r in result.values())
    return result, passed


def find_state(directory: Path) -> tuple[Path, dict]:
    matches = list(directory.glob("*-openroad-stapostpnr/state_out.json"))
    if len(matches) != 1:
        raise ValueError(f"Falta un único estado STA post-PnR en {directory}")
    return matches[0], json.loads(matches[0].read_text())


def nominal_spef(state: dict) -> Path:
    # OpenLane guarda las claves del PDK como patrones (por ejemplo nom_*).
    paths = {Path(path) for pattern, path in state["spef"].items()
             if fnmatchcase("nom_tt_025C_1v80", pattern)}
    if len(paths) != 1:
        raise ValueError("Se requiere un único SPEF nominal")
    return paths.pop()


def physical_areas(metrics: dict) -> dict:
    area = metrics["design__instance__area"]
    if not isinstance(area, (int, float)) or not math.isfinite(area) or area <= 0:
        raise ValueError("Falta área final de celdas")
    result = {"final_cell_area_um2": area}
    # floorplan.tcl de OpenLane 2.3.10 exporta bounding boxes en µm.
    for kind in ("core", "die"):
        box = metrics[f"design__{kind}__bbox"]
        coords = [float(x) for x in (box.split() if isinstance(box, str) else box)]
        if len(coords) != 4 or not all(math.isfinite(x) for x in coords):
            raise ValueError(f"Bounding box inválido: {kind}")
        x0, y0, x1, y1 = coords
        if x1 <= x0 or y1 <= y0:
            raise ValueError(f"Bounding box vacío: {kind}")
        result[f"{kind}_area_um2"] = (x1 - x0) * (y1 - y0)
    return result


def power_script(library: Path, mapped: Path, sdc: Path, spef: Path, top: str,
                 vcd: Path, scope: str) -> str:
    return ("set_cmd_units -time ns -capacitance pF -current mA -voltage V -resistance kOhm -distance um\n"
            f"read_liberty {tcl_word(library)}\n"
            f"read_verilog {tcl_word(mapped)}\nlink_design {top}\n"
            f"read_sdc {tcl_word(sdc)}\nread_spef {tcl_word(spef)}\n"
            "set_propagated_clock [all_clocks]\n"
            "report_parasitic_annotation -report_unannotated\n"
            f"read_vcd -scope {tcl_word(scope)} {tcl_word(vcd)}\n"
            "report_power -digits 9\n"
            "set corner [lindex [sta::corners] 0]\n"
            "puts \"PPA_POWER [lrange [sta::design_power $corner] 0 3]\"\n"
            "set matched 0\nset unmatched 0\nset internal_pins 0\n"
            "foreach pin [concat [get_pins -hierarchical *] [get_ports *]] {\n"
            "  if {[get_property $pin direction] eq \"internal\"} { incr internal_pins; continue }\n"
            "  set origin [lindex [get_property $pin activity] 2]\n"
            "  if {$origin in {vcd clock constant}} { incr matched } else {\n"
            "    incr unmatched\n    puts \"PPA_UNMATCHED [get_full_name $pin] $origin\"\n  }\n}\n"
            "puts \"PPA_COVERAGE $matched $unmatched\"\n"
            "puts \"PPA_INTERNAL_EXCLUDED $internal_pins\"\nexit\n")


def parse_power(log: str, metrics: dict, coverage: dict) -> dict:
    match = re.search(r"^PPA_POWER (.+)$", log, re.M)
    cov = re.search(r"^PPA_COVERAGE (\d+) (\d+)$", log, re.M)
    annotated = re.search(r"Annotated (\d+) pin activities\.", log)
    internal_pins = re.search(r"^PPA_INTERNAL_EXCLUDED (\d+)$", log, re.M)
    if (not match or not cov or not annotated or not internal_pins or int(annotated[1]) == 0
            or re.search(r"(?im)^\s*(Error|ERROR)\b|vcd period .*differs from SDC", log)):
        raise ValueError("Falta reporte de potencia/actividad válido")
    values = [float(v) for v in match[1].split()]
    if len(values) != 4 or not all(math.isfinite(v) and v >= 0 for v in values):
        raise ValueError("Potencias inválidas")
    matched, unmatched = map(int, cov.groups())
    if not matched or unmatched:
        raise ValueError(f"Actividad no corresponde a netlist: {matched} pines, {unmatched} sin anotación")
    internal, switching, leakage, total = values
    if not math.isclose(total, internal + switching + leakage, rel_tol=1e-5, abs_tol=1e-12):
        raise ValueError("Potencia total inconsistente")
    duration = metrics["activity_duration_ns"] * 1e-9
    return {"internal_w": internal, "switching_w": switching, "dynamic_w": internal + switching,
            "leakage_w": leakage, "total_w": total,
            "dynamic_energy_j": (internal + switching) * duration / metrics["output_samples"],
            "total_energy_j": total * duration / metrics["output_samples"],
            "activity_coverage_pct": 100 * matched / (matched + unmatched),
            "coverage_kind": "pin-activity-origin-vcd-clock-constant",
            "vcd_annotated_pins": int(annotated[1]),
            "excluded_liberty_internal_pins": int(internal_pins[1]),
            "activity_window": {k: coverage[k] for k in ("start_ns", "duration_ns", "sha256")}}


def physical(target: str, openlane_root: Path, liberty: str | None = None) -> Path:
    openlane_root = openlane_root.resolve()
    revision = capture(["git", "-C", str(openlane_root), "rev-parse", "HEAD"])
    if not revision.startswith(OPENLANE_REV) or capture(["git", "-C", str(openlane_root), "status", "--porcelain"]):
        raise ValueError("Se requiere el checkout OpenLane fijado y limpio: " + OPENLANE_REV)
    library = sky130_library(liberty)
    pdk_root = library.parents[4]
    if pdk_root.name != PDK_REV:
        raise ValueError("Se requiere el PDK fijado: " + PDK_REV)
    for tool in ("openlane", "openroad", "sta"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"Falta {tool}. Ejecutar: sh scripts/ppa/openlane/run.sh --target {target}")
    tools = {tool: capture([tool, flag]) for tool, flag in
             (("openlane", "--version"), ("openroad", "-version"), ("sta", "-version"))}
    if tools["openlane"].strip() != "2.3.10":
        raise ValueError("El ejecutable openlane debe ser 2.3.10 del entorno Nix fijado")
    method = {**METHOD, "openlane_revision": revision,
              "nix_lock_sha256": sha256(openlane_root / "flake.lock"),
              "environment_profile_sha256": sha256(ROOT / "scripts/ppa/openlane/flake.nix"),
              "library_sha256": {f"sky130_fd_sc_hd__{pvt}.lib":
                                 sha256(library.parent / f"sky130_fd_sc_hd__{pvt}.lib")
                                 for pvt in ("tt_025C_1v80", "ss_100C_1v60", "ff_n40C_1v95")}}
    # El ejemplo pequeño también queda dentro de build/, sin escribir en el checkout.
    preflight = ROOT / "build/ppa/openlane-preflight"
    preflight.mkdir(parents=True, exist_ok=True)
    example = openlane_root / "openlane/examples/spm"
    preflight_key = (sha256(openlane_root / "flake.lock") + sha256(library)
                     + json.dumps(tools, sort_keys=True) + method["environment_profile_sha256"])
    success = preflight / "success.json"
    if not success.exists() or json.loads(success.read_text()).get("key") != preflight_key:
        design = preflight / "design"
        if design.exists():
            shutil.rmtree(design)
        shutil.copytree(example, design)
        with (design / "config.yaml").open("a") as f:
            f.write("\nSTA_THREADS: 2\nDRT_THREADS: 2\n")
        run(["openlane", "--pdk-root", str(pdk_root), "--pdk", "sky130A", "--scl", "sky130_fd_sc_hd",
             "--to", "OpenROAD.STAPostPNR", "--tag", "preflight", str(design / "config.yaml")],
            preflight / "preflight.log")
        _, state = find_state(design / "runs/preflight")
        if not state.get("spef"):
            raise ValueError("Preflight sin parasíticos")
        write_json(success, {"key": preflight_key, "tools": tools})
    run_dir = local(target, str(library), publish=False)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    manifest.update(status="physical_running", physical_method=method)
    manifest["tools"].update(tools)
    shutil.copy2(openlane_root / "flake.lock", run_dir / "openlane-flake.lock")
    shutil.copy2(ROOT / "scripts/ppa/openlane/flake.nix", run_dir / "ppa-environment.nix")
    write_json(run_dir / "manifest.json", manifest)
    config = manifest["config"]
    try:
        sources = []
        for name in config["sources"]:
            dest = run_dir / "source" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, dest)
            sources.append(dest)
        results = {"areas": {}, "scenarios": {}}
        original_state = None
        for scenario, period in (("target", config["clock_period_ns"]), ("common", 100)):
            cfg = run_dir / f"openlane-{scenario}.json"
            write_json(cfg, configuration(config, sources, period))
            command = ["openlane", "--pdk-root", str(pdk_root), "--pdk", "sky130A",
                       "--to", "OpenROAD.STAPostPNR", "--tag", scenario]
            if original_state:
                command += ["--from", "OpenROAD.STAPostPNR", "--with-initial-state", str(original_state)]
            run(command + [str(cfg)], run_dir / f"logs/openlane-{scenario}.log")
            state_file, state = find_state(run_dir / "runs" / scenario)
            if original_state is None:
                original_state = state_file
            timing, passed = timing_metrics(state, period, state_file.parent)
            scenario_dir = run_dir / scenario
            scenario_dir.mkdir()
            mapped = Path(state["nl"])
            # La netlist final funcional incluye el árbol de reloj; las celdas
            # puramente físicas no afectan el benchmark y sus modelos no tienen puertos.
            gate = scenario_dir / "gate.out"
            run(["iverilog", "-g2012", "-DFUNCTIONAL", "-DUNIT_DELAY=", "-s", config["bench"],
                 "-o", str(gate), config["bench_path"], str(mapped),
                 str(run_dir / "library_models/primitives.v"), str(run_dir / "library_models/sky130_fd_sc_hd.v")],
                scenario_dir / "compile.log")
            raw_vcd = scenario_dir / "raw.vcd"
            run(["vvp", str(gate), f"+VECTORS={run_dir / 'ppa_vectors.txt'}",
                 f"+METRICS={scenario_dir / 'metrics.json'}", f"+POWER_VCD={raw_vcd}",
                 f"+PERIOD_NS={period}"], scenario_dir / "benchmark.log")
            metrics = json.loads((scenario_dir / "metrics.json").read_text())
            baseline = json.loads((run_dir / "local_metrics.json").read_text())
            for key in ("passed", "input_samples", "output_samples", "latency_cycles", "block_cycles", "active_cycles"):
                if metrics[key] != baseline[key]:
                    raise ValueError(f"Netlist final difiere del RTL: {key}")
            activity = scenario_dir / "activity.vcd"
            scope = config["bench"] + "/dut"
            coverage = trim_vcd(raw_vcd, activity, metrics["activity_start_ns"], metrics["activity_duration_ns"], scope)
            sdc, spef = Path(state["sdc"]), nominal_spef(state)
            if not sdc.is_file() or not spef.is_file():
                raise ValueError("Faltan SDC resuelto o SPEF nominal para potencia")
            script = scenario_dir / "power.tcl"
            script.write_text(power_script(run_dir / library.name, mapped, sdc, spef,
                                           config["top"], activity, scope))
            run(["sta", "-exit", str(script)], scenario_dir / "power.log")
            power = parse_power((scenario_dir / "power.log").read_text(), metrics, coverage)
            results["scenarios"][scenario] = {"clock_period_ns": period, "timing": timing,
                                               "timing_pass": passed, "power": power,
                                               "state": str(state_file)}
            if scenario == "target":
                results["areas"] = physical_areas(state["metrics"])
        write_json(run_dir / "physical_metrics.json", results)
        changed = [name for name, digest in manifest["inputs_sha256"].items()
                   if sha256(ROOT / name) != digest]
        if changed:
            raise ValueError(f"Fuentes cambiaron durante la corrida: {changed}")
        if any(sha256(library.parent / name) != digest for name, digest in method["library_sha256"].items()):
            raise ValueError("Bibliotecas PVT cambiaron durante la corrida")
        manifest["status"] = "physical_complete"
        manifest["artifacts_sha256"] = {p.relative_to(run_dir).as_posix(): sha256(p)
                                        for p in run_dir.rglob("*") if p.is_file()
                                        and p.name != "manifest.json" and p.suffix not in (".out", ".vcd", ".log")}
        write_json(run_dir / "manifest.json", manifest)
        result = physical_summary(run_dir, manifest, results)
        (run_dir / "physical_summary.md").write_text(result)
        record_run(run_dir.name, result, sha256(run_dir / "physical_metrics.json"),
                   architecture=config["architecture"])
        return run_dir
    except Exception as exc:
        manifest.update(status="failed", error=str(exc))
        write_json(run_dir / "manifest.json", manifest)
        raise


def physical_summary(directory: Path, manifest: dict, result: dict) -> str:
    link = Path(os.path.relpath(directory, REPORT.parent)).as_posix()
    text = f"# {manifest['config']['target']} — corrida {directory.name} (OpenLane 2 / SKY130)\n\n"
    text += "**Medición física completa; simulación funcional de netlist final, STA post-SPEF y potencia con VCD.**\n\n"
    text += "Potencia estimada TT/25 °C/1,8 V, sin retardos de simulación ni glitches temporales completos. No es signoff de fabricación.\n\n"
    text += "| Escenario | Reloj | Setup/hold todos los corners | Potencia total | Energía total/muestra |\n|---|---:|---|---:|---:|\n"
    for name, m in result["scenarios"].items():
        text += f"| {name} | {1000/m['clock_period_ns']:g} MHz | {'PASS' if m['timing_pass'] else 'FAIL'} | {m['power']['total_w']:.9g} W | {m['power']['total_energy_j']:.9g} J |\n"
    text += "\nLas tasas al reloj objetivo son hipotéticas si timing FAIL. Fmax es estimación registro a registro, sin barrido.\n\n"
    for name in ("manifest.json", "physical_metrics.json", "local_metrics.json", "gate_metrics.json",
                 "resources.json", "openlane-target.json", "openlane-common.json"):
        text += f"- [{name}]({link}/{name}).\n"
    text += f"- [STA, netlist final, SPEF, SDF y restricciones resueltas]({link}/runs/).\n"
    text += f"- [Actividad y potencia objetivo]({link}/target/) y [a 10 MHz]({link}/common/).\n"
    return text
