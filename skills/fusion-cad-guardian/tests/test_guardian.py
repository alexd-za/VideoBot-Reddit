from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "guardian.py"
SPEC = importlib.util.spec_from_file_location("guardian", SCRIPT)
assert SPEC and SPEC.loader
GUARDIAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARDIAN)


class GuardianTests(unittest.TestCase):
    def test_self_test(self) -> None:
        result = GUARDIAN.run_self_test()
        self.assertTrue(result["passed"], result)

    def test_cube_metrics(self) -> None:
        metrics = GUARDIAN.analyze_mesh(GUARDIAN._cube_triangles(10.0))
        self.assertEqual(metrics["triangle_count"], 12)
        self.assertEqual(metrics["boundary_edge_count"], 0)
        self.assertEqual(metrics["nonmanifold_edge_count"], 0)
        self.assertEqual(metrics["shell_count"], 1)
        self.assertTrue(metrics["watertight"])
        self.assertAlmostEqual(metrics["absolute_volume_mm3"], 1000.0, places=6)

    def test_contract_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mesh = root / "cube.stl"
            contract_path = root / "contract.json"
            GUARDIAN._write_binary_stl(mesh, GUARDIAN._cube_triangles(10.0))
            contract = GUARDIAN._default_contract("Cube")
            contract["expected_dimensions_mm"]["x"] = {"target": 11.0, "tolerance": 0.01}
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            report = GUARDIAN.audit_stl(mesh, contract_path=contract_path)
            self.assertEqual(report["verdict"], "FAIL")
            failed_ids = {check["id"] for check in report["checks"] if check["status"] == "FAIL"}
            self.assertIn("dimension_x", failed_ids)

    def test_unknown_contract_field_rejected(self) -> None:
        with self.assertRaises(GUARDIAN.GuardianError):
            GUARDIAN.validate_contract({"schema_version": 1, "units": "mm", "magic": True})


if __name__ == "__main__":
    unittest.main()
