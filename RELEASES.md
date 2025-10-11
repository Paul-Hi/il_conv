<p>
  <img src="res/logo.png" width="20%">
</p>

# * unreleased *
* todo: parse dir, affected, unaffected out of extension of message

# *New* Version: v3.0 beta
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
- Modified: Provide 3 different formatting options for XLSX output (compressed, normal, expanded)
- Tested:   Assure compatiblity with current issue portal and XML export format as well Inspector log output.
