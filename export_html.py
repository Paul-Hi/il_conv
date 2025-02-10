'''
File:   export_html.py 
Desc:   Script function to export html
Maturity: Beta 

Copyright (C) 2024 Peter Himmler
Apache License 2.0
'''


from html import escape as pyhtml_escape

from issuedb import IssueDB
from parse import LogDB

from resources import LOGO_BASE64_TXT, DEFAULT_CSS, FUNCTIONS_JS


def generateHTML(output_file_name: str, db: IssueDB, log_db:LogDB, verbose: bool = False) :
    '''Generate HTML output.

    Args:
        output_file_name (str): The name of the file to save
        db (IssueDB): IssueDB from portal XML export related with Inspector release note
        log_db (LogDB): Database from parse log detection entries
        fm (FormatMode): Enum value to configure generator.
        verbose (bool): Create verbose output during processing
    '''

    if verbose:
        print("INFO: Generating HTML output.")

    order_arrows = '\n     <i class="fa fa-caret-up" aria-hidden="true"></i>\n     <i class="fa fa-caret-down" aria-hidden="true"></i>'

    #overwrite heading and styles for normal mode
    headings = ['File Name', 'File Path', "Detection" ,'Issue ID',
                'SIL',   'Fixed Version',
                'Summary',
                'Line', 'Column',
                "Description", 
                "Mitigation", 
                'detection type for line (\'d\' or \'p\'']
    # (type, size, visible, , td classes)
    col_style = [('string', False, True, 'c-file' ), 
                    ('string', True, True, 'c-filepath'),
                    ('string', False, True, ''),
                    ('hyper', False, True, 'c-issueid'),
                    ('string', False, True, 'c-sil'),
                    ('string', False, True, 'c-fixedversion'),
                    
                    ('string', False, True, 'c-summary'),
                    ('int', True, True, ''), ('int', True, True, ''),
                    ('string', False, False, 'c-desc'),
                    ('string', False, False, 'c-mitigation'),
                    ('string', True, True, ''),]
    
    assert (len(col_style) == len(headings))

    
    tr_ths_row = '''
<tr>
''' + '\n'.join( ['    <th class="draggable" draggable="true", data-type="{}"> {} {} </th>'.format(col_style[i][0], order_arrows, v) for i, v in enumerate(headings)] ) + '''
</tr>
'''

    # query log database 
    curs = log_db.conn.execute( "select file, filepath, issueid, line, column, detectiontype FROM Logs ORDER By rowid")
    tr_tds_rows = ''
    for (fn, fp, id, line, column, detection) in curs:
        ii = db.getIssue( id )
        assert ii is not None,  f'ERRRO: Log includes detected issue id but we have no information about it.\n{id} {fp} line'
        detection = detection.replace("potential affected", "p")
        detection = detection.replace("affected", "d")
        raw = map( lambda x: pyhtml_escape(x), [
                        fn, fp, ii.detectiontype, ii.id , ii.sil, ii.fix_version, ii.summary,
                        line, column, ii.description, ii.mitigation, detection])
        tr_tds_row = '''
<tr>
''' + '\n'.join([ '\n'.join( ['    <td class="{}", fulltext="{}">{}</td>'.format(col_style[i][3],v, v[0:80]) for i,v in enumerate(raw)] ) ]) + '''
</tr>
'''
        tr_tds_rows += tr_tds_row 


    with open(DEFAULT_CSS) as css:
        css_style = css.read()
    with open(FUNCTIONS_JS) as functions:
        js_functions = functions.read()
    with open(LOGO_BASE64_TXT) as img:
        image_b64 = img.read().strip().replace('\n', '')

    # logo_img = '\n<img src="logo.png" id="Logo" alt="IL Converter Logo" height="96px" width=auto>'
    logo_img = '<img src="data:image/png;base64,' + image_b64 + \
        '" id="Logo" alt="IL Converter Logo" height="96px" width=auto>'

    html_table = '''
 <div class="log-table">   
 <table class="log-table" id="log_table">
  <thead>
   ''' + tr_ths_row + '''
  </thead>
  <tbody>
   ''' + tr_tds_rows + '''
  </tbody>
 </table>
 </div>
 '''


    html = '''
<!DOCTYPE html>
<html>

 <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- <link rel="stylesheet" href="default.css"> -->
  <style>
  ''' + css_style + '''
  </style>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
  <!-- <script src="functions.js"></script> -->
  <script>
  ''' + js_functions + '''
  </script>
 </head>
 <body>
 '''+  logo_img + '''
 '''+  html_table + '''
 </body>
</html>
'''   

    if verbose:
        print(f"INFO: Write to file '{output_file_name}'")
    
    with open(output_file_name, "w") as output_file:
        output_file.write(html)
