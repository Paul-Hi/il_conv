import os
import tempfile
import textwrap
import unittest
from pathlib import Path

from issuedb import IssueDB


class IssueDBTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.previous_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.addCleanup(os.chdir, self.previous_cwd)

    def write_release_note(self, filename: str = "readme_tricore_v6.3r1_inspector_v1.0r7.html", *, title_version: str = "v6.3r1", use_td_header: bool = False, body: str | None = None) -> Path:
        if body is None:
            if use_td_header:
                header = """
                <tr>
                  <td class="heading">Issue</td>
                  <td class="heading">Summary</td>
                  <td class="heading">SIL</td>
                  <td class="heading">Inspector Compiler</td>
                  <td class="heading">Asm Cmp</td>
                  <td class="heading">Detection Type</td>
                </tr>
                """
            else:
                header = """
                <tr>
                  <th>Issue</th>
                  <th>Summary</th>
                  <th>SIL</th>
                  <th>Inspector Compiler</th>
                  <th>Asm Cmp</th>
                  <th>Detection Type</th>
                </tr>
                """

            body = f"""
            <html>
              <head><title>TriCore {title_version} Inspector v1.0</title></head>
              <body>
                <table class="detectors">
                  {header}
                  <tr>
                    <td>TCVX-10000</td>
                    <td>Summary from release notes</td>
                    <td>SIL-2</td>
                    <td>Supported</td>
                    <td>x</td>
                    <td>potential affected</td>
                  </tr>
                  <tr>
                    <td>TCVX-30000</td>
                    <td>Release note only issue</td>
                    <td>SIL-3</td>
                    <td>Supported</td>
                    <td></td>
                    <td>affected</td>
                  </tr>
                </table>
              </body>
            </html>
            """

        path = Path(self.temp_dir.name) / filename
        path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
        return path

    def write_xml(self, filename: str = "issues.xml", *, product_version: str = "TASKING VX-toolset for TriCore v6.3r1", body: str | None = None) -> Path:
        if body is None:
            body = f"""
            <issues>
              <product_version>{product_version}</product_version>
              <issue>
                <id>TCVX-10000</id>
                <summary>Portal summary</summary>
                <component>Compiler</component>
                <component>Inspector</component>
                <affected_toolchain>tc3xx</affected_toolchain>
                <sil>SIL-2</sil>
                <published>2024-01-01</published>
                <updated>2024-01-02</updated>
                <mitigation>Apply workaround</mitigation>
                <affected_version>v6.3r1</affected_version>
                <affected_version>v6.3r1p1</affected_version>
                <fix_version>v6.3r1p2</fix_version>
                <description>Detailed portal description</description>
                <inspector>v1.0r7</inspector>
              </issue>
              <issue>
                <id>TCVX-20000</id>
                <summary>Portal only issue</summary>
                <sil>SIL-1</sil>
                <published></published>
                <updated></updated>
                <mitigation></mitigation>
                <description>Portal only description</description>
              </issue>
            </issues>
            """

        path = Path(self.temp_dir.name) / filename
        path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
        return path

    def make_db(self, xml_path: Path, relnote_path: Path, verbose: bool = False) -> IssueDB:
        return IssueDB("v6.3r1", "v1.0", xml_path, relnote_path, verbose)

    def test_import_release_note_with_th_header(self):
        relnote_path = self.write_release_note()
        xml_path = self.write_xml()
        db = self.make_db(xml_path, relnote_path)

        count = db.importReleaseNote()

        self.assertEqual(count, 2)
        self.assertEqual(db.getListOfDetectableIssues(), ["TCVX-10000", "TCVX-30000"])
        issue = db.getReleaseNoteIssue("TCVX-10000")
        self.assertEqual(issue.summary, "Summary from release notes")
        self.assertEqual(issue.asscmp, "Yes")

    def test_import_release_note_with_td_header(self):
        relnote_path = self.write_release_note(use_td_header=True)
        xml_path = self.write_xml()
        db = self.make_db(xml_path, relnote_path)

        count = db.importReleaseNote()

        self.assertEqual(count, 2)
        self.assertEqual(db.getReleaseNoteIssue("TCVX-30000").asscmp, "No")

    def test_import_release_note_rejects_wrong_title(self):
        relnote_path = self.write_release_note(title_version="v7.0r0")
        xml_path = self.write_xml()
        db = self.make_db(xml_path, relnote_path)

        with self.assertRaises(AssertionError):
            db.importReleaseNote()

    def test_import_release_note_returns_zero_for_empty_file(self):
        relnote_path = self.write_release_note(body="")
        xml_path = self.write_xml()
        db = self.make_db(xml_path, relnote_path, verbose=True)

        self.assertEqual(db.importReleaseNote(), 0)

    def test_import_xml_file_and_query_issues(self):
        relnote_path = self.write_release_note()
        xml_path = self.write_xml()
        db = self.make_db(xml_path, relnote_path)

        count = db.importXMLFile()

        self.assertEqual(count, 2)
        portal_issue = db.getPortalIssue("TCVX-10000")
        self.assertEqual(portal_issue.component, "Compiler,Inspector")
        self.assertEqual(portal_issue.affected_version, "v6.3r1,v6.3r1p1")
        self.assertEqual(db.getPortalIssue("TCVX-99999"), None)

    def test_import_xml_file_rejects_wrong_compiler_version(self):
        relnote_path = self.write_release_note()
        xml_path = self.write_xml(product_version="TASKING VX-toolset for TriCore v6.2r2")
        db = self.make_db(xml_path, relnote_path)

        with self.assertRaises(AssertionError):
            db.importXMLFile()

    def test_import_xml_file_returns_zero_for_empty_file(self):
        relnote_path = self.write_release_note()
        xml_path = self.write_xml(body="")
        db = self.make_db(xml_path, relnote_path, verbose=True)

        self.assertEqual(db.importXMLFile(), 0)

    def test_get_issue_merges_release_note_and_portal_information(self):
        relnote_path = self.write_release_note()
        xml_path = self.write_xml()
        db = self.make_db(xml_path, relnote_path)
        db.importReleaseNote()
        db.importXMLFile()

        merged = db.getIssue("TCVX-10000")
        portal_only = db.getIssue("TCVX-20000")
        release_only = db.getIssue("TCVX-30000")

        self.assertEqual(merged.summary, "Portal summary")
        self.assertEqual(merged.detectiontype, "potential affected")
        self.assertEqual(merged.inspcomp, "Supported")
        self.assertEqual(portal_only.description, "Portal only description")
        self.assertEqual(release_only.summary, "Release note only issue")
        self.assertEqual(db.getIssue("TCVX-99999"), None)

    def test_is_issue_affecting_compiler_version(self):
        relnote_path = self.write_release_note()
        xml_path = self.write_xml()
        db = self.make_db(xml_path, relnote_path)
        db.importReleaseNote()
        db.importXMLFile()

        self.assertTrue(db.isIssueAffectingCompilerVersion("TCVX-10000", "v6.3r1"))
        self.assertFalse(db.isIssueAffectingCompilerVersion("TCVX-10000", "v6.2r2"))
        self.assertTrue(db.isIssueAffectingCompilerVersion("TCVX-20000", "v6.2r2"))
        self.assertTrue(db.isIssueAffectingCompilerVersion("TCVX-99999", "v6.2r2"))

    def test_delete_closes_database_connection(self):
        relnote_path = self.write_release_note()
        xml_path = self.write_xml()
        db = self.make_db(xml_path, relnote_path)
        conn = db.conn

        db.__del__()

        with self.assertRaises(Exception):
            conn.execute("SELECT 1")


if __name__ == "__main__":
    unittest.main()
