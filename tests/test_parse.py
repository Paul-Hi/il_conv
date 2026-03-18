import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import sqlite3

from parse import LogDB
from parse import Detection


class ParseLogFileTests(unittest.TestCase):
    def parse_rows(self, log_text: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "build.log"
            log_path.write_text(textwrap.dedent(log_text).lstrip("\n"), encoding="utf-8")

            db = LogDB(verbose=False)
            db.parse_log_file(str(log_path))

            rows = db.conn.execute(
                """
                SELECT tstamp, cmdline, diagmsgno, filepath, file, line, column,
                       detectiontype, issueid, extension
                FROM Logs
                ORDER BY rowid
                """
            ).fetchall()

        return rows

    def test_parses_potential_detection_with_timestamp_context(self):
        rows = self.parse_rows(
            """
            2026-03-18 10:22:33 # insp_ctc -c source.c
            W998: ["C:\\project\\src\\main.c" 66/1] [INSP] detected potential occurrence of issue TCVX-44008.
            """
        )

        self.assertEqual(
            rows,
            [
                (
                    "2026-03-18 10:22:33",
                    "insp_ctc -c source.c",
                    "W998",
                    "C:\\project\\src\\main.c",
                    "main.c",
                    "66",
                    "1",
                    "p;-",
                    "TCVX-44008",
                    "",
                )
            ],
        )

    def test_parses_definite_detection_without_timestamp_using_defaults(self):
        rows = self.parse_rows(
            """
            W999: ["C:\\project\\src\\main.c" 7/9] [INSP] detected occurrence of issue TCVX-10000.
            """
        )

        self.assertEqual(rows[0][0], "1970-01-01 00:00:01")
        self.assertEqual(rows[0][1], "")
        self.assertEqual(rows[0][7], "d;-")

    def test_marks_no_change_assembly_comparison_as_n(self):
        rows = self.parse_rows(
            """
            2026-03-18 10:22:33 # insp_ctc -c source.c
            E980: ["C:\\project\\src\\main.c" 42/3] [INSP] detected potential occurrence of issue TCVX-44008. No change in assembly comparison detected. High confidence it is a false positive and therefore can be ignored.
            """
        )

        self.assertEqual(rows[0][7], "p;n")
        self.assertIn("No change in assembly comparison detected", rows[0][9])

    def test_marks_changed_assembly_comparison_as_c_with_placeholders(self):
        rows = self.parse_rows(
            """
            2026-03-18 10:22:33 # insp_ctc -c source.c
            W983: ["C:\\project\\src\\main.c" 42/3] [INSP] detected potential occurrence of issue TCVX-44008. Detected difference in assembly comparison. Assembly files are stored in directory asm as: nofix.s; with fix: withfix.s
            """
        )

        self.assertEqual(rows[0][7], "p;c;./;.affected;.unaffected")
        self.assertIn("Detected difference in assembly comparison", rows[0][9])

    def test_ignores_duplicate_detection_rows(self):
        rows = self.parse_rows(
            """
            2026-03-18 10:22:33 # insp_ctc -c source.c
            W998: ["C:\\project\\src\\main.c" 66/1] [INSP] detected potential occurrence of issue TCVX-44008.
            2026-03-18 10:22:33 # insp_ctc -c source.c
            W998: ["C:\\project\\src\\main.c" 66/1] [INSP] detected potential occurrence of issue TCVX-44008.
            """
        )

        self.assertEqual(len(rows), 1)

    def test_ignores_non_detection_inspector_messages(self):
        rows = self.parse_rows(
            """
            2026-03-18 10:22:33 # insp_ctc -c source.c
            I991: [INSP] No definite or potential issues detected for the enabled list of checks.
            E995: [INSP] problem with assembly comparison execution: failed to invoke diff tool
            """
        )

        self.assertEqual(rows, [])

    def test_empty_log_file_returns_zero(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "empty.log"
            log_path.write_text("", encoding="utf-8")

            db = LogDB(verbose=False)

            self.assertEqual(db.parse_log_file(str(log_path)), 0)

    def test_none_log_file_returns_zero(self):
        db = LogDB(verbose=False)

        self.assertEqual(db.parse_log_file(None), 0)

    def test_verbose_ignored_messages_are_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "verbose.log"
            log_path.write_text(
                textwrap.dedent(
                    """
                    2026-03-18 10:22:33 # insp_ctc -c source.c
                    I991: [INSP] No definite or potential issues detected for the enabled list of checks.
                    I992: [INSP] asm cmp: compare output
                    E993: [INSP] detected change in assembly listing for command: insp_ctc -c source.c
                    E995: [INSP] problem with assembly comparison execution: failed to invoke diff tool
                    """
                ).lstrip("\n"),
                encoding="utf-8",
            )

            db = LogDB(verbose=True)
            output = StringIO()

            with redirect_stdout(output):
                db.parse_log_file(str(log_path))

        text = output.getvalue()
        self.assertIn("INFO: Read passed log file", text)
        self.assertIn("IGNORE: no-issue-detected messages", text)
        self.assertIn("IGNORE: Asm cmp message", text)
        self.assertIn("IGNORE: Problem identified with assembler comparison execution", text)


class AddLogEntryErrorHandlingTests(unittest.TestCase):
    def test_add_log_entry_handles_programming_operational_and_database_errors(self):
        entry = Detection(
            "2026-03-18 10:22:33",
            "insp_ctc -c source.c",
            "W998",
            "C:/project/src/main.c",
            "main.c",
            "66",
            "1",
            "p;-",
            "TCVX-44008",
            "",
        )

        for exc_type, message in (
            (sqlite3.ProgrammingError, "Programming Error"),
            (sqlite3.OperationalError, "Operational Error"),
            (sqlite3.DatabaseError, "Database Error"),
        ):
            with self.subTest(exc_type=exc_type.__name__):
                db = LogDB(verbose=False)
                db.curs = Mock()
                db.curs.execute.side_effect = exc_type("boom")
                output = StringIO()

                with redirect_stdout(output):
                    db._add_log_entry(entry)

                self.assertIn(message, output.getvalue())

    def test_delete_closes_connection(self):
        db = LogDB(verbose=False)
        conn = db.conn

        db.__del__()

        with self.assertRaises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")


if __name__ == "__main__":
    unittest.main()