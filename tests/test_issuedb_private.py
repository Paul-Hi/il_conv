"""
File:   test_issuedb_private.py
Desc:   Integration tests for issuedb.py using local (non-committed) XML and
        release note files from the XML/ and RELEASENOTES/ folders.

        Tests are skipped automatically when the required files are absent,
        so this file is safe to run on any machine.

Copyright (C) 2024 Peter Himmler
Apache License 2.0
"""

import gc
import os
import unittest
from pathlib import Path

from issuedb import IssueDB, ReleaseNoteIssue, PortalIssue, Issue

# ---------------------------------------------------------------------------
# Paths to local test data (not committed)
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent.parent  # project root

XML_V63R1   = _HERE / "XML"          / "issues_tasking_TCVX_v6.3r1.xml"
XML_V62R2   = _HERE / "XML"          / "issues_tasking_TCVX_v6.2r2.xml"
RN_V63_V108 = _HERE / "RELEASENOTES" / "readme_tricore_v6.3r1_inspector_v1.0r8.html"
RN_V62_V107 = _HERE / "RELEASENOTES" / "readme_tricore_v6.2r2_inspector_v1.0r7.html"

_HAVE_V63 = XML_V63R1.exists() and RN_V63_V108.exists()
_HAVE_V62 = XML_V62R2.exists() and RN_V62_V107.exists()

_SKIP_V63 = unittest.skipUnless(_HAVE_V63, "Local v6.3r1 test data not available")
_SKIP_V62 = unittest.skipUnless(_HAVE_V62, "Local v6.2r2 test data not available")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(compiler_ver: str, inspector_ver: str, xml: Path, rn: Path) -> IssueDB:
    return IssueDB(compiler_ver, inspector_ver, xml, rn, verbose=False)


def _close_db(db: IssueDB):
    """Explicitly close the SQLite connection — required on Windows before unlink."""
    if db.conn:
        db.conn.close()
        db.conn = None


def _remove_db(compiler_ver: str, inspector_ver: str):
    """Remove the file-based SQLite DB that IssueDB creates on disk."""
    dbpath = Path("issues-{}-{}.db".format(compiler_ver, inspector_ver))
    try:
        dbpath.unlink()
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# Tests — v6.3r1 / Inspector v1.0r8
# ---------------------------------------------------------------------------

@_SKIP_V63
class TestIssueDBImport(unittest.TestCase):
    """import_release_note and import_xml_file happy-path tests."""

    def setUp(self):
        self.db = _make_db("v6.3r1", "v1.0r8", XML_V63R1, RN_V63_V108)

    def tearDown(self):
        _close_db(self.db)
        del self.db
        gc.collect()
        _remove_db("v6.3r1", "v1.0r8")

    def test_import_release_note_returns_positive_count(self):
        count = self.db.import_release_note()
        self.assertGreater(count, 0)

    def test_import_xml_returns_positive_count(self):
        count = self.db.import_xml_file()
        self.assertGreater(count, 0)

    def test_import_xml_count_matches_row_count(self):
        count = self.db.import_xml_file()
        self.db.cur.execute("SELECT COUNT(*) FROM PortalIssues")
        self.assertEqual(self.db.cur.fetchone()[0], count)

    def test_import_release_note_count_matches_row_count(self):
        count = self.db.import_release_note()
        self.db.cur.execute("SELECT COUNT(*) FROM ReleaseNoteIssues")
        self.assertEqual(self.db.cur.fetchone()[0], count)


@_SKIP_V63
class TestIssueDBGetters(unittest.TestCase):
    """get_* query methods after a full import."""

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db("v6.3r1", "v1.0r8", XML_V63R1, RN_V63_V108)
        cls.db.import_release_note()
        cls.db.import_xml_file()

    @classmethod
    def tearDownClass(cls):
        _close_db(cls.db)
        del cls.db
        gc.collect()
        _remove_db("v6.3r1", "v1.0r8")

    # --- get_release_note_issue ---

    def test_get_release_note_issue_known_id(self):
        ri = self.db.get_release_note_issue("TCVX-39753")
        self.assertIsNotNone(ri)
        self.assertIsInstance(ri, ReleaseNoteIssue)
        self.assertEqual(ri.id, "TCVX-39753")
        self.assertEqual(ri.sil, "SIL-2")
        self.assertIn("Call graph", ri.summary)
        self.assertEqual(ri.inspcomp, "insp_ctc")
        self.assertEqual(ri.detectiontype, "Potential")

    def test_get_release_note_issue_unknown_id_returns_none(self):
        self.assertIsNone(self.db.get_release_note_issue("TCVX-00000"))

    # --- get_portal_issue ---

    def test_get_portal_issue_known_id(self):
        pi = self.db.get_portal_issue("TCVX-39753")
        self.assertIsNotNone(pi)
        self.assertIsInstance(pi, PortalIssue)
        self.assertEqual(pi.id, "TCVX-39753")
        self.assertEqual(pi.sil, "SIL-2")
        self.assertGreater(len(pi.mitigation), 0)

    def test_get_portal_issue_unknown_id_returns_none(self):
        self.assertIsNone(self.db.get_portal_issue("TCVX-00000"))

    # --- get_issue (combined) ---

    def test_get_issue_combined_record(self):
        # TCVX-39753 is in both XML and release notes → full combined Issue
        i = self.db.get_issue("TCVX-39753")
        self.assertIsNotNone(i)
        self.assertIsInstance(i, Issue)
        self.assertEqual(i.id, "TCVX-39753")
        self.assertEqual(i.sil, "SIL-2")
        self.assertGreater(len(i.mitigation), 0)     # from portal XML
        self.assertEqual(i.detectiontype, "Potential")  # from release note
        self.assertEqual(i.inspcomp, "insp_ctc")         # from release note

    def test_get_issue_unknown_returns_none(self):
        self.assertIsNone(self.db.get_issue("TCVX-00000"))

    # --- get_list_of_detectable_issues ---

    def test_get_list_of_detectable_issues_non_empty(self):
        ids = self.db.get_list_of_detectable_issues()
        self.assertIsInstance(ids, list)
        self.assertGreater(len(ids), 0)

    def test_get_list_of_detectable_issues_contains_known_id(self):
        ids = self.db.get_list_of_detectable_issues()
        self.assertIn("TCVX-39753", ids)

    def test_get_list_of_detectable_issues_sorted(self):
        ids = self.db.get_list_of_detectable_issues()
        self.assertEqual(ids, sorted(ids))

    # --- is_issue_affecting_compiler_version ---

    def test_issue_affecting_v63r1_is_true(self):
        self.assertTrue(self.db.is_issue_affecting_compiler_version("TCVX-39753", "v6.3r1"))

    def test_issue_not_affecting_unrelated_version(self):
        self.assertFalse(self.db.is_issue_affecting_compiler_version("TCVX-39753", "v1.0r1"))

    def test_unknown_issue_id_defaults_to_true(self):
        self.assertTrue(self.db.is_issue_affecting_compiler_version("TCVX-00000", "v6.3r1"))


@_SKIP_V63
class TestIssueDBErrorHandling(unittest.TestCase):
    """Version mismatch and empty-input error paths."""

    def tearDown(self):
        _remove_db("v6.3r1", "v1.0r8")
        _remove_db("v6.2r2", "v1.0r7")

    def test_wrong_compiler_version_in_xml_raises(self):
        if not XML_V62R2.exists():
            self.skipTest("v6.2r2 XML not available")
        db = _make_db("v6.3r1", "v1.0r8", XML_V62R2, RN_V63_V108)
        try:
            with self.assertRaises(ValueError):
                db.import_xml_file()
        finally:
            _close_db(db)
            gc.collect()

    def test_wrong_compiler_version_in_releasenote_raises(self):
        if not RN_V62_V107.exists():
            self.skipTest("v6.2r2 release note not available")
        db = _make_db("v6.3r1", "v1.0r8", XML_V63R1, RN_V62_V107)
        try:
            with self.assertRaises(ValueError):
                db.import_release_note()
        finally:
            _close_db(db)
            gc.collect()

    def test_xml_none_returns_zero(self):
        db = _make_db("v6.3r1", "v1.0r8", None, RN_V63_V108)
        try:
            self.assertEqual(db.import_xml_file(), 0)
        finally:
            _close_db(db)
            gc.collect()

    def test_releasenote_none_returns_zero(self):
        db = _make_db("v6.3r1", "v1.0r8", XML_V63R1, None)
        try:
            self.assertEqual(db.import_release_note(), 0)
        finally:
            _close_db(db)
            gc.collect()


# ---------------------------------------------------------------------------
# Tests — v6.2r2 / Inspector v1.0r7
# ---------------------------------------------------------------------------

@_SKIP_V62
class TestIssueDBV62R2(unittest.TestCase):
    """Smoke test for the v6.2r2 data set."""

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db("v6.2r2", "v1.0r7", XML_V62R2, RN_V62_V107)
        cls.rn_count = cls.db.import_release_note()
        cls.xml_count = cls.db.import_xml_file()

    @classmethod
    def tearDownClass(cls):
        _close_db(cls.db)
        del cls.db
        gc.collect()
        _remove_db("v6.2r2", "v1.0r7")

    def test_release_note_loaded(self):
        self.assertGreater(self.rn_count, 0)

    def test_xml_loaded(self):
        self.assertGreater(self.xml_count, 0)

    def test_get_list_of_detectable_issues_non_empty(self):
        ids = self.db.get_list_of_detectable_issues()
        self.assertGreater(len(ids), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
