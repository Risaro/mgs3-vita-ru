#!/bin/bash
set -e
cd "$(dirname "$0")/.."
python3 build_font.py
python3 menu_strings.py
python3 widths.py
python3 reloc_strings.py
plugin/build.sh
