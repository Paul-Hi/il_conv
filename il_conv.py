"""
File:   il_conv.py
Desc:   Main script file

Copyright (C) 2022 Paul Himmler, Peter Himmler
Apache License 2.0
"""


import argparse
import tables
import export
import issuedb
from configs import get_defaultcfg, Config
from issue_store import Issuestore
from resources import resource_path
from parse import parse_file
import os

VERSION_STR = "0.99"


def parse_arguments() -> argparse.Namespace:
    '''Parses the command line arguments.

    Returns:
        Namespace: The namespace filled with all command line arguments

    '''

    parser = argparse.ArgumentParser(
        fromfile_prefix_chars='@',
        description='il_conv : preprocess and convert TASKING TriCore Inspector tool message Excel or HTML file.',
        epilog='NOTE: If you want to pass a options file, pass filename with prepented  @ (like @foobar.txt),\
            the tool will read the content line by line and pass them as arguments to the tool itself.')

    parser.add_argument('-?', action='help',
                        default=argparse.SUPPRESS, help='show this help message and exit.')

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + VERSION_STR)

    parser.add_argument(
        '-v', '--verbose', help="Allows to get more verbose output from the tool", action='store_true')

    parser.add_argument("-tc", "--toolset", type=str, default="v6.2r2", choices=['v6.2r2', 'v6.3r1'],
                        help="toolset/compiler toolchain version to lookup on issue portal." +
                        "Default to 'v6.2r2")

    parser.add_argument("--output-format", dest='output_format', type=str, default="xlsx", choices=['xlsx', 'html'],
                        help="Generate output format. Default to '--output-format=xlsx'.")

    parser.add_argument("--output", type=str, default="insp_output",
                        help="A filename for the output file (without file extension). Default to '--output=insp_output'")

    parser.add_argument("-u", "--user", type=str, default="",
                        help="This holds the user name from your login credential of the TASKING issue portal), default is ''")

    parser.add_argument("-p", "--password", type=str, default="",
                        help="Pass your  password for your account on TASKING issue portal, default is ''")

    parser.add_argument("-x", "--xmlfile", type=str, default="",
                        help="Pass filename of issue portal xml export, default is ''")

    parser.add_argument(
        "--dump-defaultcfg", help="Dumps default configuration and exit immediately.", action='store_true')

    parser.add_argument("--config", type=str,
                        help="Export configuration file, allowing to select column and order for export.")

    parser.add_argument("logfiles", type=str, nargs='*',
                        help="One or more  input logfiles for processing." +
                        "Dedicated created inspector log (--insp-log= ...) or normal  tools output where all unrelatede diagnostic messages are skipped!")

    args = parser.parse_args()

    return args


def il_conv():
    args = parse_arguments()

    if args.dump_defaultcfg:
        print(get_defaultcfg())
        return

    if not args.logfiles:
        print("Nothing todo...")
        return

    configuration = Config(args.config)

    table = tables.Table()

    if args.logfiles != None:
        for file in args.logfiles:
            print("... parsing file ", file, " ...")
            table.extend(parse_file(file, configuration, args.verbose))

    table.remove_duplicates()
    if args.verbose:
        print("... removing duplicates")

    db = Issuestore()

    if ((args.user != "") and (args.password != "")):
        # try website
        db = issuedb.populateDBFromIssuePortal(
            args.user, args.password, args.toolset, args.verbose)
    elif (args.xmlfile != ""):
        db = issuedb.populatIssueDBFromXMLFile(args.xmlfile, args.verbose)
    else:
        portal_test_data = os.path.join(
            resource_path('testdata'), 'issue_portal_test_data.html')
        db = issuedb.populatIssueDBFromFile(
            portal_test_data, args.toolset, args.verbose)

    if args.output_format == 'xlsx':
        exporter = export.ExcelExporter()
    else:
        exporter = export.HTMLExporter()

    print("Exporting to " + args.output + "." + args.output_format+" ...")
    exporter.export(table, args.output, configuration, args.verbose, db)


if __name__ == "__main__":
    il_conv()
