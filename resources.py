"""
File:   resources.py 
Desc:   Function to find out the 'right' relative ressource path
        in all tested call scenarious (incl. one exe file deployment )

Copyright (C) 2022 Paul Himmler, Peter Himmler
Apache License 2.0
"""

import sys
import os


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


DEFAULT_CSS = resource_path("res/default.css")

FUNCTIONS_JS = resource_path("res/functions.js")

LOGO_BASE64_TXT = resource_path("res/logo_base64.txt")

LOGO_PNG = resource_path("res/logo.png")
