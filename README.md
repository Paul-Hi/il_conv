<p>
  <img src="res/logo.png" width="20%">
</p>

A small tool to generate visually improved output from logs created by the TASKING Inspector.
Currently uses to main source of informations to create its output.
- Inspector tooling log file  or  the normaly Inspector compiler output file from console
- TASKING issue portal data, like the SIL currently assigned to the issue  (only accessible for paying cutomer)


## Example usage:
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FPaul-Hi%2Fil_conv.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FPaul-Hi%2Fil_conv?ref=badge_shield)


il_conv -?
 ...

il_conv --output-format=html log.txt

il_conv -u login@companyname.com -p password --output-format=xlsx log.txt log2.txt ...


## Features:
* [x] Command line tool
* [x] Generation of xlsx output from parsed inspector tooling output, enriched with some issue portal data
* [x] Generation of HTML output from parsed inspector tooling output, enriched with some issue portal data
* [x] HTML output styled by css stylesheet
* [x] Remove superfluos output (duplicate impact locations) generated by Inspector tool
* [x] Output in general configurable (hide/show columns, order, shortening source path)
* [x] Binary release (one file executable script) without own python installation

# Open
* [ ] Less hardcoding in table structure
* [ ] Allow more nicer names for the portal issues (hardcoded)
* [ ] Improve script design - not very well 
* [ ] Allow click-through from HTML and Excel to Ticket details
* [ ] Mid-Term - think about adding addition ticket details (currently only overview page of portal is parsed)

## Dependencies (install-dep.bat)
* Python 3.10
* openpyxl (*pip install openpyxl*)
* beautifulsoup4 (*pip install beautifulsoup4*)
* requests (*pip install requests*)
* Pillow (*pip install Pillow*)

In case you wanna build  the scripts into a onefile executable there are two  options
* pyinstaller based - not really support by us as startup is slow
* nuitka based - supported (see create_nuitka_exe.bat)

Beware that nuitka builds depends on a bunch of addtional things to be installed in addtion (e.g. gcc compiler) on the build machine
--> much easier is using the provided exe file from our release page

## Know bugs: 
Test-Coverage low - but as it is a simple script, hack it yourself or create a nice request (ticket) and we might have a look :-d

Paul & Peter

  
## This script is as is, no notion of completeness or that it works under all circumstances ...
  
### I'll not get payed for this work, so please be polite.
  




## License
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FPaul-Hi%2Fil_conv.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2FPaul-Hi%2Fil_conv?ref=badge_large)