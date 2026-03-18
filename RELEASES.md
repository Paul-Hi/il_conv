<p>
  <img src="res/logo.png" width="20%">
</p>

# * unreleased *
* todo: parse dir, affected, unaffected out of extension of message

# *New* Version: v3.0 beta2
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

# Version: v2.3
- Fix:      #10 Correct mitigation when hovered over TCVX-keys
- Add:      #7 Resolved / check column added\  

# Version: v2.2 (release skipped)
- Fix:      #8 - relaxed naming of release notes
- Fix:      Wrong warnings

# Version: v2.1 
- Add:      Excel overview sheet
- Modified: Excel export now generate all variants into one workbook
- Modified: Remove formatting mode from cmdline options to simplify
- Fix:      Usual typos, verbose output with muliple log files
- Prepare:  Release v2.1 (skipping v2.0)
- 
# Version: v2.0 (release skipped)
- Removed: Parsing of Issue Portal website - no internet access required to use
- Added:   Importing issue information from user provided product specific XML file
- Added:   Importing of Inspector information from user provided product specific release notes.
- Modified: Replaced outdated python packages by Python core modules to support Python 3.13
- Modified: Command line options. NOTE: v2.0 is not compatible with past version on output and on CLI interface!
- Modified: Provide 3 different formatting options for XLSX output (compact, normal, expanded)
- Tested:   Assure compatiblity with current issue portal and XML export format as well Inspector log output.
