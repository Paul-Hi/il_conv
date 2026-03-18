import importlib
import os
import tempfile
import unittest
from pathlib import Path

import openpyxl

import export_html
import export_xlsx
import resources
from issuedb import Issue
from parse import Detection
from parse import LogDB


class FakeDB:
    def __init__(self):
        self.xmlfile = Path("issues.xml")
        self.relnotefile = Path("readme_tricore_v6.3r1_inspector_v1.0r7.html")
        self.compiler_version = "v6.3r1"
        self.issues = {
            "TCVX-10000": Issue(
                id="TCVX-10000",
                sil="SIL-2",
                mitigation="Apply workaround",
                affected_version="v6.3r1",
                fix_version="v6.3r1p2",
                summary="Summary <unsafe>",
                description="Description <unsafe>",
                published="2024-01-01",
                last_updated="2024-01-02",
                component="Compiler",
                affected_toolchains="tc3xx",
                issue_inspector="v1.0r7",
                inspcomp="Supported",
                asscmp="Yes",
                detectiontype="potential affected",
            ),
            "TCVX-20000": Issue(
                id="TCVX-20000",
                sil="SIL-1",
                mitigation="Investigate manually",
                affected_version="v6.3r1",
                fix_version="v6.3r1p3",
                summary="Assembly difference",
                description="Assembly comparison changed",
                published="2024-01-03",
                last_updated="2024-01-04",
                component="Inspector",
                affected_toolchains="tc4xx",
                issue_inspector="v1.0r7",
                inspcomp="Supported",
                asscmp="Yes",
                detectiontype="affected",
            ),
        }

    def getIssue(self, issue_id: str):
        return self.issues.get(issue_id)


def make_log_db() -> LogDB:
    log_db = LogDB(verbose=False)
    log_db._add_log_entry(
        Detection(
            "2026-03-18 10:22:33",
            "insp_ctc -c source.c",
            "W998",
            "C:/project/src/main.c",
            "main.c",
            "10",
            "1",
            "p;-",
            "TCVX-10000",
            "",
        )
    )
    log_db._add_log_entry(
        Detection(
            "2026-03-18 10:22:34",
            "insp_ctc -c source.c",
            "W999",
            "C:/project/src/helper.c",
            "helper.c",
            "20",
            "2",
            "d;c;asm;nofix.s;withfix.s",
            "TCVX-20000",
            "Detected difference in assembly comparison",
        )
    )
    return log_db


class ResourceTests(unittest.TestCase):
    def test_resource_path_uses_module_directory_by_default(self):
        result = resources.resource_path("res/default.css")

        self.assertEqual(Path(result).name, "default.css")
        self.assertEqual(Path(result).parent.name, "res")
        self.assertTrue(Path(resources.DEFAULT_CSS).is_file())
        self.assertTrue(Path(resources.FUNCTIONS_JS).is_file())
        self.assertTrue(Path(resources.LOGO_BASE64_TXT).is_file())
        self.assertTrue(Path(resources.LOGO_PNG).is_file())

    def test_resource_path_uses_meipass_when_available(self):
        original = getattr(resources.sys, "_MEIPASS", None)
        resources.sys._MEIPASS = "C:/bundle"
        try:
            self.assertEqual(resources.resource_path("asset.txt"), os.path.join("C:/bundle", "asset.txt"))
        finally:
            if original is None:
                delattr(resources.sys, "_MEIPASS")
            else:
                resources.sys._MEIPASS = original


class ExportHtmlTests(unittest.TestCase):
    def test_generate_html_writes_expected_content(self):
        db = FakeDB()
        log_db = make_log_db()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.html"
            export_html.generateHTML(str(output_path), db, log_db, verbose=True)
            html = output_path.read_text(encoding="utf-8")

        self.assertIn("Summary &lt;unsafe&gt;", html)
        self.assertIn("Description &lt;unsafe&gt;", html)
        self.assertIn("data:image/png;base64", html)
        self.assertIn("<table class=\"log-table\" id=\"log_table\">", html)

    def test_generate_html_rejects_missing_issue_data(self):
        log_db = make_log_db()

        class MissingIssueDB(FakeDB):
            def getIssue(self, issue_id: str):
                return None

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.html"
            with self.assertRaises(AssertionError):
                export_html.generateHTML(str(output_path), MissingIssueDB(), log_db)


class ExportXlsxTests(unittest.TestCase):
    def test_map_dtype_to_auto_judgement_covers_known_paths(self):
        self.assertEqual(
            export_xlsx._map_dtype_2_auto_judgement("p;-"),
            "Potential. Further manual investigation required.",
        )
        self.assertEqual(
            export_xlsx._map_dtype_2_auto_judgement("p;n"),
            "Potential. Most likely a false positive, ignore.",
        )
        self.assertIn(
            "Assembly files 'nofix.s', 'withfix.s' generated  in 'asm'.",
            export_xlsx._map_dtype_2_auto_judgement("p;c;asm;nofix.s;withfix.s"),
        )
        self.assertIn(
            "Check if mitigation is applied.",
            export_xlsx._map_dtype_2_auto_judgement("d;c;asm;nofix.s;withfix.s"),
        )
        self.assertEqual(export_xlsx._map_dtype_2_auto_judgement("unknown"), "?!?")

    def test_generate_excel_creates_expected_workbook(self):
        db = FakeDB()
        log_db = make_log_db()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.xlsx"
            export_xlsx.generateExcel(str(output_path), db, log_db, verbose=True)
            workbook = openpyxl.load_workbook(output_path)

        self.assertEqual(
            workbook.sheetnames,
            [
                "TriCore Inspector Reports",
                "Report compact",
                "Report normal",
                "Report extended",
            ],
        )
        self.assertEqual(workbook["TriCore Inspector Reports"]["B4"].value, "il_conv (v3.0 beta)")
        self.assertEqual(workbook["Report compact"]["A3"].value, "helper.c")
        self.assertEqual(workbook["Report normal"]["A3"].value, "helper.c")
        self.assertEqual(workbook["Report normal"]["D3"].hyperlink.target, "https://issues.tasking.com/?issueid=TCVX-20000")
        self.assertIn(
            "Check if mitigation is applied.",
            workbook["Report normal"]["L3"].value,
        )
        self.assertEqual(workbook["Report extended"]["B3"].value, "C:/project/src/helper.c")

    def test_generate_excel_rejects_missing_issue_data(self):
        log_db = make_log_db()

        class MissingIssueDB(FakeDB):
            def getIssue(self, issue_id: str):
                return None

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.xlsx"
            with self.assertRaises(AssertionError):
                export_xlsx.generateExcel(str(output_path), MissingIssueDB(), log_db)


if __name__ == "__main__":
    unittest.main()