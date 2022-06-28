pip install pyinstaller

pyinstaller --noupx --add-data "style.css;res" --add-data "res/default.cfg;res" --add-data "res/functions.js;res" --add-data "testdata/issue_portal_test_data.html;testdata" --add-data "res/logo_base64.txt;res" --onefile il_conv.py

@echo If all works well you'll find the hugh binary in folder dist as il_conv.exe - should work also when you just copy this a different windows computer (selfcontained tool)


