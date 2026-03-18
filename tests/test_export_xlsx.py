"""
File:   test_export_xlsx.py
Desc:   Unit tests for export_xlsx.py — _map_dtype_2_auto_judgement

Copyright (C) 2024 Peter Himmler
Apache License 2.0
"""

import unittest

from export_xlsx import _map_dtype_2_auto_judgement


class TestMapDtype2AutoJudgement(unittest.TestCase):
    """Tests for all reachable detectiontype combinations."""

    # --- keys present in auto_judge ---

    def test_potential_no_asm(self):
        result = _map_dtype_2_auto_judgement("p;-")
        self.assertIn("Potential", result)
        self.assertIn("Manual investigation", result)

    def test_potential_no_change(self):
        result = _map_dtype_2_auto_judgement("p;n")
        self.assertIn("Potential", result)
        self.assertIn("false positive", result)

    def test_potential_asm_change_with_full_paths(self):
        result = _map_dtype_2_auto_judgement("p;c;/tmp/asm;affected.s;unaffected.s")
        self.assertIn("Potential", result)
        self.assertIn("affected.s", result)
        self.assertIn("unaffected.s", result)
        self.assertIn("/tmp/asm", result)

    def test_potential_asm_change_unknown_files(self):
        # p;c;?;?;? is stored when directory info is unavailable
        result = _map_dtype_2_auto_judgement("p;c;?;?;?")
        self.assertIn("Potential", result)

    def test_definite_no_asm(self):
        result = _map_dtype_2_auto_judgement("d;-")
        self.assertIn("Definite", result)
        self.assertIn("mitigation", result)

    def test_unclear_result(self):
        # '?;?' is the detectiontype used for the unreachable fallback branch
        result = _map_dtype_2_auto_judgement("?;?")
        self.assertIn("Unclear", result)

    # --- unknown keys fall back to "?!?" ---

    def test_unknown_key_returns_fallback(self):
        self.assertEqual(_map_dtype_2_auto_judgement("x;y"), "?!?")

    def test_empty_string_returns_fallback(self):
        # empty → t='', a="'?'" after padding → unknown key
        self.assertEqual(_map_dtype_2_auto_judgement(""), "?!?")

    def test_single_field_returns_fallback(self):
        # Only 'p', no asm field → padded a="'?'" → unknown key
        self.assertEqual(_map_dtype_2_auto_judgement("p"), "?!?")

    # --- whitespace stripping ---

    def test_whitespace_around_parts_is_stripped(self):
        result = _map_dtype_2_auto_judgement("p ; -")
        self.assertIn("Potential", result)
        self.assertIn("Manual investigation", result)

    def test_whitespace_in_all_five_fields(self):
        result = _map_dtype_2_auto_judgement("p ; c ; /tmp/asm ; affected.s ; unaffected.s")
        self.assertIn("Potential", result)
        self.assertIn("affected.s", result)

    # --- return type ---

    def test_return_type_is_str(self):
        self.assertIsInstance(_map_dtype_2_auto_judgement("p;-"), str)
        self.assertIsInstance(_map_dtype_2_auto_judgement("x;y"), str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
