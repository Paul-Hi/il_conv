"""
File:   test.py
Desc:   Some unittests.

Copyright (C) 2022 Paul Himmler, Peter Himmler
Apache License 2.0
"""

from email.policy import default
import unittest
import configs
from export import ExcelExporter, HTMLExporter
import tables
import parse


class TableTest(unittest.TestCase):

    def test_page_append(self):
        page = tables.Page()

        row = {"name": "test", "id": 1}

        for _ in range(0, 70):
            self.assertTrue(page.append(row))  # sizeof row is 232 bytes

        self.assertEqual(len(page.rows), 70)

        self.assertFalse(page.append(row))

        self.assertEqual(len(page.rows), 70)

    def test_page_iter(self):
        page = tables.Page()

        rows = []

        rows.append({"name": "zeroRow", "id": 0})
        rows.append({"name": "first", "id": 1})
        rows.append({"name": "second", "id": 2})
        rows.append({"name": "third", "id": 3})

        self.assertTrue(page.append(rows[0]))
        self.assertTrue(page.append(rows[1]))
        self.assertTrue(page.append(rows[2]))
        self.assertTrue(page.append(rows[3]))

        self.assertEqual(len(page.rows), 4)

        idx = 0
        for row in page:
            self.assertEqual(rows[idx], row)
            idx += 1

    def test_table_append(self):
        table = tables.Table()

        row = {"name": "test", "id": 1}

        for _ in range(0, 70):
            table.append(row)  # sizeof row is 232 bytes

        self.assertEqual(len(table.pages), 1)

        table.append(row)

        self.assertEqual(len(table.pages), 2)

    def test_table_iter(self):
        table = tables.Table()

        default_row = {"name": "test", "id": 100}

        for _ in range(0, 70):
            table.append(default_row)  # sizeof default_row is 232 bytes

        self.assertEqual(len(table.pages), 1)

        rows = []

        rows.append({"name": "zeroRow", "id": 0})
        rows.append({"name": "first", "id": 1})
        rows.append({"name": "second", "id": 2})
        rows.append({"name": "third", "id": 3})

        table.append(rows[0])
        table.append(rows[1])
        table.append(rows[2])
        table.append(rows[3])

        self.assertEqual(len(table.pages), 2)

        idx = -70
        for row in table:
            if idx < 0:
                self.assertEqual(default_row, row)
            else:
                self.assertEqual(rows[idx], row)
            idx += 1

    def test_table_remove_duplicates(self):
        table = tables.Table()

        default_row = {"name": "test", "id": 100}

        for _ in range(0, 120):
            table.append(default_row)  # sizeof default_row is 232 bytes

        self.assertEqual(len(table.pages), 2)
        self.assertEqual(table.row_count, 120)

        table.remove_duplicates()

        self.assertEqual(len(table.pages), 1)
        self.assertEqual(table.row_count, 1)

    def test_table_sort(self):
        table = tables.Table()

        default_row = {"name": "test", "id": 0}

        for i in reversed(range(0, 10)):
            default_row["id"] = i
            table.append(default_row.copy())

        sorted_table = table.get_sorted("id")

        i = 0
        for row in table:
            default_row["id"] = i
            self.assertNotEqual(default_row, row)
            i += 1

        i = 0
        for row in sorted_table:
            default_row["id"] = i
            self.assertEqual(default_row, row)
            i += 1


class ParserTest(unittest.TestCase):

    def test_parse_log1(self):
        configuration = configs.Config()
        table = parse.parse_file(
            "./testdata/multiple-issues.log", configuration)

        table.remove_duplicates()

        self.assertEqual(table.row_count, 11)

        for row in table:
            # Assert all columns, since we know log1 should fill all of them
            # We also know the exact source file, ticket id and command
            self.assertNotEqual(row[parse.TIMEDATE_KEY], "")
            self.assertNotEqual(row[parse.DIAG_MSG_KEY], "")
            self.assertEqual(row[parse.SOURCE_FILE_KEY],
                             "examples\insp-errors.c")
            self.assertNotEqual(row[parse.SOURCE_LINE_KEY], "")
            self.assertNotEqual(row[parse.SOURCE_COLUMN_KEY], "")
            self.assertIn("TCVX", row[parse.TICKET_ID_KEY])
            self.assertEqual(
                row[parse.COMMAND_KEY], "insp_ctc --core=tc1.3 --fp-model=+float --insp-log=log-with_multiple.txt -o c:\\tmp\cc23920a.src examples\insp-errors.c")
            self.assertIn("examples\insp-errors.c",
                          row[parse.SOURCE_FILE_KEY])


class ExcelExporterTest(unittest.TestCase):

    def test_export_simple_log_table(self):
        table = tables.Table()

        table.append({'Date&Time': '2121-12-12 21:21:12', 'IssuesPortal ID': 'TCVX-43893', 'DiagMsg Number': 'IWEFxxx', 'File impacted': 'file', 'Line impacted': 0,
                     'Col impacted': 0, 'DiagMsg': '[INSP] message for issue TCVX-43893.', 'File Line/Column': '["file" 0/0]', 'Full Cmd': 'someCommand'})
        table.append({'Date&Time': '2121-12-12 21:21:12', 'IssuesPortal ID': 'TCVX-43893', 'DiagMsg Number': 'IWEFxxx', 'File impacted': 'file', 'Line impacted': 1,
                     'Col impacted': 0, 'DiagMsg': '[INSP] message for issue TCVX-43893.', 'File Line/Column': '["file" 1/0]', 'Full Cmd': 'someCommand'})
        table.append({'Date&Time': '2121-12-12 21:21:12', 'IssuesPortal ID': 'TCVX-43893', 'DiagMsg Number': 'IWEFxxx', 'File impacted': 'file', 'Line impacted': 2,
                     'Col impacted': 0, 'DiagMsg': '[INSP] message for issue TCVX-43893.', 'File Line/Column': '["file" 2/0]', 'Full Cmd': 'someCommand'})
        table.append({'Date&Time': '2121-12-12 21:21:12', 'IssuesPortal ID': 'TCVX-43893', 'DiagMsg Number': 'IWEFxxx', 'File impacted': 'file', 'Line impacted': 3,
                     'Col impacted': 0, 'DiagMsg': '[INSP] message for issue TCVX-43893.', 'File Line/Column': '["file" 3/0]', 'Full Cmd': 'someCommand'})

        exporter = ExcelExporter()
        configuration = configs.Config()

        exporter.export(table, "test_export_simple_log_table",
                        configuration, verbose=True)


class HTMLExporterTest(unittest.TestCase):

    def test_export_simple_log_table(self):
        table = tables.Table()

        table.append({'Date&Time': '2121-12-12 21:21:12', 'IssuesPortal ID': 'TCVX-43893', 'DiagMsg Number': 'IWEFxxx', 'File impacted': 'file', 'Line impacted': 0,
                     'Col impacted': 0, 'DiagMsg': '[INSP] message for issue TCVX-43893.', 'File Line/Column': '["file" 0/0]', 'Full Cmd': 'someCommand'})
        table.append({'Date&Time': '2121-12-12 21:21:12', 'IssuesPortal ID': 'TCVX-43893', 'DiagMsg Number': 'IWEFxxx', 'File impacted': 'file', 'Line impacted': 1,
                     'Col impacted': 0, 'DiagMsg': '[INSP] message for issue TCVX-43893.', 'File Line/Column': '["file" 1/0]', 'Full Cmd': 'someCommand'})
        table.append({'Date&Time': '2121-12-12 21:21:12', 'IssuesPortal ID': 'TCVX-43893', 'DiagMsg Number': 'IWEFxxx', 'File impacted': 'file', 'Line impacted': 2,
                     'Col impacted': 0, 'DiagMsg': '[INSP] message for issue TCVX-43893.', 'File Line/Column': '["file" 2/0]', 'Full Cmd': 'someCommand'})
        table.append({'Date&Time': '2121-12-12 21:21:12', 'IssuesPortal ID': 'TCVX-43893', 'DiagMsg Number': 'IWEFxxx', 'File impacted': 'file', 'Line impacted': 3,
                     'Col impacted': 0, 'DiagMsg': '[INSP] message for issue TCVX-43893.', 'File Line/Column': '["file" 3/0]', 'Full Cmd': 'someCommand'})

        exporter = HTMLExporter()
        configuration = configs.Config()

        exporter.export(table, "test_export_simple_log_table",
                        configuration, verbose=True)


if __name__ == "__main__":
    unittest.main()
