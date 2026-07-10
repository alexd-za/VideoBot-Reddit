# Capability boundaries

## What the Fusion MCP can potentially verify

Exact availability depends on the connected server and Fusion version. Inspect the live tool list.

Typical semantic checks include:

- active document and design context;
- feature, sketch, body, and component structure;
- parameter values and dimensions;
- sketch constraints;
- joints, axes, and limits;
- interference and clearance inspection;
- feature failures;
- exports and document saves.

Do not assume every server exposes every operation.

## What the local STL auditor verifies

The included auditor deterministically measures the exported triangulated mesh:

- bounding-box dimensions;
- surface area;
- signed enclosed volume estimate;
- boundary edges;
- non-manifold edges;
- degenerate triangles;
- duplicate triangles;
- inconsistent shared-edge winding;
- edge-connected shell count;
- triangle count and unique vertices;
- file hash for traceability;
- contract ranges and tolerances.

## What neither layer proves automatically

Unless a specialised analysis is performed, do not claim verification of:

- minimum wall thickness;
- local clearances smaller than mesh tessellation error;
- stress, strain, stiffness, fatigue, impact, or safety factor;
- material suitability;
- print shrinkage or dimensional compensation;
- support requirements and slicer behaviour;
- real fastener preload, backlash, lubrication, or wear;
- servo torque and current requirements;
- centre of gravity under all configurations;
- competition-rule compliance;
- physical manufacturability beyond basic mesh validity.

These require Fusion analysis tools, dedicated simulation, slicer inspection, calculations, measurement, or human engineering review.
