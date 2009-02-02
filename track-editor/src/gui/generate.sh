#!/bin/bash

pyuic4 track_editor.ui > autogen.py
pyuic4 track_tools.ui >> autogen.py

# fix plugins imports
sed -i s/"from tileeditor"/"from gui.qt.plugins.tileeditor"/ autogen.py
