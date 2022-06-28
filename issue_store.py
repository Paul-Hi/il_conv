"""
File:   issue_store.py 
Desc:   Constants used for the Tasking Issue Portal

Copyright (C) 2022 Paul Himmler, Peter Himmler
Apache License 2.0
"""

from collections import namedtuple

###
### Constants for issue portal (state around 2022)
###

LOGIN_URL       = 'https://issues.tasking.com/cust_login'
'''Url tasking issues login'''
LOGIN_REDIRECT_URL  = 'https://issues.tasking.com/cust_redirect.php'
'''Url tasking issues login redirect'''
PROJECT         = 'TCVX' # and might be other
'''Project name'''

HEADER_ENTRIES  = [
                    'issue_id',
                    'issue_sil',
                    'issue_summary',
                    'issue_created',
                    'issue_updated',
                    'issue_component',
                    'affected_toolchains',
                    'issue_inspector'
                ]
'''Names of issue headers'''

HEADER_TYPES    = [
                    "string",
                    "string",
                    "string",
                    "datetime;%Y-%m-%d",
                    "datetime;%Y-%m-%d",
                    "string",
                    "string",
                    "string"
                ]
'''Types of issue headers'''
HEADER_ENTRIES_NO = len(HEADER_ENTRIES);
'''Number of issue header entries'''



# export namdtuple data type for web based issue information
Portalissue = namedtuple( "Portalissue", HEADER_ENTRIES, defaults = ( '', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'No') )
'''Data type to store website issue information per issue'''


Issuestore = dict #(str, Portalissue)
'''The Issuestore is a dictionary holding all issue entries'''
