<p>
  <img src="res/logo.png" width="20%">
</p>

# *New* Version: v3.0beta4
- Add: Public release notes of TASKING Inspector from vendor Website
- Add: Simple public test for release note parsing. 
- Add: Simple public test using test.log 
- Fix: Old style github action, forceing node v24
- Fix: Python 3.12 compatiblity on none-privat tests
- Add: github CI build on push
- Add: github release build on PR merged to master or 
       git tag v<version> && git push origin v<version>
- Add;      Vibe code unit & integration tests (partially privat test data not commited to OSS).
- Modified: Correct RegExp handling in general and improve info verbose logging
- Modified: RegExp to parse new inspector log messages incl. dir/affect/unaffect when assembly is different
- Fix:      Issues around static typing and inconsistent documentation
- Removed:  Remove normal sheet generation from Excel output. The workbook now produces only compact and extended report sheets.
- Fix:      Circular dependency by extracting VERSION_STR to version.py
- Fix:      Undiscovered use of none-existing Formatmode.COMPRESSED 
- Fix:      2 glitch logic errors, bare excepts, None checks, and assertions ()
            - replace .find() with `in` operator
            - replace bare `except:` with specific exception types
            - add _get_text() helper for safe BeautifulSoup tag access
            - replace assert with raise ValueError throughout
            - fix is_file (method ref) -> is_file() (call)
- Modified: Extract regex patterns to module-level compiled constants with named groups
- Modified: Some more PEP 8 compliance with naming

# Version: v3.0 beta
- Fix:      #12 Hyperlinks might not target the correct issue URL
- Add:      Support for upcoming automated execution of assembly files generated with and without bug fix applied
- Add:      Prepare for Inspector tools supporting different compiler version
- Modified: Update documentation, incl. now examples how to download XLM export files automated as TASKING customer.
**NOTE: The resolved / check column is not preserved during runs.**\
Might be a feature in future.

**[Release list](RELEASES.md)**

# **il_conv** (**I**nspector **L**og **conv**erter)
A small tool to generate Excel  report (xlsx file) enriched with all known issue information incl. direct links to latest information about each known issue from TASKING's issue portal.  
Please adapt the output to whatever format you need for your errata management approach you follow at your company. If you like you can propose new formats (issue and/or pull request) to our project and we are happy to integrate them.

## Pre-requisites
The tool requires certain input files to generate the a meaningfull report.  
You need
1. To be a user of a TASKING compiler with a valid license.
2. To be a user of the TASKING TriCore Inspector with a valid license.
3. To have login access to TASKING issue portal for the respective TASKING compiler version,
   - To export XML data file manually (Button: XML Export)  
     or
   - To frequently download the XML data file automatically, e.g. on Windows with
   > \> wget --save-cookies cookies.txt --keep-session-cookies --post-data "login_username=**ABCD@youraccount.com**&secretkey=**PASSWORD**" -O NUL "https://issues.tasking.com/cust_redirect.php"
     \>  
     \> wget --load-cookies cookies.txt --content-disposition "https://issues.tasking.com/?project=TCVX&version=v6.3r1&o=xml"  
     \> wget --load-cookies cookies.txt --content-disposition "https://issues.tasking.com/?project=TCVX&version=v6.2r2&o=xml"  
4. The release notes of your used TASKING Inspector version (e.g. 'readme_tricore_v6.3r1_inspector_v1.0r7.html').  
   You can find that in TASKING website or on the installation tree of the TASKING Inspector product.
5. To integrated and execute the TASKING Inspector 'compiler' within your build environment. During execution you have to gathered detection warnings from the analysis of your source code.  
   **Tip:** Option '--inspector-log=<absolute-filename>' passed to the Inspector compiler toolchain helps you to gather all relevant output in one file.
   
## Background:
TASKING Inspector products are modified TASKING C/C++ compiler. Inspector helps a compiler user to evaluate if he might be impacted by a know issue of the compiler and to decided if and how to mitigate the issue. Generally such an impact analyise takes place in all safety related system & software development to be confident that system/software already release or where a update is in-development can't lead to a a safety critical malfunction for the (end)-user.

Examples of a mitigation when potential issue is detect:
- Use a newer compiler version or latested patch version which most probably already have the detected issue fixed.
- Change command line option or enable / disable specific compiler option functionlity local to a function or file.
- Change / Modify source code to avoid triggering the known issue.
- Proof that potential malfunction of application area is acceptable, e.g. can't lead to a safety critical malfunction  
...

### How does it work?
TASKING customer run the Inspector 'compiler' like the normal compiler from TASKING and get an enriched log output which shows the location (issue detected, filename, line, column).

## Example usage:
```
$ il_conv -?
...
$ il_conv -v -x issues_tasking_TCVX_v6.3r1.xml -r readme_tricore_v6.3r1_inspector_v1.0r6.html logfile.txt
```
Note:  
- 'issues_tasking_TCVX_v6.3r1.xml               == XML export from the issue portal
- 'readme_tricore_v6.3r1_inspector_v1.0r7.html' == Release note for your Inspector version
- logfile.txt                                   == one or several file which have inspector detection messages gathered for you build.

## Features:
- [x] Command line tool
- [x] Can use all published information from TASKING issue portal (XML export to be done by user)
- [x] Use the latest information available for detection (from readme/release note of the respective Inspector)
- [x] Generate one XLSX workbook report with one cover sheet + 3 data sheets (compact, normal, extended) based on user feedback :-)
  - **compact:** File, Filepath (hidden), Issue ID, SIL, Fixed Compiler Version, Summary, Description (hidden), Mitigation (hidden), Lines, detection types (hidden)
  Note: multiple occurences of detection gets collapsed in one line (customer request)  
  - **normal:** File, Filepath (hidden), Issue ID, SIL, Fixed Compiler Version, Summary, Description (hidden), Mitigation (hidden), Line, Column, detection type (hidden) 
  - **extended:** same like normal but all visible beside detection type
- [x] Hover over Issue ID shows Mitigation if any
- [x] Remove superfluos output (duplicate impact locations) potentially generated by Inspector tool
- [x] Binary release possible (one file executable script) without own python installation
- [x] Click-through from XLSX Issue ID  

## Limitation: 
Note:
 - There might be several 'doublicate' detections (same filename, same column and line) or (same filename butdifferent file system access paths, same column and line).
 - **il_conv** tool tries to warn you about that fact and ask you to look more deep into your source structure that you do not require to analyse detections to many times.
 > WARN: Your project seems to have multiple times file 'Os_Timer.h' in different folders, you should use expanded format and looking at the full pathname within the report
 This is oftent detected when you include header files via relative different files path from the view of the compile unit. 
  
 - The resulting Excel reports therefor might include 
   - **Compact report** - doublicate number for the same file / row
   - **Normal, Extended** - doublicate detection in different rows
   
## Know bugs: 
- none :-)
  It's a pretty simple script, hack it yourself or create a nice feature / bug ticket for us and we might have a look :-d

## Dependencies (pip -r requirements.txt)
In case you wanna *use* the python scripts, you have to at least install python and the for dependencies.

- Python 3.10 or later
- openpyxl
- Pillow
- beautifulsoup4
  - lxml 
- ~~requests~~
- ~~numpy~~
- ~~datatable~~

In case you wanna build the scripts into a onefile executabe
- nuitka based - supported (see create_nuitka_exe.bat on windows)

Be aware that nuitka builds depends on a bunch of addtional things to be installed in addtion (e.g. gcc compiler) on the build machine
--> much easier is using the provided exe file from our release page

Paul & Peter

**Note:** 
This script is as is, no notion of completeness or that it works under all circumstances ...
### We'll get not payed for that work it's just for fun, so please be polite.
