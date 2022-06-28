@echo BE AWARE that this will install a bunch of extra stuff directly in your python environment incl. optonal a C compiler ....


# Tested with 0.8.4 nuitka as  0.9 has a bug which hinders creating the onefile executable

pip install nuitka==0.8.4
pip install ordered-set
pip install zstandard

py -m nuitka --include-data-file=res/default.css=res/default.css --include-data-file=res/default.cfg=res/default.cfg --include-data-file=res/functions.js=res/functions.js --include-data-file=testdata/issue_portal_test_data.html=testdata/issue_portal_test_data.html --include-data-file=res/logo_base64.txt=res/logo_base64.txt --onefile il_conv.py
