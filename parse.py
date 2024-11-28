"""
File:   parse.py 
Desc:   Script functions to parse Tasking Compiler/Inspector output

Copyright (C) 2022 Paul Himmler, Peter Himmler
Apache License 2.0
"""


import tables
import re
import configs

TIMEDATE_KEY = configs.info['COLUMN_TIMEDATE'][0]
'''Key for timedates'''
TICKET_ID_KEY = configs.info['COLUMN_ISSUES_ID'][0]
'''Key for ticket ids'''
SEVERITY_KEY = configs.info['COLUMN_SEVERITY'][0]
'''Key for severities'''
MESSAGEEXT_KEY = configs.info['COLUMN_MESSAGEEXT'][0]
'''Key for message extensions'''
SOURCE_FILE_KEY = configs.info['COLUMN_SOURCE_FILE'][0]
'''Key for source files'''
SOURCE_LINE_KEY = configs.info['COLUMN_SOURCE_LINE'][0]
'''Key for source lines'''
SOURCE_COLUMN_KEY = configs.info['COLUMN_SOURCE_COLUMN'][0]
'''Key for source columns'''
COMMAND_KEY = configs.info['COLUMN_COMMAND'][0]
'''Key for commands'''
DIAG_MSG_KEY = configs.info['COLUMN_DIAG_MSG_NUMBER'][0]
'''Key for dialogue messages'''


def parse_file(file_name: str, configuration: configs.Config, verbose=False) -> tables.Table:
    '''Parses a file and returns a table with the rows

    Attributes:
        file_name (str): The file name of the file to parse (relative path)
        configuration (Config): The loaded configuration

    Returns:
        Table: A table with rows consisting of the parsed data
    '''

    lines = []
    with open(file_name, 'r') as file:
        lines = file.readlines()

    table = tables.Table()
    line_nr = 0
    current_row: tables.Row
    insplogFlag = False

    for line in lines:
        line_nr += 1
        # https://regex101.com/

        # "timestamp row"
        # 2021-08-04 13:40:16 # insp_ctc -E+comments -E-noline -c99 --fp-model=3cflnrSTz -D__CPU__=tc27x .....
        pat = r'(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d) # (.*)'
        matchObj = re.match(pat, line)
        if matchObj:
            # "timestamp row" -> empty new row
            current_row = tables.Row()

            # Store the timestamp
            current_row[TIMEDATE_KEY] = matchObj.group(1)
            # Store the command
            current_row[COMMAND_KEY] = matchObj.group(2).strip()

            insplogFlag = True
            continue

        # "message row"
        #        W998: ["C:\hugo~\.KOP\erica\a.h" 66/1] [INSP] detected potential occurrence of issue TCVX-44008. MAYBE EXTRA ...
        pat = r'(.*)(W\d\d\d|E\d\d\d):\s*\["(.*)"\s(\d*)[/](\d*)\]\s\[INSP\]\s(.+?)(TCVX-\d+)\.(.*)'
        matchObj = re.match(pat, line)

        if not insplogFlag:
            current_row = tables.Row()
            current_row[TIMEDATE_KEY] = '1970-01-01 00:00:01'
            current_row[COMMAND_KEY] = ''

        if matchObj:

            current_row[DIAG_MSG_KEY] = matchObj.group(2).strip()
            current_row[SOURCE_FILE_KEY] = configuration.cut_path(
                matchObj.group(3).strip())
            current_row[SOURCE_LINE_KEY] = matchObj.group(4)
            current_row[SOURCE_COLUMN_KEY] = matchObj.group(5)
            message = matchObj.group(6).strip()
            if message.find("detected potential occurrence") > -1:
                current_row[SEVERITY_KEY] = "potential impacted"
            elif message.find("detected occurrence") > -1:
                current_row[SEVERITY_KEY] = "impacted"
            else:
                current_row[SEVERITY_KEY] = "unclear result"
            current_row[TICKET_ID_KEY] = matchObj.group(7).strip()
            current_row[MESSAGEEXT_KEY] = matchObj.group(8).strip()
            table.append(current_row)
            current_row = tables.Row
            insplogFlag = False
            continue

        if verbose:
            print ("NO match in {0} line number {1} line !".format(file_name, line_nr) )
            # NOTE: --detect-asm=<specific issue> requires to more detailed look into your self -> therefore ignored!".format(file_name, line_nr) )
            # from now on I skip the ASM special detector lines ...

    return table
