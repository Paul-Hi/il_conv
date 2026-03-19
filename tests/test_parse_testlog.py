"""
File:   test_parse_testlog.py
Desc:   Integration tests for LogDB.parse_log_file using the committed test.log.
        Covers all detection variants present in test.log:
          W998  (p;-)         — potential, no assembly comparison
          W981  (p;n)         — potential, no change in assembly
          W983  (p;c)         — potential, assembly difference with directory info
          W983  (p;c;?;?;?)   — potential, assembly difference but no directory info
        Diagnostic-only lines (I991, W984, I992, E993, W994) must NOT be stored.

Copyright (C) 2024 Peter Himmler
Apache License 2.0
"""

import unittest
from pathlib import Path

from parse import LogDB

_HERE    = Path(__file__).parent.parent   # project root
TEST_LOG = _HERE / "test.log"


def _make_db() -> LogDB:
    db = LogDB(verbose=False)
    db.parse_log_file(str(TEST_LOG))
    return db


def _rows(db: LogDB, sql: str) -> list:
    db.curs.execute(sql)
    return db.curs.fetchall()


# ---------------------------------------------------------------------------
# Overall counts
# ---------------------------------------------------------------------------

class TestTestLogTotalCount(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db()

    def test_total_stored_detections(self):
        # 3×W998 (p;-) + 4×W981 (p;n) + 3×W983 (p;c / p;c;?;?;?) = 10
        rows = _rows(self.db, "SELECT COUNT(*) FROM Logs")
        self.assertEqual(rows[0][0], 10)

    def test_p_minus_count(self):
        rows = _rows(self.db, "SELECT COUNT(*) FROM Logs WHERE detectiontype='p;-'")
        self.assertEqual(rows[0][0], 3)

    def test_p_n_count(self):
        rows = _rows(self.db, "SELECT COUNT(*) FROM Logs WHERE detectiontype='p;n'")
        self.assertEqual(rows[0][0], 4)

    def test_p_c_variants_count(self):
        # two with full dir info, one with ?;?;?
        rows = _rows(self.db, "SELECT COUNT(*) FROM Logs WHERE detectiontype LIKE 'p;c%'")
        self.assertEqual(rows[0][0], 3)


# ---------------------------------------------------------------------------
# W998 detections (p;-)
# ---------------------------------------------------------------------------

class TestTestLogW998(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db()

    def test_module_a_first_detection(self):
        self.db.curs.execute(
            "SELECT detectiontype, issueid, line, column FROM Logs WHERE file='module_a.c' AND line='100'"
        )
        row = self.db.curs.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "p;-")
        self.assertEqual(row[1], "TCVX-45285")
        self.assertEqual(row[2], "100")
        self.assertEqual(row[3], "5")

    def test_module_a_second_detection(self):
        self.db.curs.execute(
            "SELECT detectiontype, issueid FROM Logs WHERE file='module_a.c' AND line='200'"
        )
        row = self.db.curs.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "p;-")
        self.assertEqual(row[1], "TCVX-45248")

    def test_module_h_deep_path(self):
        # 5-level deep source path: src/a/b/c/d/module_h.c
        self.db.curs.execute(
            "SELECT detectiontype, issueid, filepath FROM Logs WHERE file='module_h.c'"
        )
        row = self.db.curs.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "p;-")
        self.assertEqual(row[1], "TCVX-45285")
        self.assertIn("module_h.c", row[2])

    def test_diagmsgno_is_w998(self):
        rows = _rows(self.db, "SELECT DISTINCT diagmsgno FROM Logs WHERE detectiontype='p;-'")
        self.assertEqual(rows, [("W998",)])


# ---------------------------------------------------------------------------
# W981 detections (p;n)
# ---------------------------------------------------------------------------

class TestTestLogW981(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db()

    def test_module_b_first_detection(self):
        self.db.curs.execute(
            "SELECT detectiontype, issueid FROM Logs WHERE file='module_b.c' AND line='300'"
        )
        row = self.db.curs.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "p;n")
        self.assertEqual(row[1], "TCVX-45285")

    def test_module_b_second_detection(self):
        self.db.curs.execute(
            "SELECT detectiontype, issueid FROM Logs WHERE file='module_b.c' AND line='400'"
        )
        row = self.db.curs.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "p;n")
        self.assertEqual(row[1], "TCVX-45333")

    def test_module_c_side_effect(self):
        # W981 with side-effect annotation still yields p;n
        self.db.curs.execute(
            "SELECT detectiontype, issueid FROM Logs WHERE file='module_c.c'"
        )
        row = self.db.curs.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "p;n")
        self.assertEqual(row[1], "TCVX-45396")

    def test_module_i_shallow_path(self):
        # 1-level deep source path: src/ModuleI/module_i.c
        self.db.curs.execute(
            "SELECT detectiontype, issueid FROM Logs WHERE file='module_i.c'"
        )
        row = self.db.curs.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "p;n")
        self.assertEqual(row[1], "TCVX-45248")

    def test_diagmsgno_is_w981(self):
        rows = _rows(self.db, "SELECT DISTINCT diagmsgno FROM Logs WHERE detectiontype='p;n'")
        self.assertEqual(rows, [("W981",)])


# ---------------------------------------------------------------------------
# W983 detections (p;c with full directory info)
# ---------------------------------------------------------------------------

class TestTestLogW983WithDir(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db()

    def test_module_d_detectiontype_structure(self):
        self.db.curs.execute(
            "SELECT detectiontype, issueid FROM Logs WHERE file='module_d.c'"
        )
        row = self.db.curs.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "TCVX-45285")
        parts = row[0].split(";")
        self.assertEqual(parts[0], "p")
        self.assertEqual(parts[1], "c")
        self.assertIn("ModuleD", parts[2])           # normalised directory
        self.assertEqual(parts[3], "module_d.src.affected")
        self.assertEqual(parts[4], "module_d_FIX_TCVX-45285.src.unaffected")

    def test_module_e_side_effect_with_dir(self):
        self.db.curs.execute(
            "SELECT detectiontype, issueid FROM Logs WHERE file='module_e.c'"
        )
        row = self.db.curs.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "TCVX-45406")
        parts = row[0].split(";")
        self.assertEqual(parts[0], "p")
        self.assertEqual(parts[1], "c")
        self.assertIn("ModuleE", parts[2])
        self.assertEqual(parts[3], "module_e.src.affected")
        self.assertEqual(parts[4], "module_e_FIX_TCVX-45406.src.unaffected")


# ---------------------------------------------------------------------------
# W983 detection (p;c;?;?;? — no assembly directory info)
# ---------------------------------------------------------------------------

class TestTestLogW983NoDir(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db()

    def test_module_j_unknown_assembly(self):
        self.db.curs.execute(
            "SELECT detectiontype, issueid FROM Logs WHERE file='module_j.c'"
        )
        row = self.db.curs.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "p;c;?;?;?")
        self.assertEqual(row[1], "TCVX-45285")


# ---------------------------------------------------------------------------
# Diagnostic-only lines must NOT be stored
# ---------------------------------------------------------------------------

class TestTestLogDiagnosticNotStored(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db()

    def test_module_f_i991_not_stored(self):
        # module_f.c only produced I991 — nothing stored
        rows = _rows(self.db, "SELECT COUNT(*) FROM Logs WHERE file='module_f.c'")
        self.assertEqual(rows[0][0], 0)

    def test_module_g_diagnostics_not_stored(self):
        # module_g.c produced W984, I992, E993, W994 — nothing stored
        rows = _rows(self.db, "SELECT COUNT(*) FROM Logs WHERE file='module_g.c'")
        self.assertEqual(rows[0][0], 0)

    def test_no_diagnostic_diagmsgno_in_logs(self):
        diagnostic_codes = ("I991", "W984", "I992", "E993", "W994", "I993", "E995")
        for code in diagnostic_codes:
            rows = _rows(
                self.db,
                f"SELECT COUNT(*) FROM Logs WHERE diagmsgno='{code}'"
            )
            self.assertEqual(rows[0][0], 0, f"{code} should not appear in Logs")


# ---------------------------------------------------------------------------
# Timestamp propagation
# ---------------------------------------------------------------------------

class TestTestLogTimestamps(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db()

    def test_all_rows_have_timestamp(self):
        rows = _rows(self.db, "SELECT COUNT(*) FROM Logs WHERE tstamp='' OR tstamp IS NULL")
        self.assertEqual(rows[0][0], 0)

    def test_timestamps_have_correct_format(self):
        # All timestamps in test.log are 2026-03-02
        rows = _rows(self.db, "SELECT DISTINCT tstamp FROM Logs")
        for (ts,) in rows:
            self.assertRegex(ts, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


# ---------------------------------------------------------------------------
# Issue IDs present
# ---------------------------------------------------------------------------

class TestTestLogIssueIds(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db()
        cls.db.curs.execute("SELECT DISTINCT issueid FROM Logs")
        cls.ids = {row[0] for row in cls.db.curs.fetchall()}

    def test_tcvx_45285_present(self):
        self.assertIn("TCVX-45285", self.ids)

    def test_tcvx_45248_present(self):
        self.assertIn("TCVX-45248", self.ids)

    def test_tcvx_45333_present(self):
        self.assertIn("TCVX-45333", self.ids)

    def test_tcvx_45396_present(self):
        self.assertIn("TCVX-45396", self.ids)

    def test_tcvx_45406_present(self):
        self.assertIn("TCVX-45406", self.ids)

    def test_no_unexpected_ids(self):
        expected = {"TCVX-45285", "TCVX-45248", "TCVX-45333", "TCVX-45396", "TCVX-45406"}
        self.assertEqual(self.ids, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
