"""
File:   test_issuedb_rn.py
Desc:   Public integration tests for IssueDB release-note import using the
        committed HTML files in RELEASENOTES/.  No XML portal data is required.

Copyright (C) 2024 Peter Himmler
Apache License 2.0
"""

import gc
import unittest
from pathlib import Path

from issuedb import IssueDB, ReleaseNoteIssue

# ---------------------------------------------------------------------------
# Paths to committed release note files
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent.parent  # project root

RN_V63_V108 = _HERE / "RELEASENOTES" / "readme_tricore_v6.3r1_inspector_v1.0r8.html"
RN_V62_V108 = _HERE / "RELEASENOTES" / "readme_tricore_v6.2r2_inspector_v1.0r8.html"

# Known issue present in v6.3r1 release note
_KNOWN_ID_V63 = "TCVX-39753"

# Known issue present in v6.2r2 release note
_KNOWN_ID_V62 = "TCVX-34183"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(compiler_ver: str, inspector_ver: str, rn: Path) -> IssueDB:
    """Create an IssueDB with xml=None (release-note only)."""
    return IssueDB(compiler_ver, inspector_ver, None, rn, verbose=False)


def _close_db(db: IssueDB):
    """Explicitly close the SQLite connection — required on Windows before unlink."""
    if db.conn:
        db.conn.close()
        db.conn = None


def _remove_db(compiler_ver: str, inspector_ver: str):
    dbpath = Path("issues-{}-{}.db".format(compiler_ver, inspector_ver))
    try:
        dbpath.unlink()
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# Tests — v6.3r1 / Inspector v1.0r8
# ---------------------------------------------------------------------------

class TestReleaseNoteImportV63(unittest.TestCase):
    """import_release_note happy-path for v6.3r1."""

    def setUp(self):
        self.db = _make_db("v6.3r1", "v1.0r8", RN_V63_V108)

    def tearDown(self):
        _close_db(self.db)
        del self.db
        gc.collect()
        _remove_db("v6.3r1", "v1.0r8")

    def test_import_returns_positive_count(self):
        count = self.db.import_release_note()
        self.assertGreater(count, 0)

    def test_import_count_matches_row_count(self):
        count = self.db.import_release_note()
        self.db.cur.execute("SELECT COUNT(*) FROM ReleaseNoteIssues")
        self.assertEqual(self.db.cur.fetchone()[0], count)

    def test_xml_none_returns_zero(self):
        self.assertEqual(self.db.import_xml_file(), 0)


class TestReleaseNoteGettersV63(unittest.TestCase):
    """get_* queries against v6.3r1 release note data (no XML)."""

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db("v6.3r1", "v1.0r8", RN_V63_V108)
        cls.db.import_release_note()

    @classmethod
    def tearDownClass(cls):
        _close_db(cls.db)
        del cls.db
        gc.collect()
        _remove_db("v6.3r1", "v1.0r8")

    def test_get_known_issue(self):
        ri = self.db.get_release_note_issue(_KNOWN_ID_V63)
        self.assertIsNotNone(ri)
        self.assertIsInstance(ri, ReleaseNoteIssue)
        self.assertEqual(ri.id, _KNOWN_ID_V63)
        self.assertEqual(ri.sil, "SIL-2")
        self.assertIn("Call graph", ri.summary)
        self.assertEqual(ri.inspcomp, "insp_ctc")
        self.assertEqual(ri.detectiontype, "Potential")

    def test_get_unknown_issue_returns_none(self):
        self.assertIsNone(self.db.get_release_note_issue("TCVX-00000"))

    def test_detectable_issues_non_empty(self):
        ids = self.db.get_list_of_detectable_issues()
        self.assertIsInstance(ids, list)
        self.assertGreater(len(ids), 0)

    def test_detectable_issues_contains_known_id(self):
        self.assertIn(_KNOWN_ID_V63, self.db.get_list_of_detectable_issues())

    def test_detectable_issues_sorted(self):
        ids = self.db.get_list_of_detectable_issues()
        self.assertEqual(ids, sorted(ids))

    def test_issue_affecting_compiler_version(self):
        # Without XML (no affected_version data) the method safely defaults to True
        self.assertTrue(self.db.is_issue_affecting_compiler_version(_KNOWN_ID_V63, "v6.3r1"))

    def test_unknown_issue_defaults_to_affecting(self):
        self.assertTrue(self.db.is_issue_affecting_compiler_version("TCVX-00000", "v6.3r1"))


class TestReleaseNoteErrorsV63(unittest.TestCase):
    """Error paths: version mismatch and None input."""

    def tearDown(self):
        _remove_db("v6.3r1", "v1.0r8")
        _remove_db("v6.2r2", "v1.0r8")

    def test_wrong_compiler_version_raises(self):
        db = _make_db("v6.3r1", "v1.0r8", RN_V62_V108)
        try:
            with self.assertRaises(ValueError):
                db.import_release_note()
        finally:
            _close_db(db)
            gc.collect()

    def test_releasenote_none_returns_zero(self):
        db = _make_db("v6.3r1", "v1.0r8", None)
        try:
            self.assertEqual(db.import_release_note(), 0)
        finally:
            _close_db(db)
            gc.collect()


# ---------------------------------------------------------------------------
# Tests — v6.2r2 / Inspector v1.0r8
# ---------------------------------------------------------------------------

class TestReleaseNoteImportV62(unittest.TestCase):
    """Smoke tests for the v6.2r2 release note."""

    @classmethod
    def setUpClass(cls):
        cls.db = _make_db("v6.2r2", "v1.0r8", RN_V62_V108)
        cls.rn_count = cls.db.import_release_note()

    @classmethod
    def tearDownClass(cls):
        _close_db(cls.db)
        del cls.db
        gc.collect()
        _remove_db("v6.2r2", "v1.0r8")

    def test_import_returns_positive_count(self):
        self.assertGreater(self.rn_count, 0)

    def test_get_known_issue(self):
        ri = self.db.get_release_note_issue(_KNOWN_ID_V62)
        self.assertIsNotNone(ri)
        self.assertEqual(ri.id, _KNOWN_ID_V62)
        self.assertEqual(ri.sil, "SIL-2")
        self.assertEqual(ri.inspcomp, "insp_ltc")
        self.assertEqual(ri.detectiontype, "Definite")

    def test_detectable_issues_contains_known_id(self):
        self.assertIn(_KNOWN_ID_V62, self.db.get_list_of_detectable_issues())


if __name__ == "__main__":
    unittest.main(verbosity=2)
