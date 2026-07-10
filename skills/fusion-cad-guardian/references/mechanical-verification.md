# Mechanical verification workflow

Use this for assemblies and mechanisms.

## Define intent

Record:

- fixed components;
- moving components;
- intended degrees of freedom;
- rotation and translation axes;
- motion limits;
- driving component and driven component;
- force or torque path;
- required clearances;
- forbidden contacts;
- mounting interfaces;
- fastener and bearing assumptions.

## Verify in Fusion

For each joint or relationship:

1. confirm component origins and orientation;
2. confirm joint type;
3. confirm axis and direction;
4. confirm limits;
5. inspect the neutral position;
6. inspect both motion extremes;
7. inspect at least one intermediate position;
8. run interference checks at representative positions;
9. confirm the intended parts remain connected;
10. verify the driving relationship or motion link when applicable.

## Evidence table

Use this form in the semantic report:

| Requirement | Method | Result | Evidence |
|---|---|---|---|
| Pinion rotates around shaft axis | Fusion joint inspection | PASS | Revolute joint `Pinion_Shaft`, Z axis |
| Rack translates 50 mm | Joint limits and motion test | PASS | 0 to 50 mm slider range |
| No hard interference | Interference at 0/25/50 mm | FAIL | Collision at 46.2 mm |
| Printable rack mesh | STL audit | PASS | Mesh report path |

## Do not conflate checks

- Joint motion does not prove correct gear tooth geometry.
- No interference at three sampled positions does not prove continuous collision-free motion.
- A correct pitch relationship does not prove acceptable backlash after printing.
- A valid STL does not prove that separate components are assembled correctly.
