from __future__ import annotations

from typing import Any

from .core import GuardianError, Triangle, build_plate_contact

SUPPORTED_KEYS = {
    "schema_version", "part_name", "units", "expected_dimensions_mm", "volume_mm3",
    "surface_area_mm2", "require_watertight", "max_shells", "max_boundary_edges",
    "max_nonmanifold_edges", "max_degenerate_triangles", "max_duplicate_triangles",
    "max_inconsistent_winding_edges", "min_triangles", "max_triangles",
    "require_positive_signed_volume", "build_plate", "notes",
}


def default_contract(part_name: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "part_name": part_name,
        "units": "mm",
        "expected_dimensions_mm": {
            "x": {"target": 20.0, "tolerance": 0.1},
            "y": {"target": 20.0, "tolerance": 0.1},
            "z": {"target": 10.0, "tolerance": 0.1},
        },
        "require_watertight": True,
        "max_shells": 1,
        "max_boundary_edges": 0,
        "max_nonmanifold_edges": 0,
        "max_degenerate_triangles": 0,
        "max_duplicate_triangles": 0,
        "max_inconsistent_winding_edges": 0,
        "min_triangles": 12,
        "max_triangles": 2_000_000,
        "require_positive_signed_volume": True,
        "notes": ["Replace example dimensions with actual acceptance criteria."],
    }


def _validate_range(value: Any, name: str) -> None:
    if not isinstance(value, dict) or not value:
        raise GuardianError(f"{name} must be a non-empty object")
    allowed = {"target", "tolerance", "min", "max"}
    unknown = set(value) - allowed
    if unknown:
        raise GuardianError(f"{name} has unknown keys: {sorted(unknown)}")
    if "target" in value:
        if "tolerance" not in value or len(value) != 2:
            raise GuardianError(f"{name} target requires exactly target+tolerance")
        if float(value["tolerance"]) < 0:
            raise GuardianError(f"{name}.tolerance cannot be negative")
    elif not ({"min", "max"} & set(value)):
        raise GuardianError(f"{name} requires target+tolerance or min/max")
    for key, item in value.items():
        if not isinstance(item, (int, float)):
            raise GuardianError(f"{name}.{key} must be numeric")
    if "min" in value and "max" in value and float(value["min"]) > float(value["max"]):
        raise GuardianError(f"{name}.min cannot exceed max")


def validate_contract(contract: Any) -> dict[str, Any]:
    if not isinstance(contract, dict):
        raise GuardianError("contract must be a JSON object")
    unknown = set(contract) - SUPPORTED_KEYS
    if unknown:
        raise GuardianError(f"unknown contract fields: {sorted(unknown)}")
    if contract.get("schema_version", 1) != 1:
        raise GuardianError("only schema_version 1 is supported")
    if contract.get("units", "mm") != "mm":
        raise GuardianError("STL contract units must be mm")
    dimensions = contract.get("expected_dimensions_mm", {})
    if not isinstance(dimensions, dict) or set(dimensions) - {"x", "y", "z"}:
        raise GuardianError("expected_dimensions_mm must contain only x/y/z")
    for axis, requirement in dimensions.items():
        _validate_range(requirement, f"expected_dimensions_mm.{axis}")
    for key in ("volume_mm3", "surface_area_mm2"):
        if key in contract:
            _validate_range(contract[key], key)
    for key in (
        "max_shells", "max_boundary_edges", "max_nonmanifold_edges",
        "max_degenerate_triangles", "max_duplicate_triangles",
        "max_inconsistent_winding_edges", "min_triangles", "max_triangles",
    ):
        if key in contract and (not isinstance(contract[key], int) or contract[key] < 0):
            raise GuardianError(f"{key} must be a non-negative integer")
    plate = contract.get("build_plate")
    if plate is not None:
        if not isinstance(plate, dict) or set(plate) - {"axis", "plane_mm", "tolerance_mm", "min_contact_vertices"}:
            raise GuardianError("invalid build_plate object")
        if plate.get("axis") not in {"x", "y", "z"}:
            raise GuardianError("build_plate.axis must be x, y, or z")
        if float(plate.get("tolerance_mm", 0)) < 0:
            raise GuardianError("build_plate.tolerance_mm cannot be negative")
    return contract


def _range_check(value: float, requirement: dict[str, Any]) -> tuple[bool, str]:
    if "target" in requirement:
        target, tolerance = float(requirement["target"]), float(requirement["tolerance"])
        return abs(value - target) <= tolerance, f"{target} ± {tolerance}"
    minimum = float(requirement.get("min", float("-inf")))
    maximum = float(requirement.get("max", float("inf")))
    return minimum <= value <= maximum, f"[{minimum}, {maximum}]"


def evaluate_contract(
    metrics: dict[str, Any], contract: dict[str, Any], triangles: list[Triangle]
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, actual: Any, expected: Any) -> None:
        checks.append({"id": check_id, "status": "PASS" if passed else "FAIL", "actual": actual, "expected": expected})

    for axis, requirement in contract.get("expected_dimensions_mm", {}).items():
        actual = float(metrics["dimensions_mm"][axis])
        passed, expected = _range_check(actual, requirement)
        add(f"dimension_{axis}", passed, actual, expected)
    for key, metric_key in (("volume_mm3", "absolute_volume_mm3"), ("surface_area_mm2", "surface_area_mm2")):
        if key in contract:
            actual = float(metrics[metric_key])
            passed, expected = _range_check(actual, contract[key])
            add(key, passed, actual, expected)
    mappings = {
        "max_shells": "shell_count", "max_boundary_edges": "boundary_edge_count",
        "max_nonmanifold_edges": "nonmanifold_edge_count",
        "max_degenerate_triangles": "degenerate_triangle_count",
        "max_duplicate_triangles": "duplicate_triangle_count",
        "max_inconsistent_winding_edges": "inconsistent_winding_edge_count",
        "max_triangles": "triangle_count",
    }
    for contract_key, metric_key in mappings.items():
        if contract_key in contract:
            add(contract_key, metrics[metric_key] <= contract[contract_key], metrics[metric_key], f"<= {contract[contract_key]}")
    if "min_triangles" in contract:
        add("min_triangles", metrics["triangle_count"] >= contract["min_triangles"], metrics["triangle_count"], f">= {contract['min_triangles']}")
    if contract.get("require_watertight"):
        add("watertight", bool(metrics["watertight"]), metrics["watertight"], True)
    if contract.get("require_positive_signed_volume"):
        add("positive_signed_volume", metrics["signed_volume_mm3"] > 0, metrics["signed_volume_mm3"], "> 0")
    if "build_plate" in contract:
        plate = contract["build_plate"]
        count = build_plate_contact(
            triangles, plate["axis"], float(plate.get("plane_mm", 0.0)), float(plate.get("tolerance_mm", 0.05))
        )
        minimum = int(plate.get("min_contact_vertices", 3))
        add("build_plate_contact", count >= minimum, count, f">= {minimum}")
    return checks
