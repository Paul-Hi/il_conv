"""
File:   parse.py 
Desc:   Script functions to parse Tasking Compiler/Inspector output

Copyright (C) 2022 Paul Himmler, Peter Himmler
Apache License 2.0
"""

import re
import os
from pathlib import Path 



from collections import namedtuple


_DETECTION_RECORD_INFO = [
                    #fieldname, idx / primary, default value
                    ('tstamp',      False, ''),
                    ('cmdline',      True, ''), # idx
                    ('diagmsgno',   False, ''),
                    ('filepath',     True, ''), # idx  
                    ('file',         True, ''), # idx
                    ('line',         True, ''), # idx
                    ('column',       True, ''), # idx
                    ('detectiontype',False,''), 
                    ('issueid',      True, ''), # idx
                    ('extension',   False, ''), 
                ]


DETECTION_RECORD = [ v for (v, pk, df) in _DETECTION_RECORD_INFO]
                
Detection = namedtuple( "Detection", DETECTION_RECORD,
                                defaults = ( '', '', '', '', '', '', '', '', '', '' ) )
'''Data type to store release note information per issue'''



import sqlite3

class LogDB(object):
    '''The LogDB stores all information we gather from log files passed.'''

    def __init__(self, verbose : False) :
        self.conn = sqlite3.connect(":memory:");#"log.db") #":memory:")
        self.curs = self.conn.cursor()
        self.verbose = verbose
        self._create_tables()
        
    def __del__(self):
        if self.conn:
            self.conn.close()
   
    def _create_tables(self): 
        cols = ','.join(["{} TEXT DEFAULT '{}'".format(n,dv) for (n, idx, dv) in _DETECTION_RECORD_INFO] + [" PRIMARY KEY ( "])
        cols += ','.join([ n for (n, idx, dv) in _DETECTION_RECORD_INFO if idx]) + ")"
        self.curs.execute("DROP TABLE IF EXISTS Logs");
        create = "CREATE TABLE IF NOT EXISTS Logs (" + cols + ")"                
        self.curs.execute(create)
        
        # create unique index
        #cols = [ v for (v, idx) in _DETECTION_RECORD_INFO if idx]
        #cols = ','.join(cols)
        #create = "CREATE UNIQUE INDEX IF NOT EXISTS Logs_idx ON Logs (" + cols + ")"
        #self.cur.execute(create)        
        self.conn.commit()
    
    def _add_log_entry(self, e : Detection):
        number_of_fields = len(Detection._fields)
        sql = "INSERT INTO Logs (" + ",".join(Detection._fields) + " ) " 
        sql += " VALUES ( " + ",".join(['?'] * number_of_fields) + " )"
    
        try:
            self.curs.execute( sql, (e.tstamp, e.cmdline, e.diagmsgno, e.filepath,
                                e.file, e.line, e.column, e.detectiontype, e.issueid, e.extension))
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

        if file_name != None:
            if self.verbose:
                print("INFO: Read passed log file '" + str(file_name)+ "'")
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
            # https://regex101.com/
            # "timestamp row"
            # 2021-08-04 13:40:16 # insp_ctc -E+comments -E-noline -c99 --fp-model=3cflnrSTz -D__CPU__=tc27x .....
            pat = r'(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d) # (.*)'
            matchObj = re.match(pat, li)
            if matchObj:
                # "timestamp row" -> empty new row
                if reusePreviousRow:
                    current_row = dict()

                # Store the timestamp
                tstamp = matchObj.group(1)
                # Store the command
                cmdline = matchObj.group(2).strip()

                reusePreviousRow = True
                continue

            # "message row"
            #        W998: ["C:\hugo~\.KOP\erica\a.h" 66/1] [INSP] detected potential occurrence of issue TCVX-44008. MAYBE EXTRA ...
            # E996: [<"full filename>" <line>/<column>] [INSP] detected potential occurrence of issue <id>
            # E997: [<"full filename>" <line>/<column>] [INSP] detected occurrence of issue <id>
            # W998: [<"full filename>" <line>/<column>] [INSP] detected potential occurrence of issue <id>
            # W999: [<"full filename>" <line>/<column>] [INSP] detected occurrence of issue <id>
            #
            #  gr2         gr3           gr4    gr5                   gr6                    gr7                gr8       
            # 
            pat = r'(.*)(W999|W998|E997|E996):\s*\["(.*)"\s(\d*)[/](\d*)\]\s\[INSP\]\s(.+?)(TCVX-\d+)\.(.*)'

            matchObj = re.match(pat, li)
                
            if matchObj:
                if not reusePreviousRow:
                    tstamp  = '1970-01-01 00:00:01'
                    cmdline = ''

                diagmsgno = matchObj.group(2).strip()
                fp = matchObj.group(3).strip()   ## TODO replace with Path
                fp = os.path.normpath(fp)
                fp = fp.replace('\\', '/')
                fp = os.path.normpath(fp)
                filepath = fp #configuration.cut_path(fp)
                file = os.path.basename(fp)
                line = matchObj.group(4)
                column = matchObj.group(5)
                message = matchObj.group(6).strip()
                if message.find("detected potential occurrence") > -1:
                    detectiontype = "potential affected"
                elif message.find("detected occurrence") > -1:
                    detectiontype = "affected"
                else:
                    assert False, "ERROR: Script is wrong - no unclear result possible!"
                    detectiontype = "unclear result"
                issueid = matchObj.group(7).strip()
                extension = matchObj.group(8).strip()
                
                e = Detection( tstamp, cmdline, diagmsgno, filepath, file, line, column, detectiontype, issueid, extension )
                self._add_log_entry( e )
                
                reusePreviousRow = False
                continue

            # "message row"
            # I991: [INSP] No definite or potential issues detected for the enabled list of
            pat = r'(.*)(I991):\s\[INSP\]\s(.*)'

            matchObj = re.match(pat, li)
            if matchObj:
                if not reusePreviousRow:
                    tstamp = '1970-01-01 00:00:02'
                    cmdline = ''

                diagmsgno = matchObj.group(2).strip()
                if diagmsgno.find("I991"):
                    if self.verbose:
                        print("IGNORE: no-issue-detected messages\n");

                reusePreviousRow = True
                continue

            # "message row"
            # I992: [INSP] asm cmp: <text>
            # E993: [INSP] detected change in assembly listing for command: <cmd>
            # W994: [INSP] detected change in assembly listing for command: <cmd>
            # E995: [INSP] problem with assembly comparison execution: <problem>
            #  gr2    gr3           gr4                              gr5   gr6
            pat = r'(.*)(I991|I992|E993|W994|E995):\s\[INSP\]\s(.+?)(:\s)(.*)'

            matchObj = re.match(pat, li)
            if matchObj:
                if not reusePreviousRow:
                    tstamp = '1970-01-01 00:00:03'
                    cmdline = ''

                diagmsgno = matchObj.group(2).strip()
                if diagmsgno.find("E993") or diagmsgno.find("W994"):
                    if self.verbose:
                        print("IGNORE: Detected change in assembler listing messages cmd {0}\n", matchObj.group(5))
                elif diagmsgno.find("I992"):
                    if self.verbose:
                        print("IGNORE: Asm cmp message. You want to manually evaluate / compare the generated files.\n")
                elif diagmsgno.find("E995"):
                    if self.verbose:
                        print("IGNORE: Problem identified with assembler comparison execution: {0}.\n", matchObj.group(5))
                reusePreviousRow = True
                continue            

        return 
