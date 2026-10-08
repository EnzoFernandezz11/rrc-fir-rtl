#!/usr/bin/env python3
"""Valida la configuración compartida y el registro de RTL."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CONFIRMED = {
    "modulation": "QPSK",
    "complex_data": True,
    "filter_family": "RRCOS",
    "coefficient_count": 8,
    "rolloff": 0.5,
    "minimum_sqnr_db": 40,
    "minimum_clock_mhz": {"fast": 100, "slow": 10},
}
REQUIRED_DECISIONS = {
    "coefficients",
    "coefficient_normalization",
    "frequency_method",
    "fixed_point_format",
    "rtl_interface",
    "target_technology",
    "power_method",
}
TARGET_NAME = re.compile(r"^[a-z][a-z0-9_-]*$")


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"No se pudo leer {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: la raíz debe ser un objeto JSON")
    return data


def validate_project(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise ValueError("config/project.json: schema_version debe ser 1")
    confirmed = data.get("confirmed")
    if confirmed != EXPECTED_CONFIRMED:
        raise ValueError(
            "config/project.json: los requisitos confirmados no coinciden con la "
            "consigna y las aclaraciones registradas; revisar docs/contrato-tecnico.md antes de cambiarlos"
        )
    decisions = data.get("decisions")
    if not isinstance(decisions, dict) or not REQUIRED_DECISIONS <= decisions.keys():
        raise ValueError("config/project.json: faltan decisiones de etapa 0")
    coefficients = decisions["coefficients"]
    if coefficients is not None:
        if not isinstance(coefficients, list) or len(coefficients) != 8:
            raise ValueError("decisions.coefficients debe tener exactamente 8 valores")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in coefficients
        ):
            raise ValueError("los coeficientes deben ser números reales finitos")


def relative_file(root: Path, raw: Any, field: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"{field}: se requiere una ruta relativa")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field}: la ruta debe quedar dentro del repositorio")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise ValueError(f"{field}: no existe el archivo {raw}")
    return resolved


def validate_targets(data: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    if data.get("schema_version") != 1:
        raise ValueError("config/rtl_targets.json: schema_version debe ser 1")
    targets = data.get("targets")
    if not isinstance(targets, list):
        raise ValueError("config/rtl_targets.json: targets debe ser una lista")
    seen: set[str] = set()
    for index, target in enumerate(targets):
        prefix = f"targets[{index}]"
        if not isinstance(target, dict):
            raise ValueError(f"{prefix}: debe ser un objeto")
        name = target.get("name")
        if not isinstance(name, str) or not TARGET_NAME.fullmatch(name):
            raise ValueError(f"{prefix}.name: usar minúsculas, números, _ o -")
        if name in seen:
            raise ValueError(f"nombre de variante duplicado: {name}")
        seen.add(name)
        if target.get("domain") not in {"time", "frequency"}:
            raise ValueError(f"{prefix}.domain: usar time o frequency")
        if target.get("architecture") not in {"serial", "optimized"}:
            raise ValueError(f"{prefix}.architecture: usar serial u optimized")
        for field in ("testbench_top", "rtl_top"):
            if not isinstance(target.get(field), str) or not target[field]:
                raise ValueError(f"{prefix}.{field}: nombre de módulo requerido")
        sources = target.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError(f"{prefix}.sources: lista no vacía requerida")
        for source in sources:
            relative_file(root, source, f"{prefix}.sources")
        relative_file(root, target.get("testbench"), f"{prefix}.testbench")
        if target.get("synth_script") is not None:
            relative_file(root, target["synth_script"], f"{prefix}.synth_script")
    return targets


def load_project(root: Path = ROOT) -> dict[str, Any]:
    data = read_json(root / "config/project.json")
    validate_project(data)
    return data


def load_targets(root: Path = ROOT) -> list[dict[str, Any]]:
    return validate_targets(read_json(root / "config/rtl_targets.json"), root)


def main() -> int:
    try:
        project = load_project()
        targets = load_targets()
        if not (ROOT / "docs/consigna-actualizada.md").is_file():
            raise ValueError("falta docs/consigna-actualizada.md")
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    pending = [
        key for key, value in project["decisions"].items()
        if value is None or (isinstance(value, dict) and value.get("status") == "proposed")
    ]
    print("Contrato: requisitos formales válidos")
    print(f"Decisiones pendientes: {', '.join(pending) if pending else 'ninguna'}")
    print(f"Variantes RTL registradas: {len(targets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
