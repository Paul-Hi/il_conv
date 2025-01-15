'''
File:   export.py 
Desc:   Generic types and stuff used for all exporters

Copyright (C) 2024 Peter Himmler
Apache License 2.0

'''

from issuedb import IssueDB, ReleaseNoteIssue, PortalIssue, Issue

from parse import LogDB, _DETECTION_RECORD_INFO, Detection


from enum import Enum
Formatmode = Enum('Formatmode', ['COMPACT', 'NORMAL', 'EXTENDED'])
