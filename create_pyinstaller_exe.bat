pip install pyinstaller

pyinstaller --noupx --add-data "res/default.css;res" --add-data "res/functions.js;res" --add-data "res/logo_base64.txt;res" --add-data "res/logo.png;res" --onefile il_conv.py

@echo If all works well you'll find the hugh binary in folder dist as il_conv.exe - should work also when you just copy this a different windows computer (selfcontained tool)


