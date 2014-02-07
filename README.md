rtw
===

An interrupted attempt at improving the game Trailblazer (Commodore era...) with curves and slopes.

It's about 10K lines of Python2 code, written in a few months in 2009. Have a look at the media folder to see some screenshots and .ogg videos.

It used the [Panda3D](https://www.panda3d.org/) game engine and Qt for the desktop apps. 

![Screenshot]("screenshot.png?raw=true")


## Contents

**contrib**: contains a Python utility library I've written (mdlib) and 3rd party code.

**demos**: source code for some game demos.

**doc**: documentation files 

**editor**: source code for the world editor. I experimented with Qt, GTK, WxWindows, and the OpenGL based Panda3D direct window manager. I ended up choosing Qt.

**game**: game engine code, all Python with a few Cg shaders. 

**media**: screenshots and videos documenting the development.

**pipeline**: simple Python scripts to edit the tracks.

**track-editor**: a Python and Qt application used to prototype the 3D tracks. Check out track_editor_31_01_2009.ogg in the media to see what it looked like.
