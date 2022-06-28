<p>
  <img src="res/logo.png" width="20%">
</p>

A small tool to generate visually improved output from logs created by the Tasking inspector.

Features:
* [x] Relaxed parsing of log files created by the tasking inspector & compiler
* [x] Generation of xlsx output from parsed data
* [x] Command line input of files including options
* [x] Option to remove duplicates
* [x] Generation of HTML output from parsed data
* [x] HTML output styled by css stylesheet
* [x] Output in general configurable (hide/show columns, order)
* [x] Binary release (one file executable script) without own python installation

* [ ] Less hardcoding in table structure
* [ ] Allow more nicer names for the portal issues

Dependencies (install-dep.bat)

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

Know bugs: Test-Coverage low - but as it is a simple script, hack it yourself or create a nice request (ticket) and we might have a look :-d

Paul & Peter

Note: This script is as is, no notion of completeness or that it works under all cirumstances ...
