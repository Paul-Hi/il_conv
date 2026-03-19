<p>
  <img src="res/logo.png" width="20%">
</p>

# * unreleased *
- Add: Public release notes of TASKING Inspector from vendor Website
- Add: Simple public test for release note parsing. 
- Add: Simple public test using test.log 
- Fix: Old style github action, forceing node v24
- Fix: Python 3.12 compatiblity on none-privat tests
- Add: github CI build on push
- Add: github release build on PR merged to master or 
  git tag v<version> && git push origin v<version>

# *New* Version: v3.0 beta3
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
