'''
File:   export_xlsx.py 
Desc:   Script function to xlsx

Copyright (C) 2024 Peter Himmler
Apache License 2.0
'''

from ast import Dict
from datetime import datetime

import openpyxl
import openpyxl.styles
import openpyxl.worksheet.table as xltables
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.cell_range import CellRange
from openpyxl.styles import Font, Alignment
'''
from openpyxl.worksheet import dimensions
'''

from resources import LOGO_PNG

from issuedb import IssueDB, ReleaseNoteIssue, PortalIssue, Issue

from parse import LogDB, _DETECTION_RECORD_INFO, Detection


from export import Formatmode


def generateExcel(output_file_name: str, db: IssueDB, log_db:LogDB,  
            fm : Formatmode = Formatmode.NORMAL, verbose: bool = False) :
    '''Generate Excel output.

    Args:
        output_file_name (str): The name of the file to save
        db (IssueDB): IssueDB from portal XML export related with Inspector release note
        log_db (LogDB): Database from parse log detection entries
        fm (FormatMode): Enum value to configure generator.
        verbose (bool): Create verbose output during processing
    '''

    if verbose:
        print("INFO: Generating Excel Workbook")

    wb = Workbook()
    wb.iso_dates = True
    ws = wb.active
    ws.title = "INSPECTOR Report"

    # dict of filename to filepath mapping
    fn2fp = {}


    if fm == Formatmode.COMPRESSED:
        headings = ['File Name', 'File Path', "Detector" ,'Issue ID',
                    'SIL',   'Fixed Version', 'Summary', "Description", 
                    "Mitigation", 'Lines', 'detection type for each line in lines (\'d\' or \'p\')']
        # (type, Autofit, visible, , autofit max chars)
        col_style = [('file', False, True, -1),  ('string', True, False, 40),  ('string', False, True, -1),  ('hyper', False, True, 10),
                        ('string', False, True, -1),  ('string', False, True, -1), ('string', False, True, 60), ('string', False, False, 60),
                        ('string', False, False, 60), ('string', True, True, -1), ('string', True, False, -1)
                        ]
        # Add headings
        ws.append(headings)

        curs = log_db.conn.execute( "select file, filepath, issueid, group_concat(line), group_concat(detectiontype) FROM Logs GROUP By filepath, issueid ORDER BY file, issueid")
    
        for (fn, fp, id, lines, detections) in curs:
            
            if fn2fp.get(fn) != None and fn2fp[fn]!=fp:
                print(f"WARN: Your project seems to have multiple times file '{fn}' in different folders, you should use expaned format and looking at the full pathname within the report.")
            fn2fp[fn] = fp
            
            
            #print (row)
            ii = db.getIssue( id )

            assert ii != None,  f"ERROR: Log includes detected issue id '{id}' in file '{fp}'but we have no information about it."
        
            detections = detections.replace("potential affected", "p")
            detections = detections.replace("affected", "d")
            
            csvrow = [fn, fp, ii.detectiontype, ii.id , ii.sil, ii.fix_version, ii.summary, ii.description, 
                        ii.mitigation, lines, detections]
            
            ws.append(csvrow)
    
    elif fm == Formatmode.NORMAL:
        #overwrite heading and styles for normal mode
        headings = ['File Name', 'File Path', "Detector" ,'Issue ID',
                    'SIL',   'Fixed Version', 'Summary', "Description", 
                    "Mitigation", 'Line', 'Column', 'detection type for line (\'d\' or \'p\')']
        
        col_style = [('file', False, True, -1),  ('string', True, False, 40),  ('string', False, True, -1),  ('hyper', False, True, 10),
                        ('string', False, True, -1),  ('string', False, True, -1), ('string', False, True, 60), ('string', False, False, 60),
                        ('string', False, False, 60), ('string', True, True, -1), ('string', True, True, -1), ('string', True, False, -1)
                        ]

        # Add headings
        ws.append(headings)

        curs = log_db.conn.execute( "select file, filepath, issueid, line, column, detectiontype FROM Logs ORDER By file, rowid")
    
        for (fn, fp, id, line, column, detection) in curs:
            
            fn2fp[fn] = fp
            
            ii = db.getIssue( id )

            assert ii != None,  f'ERRRO: Log includes detected issue id but we have no information about it.\n{id} {fp} line'
        
            detection = detection.replace("potential affected", "p")
            detection = detection.replace("affected", "d")
            
            csvrow = [fn, fp, ii.detectiontype, ii.id , ii.sil, ii.fix_version, ii.summary, ii.description, 
                        ii.mitigation, line, column, detection]
            
            ws.append(csvrow)

    elif fm == Formatmode.EXPANDED:
        headings = ['File Name', 'File Path', "Detector" ,'Issue ID',
                    'SIL',   'Fixed Version', 'Summary', "Description", 
                    "Mitigation", 'Line', 'detection type for line (\'d\' or \'p\')']
        # (type, Autofit, visible, , autofit max chars)
        col_style = [('file', False, True, -1),  ('string', True, True, 40),  ('string', False, True, -1),  ('hyper', False, True, 10),
                        ('string', False, True, -1),  ('string', False, True, -1), ('string', False, True, 60), ('string', False, False, 60),
                        ('string', False, True, 60), ('string', True, True, -1), ('string', True, False, -1)
                        ]
        # Add headings
        ws.append(headings)

        curs = log_db.conn.execute( "select file, filepath, issueid, line, column, detectiontype FROM Logs ORDER By file, issueid, line")
    
        for (fn, fp, id, line, detection) in curs:
            fn2fp[fn] = fp
            
            ii = db.getIssue( id )

            assert ii != None,  f'ERRRO: Log includes detected issue id but we have no information about it.\n{id} {fp} line'
        
            detection = detection.replace("potential affected", "p")
            detection = detection.replace("affected", "d")
            
            csvrow = [fn, fp, ii.detectiontype, ii.id , ii.sil, ii.fix_version, ii.summary, ii.description, 
                        ii.mitigation, line, detection]
            
            ws.append(csvrow)



    
    # calculate max # of character for all columns
    max_chars = []
    for col in ws.iter_cols(min_row=1, max_col=ws.max_column):
        max_chars.append(max(len(str(cell.value)) for cell in col))

    # define dimension and style of column
    dim_holder = ws.column_dimensions
    for i, col in enumerate(ws.iter_cols(min_row=1, max_col=ws.max_column, max_row=1)):
        #        for column_cells in ws['A:H']:
        _, _, _, pro_chars = col_style[i]
        column_letter = get_column_letter(col[0].column)

        if pro_chars == - 1:
            pro_chars = max_chars[i]

#        ws.column_dimensions[column_letter].hidden = not visible
        dim_holder[column_letter].width = min(100, (pro_chars + 2) * 1.23)

    # we know the table starts at column A, so we can use the types
    dim_holder = ws.column_dimensions
    types, autofits, visiblities, maxchars = list(zip(*col_style))
    for i in range(0,len(types)):
        type_str = types[i]
        column_letter = (get_column_letter(i+1))
                
        dim_holder[column_letter].hidden = not visiblities[i]

        for cell in ws[column_letter][1:]:
            
            cell.alignment = Alignment(wrap_text=autofits[i])

            cell.number_format = openpyxl.styles.numbers.FORMAT_TEXT
            if "file" in type_str:
                try:
                    ii = db.getIssue(id)
                    cell.comment = openpyxl.comments.Comment(
                        'HINT (file name might not have a unique path in your project):\n{}'.format(fn2fp[cell.value]), "generated", 100,640)
                except:
                    pass
            elif "datetime" in type_str:
                try:
                    cell.value = datetime.strptime(
                        cell.value, type_str.split(';')[-1])
                except:
                    pass
                cell.number_format = openpyxl.styles.numbers.FORMAT_DATE_DDMMYY

            elif "int" in type_str:
                try:
                    cell.value = int(cell.value)
                except:
                    pass
                cell.number_format = openpyxl.styles.numbers.FORMAT_NUMBER
            elif "hyper" in type_str:
                try:
                    cell.style = 'Hyperlink'
                    ii = db.getIssue(id)
                    cell.comment = openpyxl.comments.Comment('MITIGATION:\n{}'.format(ii.mitigation), "generated", 400,520)
                    cell.hyperlink = 'https://issues.tasking.com/?issueid={}'.format(cell.value)
                except:
                    pass

    
    cell_range = CellRange(min_col=1, min_row=2, max_col=ws.max_column, max_row=ws.max_row+1)

    tab = xltables.Table(displayName="Data", ref=str(cell_range))

    style = xltables.TableStyleInfo(name="TableStyleLight9")

    tab.tableStyleInfo = style
    ws.add_table(tab)

    ws.insert_rows(1)

    img = openpyxl.drawing.image.Image(LOGO_PNG)
    img.anchor = 'A1'
    img.width = 48
    img.height = 48
    ws.add_image(img)
    openpyxl.comments.Comment

    ws.row_dimensions[1].height=None # get dimension for row 3
    ws['E1'] = 'INSPECTOR Report.'
    ws['E1'].font = Font(bold=True, size=26)
    now = "Generated: " + datetime.today().isoformat() 
    ws['C1'] = now
    ws['C1'].number_format = openpyxl.styles.numbers.FORMAT_TEXT
    ws['C1'].font = Font(bold=True, size=9)

    if verbose:
        print(f"INFO: Write to file '{output_file_name}'")
    
    wb.save(filename=output_file_name)


