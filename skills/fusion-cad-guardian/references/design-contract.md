# Design contract

The contract is JSON and applies to one exported STL. Use one contract per printable part when acceptance criteria differ.

## Supported fields

```json
{
  "schema_version": 1,
  "part_name": "Rover Camera Bracket",
  "units": "mm",
  "expected_dimensions_mm": {
    "x": {"target": 80.0, "tolerance": 0.2},
    "y": {"min": 39.8, "max": 40.2},
    "z": {"target": 5.0, "tolerance": 0.1}
  },
  "volume_mm3": {"min": 1000, "max": 20000},
  "surface_area_mm2": {"min": 100},
  "require_watertight": true,
  "max_shells": 1,
  "max_boundary_edges": 0,
  "max_nonmanifold_edges": 0,
  "max_degenerate_triangles": 0,
  "max_duplicate_triangles": 0,
  "max_inconsistent_winding_edges": 0,
  "min_triangles": 12,
  "max_triangles": 2000000,
  "require_positive_signed_volume": true,
  "build_plate": {
    "axis": "z",
    "plane_mm": 0.0,
    "tolerance_mm": 0.05,
    "min_contact_vertices": 3
  },
  "notes": ["Export only the final printable body"]
}
```

## Range forms

A numeric metric can use any of these forms:

```json
{"target": 10.0, "tolerance": 0.1}
```

```json
{"min": 9.9, "max": 10.1}
```

```json
{"min": 9.9}
```

```json
{"max": 10.1}
```

For dimensions, the axis keys are `x`, `y`, and `z`.

## Contract principles

- Use tolerances that account for STL tessellation and export resolution.
- A bounding box cannot prove the location of internal holes or interfaces.
- Do not invent a volume range merely to obtain a pass.
- Keep semantic Fusion requirements in the Fusion report, not in the STL contract.
- Record uncertain values as assumptions and seek engineering confirmation before manufacture.
