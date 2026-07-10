---
name: fusion-cad-guardian
description: Verify Autodesk Fusion CAD work created or modified through a Fusion MCP server. Use for mechanical parts, assemblies, rover components, 3D-printable models, dimensional acceptance criteria, interference and motion checks, STL mesh auditing, before/after regression checks, and evidence-based repair loops. Do not use as a replacement for the Fusion MCP server or claim that STL analysis verifies joints, interference, clearances, or wall thickness.
---

# Fusion CAD Guardian

Use this skill **alongside** an Autodesk Fusion MCP server. The MCP edits and inspects the live Fusion design. This skill adds what a generic MCP connection usually lacks:

- a machine-readable design contract;
- explicit pass/fail criteria before modeling starts;
- a bounded create -> inspect -> repair loop;
- deterministic offline auditing of exported STL files;
- before/after mesh regression comparison;
- a combined evidence report that separates verified facts from assumptions.

The local auditor is dependency-free Python and runs outside Fusion. It never executes arbitrary Python inside Fusion.

## Non-negotiable boundaries

1. Use the official or user-selected Fusion MCP server for live CAD actions.
2. Do not install another Fusion add-in unless the user explicitly requests it.
3. Never claim a design passes because it looks correct in the viewport.
4. Never claim STL analysis verifies:
   - assembly interference;
   - joint definitions or range of motion;
   - component connectivity or fasteners;
   - minimum wall thickness;
   - manufacturing tolerances;
   - structural strength.
5. Verify those items in Fusion through available MCP tools or mark them `NOT VERIFIED`.
6. Run mesh checks only on exported geometry that corresponds to the final candidate design.
7. Preserve the user’s original document. Work in a new design, duplicate, version, or explicit checkpoint whenever Fusion supports it.

Read `references/capability-boundaries.md` when deciding what can be proven.

## Required workflow

### 1. Discover the live Fusion environment

- Confirm a Fusion MCP server is connected.
- Inspect the available MCP tools instead of assuming tool names.
- Confirm the active document and design workspace.
- Identify whether the task concerns a single part, multiple printable parts, or an assembly.
- Record the units. Default to millimetres only when the user did not specify units.

If Fusion or the MCP server is unavailable, stop live CAD work. You may still prepare a design contract or audit an existing STL.

### 2. Create the design contract before editing

Translate the request into explicit requirements. Create a project-local file such as:

```text
fusion-guardian/<part-name>.contract.json
```

Start from `assets/contract.example.json` or run:

```powershell
py -3 "<skill-dir>\scripts\guardian.py" init --out "fusion-guardian\part.contract.json" --part-name "Part Name"
```

Include only requirements supported by evidence. Distinguish:

- **Fusion semantic requirements**: components, sketches, parameters, joints, interference, motion, naming, feature structure.
- **Mesh requirements**: exported dimensions, closed-manifold status, shell count, triangle defects, approximate volume and surface area.
- **Human/mechanical requirements**: load cases, material choice, tolerances, safety factor, print orientation, fastener selection.

State assumptions before making geometry. Do not silently invent critical mechanical dimensions.

Read `references/design-contract.md` for the schema and examples.

### 3. Plan the model as testable phases

Break work into short phases. A typical sequence is:

1. parameters and component structure;
2. primary constrained sketches;
3. base features;
4. interfaces, holes, clearances, and mounting geometry;
5. joints or assembly relationships;
6. semantic verification in Fusion;
7. export and deterministic mesh verification.

For mechanisms, use `references/mechanical-verification.md`.

### 4. Build through Fusion MCP

For each phase:

- perform only the planned changes;
- use named parameters where practical;
- use separate components for separate physical parts;
- use descriptive feature, sketch, body, and component names;
- prefer fully constrained sketches;
- inspect the result before proceeding;
- record failures instead of masking them with unrelated geometry.

Do not use an unrestricted Python-execution bridge merely because it is easier. Use it only if the user explicitly chose that architecture and approves the script.

### 5. Run semantic checks inside Fusion

Use the available MCP tools to verify the live design. At minimum, check every applicable item:

- expected component and body counts;
- expected component/body names;
- critical dimensions and named parameters;
- sketch constraint status;
- feature health and timeline errors;
- component relationships;
- joint type, axis, limits, and range of motion;
- interference over representative motion positions;
- clearances at critical interfaces;
- intended connection between parts;
- export selection matches the intended printable body/component.

Save a concise semantic report, for example:

```text
fusion-guardian/<part-name>.fusion-report.md
```

Use the statuses `PASS`, `FAIL`, `NOT VERIFIED`, and `NOT APPLICABLE`.

### 6. Export final candidates

Export each final printable part or body to STL in millimetres, preferably with a descriptive filename:

```text
fusion-guardian/exports/<component-name>.stl
```

Use an MCP export tool when available. If the current MCP server cannot export meshes, explain the limitation and request a one-time manual STL export. Do not pretend the local auditor can read `.f3d` files.

### 7. Run deterministic mesh audit

Run:

```powershell
py -3 "<skill-dir>\scripts\guardian.py" audit `
  "fusion-guardian\exports\part.stl" `
  --contract "fusion-guardian\part.contract.json" `
  --json "fusion-guardian\part.mesh-report.json" `
  --markdown "fusion-guardian\part.mesh-report.md"
```

The auditor checks:

- STL format and file hash;
- bounding-box dimensions;
- triangle and unique-vertex counts;
- degenerate and duplicate triangles;
- boundary and non-manifold edges;
- inconsistent winding edges;
- edge-connected shell count;
- signed volume and surface area;
- optional build-plane contact criteria;
- explicit contract ranges and tolerances.

Treat the command exit code as authoritative:

- `0`: audit completed and contract passed, or audit-only mode completed;
- `1`: contract failed or batch contained failures;
- `2`: input, schema, or execution error.

### 8. Compare revisions when repairing

Before a risky change, audit the current exported STL. After the change, audit again and run:

```powershell
py -3 "<skill-dir>\scripts\guardian.py" compare `
  "fusion-guardian\before.mesh-report.json" `
  "fusion-guardian\after.mesh-report.json" `
  --json "fusion-guardian\regression.json" `
  --markdown "fusion-guardian\regression.md"
```

Review regressions in manifoldness, shell count, defects, dimensions, volume, and contract verdict.

### 9. Repair with a bounded loop

Use at most three automatic repair iterations unless the user requests more.

For each iteration:

1. identify the smallest failed requirement;
2. modify only the relevant Fusion features;
3. rerun the corresponding Fusion semantic check;
4. re-export the affected STL;
5. rerun the mesh audit;
6. compare against the previous report;
7. stop when the design passes or when the same failure repeats twice.

Do not repeatedly regenerate the full model when a local repair is possible.

### 10. Produce the final evidence report

The final response must include:

- design/document examined;
- requirements and assumptions;
- Fusion semantic checks with statuses;
- mesh-audit verdict and report paths;
- before/after regressions if applicable;
- remaining `NOT VERIFIED` items;
- exact reasons for any failure;
- recommended human checks before manufacturing or competition use.

Overall status rules:

- `PASS`: all required Fusion semantic checks pass and all required mesh checks pass.
- `CONDITIONAL PASS`: automated checks pass, but material, load, tolerance, or other human engineering checks remain.
- `FAIL`: at least one required check fails.
- `INCOMPLETE`: required evidence could not be collected.

## Local auditor commands

```powershell
# Create a contract template
py -3 "<skill-dir>\scripts\guardian.py" init --out contract.json --part-name "Bracket"

# Audit one STL
py -3 "<skill-dir>\scripts\guardian.py" audit part.stl --contract contract.json

# Audit and write reports
py -3 "<skill-dir>\scripts\guardian.py" audit part.stl --contract contract.json --json report.json --markdown report.md

# Compare two JSON reports
py -3 "<skill-dir>\scripts\guardian.py" compare before.json after.json --markdown comparison.md

# Audit several parts from a manifest
py -3 "<skill-dir>\scripts\guardian.py" batch batch.json --out-dir reports

# Verify the installed scripts
py -3 "<skill-dir>\scripts\guardian.py" self-test
```

On Windows, `scripts/guardian.ps1` is a convenience wrapper that locates `py -3` or `python`.

## Reporting discipline

Always separate:

- **Observed through Fusion MCP**
- **Measured from exported mesh**
- **Inferred**
- **Not verified**

A screenshot is evidence of appearance, not mechanical function. A closed STL is evidence of mesh topology, not structural adequacy. A moving joint is evidence of configured motion, not proof that a manufactured mechanism will work under load.
