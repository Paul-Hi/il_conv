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
## Note: Exxx messages only used internal at TASKING (according to TASKING) and can't be generated
##       by a release Inspector tool
# insp_cctc.exe --diag=all|rg \[INSP
#  I991: [INSP] No definite or potential issues detected for the enabled list of
#  E996: [INSP] detected occurrence of issue <id>
#  E997: [INSP] detected potential occurrence of issue <id>
#  W998: [INSP] detected potential occurrence of issue <id>
#  W999: [INSP] detected occurrence of issue <id>
# insp_cptc.exe --diag|rg \[INSP
#  2950: [INSP] detected potential occurrence of issue %s.
#  2951: [INSP] detected occurrence of issue %s.
#  2952: [INSP] No definite or potential issues detected for the enabled list of detectors
# insp_ctc.exe --diag=all|rg \[INSP
##  E980: [INSP] detected potential occurrence of issue <id> No change in assembly
###  W981: [INSP] detected potential occurrence of issue <id> No change in assembly
##  E982: [INSP] detected potential occurrence of issue <id> Detected difference
###  W983: [INSP] detected potential occurrence of issue <id> Detected difference
##  W984: [INSP] Input MIL files (.mil, .ma, .ms) are identified. Inspector cannot
#  I991: [INSP] No definite or potential issues detected for the enabled list of
##  I992: [INSP] asm cmp: <text>
##  E993: [INSP] detected change in assembly listing for command: <cmd>
##  W994: [INSP] detected change in assembly listing for command: <cmd>
##  E995: [INSP] problem with assembly comparison execution: <problem>
#  E996: [INSP] detected potential occurrence of issue <id>
#  E997: [INSP] detected occurrence of issue <id>
#  W998: [INSP] detected potential occurrence of issue <id>
#  W999: [INSP] detected occurrence of issue <id>
# insp_astc.exe --diag=all|rg \[INSP
##  I991: [INSP] No definite or potential issues detected for the enabled list of
#  E996: [INSP] detected occurrence of issue <id>
#  E997: [INSP] detected potential occurrence of issue <id>
#  W998: [INSP] detected potential occurrence of issue <id>
#  W999: [INSP] detected occurrence of issue <id>
# insp_ltc.exe --diag=all|rg \[INSP
##  I993: [INSP] No definite or potential issues detected for the enabled list of
#  E996: [INSP] detected occurrence of issue <id>
#  E997: [INSP] detected potential occurrence of issue <id>
#  W998: [INSP] detected potential occurrence of issue <id>
#  W999: [INSP] detected occurrence of issue <id>

# Diagnostic codes:
#   E996/E997: Error - potential/definite occurrence
#   W998/W999: Warning - potential/definite occurrence
#   E980/W981: Potential occurrence, no assembly change (likely false positive)
#   E982/W983: Potential occurrence, assembly difference detected
# Example: W998: ["C:\path\file.h" 66/1] [INSP] detected potential occurrence of issue TCVX-44008.
RE_DETECTION = re.compile(
    r"(?P<prefix>.*)"
    r"(?P<diagcode>W998|W999|E996|E997):\s*"
    r'\["(?P<filepath>.*)"\s(?P<line>\d*)/(?P<column>\d*)\]\s'
    r"\[INSP\]\s(?P<message>.+?)"
    r"(?P<issueid>(TCVX-|SMRT-)\d+)[\.\s]"
    r"(?P<extension>.*)"
)

# No issues detected pattern
# Example:
#  I991: [INSP] No definite or potential issues detected for the enabled list of
# insp_ctc.exe
#  W984: [INSP] Input MIL files (.mil, .ma, .ms) are identified. Inspector cannot
#  I992: [INSP] asm cmp: <text>
#  E993: [INSP] detected change in assembly listing for command: <cmd>
#  W994: [INSP] detected change in assembly listing for command: <cmd>
#  E995: [INSP] problem with assembly comparison execution: <problem>
# insp_ltc.exe
#  I993: [INSP] No definite or potential issues detected for the enabled list of# I993 same but other tool

RE_DIAG_ONLY_VERBOSE_LOG = re.compile(
    r"(?P<prefix>.*)(?P<diagcode>I991|W984|I993|I992|E993|W994|E995):\s\[INSP\]\s(?P<message>.*)"
)

# Assembly comparison / informational messages pattern
##  E980: [INSP] detected potential occurrence of issue <id> No change in assembly
###  W981: [INSP] detected potential occurrence of issue <id> No change in assembly
##  E982: [INSP] detected potential occurrence of issue <id> Detected difference
###  W983: [INSP] detected potential occurrence of issue <id> Detected difference
RE_ASM_INFO = re.compile(
    r"(?P<prefix>.*)"
    r"(?P<diagcode>E980|W981|E982|W983):\s*"
    r'\["(?P<filepath>.*)"\s(?P<line>\d*)/(?P<column>\d*)\]\s'
    r"\[INSP\]\s(?P<message>.+ of issue )"
    r"(?P<issueid>(TCVX-|SMRT-)\d+)[\.\s]"
    r"(?P<extension>.*)"
)

RE_ASM_INFO_DIFFERENCE = re.compile(
    r"(?P<prefix>.*Assembly files are stored in directory )"
    r"(?P<directory>.+) as: "
    r"(?P<file_affected>.*); with fix: (?P<file_unaffected>.*)\.$"
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
    (
        "detectiontype",
        False,
        "",
    ),  # str: (p | d ) ; ( c | n | - ) [; <file.affexted> ; <file.notaffected> ]
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

    def __init__(self, verbose: bool = False):
        self.conn = sqlite3.connect(":memory:")
        # "log.db") #":memory:")
        self.curs = self.conn.cursor()
        self.verbose = verbose
        self._create_tables()

    def __del__(self):
        conn = getattr(self, "conn", None)
        if conn:
            conn.close()

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

    def parse_log_file(self, file_name: str) -> None:
        """Import build log files into database table.
            Does some dump cross checks ...
        Attributes:
            file_name (str): The file name of the file to parse (relative path)

        Returns:
            None
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
            return

        if self.verbose:
            print("INFO: Parse log file information!")

        # parse algo
        reusePreviousRow = False

        for log_line_no, li in enumerate(lines):
            # Match timestamp rows  (only available in insp-log file)
            match = RE_TIMESTAMP.match(li)
            if match:
                # "timestamp row"
                tstamp = match.group("timestamp")
                cmdline = match.group("cmdline").strip()

                reusePreviousRow = True
                continue

            # Match detection messages
            match = RE_DETECTION.match(li)
            if match:
                if not reusePreviousRow:
                    tstamp = "1970-01-01 00:00:01"
                    cmdline = "Note: Without using --insp-log the cmdline is unknown!"

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
                    detectiontype = (
                        "p;-"  # normal detection, no assembly comparison available
                    )
                elif message.find("detected occurrence") > -1:
                    detectiontype = (
                        "d;-"  # normal detection, no assembly comparison available
                    )
                else:
                    raise RuntimeError("ERROR: Script is wrong - no unclear result possible!")
                    
                issueid = match.group("issueid").strip()
                extension = match.group("extension").strip()

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

            # Match msg - to be ignored - only give a verbose log messge here
            match = RE_DIAG_ONLY_VERBOSE_LOG.match(li)
            if match:
                if not reusePreviousRow:
                    tstamp = "1970-01-01 00:00:02"
                    cmdline = ""

                diagmsgno = match.group("diagcode").strip()
                if "I991" in diagmsgno or "I993" in diagmsgno:
                    if self.verbose:
                        print("IGNORE: No-issue-detected messages\n")
                elif "W984" in diagmsgno:
                    if self.verbose:
                        print(
                            "IGNORE: Input MIL files (.mil, .ma, .ms) are identified. Inspection might not be accurate or even wrong!\n"
                        )
                elif "I992" in diagmsgno or "E995" in diagmsgno:
                    if self.verbose:
                        print("IGNORE: Manual asm comparison or problem problems\n")
                elif "E993" in diagmsgno or "W994" in diagmsgno:
                    if self.verbose:
                        print("IGNORE: Manual asm comparison results\n")
                reusePreviousRow = False
                continue

            # Match assembly comparison / informational messages
            match = RE_ASM_INFO.match(li)
            if match:
                if not reusePreviousRow:
                    tstamp = "1970-01-01 00:00:03"
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
                issueid = match.group("issueid").strip()
                extension = match.group("extension").strip()

                # find out if it's a likely a false positive - which should be ignored
                # or a real problem to check manually.
                if "E980" in diagmsgno or "W981" in diagmsgno:
                    if self.verbose:  # No change in assembly a potential false positive?
                        print(f"INFO ({log_line_no}):\t{extension}")
                    detectiontype = "p;n"

                elif "E982" in diagmsgno or "W983" in diagmsgno:
                    if self.verbose:
                        print(f"INFO ({log_line_no}):\tManual check required! {extension}")

                    match2 = RE_ASM_INFO_DIFFERENCE.match(extension)
                    if match2:
                        dir = match2.group("directory").strip()
                        dir = os.path.normpath(dir)
                        dir = dir.replace("\\", "/")
                        dir = os.path.normpath(dir)
                        file_affected = match2.group("file_affected").strip()
                        file_unaffected = match2.group("file_unaffected").strip()
                        if self.verbose:
                            print(f"INFO ({log_line_no}): \tDirectory\t'{dir}'\n\t\tAffected:\t'{file_affected}'\n\t\tUnaffected:\t'{file_unaffected}'")

                        detectiontype = (
                            "p;c;"
                            + dir
                            + ";"
                            + file_affected
                            + ";"
                            + file_unaffected
                        )
                    else:
                        detectiontype = "p;c;?;?;?"
                else:
                    detectiontype = "unclear result"

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
            print(f"ERROR: UNKNOWN LINE {log_line_no} skipped:\n{li}\n")
        return
