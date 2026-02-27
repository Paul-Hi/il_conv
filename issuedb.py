"""
File:   issuedb.py 
Desc:   Script function to parse Tasking Issue Portal XML file and readme release note HTML file in a database

Copyright (C) 2024 Peter Himmler
Apache License 2.0
"""

# import sys
# assert sys.version_info.major == 3 and sys.version_info.minor in (10, 11), "ERROR: script works only with Python 3.10 or 3.11"
# import os


from pathlib import Path
from bs4 import BeautifulSoup
import sqlite3
from collections import namedtuple


RELEASE_NOTE_RECORD = [
    "id",
    "sil",
    "summary",
    "inspcomp",
    "asscmp",
    "detectiontype",
]

ReleaseNoteIssue = namedtuple(
    "ReleaseNoteIssue",
    RELEASE_NOTE_RECORD,  # ['id', 'sil', 'summary', 'inspcomp', 'asscmp', 'detectiontype'] ,
    defaults=("", "", "", "", "", ""),
)
"""Data type to store release note information per issue"""

XML_EXPORT_RECORD = [
    "id",
    "sil",
    "mitigation",
    "affected_version",
    "fix_version",
    "summary",
    "description",
    "published",
    "last_updated",
    "component",
    "affected_toolchains",
    "issue_inspector",
]

PortalIssue = namedtuple(
    "PortalIssue",
    XML_EXPORT_RECORD,
    defaults=(
        "",
        "",
        "PLEASE LOOKUP issue in issue portal!",
        "",
        "",
        "",
        "",
        "1-1-1970",
        "1-1-1970",
        "",
        "",
        "??",
    ),
)
"""Data type to store portal issue / / XML export information per issue"""

ISSUE_RECORD = [
    "id",
    "sil",
    "mitigation",
    "affected_version",
    "fix_version",
    "summary",
    "description",
    "published",
    "last_updated",
    "component",
    "affected_toolchains",
    "issue_inspector",
    "inspcomp",
    "asscmp",
    "detectiontype",
]

Issue = namedtuple(
    "Issue",
    ISSUE_RECORD,
    defaults=(
        "",
        "",
        "PLEASE LOOKUP issue in issue portal!",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    ),
)


def _get_text(tag, default: str = "") -> str:
    """Return stripped text of a BeautifulSoup tag, or default if the tag is None."""
    return tag.get_text(strip=True) if tag is not None else default


class IssueDB(object):
    """The IssueDB hosting all information we know from issues."""

    def __init__(
        self,
        compiler_version: str,
        inspector_version: str,
        xmlfile: Path,
        relnotefile: Path,
        verbose: False,
    ):

        self.compiler_version = compiler_version
        self.inspector_version = inspector_version
        self.dbname = "issues-{}-{}.db".format(compiler_version, inspector_version)
        self.xmlfile = xmlfile
        self.relnotefile = relnotefile
        self.verbose = verbose
        self.conn = sqlite3.connect(self.dbname)  # , autocommit = True)
        self.cur = self.conn.cursor()
        self._create_tables()

    def __del__(self):
        if self.conn:
            self.conn.close()

    def _create_tables(self):
        # create ReleaseNoteIssue table
        defaultVal = ReleaseNoteIssue()._asdict()

        cols = ["{} TEXT DEFAULT '{}'".format(n, v) for n, v in defaultVal.items()]
        cols[0] = "{} TEXT PRIMARY KEY".format(ReleaseNoteIssue._fields[0])
        line = ",".join(cols)
        cols = line
        self.cur.execute("DROP TABLE IF EXISTS ReleaseNoteIssues")
        create = "CREATE TABLE IF NOT EXISTS ReleaseNoteIssues (" + cols + ")"
        self.cur.execute(create)

        # create PortalIssue table
        defaultVal = PortalIssue()._asdict()

        cols = ["{} TEXT DEFAULT '{}'".format(n, v) for n, v in defaultVal.items()]
        cols[0] = "{} TEXT PRIMARY KEY".format(ReleaseNoteIssue._fields[0])
        line = ",".join(cols)
        cols = line
        self.cur.execute("DROP TABLE IF EXISTS PortalIssues")
        create = "CREATE TABLE IF NOT EXISTS PortalIssues (" + cols + ")"
        self.cur.execute(create)
        self.conn.commit()

    def _count_of_rows(self, tablename: str) -> int:
        sql = "SELECT count(*) FROM " + tablename
        num = self.cur.execute(sql).fetchone()[0]
        return num

    def _add_release_note_issue(self, row: ReleaseNoteIssue):
        number_of_fields = len(ReleaseNoteIssue._fields)
        sql = (
            "INSERT INTO ReleaseNoteIssues ("
            + ",".join(ReleaseNoteIssue._fields)
            + " ) "
        )
        sql += " VALUES ( " + ",".join(["?"] * number_of_fields) + " )"
        "INSERT INTO ReleaseNoteIssues (id,sil,summary,inspcomp,asscmp,detectiontype)VALUES ( ?,?,?,?,?,?)"
        self.cur.execute(
            sql,
            (row.id, row.sil, row.summary, row.inspcomp, row.asscmp, row.detectiontype),
        )
        self.conn.commit()

    def _add_portal_issue(self, row: PortalIssue):
        number_of_fields = len(PortalIssue._fields)
        sql = "INSERT INTO PortalIssues (" + ",".join(PortalIssue._fields) + " ) "
        sql += " VALUES ( " + ",".join(["?"] * number_of_fields) + " )"
        "INSERT INTO PortalIssues (id,...) VALUES ( ?,...)"
        self.cur.execute(sql, tuple(row))
        self.conn.commit()

    def import_release_note(self) -> int:
        """Import Inspector release note file into database table.
            Does some dump cross checks with passed inspector compiler version ...

        Args:

        Returns:
            int: return number of inserted release note issues / inspector detectors
        """

        input = ""

        if self.relnotefile is not None:
            if self.verbose:
                print(
                    "INFO: Read issue information from release note '"
                    + str(self.relnotefile)
                    + "'"
                )
            with open(self.relnotefile) as fp:
                input = fp.read()

        if not input:
            if self.verbose:
                print("ERROR: No input in passed release notes file!")
            return 0
        if self.verbose:
            print("INFO: Import issue information")

        soup = BeautifulSoup(input, "html.parser")
        title_tag = soup.title
        if title_tag is None:
            raise ValueError(
                "\nERROR: Release Notes / Readme file is missing a <title> tag"
            )
        title = title_tag.get_text(strip=True)
        err = "\nERROR: Release Notes / Readme file has wrong structure for 'TriCore {} Inspector {}' , saw title '{}' ".format(
            self.compiler_version, self.inspector_version, title
        )
        if self.compiler_version not in title:
            raise ValueError(err)

        #
        # Parse out the table from html file.
        # Note: This is a clear miss-use of the HTML file, but ....
        # CHECK_ON_NEW_RELEASES
        #
        htmltable = soup.body.find("table", attrs={"class": "detectors"})
        trows = htmltable.find_all("tr")

        headerrow = [
            th.get_text(strip=True) for th in trows[0].find_all("th")
        ]  # header row

        if len(headerrow) == 0:
            headerrow = [
                th.get_text(strip=True)
                for th in trows[0].find_all("td", attrs={"class": "heading"})
            ]  # header row

        if len(headerrow) > 0:
            trows = trows[1:]  # skip header row if any

        if self.verbose:
            print(
                "INFO: HTML header row(s) ignored when importing the inspector readme / release notes"
            )

        for row in trows:
            td = row.find("td")
            # url = td.a['href']
            id = td.get_text(strip=True)

            td = td.find_next_sibling()
            summary = td.get_text(strip=True)

            td = td.find_next_sibling()
            sil = td.get_text(strip=True)

            td = td.find_next_sibling()
            inspcomp = td.get_text(strip=True)

            td = td.find_next_sibling()
            asscmp = td.get_text(strip=True)
            if len(asscmp) > 0:
                asscmp = "Yes"
            else:
                asscmp = "No"

            td = td.find_next_sibling()
            detectiontype = td.get_text(strip=True)

            newrow = [id, sil, summary, inspcomp, asscmp, detectiontype]

            # unpack list into ReleaseNoteIssue
            entry = ReleaseNoteIssue(*newrow)

            self._add_release_note_issue(entry)

        return self._count_of_rows("ReleaseNoteIssues")

    def import_xml_file(self) -> int:
        """Import TASKING issue portal compiler XML-export files into database table.
            Does some dump cross checks with passed inspector compiler version ...

        Args:

        Returns:
            int: return number of inserted XML export portal issue information.

        Note: XML export from portal includes no 'closed' ticket information = won't fix or dublicated
        """

        input = ""

        if self.xmlfile is not None:
            if self.verbose:
                print(
                    "INFO: Read issue portal XML file passed '"
                    + str(self.xmlfile)
                    + "'"
                )
            with open(self.xmlfile, encoding="utf-8") as fp:
                input = fp.read()

        if not input:
            if self.verbose:
                print("ERROR: No input in passed XML issue portal export file file!")
            return 0
        if self.verbose:
            print("INFO: Import detector / issue information.")

        soup = BeautifulSoup(input, "xml")
        pv_tag = soup.find("product_version")
        if pv_tag is None:
            raise ValueError("ERROR: XML file is missing required <product_version> tag")
        pv = pv_tag.get_text(strip=True)
        pvv = pv[-len(self.compiler_version) :]
        err = "\nERROR: XML file is for wrong compiler version\nERROR: Expect file for 'TriCore {}' saw tag '{}' ".format(
            self.compiler_version, pv
        )
        if self.compiler_version != pvv:
            raise ValueError(err)

        all_issues = soup.find_all("issue")
        # number_of_issues = len(all_issues)

        for index, issue in enumerate(all_issues):
            id = _get_text(issue.find("id"))
            summary = _get_text(issue.find("summary"))

            component = ",".join(
                [co.get_text(strip=True) for co in issue.find_all("component")]
            )

            affected_toolchain = ",".join(
                [af.get_text(strip=True) for af in issue.find_all("affected_toolchain")]
            )

            sil = _get_text(issue.find("sil"))
            published = _get_text(issue.find("published"))
            updated = _get_text(issue.find("updated"))
            mitigation = _get_text(issue.find("mitigation"))

            affected_version = ",".join(
                [av.get_text(strip=True) for av in issue.find_all("affected_version")]
            )

            fix_version = ",".join(
                [fv.get_text(strip=True) for fv in issue.find_all("fix_version")]
            )

            description = _get_text(issue.find("description"))

            inspector_version = ",".join(
                [iv.get_text(strip=True) for iv in issue.find_all("inspector")]
            )

            row = [
                id,
                sil,
                mitigation,
                affected_version,
                fix_version,
                summary,
                description,
                published,
                updated,
                component,
                affected_toolchain,
                inspector_version,
            ]

            if len(XML_EXPORT_RECORD) != len(row):
                raise ValueError("ERROR: There might be an inconsistency with assumed XML structure.")

            # unpack list into PortalIssue
            entry = PortalIssue(*row)
            self._add_portal_issue(entry)

        return self._count_of_rows("PortalIssues")

    def get_list_of_detectable_issues(self) -> list:
        self.cur.execute("SELECT id FROM ReleaseNoteIssues ORDER BY id")
        return [id[0] for (id) in self.cur.fetchall()]

    def get_portal_issue(self, id: str) -> PortalIssue:
        """Search issue id in passed dataframe.
        Args:
            id (str): issue id, e.g. TCVX-xxxxx

        Returns:
            PortalIssue:  Record for the issue id or None when not found

            Note: Within current TASKING issue portal XML export no issue which was closed with won't fix is include ...
        """
        row = self.cur.execute(
            "SELECT * FROM PortalIssues WHERE id = ? ORDER BY id", (id,)
        ).fetchone()

        if row:
            return PortalIssue(*row)
        else:
            return None

    def get_release_note_issue(self, id: str) -> ReleaseNoteIssue:
        """Search issue id in ReleaseNoteIssues Table
        Args:
            id (str): issue id, e.g. TCVX-xxxxx

        Returns:
            ReleaseNoteIssue:  Record for the issue id or None when not found

            Note: For each issue which has a detector there is only one release note issue record ...
        """
        row = self.cur.execute(
            "SELECT * FROM ReleaseNoteIssues WHERE id = ? ORDER BY id", (id,)
        ).fetchone()

        if row:
            return ReleaseNoteIssue(*row)
        else:
            return None

    def get_issue(self, id: str) -> Issue:
        """_summary_

        Args:
            id (str): issue id, e.g. TCVX-xxxxx

        Returns:
            Issue: Record for the issue id or None when not found

            Note: The issue might only include partial information from release note.
        """
        ri = self.get_release_note_issue(id)
        pi = self.get_portal_issue(id)

        if pi and ri:
            pd = pi._asdict()
            rd = ri._asdict()
            # remove the common fields
            # CHECK we could assert here...
            del rd["id"]
            del rd["summary"]
            pd.update(rd)
            i = Issue(**pd)
            return i
        elif pi:
            pd = pi._asdict()
            i = Issue(**pd)
            return i
        elif ri:
            rd = ri._asdict()
            i = Issue(**rd)
            return i
        return None

    def is_issue_affecting_compiler_version(self, id: str, cv: str) -> bool:
        """Check if issue id is affecting a specific compiler version.

        Args:
            id (str): issue id, e.g. TCVX-xxxxx
            cv (str): compiler version to check, e.g. v6.3r1p7 or v6.3rp9

        Returns:
            bool: if issue affects compiler version. True if no data avilable available
            Note: Within current TASKING issue portal XML export no issue which was closed with won't fix is include ...
        """
        i = self.get_issue(
            id,
        )
        if i and len(i.affected_version) > 0:
            affected = i.affected_version.split(",")
            if cv in affected:
                return True
            else:
                return False

        # Safe approach:
        # - No affected version found in issue in database (because XML export is not including 'closed' issues)
        # or
        # - Issue not found in database (bogus key)
        return True
