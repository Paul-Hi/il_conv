"""
File:   parse.py 
Desc:   Script functions to parse Tasking Compiler/Inspector output

Copyright (C) 2022 Paul Himmler, Peter Himmler
Apache License 2.0
"""

import re
import os
import sqlite3

from collections import namedtuple


# =============================================================================
# Regex patterns for parsing TASKING Inspector log output
# =============================================================================

# Timestamp row pattern
# Example: "2021-08-04 13:40:16 # insp_ctc -E+comments -c99 ..."
RE_TIMESTAMP = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) # (?P<cmdline>.*)"
)

# Detection message pattern (main Inspector output)
# Diagnostic codes:
#   E996/E997: Error - potential/definite occurrence
#   W998/W999: Warning - potential/definite occurrence
#   E980/W981: Potential occurrence, no assembly change (likely false positive)
#   E982/W983: Potential occurrence, assembly difference detected
# Example: W998: ["C:\path\file.h" 66/1] [INSP] detected potential occurrence of issue TCVX-44008.
RE_DETECTION = re.compile(
    r"(?P<prefix>.*)"
    r"(?P<diagcode>E980|W981|E982|W983|W999|W998|E997|E996):\s*"
    r'\["(?P<filepath>.*)"\s(?P<line>\d*)[/](?P<column>\d*)\]\s'
    r"\[INSP\]\s(?P<message>.+?)"
    r"(?P<issueid>TCVX-\d+)\."
    r"(?P<extension>.*)"
)

# No issues detected pattern
# Example: I991: [INSP] No definite or potential issues detected for the enabled list of ...
RE_NO_ISSUES = re.compile(
    r"(?P<prefix>.*)(?P<diagcode>I991|I993):\s\[INSP\]\s(?P<message>.*)"
)

# Assembly comparison / informational messages pattern
# Diagnostic codes:
#   I991: No issues detected (also matched above)
#   I992: Assembly comparison info
#   E993/W994: Change detected in assembly listing
#   E995: Problem with assembly comparison execution
# Example: E993: [INSP] detected change in assembly listing for command: <cmd>
RE_ASM_INFO = re.compile(
    r"(?P<prefix>.*)"
    r"(?P<diagcode>I991|I992|E993|W994|E995):\s\[INSP\]\s"
    r"(?P<message>.+?)(?P<separator>:\s)(?P<detail>.*)"
)


_DETECTION_RECORD_INFO = [
    # fieldname, idx / primary, default value
    ("tstamp", False, ""),
    ("cmdline", True, ""),  # idx
    ("diagmsgno", False, ""),
    ("filepath", True, ""),  # idx
    ("file", True, ""),  # idx
    ("line", True, ""),  # idx
    ("column", True, ""),  # idx
    ("detectiontype", False, ""),  # str: (p | d ) ; ( c | n | - ) [; <file.affexted> ; <file.notaffected> ]
                                   #  p = potential, d = definite, c = asm changed, n = no change, optional assembly files
    ("issueid", True, ""),  # idx
    ("extension", False, ""),
]


DETECTION_RECORD = [v for (v, pk, df) in _DETECTION_RECORD_INFO]

Detection = namedtuple(
    "Detection", DETECTION_RECORD, defaults=("", "", "", "", "", "", "", "", "", "")
)
"""Data type to store release note information per issue"""


class LogDB(object):
    """The LogDB stores all information we gather from log files passed."""

    def __init__(self, verbose: False):
        self.conn = sqlite3.connect(":memory:")
        # "log.db") #":memory:")
        self.curs = self.conn.cursor()
        self.verbose = verbose
        self._create_tables()

    def __del__(self):
        if self.conn:
            self.conn.close()

    def _create_tables(self):
        cols = ",".join(
            [
                "{} TEXT DEFAULT '{}'".format(n, dv)
                for (n, idx, dv) in _DETECTION_RECORD_INFO
            ]
            + [" PRIMARY KEY ( "]
        )
        cols += ",".join([n for (n, idx, dv) in _DETECTION_RECORD_INFO if idx]) + ")"
        self.curs.execute("DROP TABLE IF EXISTS Logs")
        create = "CREATE TABLE IF NOT EXISTS Logs (" + cols + ")"
        self.curs.execute(create)

        # create unique index
        # cols = [ v for (v, idx) in _DETECTION_RECORD_INFO if idx]
        # cols = ','.join(cols)
        # create = "CREATE UNIQUE INDEX IF NOT EXISTS Logs_idx ON Logs (" + cols + ")"
        # self.cur.execute(create)
        self.conn.commit()

    def _add_log_entry(self, e: Detection):
        number_of_fields = len(Detection._fields)
        sql = "INSERT INTO Logs (" + ",".join(Detection._fields) + " ) "
        sql += " VALUES ( " + ",".join(["?"] * number_of_fields) + " )"

        try:
            self.curs.execute(
                sql,
                (
                    e.tstamp,
                    e.cmdline,
                    e.diagmsgno,
                    e.filepath,
                    e.file,
                    e.line,
                    e.column,
                    e.detectiontype,
                    e.issueid,
                    e.extension,
                ),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as ie:
            # Following would be helpful but as Inspector diagnostic messages might be unavoidably duplicated this is commented out
            #           if self.verbose:
            #                print(f"IGNORE: DB Integrity Error. You might have added a log file twice. Same (locations of) detection message are ignored. {e}.")
            pass

        except sqlite3.ProgrammingError as pe:
            print(f"Programming Error: {pe}")
        except sqlite3.OperationalError as oe:
            print(f"Operational Error: {oe}")
        except sqlite3.DatabaseError as de:
            print(f"Database Error: {de}")

    def parse_log_file(self, file_name: str) -> int:
        """Import build log files into database table.
            Does some dump cross checks ...
        Attributes:
            file_name (str): The file name of the file to parse (relative path)

        Returns:
            int: return number of inserted new logs
        """
        lines = []

        if file_name is not None:
            if self.verbose:
                print("INFO: Read passed log file '" + str(file_name) + "'")
            with open(file_name) as fp:
                lines = fp.readlines()

        if not lines:
            if self.verbose:
                print("ERROR: No input in passed log file!")
            return 0

        if self.verbose:
            print("INFO: Parse log file information!")

        # parse algo
        reusePreviousRow = False

        for log_line_no, li in enumerate(lines):
            # Match timestamp rows
            match = RE_TIMESTAMP.match(li)
            if match:
                # "timestamp row" -> empty new row
                if reusePreviousRow:
                    current_row = dict()

                tstamp = match.group("timestamp")
                cmdline = match.group("cmdline").strip()

                reusePreviousRow = True
                continue

            # Match detection messages
            match = RE_DETECTION.match(li)
            if match:
                if not reusePreviousRow:
                    tstamp = "1970-01-01 00:00:01"
                    cmdline = ""

                diagmsgno = match.group("diagcode").strip()
                fp = match.group("filepath").strip()
                fp = os.path.normpath(fp)
                fp = fp.replace("\\", "/")
                fp = os.path.normpath(fp)
                filepath = fp
                file = os.path.basename(fp)
                line = match.group("line")
                column = match.group("column")
                message = match.group("message").strip()
                if message.find("detected potential occurrence") > -1:
                    detectiontype = "p"
                elif message.find("detected occurrence") > -1:
                    detectiontype = "d"
                else:
                    assert False, "ERROR: Script is wrong - no unclear result possible!"
                    detectiontype = "unclear result"

                issueid = match.group("issueid").strip()
                extension = match.group("extension").strip()
                
                ## NEW additional information if assembly comparison resulted in relevant diff within the same log message
                if extension.find("No change in assembly comparison") > -1:
                    detectiontype = detectiontype + ";n" # likely a false positive detection, no change in assembly comparison detected"
                elif extension.find("Detected difference in assembly comparison") > -1:
                    detectiontype = detectiontype + ";c" # needs manual impact analysis which you can start based on generated assembly files {extension}"
                    # TODO parse out the affected / non-affected assembly files out when we require them
                    detectiontype = detectiontype + ";./;.affected;.unaffected"

                else:
                    detectiontype = detectiontype + ";-" # normal detection, no assembly comparison available
                    
    
    
                e = Detection(
                    tstamp,
                    cmdline,
                    diagmsgno,
                    filepath,
                    file,
                    line,
                    column,
                    detectiontype,
                    issueid,
                    extension,
                )
                
                self._add_log_entry(e)

                reusePreviousRow = False
                continue

            # Match "no issues detected" messages
            match = RE_NO_ISSUES.match(li)
            if match:
                if not reusePreviousRow:
                    tstamp = "1970-01-01 00:00:02"
                    cmdline = ""

                diagmsgno = match.group("diagcode").strip()
                if "I991" in diagmsgno:
                    if self.verbose:
                        print("IGNORE: no-issue-detected messages\n")

                reusePreviousRow = True
                continue

            # Match assembly comparison / informational messages
            match = RE_ASM_INFO.match(li)
            if match:
                if not reusePreviousRow:
                    tstamp = "1970-01-01 00:00:03"
                    cmdline = ""

                diagmsgno = match.group("diagcode").strip()
                detail = match.group("detail")
                if "E993" in diagmsgno or "W994" in diagmsgno:
                    if self.verbose:
                        print(
                            "IGNORE: Detected change in assembler listing messages cmd {0}\n",
                            detail,
                        )
                elif "I992" in diagmsgno:
                    if self.verbose:
                        print(
                            "IGNORE: Asm cmp message. You want to manually evaluate / compare the generated files.\n"
                        )
                elif "E995" in diagmsgno:
                    if self.verbose:
                        print(
                            "IGNORE: Problem identified with assembler comparison execution: {0}.\n",
                            detail,
                        )
                reusePreviousRow = True
                continue

        return
