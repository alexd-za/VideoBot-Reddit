# Fusion CAD Guardian

A Codex skill that works **alongside Autodesk Fusion MCP** to make AI-assisted CAD more testable.

Fusion MCP performs live CAD operations. Guardian adds a design contract, structured semantic verification, deterministic STL mesh checks, regression comparison, and an evidence-based repair loop.

## The capability it adds

A normal MCP connection can create and inspect a design, but it does not automatically give Codex a repeatable acceptance test. Guardian adds:

- explicit pass/fail criteria before modeling;
- separation of Fusion-semantic checks from exported-mesh checks;
- deterministic STL auditing without third-party Python packages;
- JSON and Markdown evidence reports;
- before/after regression detection;
- a bounded repair workflow that avoids blindly regenerating a full design.

It deliberately does **not** install an arbitrary Python execution bridge inside Fusion.

## Requirements

- Windows with native Codex
- Autodesk Fusion and a connected Fusion MCP server
- Python 3.10 or newer for STL auditing
- STL exports in millimetres

No Python packages need to be installed.

## Install with Skill Installer

The documented, reliable route is to place this folder in a GitHub repository and install the folder URL.

Example repository layout:

```text
my-codex-skills/
└── fusion-cad-guardian/
    ├── SKILL.md
    ├── scripts/
    ├── references/
    ├── assets/
    └── agents/
```

In Codex, invoke the built-in installer and provide the directory URL:

```text
$skill-installer install https://github.com/YOUR-NAME/my-codex-skills/tree/main/fusion-cad-guardian
```

Some Codex interfaces expose the installer through a slash command or skill picker. The important part is supplying the GitHub **directory** containing `SKILL.md`.

Restart Codex if the new skill does not appear automatically.

## Local manual installation

Copy the complete folder to:

```text
%USERPROFILE%\.agents\skills\fusion-cad-guardian
```

Then restart Codex.

## Verify the installation

From PowerShell:

```powershell
py -3 "$HOME\.agents\skills\fusion-cad-guardian\scripts\guardian.py" self-test
```

Expected result:

```json
{
  "passed": true
}
```

## Typical use

In Codex:

```text
Use $fusion-cad-guardian with my connected Autodesk Fusion MCP server.
Create a 3D-printable camera bracket, define measurable acceptance criteria first,
verify the Fusion feature structure and critical dimensions, export the final body
to STL, audit it, and do not claim anything that was not actually verified.
```

Or explicitly audit an existing STL:

```powershell
py -3 .\scripts\guardian.py init --out bracket.contract.json --part-name "Camera Bracket"
py -3 .\scripts\guardian.py audit bracket.stl --contract bracket.contract.json --json bracket.report.json --markdown bracket.report.md
```

## What it checks

- STL dimensions and bounding box
- surface area and signed volume
- watertightness indicators
- boundary and non-manifold edges
- degenerate and duplicate triangles
- inconsistent shared-edge winding
- disconnected edge-connected shells
- triangle limits
- optional build-plane contact
- contract tolerances

## What it does not check

It does not prove joint motion, continuous collision avoidance, minimum wall thickness, strength, material suitability, servo torque, backlash, print shrinkage, or rule compliance. Those remain Fusion, simulation, calculation, slicer, test, or human-review tasks.

## Inspiration

The workflow is independently implemented but takes architectural inspiration from:

- Autodesk Fusion MCP workflows demonstrated by Fooping
- `AuraFriday/Fusion-360-MCP-Server` for broad Fusion API orchestration and context-aware workflows
- `Ravva/codex-fusion360-connector` for focused local execution, screenshots, and Codex skill packaging

Guardian intentionally chooses a different boundary: official Fusion MCP for live actions, dependency-free local scripts for deterministic verification.
