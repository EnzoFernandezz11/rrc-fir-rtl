"""OpenLane 2 fijado, STA post-SPEF y potencia con actividad de netlist."""

from __future__ import annotations

import json
from fnmatch import fnmatchcase
import math
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import time

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


def split_vcd(source: Path, destination: Path, start_ns: float, duration_ns: float,
              scope: str, segments: int = 64, clock_period_ns: float | None = None) -> dict:
    """Rebase la ventana en partes pequeñas para limitar la memoria de OpenSTA."""
    header, stack, nets, states = [], [], set(), {}
    scale_ns, timestamp, emitted = None, 0, False
    last_time, segment, writer = 0, 0, None
    paths = []
    with source.open() as src:
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
        start = round(start_ns / scale_ns)
        end = round((start_ns + duration_ns) / scale_ns)
        if clock_period_ns:
            period_ticks = round(clock_period_ns / scale_ns)
            cycles = round((end - start) / period_ticks)
            segments = min(segments, cycles)
            bounds = [start + round(cycles * i / segments) * period_ticks
                      for i in range(segments + 1)]
        else:
            bounds = [start + round((end - start) * i / segments) for i in range(segments + 1)]
        if any(a >= b for a, b in zip(bounds, bounds[1:])):
            raise ValueError("Segmentación VCD demasiado fina para su timescale")

        def begin(index: int) -> None:
            nonlocal writer
            path = destination / f"activity-{index:03d}.vcd"
            writer = path.open("w")
            writer.write(joined)
            writer.write("#0\n$dumpvars\n" + "".join(states.values()) + "$end\n")
            paths.append(path)

        def finish(boundary: int) -> None:
            nonlocal writer
            if writer:
                writer.write(f"#{boundary - bounds[segment]}\n")
                writer.close()
                writer = None

        for line in src:
            value = line.strip()
            if value.startswith("#"):
                timestamp = int(value[1:])
                last_time = timestamp
                if timestamp > end:
                    break
                if timestamp >= start and not emitted:
                    begin(segment)
                    emitted = True
                while emitted and segment < segments - 1 and timestamp >= bounds[segment + 1]:
                    finish(bounds[segment + 1])
                    segment += 1
                    begin(segment)
                if emitted:
                    writer.write(f"#{timestamp - bounds[segment]}\n")
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
                    writer.write(line)
                states[identifier] = line
        if not emitted or last_time < end:
            if writer:
                writer.close()
            raise ValueError("VCD truncado: falta parte de la ventana activa")
        finish(bounds[segment + 1])
    if len(paths) != segments:
        raise ValueError(f"VCD incompleto: {len(paths)} de {segments} segmentos")
    return {"start_ns": start_ns, "duration_ns": duration_ns, "nets": sorted(nets),
            "scope": scope, "time_origin": "segment-start", "segments": [
                {"path": p, "duration_ns": (bounds[i + 1] - bounds[i]) * scale_ns,
                 "sha256": sha256(p)} for i, p in enumerate(paths)]}


def timing_metrics(state: dict, period: float, reports: Path) -> tuple[dict, bool, bool, bool]:
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
        if row["fmax_estimate_mhz"] is None:
            clock_report = reports / corner / "clock.rpt"
            clock_text = clock_report.read_text() if clock_report.is_file() else ""
            printed_fmax = re.search(r"\bfmax\s*=\s*(\S+)", clock_text)
            try:
                fmax = float(printed_fmax[1]) if printed_fmax else math.nan
            except ValueError:
                fmax = math.nan
            if math.isfinite(fmax) and fmax > 0:
                row["fmax_estimate_mhz"] = fmax
            else:
                min_period = re.search(r"period_min\s*=\s*([\d.eE+-]+)", clock_text)
                if min_period:
                    try:
                        value = float(min_period[1])
                    except ValueError:
                        value = math.nan
                    if math.isfinite(value) and value > 0:
                        row["fmax_estimate_mhz"] = 1000 / value
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
    setup_hold_pass = all(r["setup_ws_ns"] >= 0 and r["hold_ws_ns"] >= 0
                 and r["setup_violations"] == 0 and r["hold_violations"] == 0
                 for r in result.values())
    electrical_constraints_pass = all(r["constraint_warnings"] == 0 and r["unconstrained_endpoints"] == 0
                 and r["unannotated_routed_nets"] == 0
                 and r["max_slew_violations"] == 0 and r["max_cap_violations"] == 0
                 and r["max_fanout_violations"] == 0
                 for r in result.values())
    return result, setup_hold_pass and electrical_constraints_pass, setup_hold_pass, electrical_constraints_pass


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


def profiled_run(command: list[str], log: Path, timeout: float | None = None,
                 watch_paths: tuple[Path, ...] = ()) -> Path:
    """Run one process with GNU time and five-second memory/disk snapshots."""
    timer = shutil.which("/usr/bin/time")
    if not timer:
        raise RuntimeError("Se requiere GNU time (/usr/bin/time) para registrar consumo físico")
    def memory() -> dict[str, int]:
        values = {key: int(value) * 1024 for key, value in re.findall(
            r"^(MemAvailable|SwapFree):\s+(\d+) kB$", Path("/proc/meminfo").read_text(), re.M)}
        if "MemAvailable" not in values or "SwapFree" not in values:
            raise RuntimeError("No se pudieron leer MemAvailable/SwapFree de /proc/meminfo")
        return values

    available = memory()["MemAvailable"]
    if available < 1024**3:
        raise RuntimeError(f"MemAvailable inferior a 1 GiB antes de iniciar: {available} bytes")
    usage = log.with_name(log.stem + ".resource.txt")
    monitor = log.with_name(log.stem + ".monitor.jsonl")
    wrapped = [timer, "-v", "-o", str(usage), *command]
    print(f"$ {' '.join(wrapped)}", flush=True)
    environment = os.environ.copy()
    temporary = ROOT / "build/tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    environment["TMPDIR"] = str(temporary)
    environment["LC_ALL"] = "C"
    started, low_memory = time.monotonic(), 0
    with log.open("w", encoding="utf-8") as output, monitor.open("w", encoding="utf-8") as snapshots:
        process = subprocess.Popen(wrapped, cwd=ROOT, env=environment, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            while process.poll() is None:
                try:
                    remaining = None if timeout is None else max(0.01, timeout - (time.monotonic() - started))
                    process.wait(timeout=min(5, remaining) if remaining is not None else 5)
                except subprocess.TimeoutExpired:
                    pass
                current = memory()
                row = {"elapsed_s": round(time.monotonic() - started, 1), **current,
                       "disk_free_bytes": shutil.disk_usage(log.parent).free,
                       "watched_files_bytes": {str(path): path.stat().st_size for path in watch_paths if path.exists()}}
                snapshots.write(json.dumps(row, sort_keys=True) + "\n")
                snapshots.flush()
                low_memory = low_memory + 1 if current["MemAvailable"] < 512 * 1024**2 else 0
                if low_memory >= 2:
                    raise RuntimeError(f"MemAvailable inferior a 512 MiB en dos muestras: {current['MemAvailable']} bytes")
                if timeout is not None and time.monotonic() - started > timeout:
                    raise subprocess.TimeoutExpired(wrapped, timeout)
        except BaseException as exc:
            final = {"elapsed_s": round(time.monotonic() - started, 1), **memory(),
                     "disk_free_bytes": shutil.disk_usage(log.parent).free,
                     "watched_files_bytes": {str(path): path.stat().st_size
                                             for path in watch_paths if path.exists()},
                     "final": True, "abort_reason": type(exc).__name__}
            snapshots.write(json.dumps(final, sort_keys=True) + "\n")
            snapshots.flush()
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait()
            raise
        current = memory()
        snapshots.write(json.dumps({"elapsed_s": round(time.monotonic() - started, 1), **current,
                                    "disk_free_bytes": shutil.disk_usage(log.parent).free,
                                    "watched_files_bytes": {str(path): path.stat().st_size
                                                            for path in watch_paths if path.exists()},
                                    "final": True}, sort_keys=True) + "\n")
        snapshots.flush()
    if process.returncode:
        print("\n".join(log.read_text(errors="replace").splitlines()[-40:]))
        raise RuntimeError(f"{command[0]} falló ({process.returncode}); ver {log}")
    return usage


def write_power_sdc(source: Path, destination: Path, period: float) -> None:
    text, count = re.subn(
        r"(?m)(create_clock\s+-name\s+clk\s+-period\s+)\S+",
        lambda match: f"{match[1]}{period:.4f}", source.read_text())
    if count != 1 or not re.search(
            rf"(?m)create_clock\s+-name\s+clk\s+-period\s+{period:.4f}(?:\s|$)", text):
        raise ValueError(f"No se pudo ajustar el período de reloj en {source}")
    destination.write_text(text)


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
    diagnostic = re.search(r"(?im)^\s*(?:Error|ERROR)\b.*$|^.*vcd period .*differs from SDC.*$", log)
    if diagnostic:
        raise ValueError(diagnostic[0].strip())
    if not match or not cov or not annotated or not internal_pins or int(annotated[1]) == 0:
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


def combine_segment_power(parts: list[tuple[dict, float]], duration_ns: float) -> dict:
    keys = ("internal_w", "switching_w", "leakage_w", "total_w",
            "dynamic_energy_j", "total_energy_j")
    duration = sum(part_duration for _, part_duration in parts)
    if not math.isclose(duration, duration_ns, rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"Duración VCD segmentada {duration} ns difiere de la ventana {duration_ns} ns")
    result = {key: sum(power[key] * part_duration if key.endswith("_w") else power[key]
                       for power, part_duration in parts) for key in keys}
    result = {key: value / duration_ns if key.endswith("_w") else value
              for key, value in result.items()}
    result["dynamic_w"] = result["internal_w"] + result["switching_w"]
    return result


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
             (("openlane", "--bare-version"), ("openroad", "-version"), ("sta", "-version"))}
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
        run(["openlane", "--manual-pdk", "--pdk-root", str(pdk_root), "--pdk", "sky130A", "--scl", "sky130_fd_sc_hd",
             "--to", "OpenROAD.STAPostPNR", "--run-tag", "preflight", str(design / "config.yaml")],
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
            if scenario == "common" and period == config["clock_period_ns"]:
                results["scenarios"][scenario] = results["scenarios"]["target"]
                continue
            cfg = run_dir / f"openlane-{scenario}.json"
            write_json(cfg, configuration(config, sources, period))
            command = ["openlane", "--manual-pdk", "--pdk-root", str(pdk_root), "--pdk", "sky130A",
                       "--to", "OpenROAD.STAPostPNR", "--run-tag", scenario]
            if original_state:
                command += ["--from", "OpenROAD.STAPostPNR", "--with-initial-state", str(original_state)]
            run(command + [str(cfg)], run_dir / f"logs/openlane-{scenario}.log")
            state_file, state = find_state(run_dir / "runs" / scenario)
            if original_state is None:
                original_state = state_file
            timing, passed, setup_hold_pass, electrical_constraints_pass = timing_metrics(state, period, state_file.parent)
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
            profiled_run(["vvp", str(gate), f"+VECTORS={run_dir / 'ppa_vectors.txt'}",
                 f"+METRICS={scenario_dir / 'metrics.json'}", f"+POWER_VCD={raw_vcd}",
                 f"+PERIOD_NS={period}"], scenario_dir / "benchmark.log", watch_paths=(raw_vcd,))
            metrics = json.loads((scenario_dir / "metrics.json").read_text())
            baseline = json.loads((run_dir / "local_metrics.json").read_text())
            for key in ("passed", "input_samples", "output_samples", "latency_cycles", "block_cycles", "active_cycles"):
                if metrics[key] != baseline[key]:
                    raise ValueError(f"Netlist final difiere del RTL: {key}")
            activity_dir = scenario_dir / "activity-segments"
            activity_dir.mkdir()
            scope = config["bench"] + "/dut"
            coverage = split_vcd(raw_vcd, activity_dir, metrics["activity_start_ns"],
                                 metrics["activity_duration_ns"], scope,
                                 clock_period_ns=period)
            raw_vcd.unlink()
            sdc, spef = Path(state["sdc"]), nominal_spef(state)
            if not sdc.is_file() or not spef.is_file():
                raise ValueError("Faltan SDC resuelto o SPEF nominal para potencia")
            # --with-initial-state reuses the target P&R SDC for the common
            # frequency run. Keep the same physical constraints, but match the
            # clock period to the simulated activity or OpenSTA extrapolates
            # clock power at the wrong frequency.
            power_sdc = scenario_dir / "power.sdc"
            write_power_sdc(sdc, power_sdc, period)
            power_log = scenario_dir / "power.log"
            elapsed_ns = 0.0
            power_parts = []
            with power_log.open("w") as combined_log:
                for index, segment in enumerate(coverage["segments"]):
                    script = scenario_dir / f"power-{index:03d}.tcl"
                    script.write_text(power_script(run_dir / library.name, mapped, power_sdc, spef,
                                                   config["top"], segment["path"], scope))
                    log = scenario_dir / f"power-{index:03d}.log"
                    profiled_run(["sta", "-exit", str(script)], log, timeout=120,
                                 watch_paths=(segment["path"],))
                    part_metrics = {**metrics, "activity_duration_ns": segment["duration_ns"]}
                    part_coverage = {"start_ns": metrics["activity_start_ns"] + elapsed_ns,
                                     "duration_ns": segment["duration_ns"], "sha256": segment["sha256"]}
                    part = parse_power(log.read_text(), part_metrics, part_coverage)
                    elapsed_ns += segment["duration_ns"]
                    power_parts.append((part, segment["duration_ns"]))
                    combined_log.write(f"--- segment {index + 1}/{len(coverage['segments'])} ---\n")
                    combined_log.write(log.read_text())
                    log.unlink()
                    script.unlink()
                    segment["path"].unlink()
            total_duration = metrics["activity_duration_ns"]
            power = combine_segment_power(power_parts, total_duration)
            power.update(activity_coverage_pct=100.0,
                         coverage_kind="pin-activity-origin-vcd-clock-constant",
                         vcd_annotated_pins=part["vcd_annotated_pins"],
                         excluded_liberty_internal_pins=part["excluded_liberty_internal_pins"],
                         activity_window={"start_ns": metrics["activity_start_ns"],
                                          "duration_ns": total_duration,
                                          "segments": len(coverage["segments"]),
                                          "sha256": [s["sha256"] for s in coverage["segments"]]})
            activity_dir.rmdir()
            results["scenarios"][scenario] = {"clock_period_ns": period, "timing": timing,
                                               "timing_pass": passed, "setup_hold_pass": setup_hold_pass,
                                               "electrical_constraints_pass": electrical_constraints_pass,
                                               "power": power,
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
        for raw_vcd in run_dir.rglob("raw.vcd"):
            raw_vcd.unlink(missing_ok=True)
        for segments in run_dir.rglob("activity-segments"):
            shutil.rmtree(segments, ignore_errors=True)
        manifest.update(status="failed", error=str(exc))
        write_json(run_dir / "manifest.json", manifest)
        raise


def physical_summary(directory: Path, manifest: dict, result: dict) -> str:
    from scripts.ppa_compare import scenario_status

    link = Path(os.path.relpath(directory, REPORT.parent)).as_posix()
    text = f"# {manifest['config']['target']} — corrida {directory.name} (OpenLane 2 / SKY130)\n\n"
    text += "**Medición física completa; simulación funcional de netlist final, STA post-SPEF y potencia con VCD.**\n\n"
    provenance = manifest.get("resume_provenance")
    if provenance and provenance.get("reused_physical_layout"):
        source_run = Path(provenance["source_run"])
        source_link = Path(os.path.relpath(source_run, REPORT.parent)).as_posix()
        text += (f"Layout físico reutilizado de [{source_run.name}]({source_link}/manifest.json); "
                 "esta corrida no hizo placement ni routing nuevos. Se volvió a ejecutar "
                 "la simulación funcional de la netlist y el análisis de potencia.\n\n")
    text += "Potencia estimada TT/25 °C/1,8 V, sin retardos de simulación ni glitches temporales completos. No es signoff de fabricación.\n\n"
    text += "| Escenario | Reloj | Setup/hold | Restricciones eléctricas | Timing global | Potencia total | Energía total/muestra |\n|---|---:|---|---|---|---:|---:|\n"
    for name, m in result["scenarios"].items():
        setup, electrical, global_pass = scenario_status(m)
        text += f"| {name} | {1000/m['clock_period_ns']:g} MHz | {'PASS' if setup else 'FAIL'} | {'PASS' if electrical else 'FAIL'} | {'PASS' if global_pass else 'FAIL'} | {m['power']['total_w']:.9g} W | {m['power']['total_energy_j']:.9g} J |\n"
    target_metrics = json.loads((directory / "target/metrics.json").read_text())
    text += "\n## Área y benchmark\n\n"
    text += "| Medición | Resultado |\n|---|---:|\n"
    for label, key in (("Área final de celdas", "final_cell_area_um2"), ("Área del core", "core_area_um2"), ("Área del die", "die_area_um2")):
        text += f"| {label} | {result['areas'][key]:.3f} µm² |\n"
    for label, key, suffix in (("Latencia", "latency_cycles", "ciclos"), ("Ciclos por bloque", "block_cycles", "ciclos"), ("Ciclos activos", "active_cycles", "ciclos")):
        text += f"| {label} | {target_metrics[key]} {suffix} |\n"
    target_timing = result["scenarios"]["target"]
    qualifier = "demostrado" if target_timing["timing_pass"] else "condicionado; timing global FAIL"
    text += f"| Throughput efectivo ({qualifier}) | {target_metrics['throughput_samples_per_second']:.3f} muestras/s |\n"
    sustained = 8e9 / (target_metrics["block_cycles"] * target_timing["clock_period_ns"])
    text += f"| Throughput sostenido ({qualifier}) | {sustained:.3f} muestras/s |\n"
    text += "\nEl throughput al reloj objetivo queda condicionado a PASS global de timing. Fmax es estimación registro a registro, sin barrido.\n\n"
    text += "## Potencia y energía\n\n"
    text += "| Escenario | Interna (W) | Switching (W) | Dinámica (W) | Leakage (W) | Total (W) | Energía dinámica/muestra (J) | Energía total/muestra (J) |\n|---|---:|---:|---:|---:|---:|---:|---:|\n"
    for name, m in result["scenarios"].items():
        p = m["power"]
        dynamic = p.get("dynamic_w", p["internal_w"] + p["switching_w"])
        text += f"| {name} | {p['internal_w']:.9g} | {p['switching_w']:.9g} | {dynamic:.9g} | {p['leakage_w']:.9g} | {p['total_w']:.9g} | {p['dynamic_energy_j']:.9g} | {p['total_energy_j']:.9g} |\n"
    text += "\n## Timing por corner\n\n| Escenario | Corner | Setup WS (ns) | Hold WS (ns) | Setup/hold violaciones | Slew / cap / fanout violaciones | Fmax estimada (MHz) |\n|---|---|---:|---:|---:|---:|---:|\n"
    for name, m in result["scenarios"].items():
        for corner, row in m["timing"].items():
            fmax = row.get("fmax_estimate_mhz")
            fmax_text = f"{fmax:.2f}" if isinstance(fmax, (int, float)) and math.isfinite(fmax) else "No medida"
            text += (f"| {name} | {corner} | {row['setup_ws_ns']:.4f} | {row['hold_ws_ns']:.4f} | "
                     f"{row['setup_violations']} / {row['hold_violations']} | "
                     f"{row['max_slew_violations']} / {row['max_cap_violations']} / {row['max_fanout_violations']} | "
                     f"{fmax_text} |\n")
    for name in ("manifest.json", "physical_metrics.json", "local_metrics.json", "gate_metrics.json",
                 "resources.json", "openlane-target.json", "openlane-common.json"):
        if (directory / name).is_file():
            text += f"- [{name}]({link}/{name}).\n"
    if (directory / "runs").is_dir():
        text += f"- [STA, netlist final, SPEF, SDF y restricciones resueltas]({link}/runs/).\n"
    activity_links = []
    for scenario in ("target", "common"):
        if (directory / scenario).is_dir():
            activity_links.append((scenario, scenario))
        elif (scenario == "common" and "common" in result["scenarios"]
              and result["scenarios"]["common"]["clock_period_ns"] == result["scenarios"]["target"]["clock_period_ns"]
              and (directory / "target").is_dir()):
            activity_links.append((scenario, "target"))
            text += "El escenario common comparte la corrida target al mismo reloj; no se creó un directorio adicional.\n"
    if activity_links:
        text += "- " + " y ".join(f"[Actividad y potencia {label}]({link}/{path}/)"
                                      for label, path in activity_links) + ".\n"
    text += "- Los directorios de escenario existentes conservan `power.sdc` y el log combinado `power.log`.\n"
    return text
