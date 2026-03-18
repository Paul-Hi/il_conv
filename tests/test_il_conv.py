import importlib
import io
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from unittest.mock import Mock


class ParseArgumentsTests(unittest.TestCase):
    def setUp(self):
        export_html = types.ModuleType("export_html")
        export_xlsx = types.ModuleType("export_xlsx")
        issuedb = types.ModuleType("issuedb")
        issuedb.IssueDB = object

        self.module_patcher = patch.dict(
            sys.modules,
            {
                "export_html": export_html,
                "export_xlsx": export_xlsx,
                "issuedb": issuedb,
            },
        )
        self.module_patcher.start()
        sys.modules.pop("il_conv", None)
        self.il_conv = importlib.import_module("il_conv")

    def tearDown(self):
        sys.modules.pop("il_conv", None)
        self.module_patcher.stop()

    def test_parse_arguments_uses_defaults(self):
        with patch.object(
            sys,
            "argv",
            [
                "il_conv.py",
                "-x",
                "issues.xml",
                "-r",
                "readme_tricore_v6.3r1_inspector_v1.0r7.html",
                "build.log",
            ],
        ):
            args = self.il_conv.parse_arguments()

        self.assertFalse(args.verbose)
        self.assertEqual(args.output, "insp_output")
        self.assertEqual(args.output_format, "xlsx")
        self.assertEqual(args.xmlfile, "issues.xml")
        self.assertEqual(
            args.relnotefile,
            "readme_tricore_v6.3r1_inspector_v1.0r7.html",
        )
        self.assertEqual(args.logfiles, ["build.log"])

    def test_parse_arguments_accepts_explicit_options(self):
        with patch.object(
            sys,
            "argv",
            [
                "il_conv.py",
                "-v",
                "--output",
                "report",
                "--output-format",
                "XLSX",
                "-x",
                "issues.xml",
                "-r",
                "readme_tricore_v6.2r2_inspector_v1.0r7.html",
                "build_a.log",
                "build_b.log",
            ],
        ):
            args = self.il_conv.parse_arguments()

        self.assertTrue(args.verbose)
        self.assertEqual(args.output, "report")
        self.assertEqual(args.output_format, "XLSX")
        self.assertEqual(args.logfiles, ["build_a.log", "build_b.log"])

    def test_parse_arguments_requires_mandatory_inputs(self):
        with patch.object(sys, "argv", ["il_conv.py", "build.log"]):
            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exc_info:
                    self.il_conv.parse_arguments()

        self.assertNotEqual(exc_info.exception.code, 0)


class IlConvFlowTests(unittest.TestCase):
    def setUp(self):
        export_html = types.ModuleType("export_html")
        export_xlsx = types.ModuleType("export_xlsx")
        issuedb = types.ModuleType("issuedb")
        issuedb.IssueDB = object

        self.module_patcher = patch.dict(
            sys.modules,
            {
                "export_html": export_html,
                "export_xlsx": export_xlsx,
                "issuedb": issuedb,
            },
        )
        self.module_patcher.start()
        sys.modules.pop("il_conv", None)
        self.il_conv = importlib.import_module("il_conv")

    def tearDown(self):
        sys.modules.pop("il_conv", None)
        self.module_patcher.stop()

    def make_args(self, temp_dir: str, **overrides):
        xml_path = Path(temp_dir) / "issues.xml"
        relnote_path = Path(temp_dir) / "readme_tricore_v6.3r1_inspector_v1.0r7.html"
        log_path = Path(temp_dir) / "build.log"

        xml_path.write_text("<xml></xml>", encoding="utf-8")
        relnote_path.write_text("<html></html>", encoding="utf-8")
        log_path.write_text("log", encoding="utf-8")

        values = {
            "verbose": False,
            "output": "insp_output",
            "output_format": "xlsx",
            "xmlfile": str(xml_path),
            "relnotefile": str(relnote_path),
            "logfiles": [str(log_path)],
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_il_conv_generates_xlsx_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            args = self.make_args(temp_dir, verbose=True)
            db = Mock()
            db.importReleaseNote.return_value = 2
            db.importXMLFile.return_value = 3
            log_db = Mock()

            with patch.object(self.il_conv, "parse_arguments", return_value=args), patch.object(
                self.il_conv, "IssueDB", return_value=db
            ) as issue_db_cls, patch.object(self.il_conv, "LogDB", return_value=log_db), patch.object(
                self.il_conv.export_xlsx, "generateExcel", create=True
            ) as generate_excel, patch.object(
                self.il_conv.export_html, "generateHTML", create=True
            ) as generate_html:
                self.il_conv.il_conv()

        issue_db_cls.assert_called_once()
        log_db.parse_log_file.assert_called_once_with(args.logfiles[0])
        generate_excel.assert_called_once_with("insp_output.xlsx", db, log_db, True)
        generate_html.assert_not_called()

    def test_il_conv_generates_html_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            args = self.make_args(temp_dir, output_format="html")
            db = Mock()
            db.importReleaseNote.return_value = 1
            db.importXMLFile.return_value = 1
            log_db = Mock()

            with patch.object(self.il_conv, "parse_arguments", return_value=args), patch.object(
                self.il_conv, "IssueDB", return_value=db
            ), patch.object(self.il_conv, "LogDB", return_value=log_db), patch.object(
                self.il_conv.export_xlsx, "generateExcel", create=True
            ) as generate_excel, patch.object(
                self.il_conv.export_html, "generateHTML", create=True
            ) as generate_html:
                self.il_conv.il_conv()

        generate_html.assert_called_once_with("insp_output.html", db, log_db, False)
        generate_excel.assert_not_called()

    def test_il_conv_returns_early_without_logfiles(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            args = self.make_args(temp_dir, logfiles=[])
            db = Mock()
            db.importReleaseNote.return_value = 1
            db.importXMLFile.return_value = 1

            stdout = io.StringIO()
            with patch.object(self.il_conv, "parse_arguments", return_value=args), patch.object(
                self.il_conv, "IssueDB", return_value=db
            ), patch.object(self.il_conv, "LogDB") as log_db_cls, redirect_stderr(io.StringIO()), patch(
                "sys.stdout", stdout
            ):
                self.il_conv.il_conv()

        self.assertIn("Nothing todo...", stdout.getvalue())
        log_db_cls.assert_not_called()

    def test_il_conv_rejects_invalid_release_note_prefix(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_path = Path(temp_dir) / "issues.xml"
            relnote_path = Path(temp_dir) / "wrong_name.html"
            log_path = Path(temp_dir) / "build.log"
            xml_path.write_text("<xml></xml>", encoding="utf-8")
            relnote_path.write_text("<html></html>", encoding="utf-8")
            log_path.write_text("log", encoding="utf-8")
            args = SimpleNamespace(
                verbose=False,
                output="insp_output",
                output_format="xlsx",
                xmlfile=str(xml_path),
                relnotefile=str(relnote_path),
                logfiles=[str(log_path)],
            )

            with patch.object(self.il_conv, "parse_arguments", return_value=args):
                with self.assertRaises(AssertionError):
                    self.il_conv.il_conv()

    def test_il_conv_rejects_invalid_release_note_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_path = Path(temp_dir) / "issues.xml"
            relnote_path = Path(temp_dir) / "readme_tricore_v7.0r0_inspector_v1.0r7.html"
            log_path = Path(temp_dir) / "build.log"
            xml_path.write_text("<xml></xml>", encoding="utf-8")
            relnote_path.write_text("<html></html>", encoding="utf-8")
            log_path.write_text("log", encoding="utf-8")
            args = SimpleNamespace(
                verbose=False,
                output="insp_output",
                output_format="xlsx",
                xmlfile=str(xml_path),
                relnotefile=str(relnote_path),
                logfiles=[str(log_path)],
            )

            with patch.object(self.il_conv, "parse_arguments", return_value=args):
                with self.assertRaises(AssertionError):
                    self.il_conv.il_conv()

    def test_il_conv_rejects_missing_xml_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            relnote_path = Path(temp_dir) / "readme_tricore_v6.3r1_inspector_v1.0r7.html"
            log_path = Path(temp_dir) / "build.log"
            relnote_path.write_text("<html></html>", encoding="utf-8")
            log_path.write_text("log", encoding="utf-8")
            args = SimpleNamespace(
                verbose=False,
                output="insp_output",
                output_format="xlsx",
                xmlfile=str(Path(temp_dir) / "missing.xml"),
                relnotefile=str(relnote_path),
                logfiles=[str(log_path)],
            )

            with patch.object(self.il_conv, "parse_arguments", return_value=args):
                with self.assertRaises(AssertionError):
                    self.il_conv.il_conv()

    def test_il_conv_rejects_missing_release_note_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            xml_path = Path(temp_dir) / "issues.xml"
            log_path = Path(temp_dir) / "build.log"
            xml_path.write_text("<xml></xml>", encoding="utf-8")
            log_path.write_text("log", encoding="utf-8")
            args = SimpleNamespace(
                verbose=False,
                output="insp_output",
                output_format="xlsx",
                xmlfile=str(xml_path),
                relnotefile=str(Path(temp_dir) / "missing.html"),
                logfiles=[str(log_path)],
            )

            with patch.object(self.il_conv, "parse_arguments", return_value=args):
                with self.assertRaises(AssertionError):
                    self.il_conv.il_conv()


if __name__ == "__main__":
    unittest.main()
