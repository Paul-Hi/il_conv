"""
File:   il_conv.py
Desc:   Main script file

Copyright (C) 2022 Paul Himmler, Peter Himmler
Copyright (C) 2024 Peter Himmler
Apache License 2.0
"""

import argparse
from pathlib import Path
from issuedb import IssueDB
from parse import LogDB

import export
import export_xlsx
import export_html

VERSION_STR = "2.0 (beta)"


def parse_arguments() -> argparse.Namespace:
    '''Parses the command line arguments.

    Returns:
        Namespace: The namespace filled with all command line arguments

    '''
    parser = argparse.ArgumentParser(
        fromfile_prefix_chars='@',
        description='il_conv : Processes TASKING TriCore Inspector tool message and generate xlsx (Excel) report.',
        epilog='NOTE: If you want to pass a options file, pass filename with prepented  @ (like @foobar.txt),\
            the tool will read the content line by line and pass them as arguments to the tool itself.')

    parser.add_argument('-?', action='help',
                        default=argparse.SUPPRESS, help='show this help message and exit.')

    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s ' + VERSION_STR)

    parser.add_argument( '-v', '--verbose', 
                        help="Allows to get more verbose output from the tool", action='store_true')

    parser.add_argument("--output", type=str, default="insp_output",
                        help="A filename for the output file (without file extension). Default to '--output=insp_output'")

#    parser.add_argument("--output-format", dest='output_format', type=str, default="xlsx", choices=['XLSX', 'xlsx', 'HTML', 'html'],
    parser.add_argument("--output-format", dest='output_format', type=str, default="xlsx", choices=['XLSX', 'xlsx],
                        help="Generate output format (HTML not supported in this version) Default to '--output-format=xlsx'.")

    parser.add_argument("--format-mode", dest='format_mode', type=str, default="normal", choices=['COMPRESSED', 'NORMAL', 'EXPANDED'],
                        help="Set formatting mode, behaviour might not be available on all output formats (default: NORMAL)'.")

    parser.add_argument("-x", "--xmlfile", type=str, required=True,
                        help="Pass filename of issue portal xml export file.") 

    parser.add_argument("-r", "--relnotefile", type=str, required=True,
                        help="Pass used Inspector Release Notes file name <readme_tricore_<COMPVERSION>_inspector_<INSPVERSION>.html")
    
    parser.add_argument("logfile(s)", type=str, nargs='+',
                        help="One or more  input logfiles for processing." +
                        "E.g. dedicated created inspector log (--insp-log= ...) or normal inspector log output from your build!")

    args = parser.parse_args()

    return args


def il_conv():
    """Main working horse. Parse cmdline arguments, imports files, does some magic
        and generate ignore files.
    """     
    args = parse_arguments()

    # check release notes file name and derive compiler and inspector version from it
    relnote = Path(args.relnotefile)
    assert relnote.is_file, "ERROR: Passed release note file '{}' is not a file".format(relnote)
    stem = relnote.stem
    assert stem.startswith( "readme_tricore_"), "ERROR: Passed release note file name '{}' doesn't start with 'readme_tricore_'".format(relnote)
    
    compiler_version= stem[ len("readme_tricore_") : ]
    assert compiler_version.startswith("v6.2r2") or compiler_version.startswith("v6.3r1"), "ERROR: Passed release note file name compiler '{}' doesn't match 'v6.2r2' or 'v6.3r1'".format(relnote)
    compiler_version = compiler_version[ : len('v6.3r1') ]

    sidx = stem.rfind("v1.0r")
    assert sidx != -1 and sidx >= len("readme_tricore_v6.3r1_inspector" ) -1, "ERROR:"
    inspector_version = stem[ sidx : ]


    xmlfile = Path(args.xmlfile)
    assert xmlfile.is_file, "ERROR: Passed XML export file  '{}' is not a file".format(relnote)
    
    # generate
    db = IssueDB( compiler_version, inspector_version, xmlfile, relnote, args.verbose)
    
    num = db.importReleaseNote()
    if args.verbose:
        print(f"INFO: Import {num} rows of detector information.")
        
    num = db.importXMLFile()
    if args.verbose:
        print(f"INFO: Import {num} rows of portal issue information.")
    

    if not args.logfiles:
        print("Nothing todo...")
        return
    
    log_db = LogDB(args.verbose)
        
    if args.logfiles != None:
        for file in args.logfiles:
            print("... parsing file ", file, " ...")
            log_db.parse_log_file( file)

    fm = export.Formatmode[args.format_mode.upper()]
    output_fn = args.output + '-' + str(fm)[str(fm).find('.')+1:] + '.' + args.output_format.lower()
    
    if args.output_format == 'xlsx':                
        export_xlsx.generateExcel(output_fn, db, log_db, fm,  args.verbose)
    else:
        export_html.generateHTML( output_fn, db, log_db, fm, args.verbose)

if __name__ == "__main__":
    il_conv()
