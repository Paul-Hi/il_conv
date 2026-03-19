"""
File:   test_parse.py
Desc:   Unit tests for parse.py — regex patterns and LogDB behaviour

Copyright (C) 2024 Peter Himmler
Apache License 2.0
"""

import os
import tempfile
import unittest

from parse import (
    RE_ASM_INFO,
    RE_ASM_INFO_DIFFERENCE,
    RE_DETECTION,
    RE_DIAG_ONLY_VERBOSE_LOG,
    RE_TIMESTAMP,
    Detection,
    LogDB,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_tmp(content: str) -> str:
    """Write *content* to a temporary file and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
    f.write(content)
    f.close()
    return f.name


def _query(db: LogDB, sql: str):
    db.curs.execute(sql)
    return db.curs.fetchall()


# ---------------------------------------------------------------------------
# RE_TIMESTAMP
# ---------------------------------------------------------------------------

class TestReTimestamp(unittest.TestCase):

    def test_valid_line(self):
        line = "2021-08-04 13:40:16 # insp_ctc -E+comments -c99 foo.c"
        m = RE_TIMESTAMP.match(line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("timestamp"), "2021-08-04 13:40:16")
        self.assertEqual(m.group("cmdline"), "insp_ctc -E+comments -c99 foo.c")

    def test_no_match_on_blank(self):
        self.assertIsNone(RE_TIMESTAMP.match(""))

    def test_no_match_on_detection_line(self):
        line = 'W998: ["file.h" 66/1] [INSP] detected potential occurrence of issue TCVX-44008.'
        self.assertIsNone(RE_TIMESTAMP.match(line))


# ---------------------------------------------------------------------------
# RE_DETECTION
# ---------------------------------------------------------------------------

class TestReDetection(unittest.TestCase):

    W998 = r'W998: ["C:\path/file.h" 66/1] [INSP] detected potential occurrence of issue TCVX-44008.'
    W999 = 'W999: ["C:/path/file.c" 10/2] [INSP] detected occurrence of issue TCVX-12345.'
    E996 = 'E996: ["src/foo.c" 1/1] [INSP] detected occurrence of issue SMRT-9999.'
    E997 = 'E997: ["src/foo.c" 2/3] [INSP] detected potential occurrence of issue SMRT-1234.'

    def test_w998_potential(self):
        m = RE_DETECTION.match(self.W998)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "W998")
        self.assertEqual(m.group("issueid"), "TCVX-44008")
        self.assertIn("potential occurrence", m.group("message"))

    def test_w999_definite(self):
        m = RE_DETECTION.match(self.W999)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "W999")
        self.assertEqual(m.group("issueid"), "TCVX-12345")

    def test_e996_definite(self):
        m = RE_DETECTION.match(self.E996)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "E996")
        self.assertEqual(m.group("issueid"), "SMRT-9999")

    def test_e997_potential(self):
        m = RE_DETECTION.match(self.E997)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "E997")
        self.assertEqual(m.group("issueid"), "SMRT-1234")

    def test_filepath_line_column(self):
        m = RE_DETECTION.match(self.W998)
        self.assertEqual(m.group("filepath"), r"C:\path/file.h")
        self.assertEqual(m.group("line"), "66")
        self.assertEqual(m.group("column"), "1")

    def test_no_match_on_timestamp(self):
        self.assertIsNone(RE_DETECTION.match("2021-08-04 13:40:16 # insp_ctc"))

    def test_no_match_on_asm_info_code(self):
        # W981 must NOT be matched by RE_DETECTION
        line = 'W981: ["file.c" 1/1] [INSP] detected potential occurrence of issue TCVX-100. No change in assembly comparison detected.'
        m = RE_DETECTION.match(line)
        # If it matches at all (via prefix greedy), diagcode must not be W981
        if m:
            self.assertNotEqual(m.group("diagcode"), "W981")


# ---------------------------------------------------------------------------
# RE_DIAG_ONLY_VERBOSE_LOG
# ---------------------------------------------------------------------------

class TestReDiagOnly(unittest.TestCase):

    def test_i991(self):
        line = "I991: [INSP] No definite or potential issues detected for the enabled list of detectors"
        m = RE_DIAG_ONLY_VERBOSE_LOG.match(line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "I991")

    def test_i993(self):
        line = "I993: [INSP] No definite or potential issues detected for the enabled list of"
        m = RE_DIAG_ONLY_VERBOSE_LOG.match(line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "I993")

    def test_w984(self):
        line = "W984: [INSP] Input MIL files (.mil, .ma, .ms) are identified. Inspector cannot check"
        m = RE_DIAG_ONLY_VERBOSE_LOG.match(line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "W984")

    def test_e993(self):
        line = "E993: [INSP] detected change in assembly listing for command: foo"
        m = RE_DIAG_ONLY_VERBOSE_LOG.match(line)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "E993")

    def test_no_match_on_detection(self):
        line = 'W998: ["file.h" 10/1] [INSP] detected potential occurrence of issue TCVX-44008.'
        self.assertIsNone(RE_DIAG_ONLY_VERBOSE_LOG.match(line))


# ---------------------------------------------------------------------------
# RE_ASM_INFO
# ---------------------------------------------------------------------------

class TestReAsmInfo(unittest.TestCase):

    E980 = 'E980: ["src/foo.c" 5/1] [INSP] detected potential occurrence of issue TCVX-100. No change in assembly comparison detected.'
    W981 = '\tW981: ["../../../BswM.c" 1813/8] [INSP] detected potential occurrence of issue TCVX-45285. No change in assembly comparison detected.'
    E982 = ('E982: ["src/bar.c" 10/2] [INSP] detected potential occurrence of issue TCVX-200. '
            'Assembly files are stored in directory /tmp/asm as: affected.s; with fix: unaffected.s.')
    W983 = 'W983: ["src/bar.c" 20/3] [INSP] detected potential occurrence of issue SMRT-42. Detected difference in assembly.'

    def test_e980(self):
        m = RE_ASM_INFO.match(self.E980)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "E980")
        self.assertEqual(m.group("issueid"), "TCVX-100")

    def test_w981_with_leading_whitespace(self):
        m = RE_ASM_INFO.match(self.W981)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "W981")
        self.assertEqual(m.group("issueid"), "TCVX-45285")

    def test_e982_with_directory(self):
        m = RE_ASM_INFO.match(self.E982)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "E982")
        self.assertEqual(m.group("issueid"), "TCVX-200")
        self.assertIn("Assembly files", m.group("extension"))

    def test_w983(self):
        m = RE_ASM_INFO.match(self.W983)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("diagcode"), "W983")
        self.assertEqual(m.group("issueid"), "SMRT-42")

    def test_no_match_on_normal_detection(self):
        line = 'W998: ["file.h" 10/1] [INSP] detected potential occurrence of issue TCVX-44008.'
        self.assertIsNone(RE_ASM_INFO.match(line))


# ---------------------------------------------------------------------------
# RE_ASM_INFO_DIFFERENCE
# ---------------------------------------------------------------------------

class TestReAsmInfoDifference(unittest.TestCase):

    def test_full_match(self):
        ext = "Assembly files are stored in directory /tmp/asm/v1 as: affected.s; with fix: unaffected.s."
        m = RE_ASM_INFO_DIFFERENCE.match(ext)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("directory"), "/tmp/asm/v1")
        self.assertEqual(m.group("file_affected"), "affected.s")
        self.assertEqual(m.group("file_unaffected"), "unaffected.s")

    def test_no_match_plain_difference_text(self):
        self.assertIsNone(RE_ASM_INFO_DIFFERENCE.match("Detected difference in assembly."))

    def test_no_match_empty(self):
        self.assertIsNone(RE_ASM_INFO_DIFFERENCE.match(""))


# ---------------------------------------------------------------------------
# Detection namedtuple
# ---------------------------------------------------------------------------

class TestDetection(unittest.TestCase):

    def test_all_defaults_are_empty_string(self):
        d = Detection()
        for field in Detection._fields:
            self.assertEqual(getattr(d, field), "")

    def test_keyword_construction(self):
        d = Detection(issueid="TCVX-123", detectiontype="p;-")
        self.assertEqual(d.issueid, "TCVX-123")
        self.assertEqual(d.detectiontype, "p;-")
        self.assertEqual(d.tstamp, "")  # default


# ---------------------------------------------------------------------------
# LogDB — parse_log_file
# ---------------------------------------------------------------------------

class TestLogDB(unittest.TestCase):

    def tearDown(self):
        for path in getattr(self, "_tmps", []):
            try:
                os.unlink(path)
            except OSError:
                pass

    def _tmp(self, content: str) -> str:
        path = _write_tmp(content)
        self._tmps = getattr(self, "_tmps", []) + [path]
        return path

    # --- empty / missing input ---

    def test_empty_file_inserts_nothing(self):
        db = LogDB()
        db.parse_log_file(self._tmp(""))
        rows = _query(db, "SELECT COUNT(*) FROM Logs")
        self.assertEqual(rows[0][0], 0)

    # --- RE_DETECTION branch ---

    def test_w998_stores_potential_detectiontype(self):
        line = 'W998: ["C:/src/foo.h" 66/1] [INSP] detected potential occurrence of issue TCVX-44008.\n'
        db = LogDB()
        db.parse_log_file(self._tmp(line))
        db.curs.execute("SELECT detectiontype, issueid, diagmsgno, file FROM Logs")
        row = db.curs.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "p;-")
        self.assertEqual(row[1], "TCVX-44008")
        self.assertEqual(row[2], "W998")
        self.assertEqual(row[3], "foo.h")

    def test_w999_stores_definite_detectiontype(self):
        line = 'W999: ["C:/src/bar.c" 10/2] [INSP] detected occurrence of issue TCVX-12345.\n'
        db = LogDB()
        db.parse_log_file(self._tmp(line))
        db.curs.execute("SELECT detectiontype, issueid FROM Logs")
        row = db.curs.fetchone()
        self.assertEqual(row[0], "d;-")
        self.assertEqual(row[1], "TCVX-12345")

    def test_e996_definite_smrt_id(self):
        line = 'E996: ["src/x.c" 1/1] [INSP] detected occurrence of issue SMRT-9999.\n'
        db = LogDB()
        db.parse_log_file(self._tmp(line))
        db.curs.execute("SELECT issueid, detectiontype FROM Logs")
        row = db.curs.fetchone()
        self.assertEqual(row[0], "SMRT-9999")
        self.assertEqual(row[1], "d;-")

    def test_e997_potential_smrt_id(self):
        line = 'E997: ["src/x.c" 2/3] [INSP] detected potential occurrence of issue SMRT-1234.\n'
        db = LogDB()
        db.parse_log_file(self._tmp(line))
        db.curs.execute("SELECT issueid, detectiontype FROM Logs")
        row = db.curs.fetchone()
        self.assertEqual(row[0], "SMRT-1234")
        self.assertEqual(row[1], "p;-")

    # --- timestamp propagation ---

    def test_timestamp_propagates_to_detection(self):
        content = (
            "2021-08-04 13:40:16 # insp_ctc -E+comments -c99 foo.c\n"
            'W998: ["foo.c" 1/1] [INSP] detected potential occurrence of issue TCVX-99999.\n'
        )
        db = LogDB()
        db.parse_log_file(self._tmp(content))
        db.curs.execute("SELECT tstamp, cmdline FROM Logs")
        row = db.curs.fetchone()
        self.assertEqual(row[0], "2021-08-04 13:40:16")
        self.assertIn("insp_ctc", row[1])

    def test_no_timestamp_uses_epoch_default(self):
        line = 'W998: ["foo.c" 1/1] [INSP] detected potential occurrence of issue TCVX-99999.\n'
        db = LogDB()
        db.parse_log_file(self._tmp(line))
        db.curs.execute("SELECT tstamp FROM Logs")
        row = db.curs.fetchone()
        self.assertEqual(row[0], "1970-01-01 00:00:01")

    # --- RE_ASM_INFO branch ---

    def test_e980_stores_p_n(self):
        line = 'E980: ["src/foo.c" 5/1] [INSP] detected potential occurrence of issue TCVX-100. No change in assembly comparison detected.\n'
        db = LogDB()
        db.parse_log_file(self._tmp(line))
        db.curs.execute("SELECT detectiontype, issueid FROM Logs")
        row = db.curs.fetchone()
        self.assertEqual(row[0], "p;n")
        self.assertEqual(row[1], "TCVX-100")

    def test_w981_with_leading_tab_stores_p_n(self):
        line = '\tW981: ["../BswM.c" 1813/8] [INSP] detected potential occurrence of issue TCVX-45285. No change in assembly comparison detected.\n'
        db = LogDB()
        db.parse_log_file(self._tmp(line))
        db.curs.execute("SELECT detectiontype FROM Logs")
        row = db.curs.fetchone()
        self.assertEqual(row[0], "p;n")

    def test_e982_with_full_directory_info(self):
        line = (
            'E982: ["src/bar.c" 10/2] [INSP] detected potential occurrence of issue TCVX-200. '
            'Assembly files are stored in directory /tmp/asm as: affected.s; with fix: unaffected.s.\n'
        )
        db = LogDB()
        db.parse_log_file(self._tmp(line))
        db.curs.execute("SELECT detectiontype FROM Logs")
        row = db.curs.fetchone()
        parts = row[0].split(";")
        self.assertEqual(parts[0], "p")
        self.assertEqual(parts[1], "c")
        self.assertIn("tmp", parts[2])       # directory
        self.assertEqual(parts[3], "affected.s")
        self.assertEqual(parts[4], "unaffected.s")

    def test_w983_without_directory_info_stores_p_c_unknown(self):
        line = (
            'W983: ["src/bar.c" 20/3] [INSP] detected potential occurrence of issue SMRT-42. '
            'Detected difference in assembly.\n'
        )
        db = LogDB()
        db.parse_log_file(self._tmp(line))
        db.curs.execute("SELECT detectiontype FROM Logs")
        row = db.curs.fetchone()
        self.assertEqual(row[0], "p;c;?;?;?")

    # --- RE_DIAG_ONLY_VERBOSE_LOG branch (must NOT store rows) ---

    def test_i991_not_stored(self):
        line = "I991: [INSP] No definite or potential issues detected for the enabled list of detectors.\n"
        db = LogDB()
        db.parse_log_file(self._tmp(line))
        rows = _query(db, "SELECT COUNT(*) FROM Logs")
        self.assertEqual(rows[0][0], 0)

    def test_w984_not_stored(self):
        line = "W984: [INSP] Input MIL files (.mil, .ma, .ms) are identified. Inspector cannot check.\n"
        db = LogDB()
        db.parse_log_file(self._tmp(line))
        rows = _query(db, "SELECT COUNT(*) FROM Logs")
        self.assertEqual(rows[0][0], 0)

    # --- duplicate handling ---

    def test_duplicate_detection_stored_once(self):
        line = 'W998: ["foo.c" 1/1] [INSP] detected potential occurrence of issue TCVX-11111.\n'
        db = LogDB()
        db.parse_log_file(self._tmp(line + line))
        rows = _query(db, "SELECT COUNT(*) FROM Logs")
        self.assertEqual(rows[0][0], 1)

    # --- multiple detections ---

    def test_multiple_distinct_detections(self):
        content = (
            'W998: ["a.c" 1/1] [INSP] detected potential occurrence of issue TCVX-11111.\n'
            'W999: ["b.c" 2/2] [INSP] detected occurrence of issue TCVX-22222.\n'
        )
        db = LogDB()
        db.parse_log_file(self._tmp(content))
        rows = _query(db, "SELECT COUNT(*) FROM Logs")
        self.assertEqual(rows[0][0], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
