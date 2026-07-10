from __future__ import annotations

import hashlib
import math
from pathlib import Path
import struct
from typing import Any, Sequence

Vec3 = tuple[float, float, float]
Triangle = tuple[Vec3, Vec3, Vec3]


class GuardianError(Exception):
    """Expected user input, schema, or mesh error."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(value: Vec3) -> float:
    return math.sqrt(_dot(value, value))


def _finite(vertex: Vec3) -> bool:
    return all(math.isfinite(value) for value in vertex)


def read_stl(path: Path) -> tuple[str, list[Triangle]]:
    if not path.is_file():
        raise GuardianError(f"STL file not found: {path}")
    size = path.stat().st_size
    if size < 15:
        raise GuardianError(f"STL file is too small to be valid: {path}")
    with path.open("rb") as handle:
        header = handle.read(84)
    if len(header) == 84:
        count = struct.unpack_from("<I", header, 80)[0]
        expected = 84 + count * 50
        if count > 0 and expected <= size and size - expected <= 1024:
            return "binary", _read_binary(path, count)
    try:
        return "ascii", _read_ascii(path)
    except UnicodeDecodeError as exc:
        raise GuardianError("File is neither a valid binary nor ASCII STL") from exc


def _read_binary(path: Path, count: int) -> list[Triangle]:
    triangles: list[Triangle] = []
    with path.open("rb") as handle:
        handle.seek(84)
        for index in range(count):
            record = handle.read(50)
            if len(record) != 50:
                raise GuardianError(f"Binary STL ended early at triangle {index}")
            values = struct.unpack("<12fH", record)
            triangle: Triangle = (
                (float(values[3]), float(values[4]), float(values[5])),
                (float(values[6]), float(values[7]), float(values[8])),
                (float(values[9]), float(values[10]), float(values[11])),
            )
            if not all(_finite(vertex) for vertex in triangle):
                raise GuardianError(f"Triangle {index} contains invalid coordinates")
            triangles.append(triangle)
    if not triangles:
        raise GuardianError("STL contains no triangles")
    return triangles


def _read_ascii(path: Path) -> list[Triangle]:
    vertices: list[Vec3] = []
    with path.open("r", encoding="utf-8-sig", errors="strict") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped.lower().startswith("vertex "):
                continue
            parts = stripped.split()
            if len(parts) != 4:
                raise GuardianError(f"Malformed vertex at line {line_number}")
            try:
                vertex = float(parts[1]), float(parts[2]), float(parts[3])
            except ValueError as exc:
                raise GuardianError(f"Invalid numeric vertex at line {line_number}") from exc
            if not _finite(vertex):
                raise GuardianError(f"Invalid coordinate at line {line_number}")
            vertices.append(vertex)
    if not vertices or len(vertices) % 3:
        raise GuardianError("ASCII STL has no complete triangle records")
    return [tuple(vertices[i : i + 3]) for i in range(0, len(vertices), 3)]  # type: ignore[list-item]


class _DisjointSet:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left, right = self.find(left), self.find(right)
        if left == right:
            return
        if self.rank[left] < self.rank[right]:
            left, right = right, left
        self.parent[right] = left
        if self.rank[left] == self.rank[right]:
            self.rank[left] += 1


def _quantize(vertex: Vec3, tolerance: float) -> tuple[int, int, int]:
    return tuple(int(round(value / tolerance)) for value in vertex)  # type: ignore[return-value]


def analyze_mesh(
    triangles: Sequence[Triangle],
    *,
    weld_tolerance_mm: float = 1e-6,
    area_epsilon_mm2: float = 1e-12,
) -> dict[str, Any]:
    if not triangles:
        raise GuardianError("mesh contains no triangles")
    if weld_tolerance_mm <= 0 or area_epsilon_mm2 < 0:
        raise GuardianError("invalid analysis tolerances")

    mins = [math.inf] * 3
    maxs = [-math.inf] * 3
    unique_vertices: set[tuple[int, int, int]] = set()
    edge_records: dict[tuple[Any, Any], dict[str, Any]] = {}
    duplicate_counts: dict[tuple[Any, ...], int] = {}
    dsu = _DisjointSet(len(triangles))
    surface_area = signed_volume = 0.0
    degenerate = 0

    for index, triangle in enumerate(triangles):
        keys = [_quantize(vertex, weld_tolerance_mm) for vertex in triangle]
        unique_vertices.update(keys)
        for vertex in triangle:
            for axis in range(3):
                mins[axis] = min(mins[axis], vertex[axis])
                maxs[axis] = max(maxs[axis], vertex[axis])
        cross = _cross(_sub(triangle[1], triangle[0]), _sub(triangle[2], triangle[0]))
        area = 0.5 * _norm(cross)
        surface_area += area
        degenerate += int(area <= area_epsilon_mm2)
        signed_volume += _dot(triangle[0], _cross(triangle[1], triangle[2])) / 6.0
        duplicate_key = tuple(sorted(keys))
        duplicate_counts[duplicate_key] = duplicate_counts.get(duplicate_key, 0) + 1
        for start, end in ((keys[0], keys[1]), (keys[1], keys[2]), (keys[2], keys[0])):
            edge = (start, end) if start <= end else (end, start)
            direction = 1 if start <= end else -1
            record = edge_records.setdefault(edge, {"count": 0, "direction": 0, "triangles": []})
            record["count"] += 1
            record["direction"] += direction
            record["triangles"].append(index)

    boundary = nonmanifold = inconsistent = manifold = 0
    for record in edge_records.values():
        count = int(record["count"])
        if count == 1:
            boundary += 1
        elif count == 2:
            manifold += 1
            inconsistent += int(abs(int(record["direction"])) == 2)
        else:
            nonmanifold += 1
        attached = record["triangles"]
        for other in attached[1:]:
            dsu.union(attached[0], other)

    dimensions = [maxs[i] - mins[i] for i in range(3)]
    duplicate_triangles = sum(count - 1 for count in duplicate_counts.values() if count > 1)
    return {
        "triangle_count": len(triangles),
        "unique_vertex_count": len(unique_vertices),
        "edge_count": len(edge_records),
        "manifold_edge_count": manifold,
        "boundary_edge_count": boundary,
        "nonmanifold_edge_count": nonmanifold,
        "inconsistent_winding_edge_count": inconsistent,
        "degenerate_triangle_count": degenerate,
        "duplicate_triangle_count": duplicate_triangles,
        "shell_count": len({dsu.find(i) for i in range(len(triangles))}),
        "bounding_box_mm": {
            "min": {"x": mins[0], "y": mins[1], "z": mins[2]},
            "max": {"x": maxs[0], "y": maxs[1], "z": maxs[2]},
        },
        "dimensions_mm": {"x": dimensions[0], "y": dimensions[1], "z": dimensions[2]},
        "surface_area_mm2": surface_area,
        "signed_volume_mm3": signed_volume,
        "absolute_volume_mm3": abs(signed_volume),
        "watertight": boundary == 0 and nonmanifold == 0 and degenerate == 0,
    }


def build_plate_contact(
    triangles: Sequence[Triangle], axis: str, plane_mm: float, tolerance_mm: float
) -> int:
    if axis not in {"x", "y", "z"} or tolerance_mm < 0:
        raise GuardianError("invalid build_plate settings")
    axis_index = {"x": 0, "y": 1, "z": 2}[axis]
    vertices = {
        vertex
        for triangle in triangles
        for vertex in triangle
        if abs(vertex[axis_index] - plane_mm) <= tolerance_mm
    }
    return len(vertices)


def cube_triangles(size: float = 10.0) -> list[Triangle]:
    p = [
        (0.0, 0.0, 0.0), (size, 0.0, 0.0), (size, size, 0.0), (0.0, size, 0.0),
        (0.0, 0.0, size), (size, 0.0, size), (size, size, size), (0.0, size, size),
    ]
    faces = [
        (0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4), (3, 7, 6), (3, 6, 2),
        (0, 4, 7), (0, 7, 3), (1, 2, 6), (1, 6, 5),
    ]
    return [(p[a], p[b], p[c]) for a, b, c in faces]


def write_binary_stl(path: Path, triangles: Sequence[Triangle]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(b"Fusion CAD Guardian".ljust(80, b"\0"))
        handle.write(struct.pack("<I", len(triangles)))
        for triangle in triangles:
            cross = _cross(_sub(triangle[1], triangle[0]), _sub(triangle[2], triangle[0]))
            length = _norm(cross)
            normal = (0.0, 0.0, 0.0) if not length else tuple(v / length for v in cross)
            values = (*normal, *triangle[0], *triangle[1], *triangle[2], 0)
            handle.write(struct.pack("<12fH", *values))
